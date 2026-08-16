<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import {
  AppstoreOutlined,
  CheckCircleFilled,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  EyeOutlined,
  FileTextOutlined,
  SearchOutlined,
  SettingOutlined,
  SyncOutlined,
} from '@ant-design/icons-vue'
import dataEmptyImg from '@/assets/data_empty.png'
import SplitPane from '@/components/SplitPane/SplitPane.vue'
import {
  getADCCiTypes,
  getAdc,
  updateADCAccept,
  getADCCiTypesAttrs,
  deleteAdc,
  getAdcExecHistories,
  getAdcById,
  deleteAdcExecHistories,
} from '@/modules/cmdb/api/discovery'
import { getSystemConfig, saveSystemConfig } from '@/modules/cmdb/api/system_config'
import { getCITableColumns, cloneDeep } from '@/modules/cmdb/utils/helper'
import AdcCounter from './components/adcCounter.vue'
import PasswordField from './components/passwordField.vue'
import RawDataModal from './components/rawDataModal.vue'

const { t } = useI18n()

const paneLengthPixel = ref(204)
const windowHeight = computed(() => window.innerHeight)
const tableHeight = computed(() => windowHeight.value - 240)

const ci_types_list = ref<any[]>([])
const currentType = ref<number | null>(null)
const attributes = ref<any[]>([])
const tableData = ref<any[]>([])
const columns = ref<any[]>([])
const selectedRowKeys = ref<any[]>([])
const searchValue = ref('')
const logModalVisible = ref(false)
const logTextArray = ref<string[]>([])
const showLogConfig = ref(false)
const execLogTypes = ref<string[]>(['add', 'update', 'delete', 'accept'])
const logConfigSaving = ref(false)
const logClearing = ref(false)
const acceptByFilters = ref<any[]>([])
const selectedCount = ref(0)
const loading = ref(false)
const loadTip = ref('')

const xTableRef = ref<any>()
const rawDataModalRef = ref<InstanceType<typeof RawDataModal>>()
const logModelText = ref<HTMLElement>()

const filterTableData = computed(() => {
  const value = searchValue.value
  if (value) {
    const searchProps = attributes.value.map((item) => item.name)
    const rest = tableData.value.filter((item) =>
      searchProps.some((key: string) => String(item[key] ?? '').toLowerCase().indexOf(value.toLowerCase()) > -1)
    )
    return rest
  }
  return tableData.value
})

/** Approximate rendered width of a value (drop-in for the legacy helper). */
function strLength(fData: unknown): number {
  if (!fData) return 0
  let value: unknown = fData
  if (Array.isArray(value)) {
    value = value.join(' ')
  }
  const str = String(value)
  let intLength = 0
  for (let i = 0; i < str.length; i++) {
    if (str.charCodeAt(i) < 0 || str.charCodeAt(i) > 255) {
      intLength += 2
    } else {
      intLength += 1
    }
  }
  return Math.floor(intLength * 7)
}

function uniqBy(list: any[], key: string): any[] {
  const seen = new Set()
  const result: any[] = []
  list.forEach((item) => {
    const v = item[key]
    if (!seen.has(v)) {
      seen.add(v)
      result.push(item)
    }
  })
  return result
}

async function clickSidebar(id: number) {
  currentType.value = id
  attributes.value = await getADCCiTypesAttrs(currentType.value)
  loadAdc(true)
  selectedRowKeys.value = []
  xTableRef.value?.clearCheckboxRow()
  xTableRef.value?.clearCheckboxReserve()
  xTableRef.value?.clearSort()
}

function loadAdc(isInit?: boolean) {
  loading.value = true
  loadTip.value = t('loading')

  getAdc({
    type_id: currentType.value,
    page_size: 100000,
  })
    .then((res: any) => {
      const $table = xTableRef.value
      if ($table) {
        const nameColumn = $table.getColumnByField('accept_by')
        if (nameColumn) {
          const filters = uniqBy(
            (res.result || [])
              .filter((item: any) => item.accept_by)
              .map((item: any) => ({
                value: item.accept_by,
                label: item.accept_by,
              })),
            'value'
          )
          $table.setFilter(nameColumn, filters)
          acceptByFilters.value = filters
        }
      }
      tableData.value = (res.result || []).map((item: any) => ({ ...cloneDeep(item), ...item.instance }))
      if (isInit) {
        columns.value = getColumns(tableData.value, attributes.value)
        xTableRef.value?.refreshColumn()
      }
    })
    .finally(() => {
      loading.value = false
    })
}

function getColumns(data: any[], attrList: any[]): any[] {
  const el = document.getElementById('discovery-ci')
  const width = el ? el.clientWidth - 50 : 1600
  const cols = getCITableColumns(data, attrList, width)
  // getCITableColumns sizes columns from the cell data only; when the header
  // title is wider than the data (e.g. short id, Chinese aliases) vxe-table
  // ellipsizes the header. Give each column a width that fits its title plus padding.
  cols.forEach((col: any) => {
    const headerWidth = strLength(col.title) + 50
    if (col.width === undefined || col.width < headerWidth) {
      col.width = headerWidth
    }
  })
  return cols
}

function accept(row: any) {
  selectedRowKeys.value = []
  xTableRef.value?.clearCheckboxRow()
  xTableRef.value?.clearCheckboxReserve()
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ad.confirmAccept'),
    onOk() {
      updateADCAccept(row.id).then(() => {
        message.success(t('cmdb.ad.acceptSuccess'))
        loadAdc(false)
      })
    },
  })
}

function deleteADC(row: any) {
  selectedRowKeys.value = []
  xTableRef.value?.clearCheckboxRow()
  xTableRef.value?.clearCheckboxReserve()
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ad.deleteADC'),
    onOk() {
      deleteAdc(row.id).then(() => {
        message.success(t('deleteSuccess'))
        loadAdc(false)
      })
    },
    onCancel() {},
  })
}

async function viewADC(row: any) {
  const res = await getAdcById(row.id)
  rawDataModalRef.value?.open(res || {})
}

async function batchAccept() {
  let successNum = 0
  let errorNum = 0
  loading.value = true
  loadTip.value = t('cmdb.ad.batchAccept')

  for (let i = 0; i < selectedRowKeys.value.length; i++) {
    await updateADCAccept(selectedRowKeys.value[i])
      .then(() => {
        successNum += 1
      })
      .catch(() => {
        errorNum += 1
      })
      .finally(() => {
        loadTip.value = t('cmdb.ad.batchAccept2', {
          total: selectedRowKeys.value.length,
          successNum,
          errorNum,
        })
      })
  }

  loading.value = false
  loadTip.value = ''
  selectedRowKeys.value = []
  loadAdc(false)
  xTableRef.value?.clearCheckboxRow()
  xTableRef.value?.clearCheckboxReserve()
  xTableRef.value?.clearSort()
}

function batchDelete() {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ad.batchDelete'),
    onOk: () => {
      batchDeleteAsync()
    },
  })
}

async function batchDeleteAsync() {
  let successNum = 0
  let errorNum = 0
  loading.value = true
  loadTip.value = t('cmdb.ci.batchDeleting')

  for (let i = 0; i < selectedRowKeys.value.length; i++) {
    await deleteAdc(selectedRowKeys.value[i])
      .then(() => {
        successNum += 1
      })
      .catch(() => {
        errorNum += 1
      })
      .finally(() => {
        loadTip.value = t('cmdb.ci.batchDeleting2', {
          total: selectedRowKeys.value.length,
          successNum,
          errorNum,
        })
      })
  }

  loading.value = false
  loadTip.value = ''
  selectedRowKeys.value = []
  loadAdc(false)
  xTableRef.value?.clearCheckboxRow()
  xTableRef.value?.clearCheckboxReserve()
  xTableRef.value?.clearSort()
}

function onSelectChange({ records }: any) {
  selectedRowKeys.value = records.map((item: any) => item.id)
}

function handleSearch(value: string) {
  searchValue.value = value
}

async function clickLog() {
  logModalVisible.value = true
  showLogConfig.value = false

  const [logRes, configRes] = await Promise.all([
    getAdcExecHistories({
      type_id: currentType.value,
      last_size: 1000,
    }),
    getSystemConfig({ name: 'auto_discovery_exec_log_types' }).catch(() => null),
  ])

  if (configRes?.option?.v) {
    execLogTypes.value = configRes.option.v
  } else {
    execLogTypes.value = ['add', 'update', 'delete', 'accept']
  }

  let logArray: string[] = []
  if (logRes?.result?.length) {
    logArray = logRes.result.map((log: any) => {
      return `[${log.created_at}] ${log.stdout}`
    })
  }
  logTextArray.value = logArray
  nextTick(() => {
    const textEl = logModelText.value
    if (textEl) {
      textEl.scrollTop = textEl.scrollHeight
    }
  })
}

async function handleLogTypesChange(checkedValues: any[]) {
  logConfigSaving.value = true
  try {
    await saveSystemConfig({
      name: 'auto_discovery_exec_log_types',
      option: { v: checkedValues },
    })
  } finally {
    logConfigSaving.value = false
  }
}

function clearLogs() {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ad.confirmClearLog'),
    onOk() {
      logClearing.value = true
      deleteAdcExecHistories(currentType.value as number)
        .then(() => {
          logTextArray.value = []
          message.success(t('cmdb.ad.clearLogSuccess'))
        })
        .finally(() => {
          logClearing.value = false
        })
    },
  })
}

function getRowSeq(row: any): number {
  return xTableRef.value?.getRowSeq(row)
}

watch(
  currentType,
  (newValue) => {
    if (newValue) {
      localStorage.setItem('ops_adc_typeid', String(newValue))
    }
  },
  { immediate: true }
)

watch(
  selectedRowKeys,
  (val) => {
    selectedCount.value = val.length
  },
  { deep: true, immediate: true }
)

onMounted(() => {
  getADCCiTypes({ need_other: true }).then((res: any) => {
    ci_types_list.value = res.filter((item: any) => item.ci_types && item.ci_types.length)
    const _currentType = localStorage.getItem('ops_adc_typeid')
    if (_currentType) {
      clickSidebar(Number(_currentType))
      return
    }
    if (res && res.length && res[0].ci_types && res[0].ci_types.length) {
      clickSidebar(res[0].ci_types[0].id)
    }
  })
})
</script>

<template>
  <div class="two-column-layout" :style="{ height: `${windowHeight - 64}px` }">
    <SplitPane v-model:pane-length-pixel="paneLengthPixel" :min="200" :max="500" app-name="cmdb-adc" :trigger-length="18" calc-based-parent>
      <template #one>
        <div class="two-column-layout-sidebar">
          <div v-for="group in ci_types_list" :key="group.id" class="cmdb-adc-group">
            <div class="cmdb-adc-group-title">
              <span>{{ group.name || t('other') }} <span class="cmdb-adc-group-count">{{ group.ci_types.length }}</span></span>
            </div>
            <div
              v-for="ciType in group.ci_types"
              :key="ciType.id"
              :class="{ 'cmdb-adc-side-item': true, 'cmdb-adc-side-item-selected': currentType === ciType.id }"
              @click="clickSidebar(ciType.id)"
            >
              <span class="cmdb-adc-side-icon">
                <template v-if="ciType.icon">
                  <img v-if="ciType.icon.split('$$')[2]" :src="`/api/common-setting/v1/file/${ciType.icon.split('$$')[3]}`" />
                  <AppstoreOutlined v-else :style="{ color: ciType.icon.split('$$')[1], fontSize: '14px' }" />
                </template>
                <span v-else class="primary-color">{{ ciType.name[0].toUpperCase() }}</span>
              </span>
              <span :title="ciType.alias || ciType.name" class="cmdb-adc-side-name">{{ ciType.alias || ciType.name }}</span>
            </div>
          </div>
        </div>
      </template>

      <template #two>
        <div class="two-column-layout-main">
          <div id="discovery-ci">
            <AdcCounter :type-id="currentType ?? 0" />
          <a-spin :tip="loadTip" :spinning="loading">
            <div class="discovery-ci-header">
              <a-input-search :placeholder="t('cmdb.components.pleaseSearch')" allow-clear @search="handleSearch">
                <template #prefix><SearchOutlined /></template>
              </a-input-search>
              <span v-show="selectedCount" class="ops-list-batch-action">
                <span @click="batchAccept">{{ t('cmdb.ad.accept') }}</span>
                <a-divider type="vertical" />
                <span @click="batchDelete">{{ t('delete') }}</span>
                <span>{{ t('cmdb.ci.selectRows', { rows: selectedCount }) }}</span>
              </span>
              <a-button type="primary" class="ops-button-ghost" ghost @click="loadAdc()">
                <template #icon><SyncOutlined /></template>
                {{ t('refresh') }}
              </a-button>
              <a-button type="primary" ghost class="ops-button-ghost discovery-ci-log" @click="clickLog">
                <template #icon><FileTextOutlined /></template>
                <span>{{ t('cmdb.ad.log') }}</span>
              </a-button>
            </div>
            <vxe-table
              ref="xTableRef"
              show-overflow
              show-header-overflow
              resizable
              size="mini"
              stripe
              class="ops-stripe-table checkbox-hover-table"
              :data="filterTableData"
              :height="tableHeight"
              :scroll-y="{ enabled: true, gt: 50 }"
              :scroll-x="{ enabled: true, gt: 0 }"
              :checkbox-config="{ reserve: true, highlight: true, range: true }"
              :sort-config="{ remote: false, trigger: 'cell' }"
              @checkbox-change="onSelectChange"
              @checkbox-all="onSelectChange"
              @checkbox-range-end="onSelectChange"
            >
              <vxe-column align="center" type="checkbox" width="60" fixed="left">
                <template #default="{ row }">
                  {{ getRowSeq(row) }}
                </template>
              </vxe-column>
              <vxe-column
                v-for="(col, index) in columns"
                :key="`${col.field}_${index}`"
                :title="col.title"
                :field="col.field"
                :width="col.width"
                :sortable="col.sortable"
              >
                <template #default="{ row }">
                  <PasswordField v-if="col.is_password" :password="row[col.field]" />
                  <span>
                    {{ typeof row[col.field] === 'object' ? JSON.stringify(row[col.field]) : row[col.field] }}
                  </span>
                </template>
              </vxe-column>
              <vxe-column field="oneagent_name" :title="t('cmdb.ad.oneagentName')" :width="columns.length ? '130px' : undefined" :min-width="columns.length ? undefined : '130px'"></vxe-column>
              <vxe-column field="oneagent_id" :title="t('cmdb.ad.oneagentId')" :width="columns.length ? '110px' : undefined" :min-width="columns.length ? undefined : '110px'"></vxe-column>
              <vxe-column field="adr_name" :title="t('cmdb.ad.adrName')" :width="columns.length ? '130px' : undefined" :min-width="columns.length ? undefined : '130px'"></vxe-column>
              <vxe-column field="adr_type" :title="t('cmdb.ad.adrType')" :width="columns.length ? '80px' : undefined" :min-width="columns.length ? undefined : '80px'"></vxe-column>
              <vxe-column field="is_inner" :title="t('cmdb.ad.isInner')" align="center" :width="columns.length ? '80px' : undefined" :min-width="columns.length ? undefined : '80px'">
                <template #default="{ row }">{{ row.is_inner ? t('yes') : t('no') }}</template>
              </vxe-column>
              <vxe-column field="created_at" :title="t('cmdb.ad.createdAt')" sortable :width="columns.length ? '170px' : undefined" :min-width="columns.length ? undefined : '170px'"></vxe-column>
              <vxe-column field="updated_at" :title="t('cmdb.ad.updatedAt')" sortable :width="columns.length ? '180px' : undefined" :min-width="columns.length ? undefined : '180px'"></vxe-column>
              <vxe-column field="accept_by" :title="t('cmdb.ad.acceptBy')" :width="columns.length ? '80px' : undefined" :min-width="columns.length ? undefined : '80px'" :filters="acceptByFilters"></vxe-column>
              <vxe-column
                align="center"
                field="is_accept"
                :title="t('cmdb.ad.isAccept')"
                :width="columns.length ? '80px' : undefined"
                :min-width="columns.length ? undefined : '80px'"
                :filters="[
                  { label: t('yes'), value: true },
                  { label: t('no'), value: false },
                ]"
                fixed="right"
              >
                <template #default="{ row }">
                  <CheckCircleFilled v-if="row.is_accept" :style="{ color: '#00B42A' }" />
                  <CloseCircleOutlined v-else :style="{ color: '#A5A9BC' }" />
                </template>
              </vxe-column>
              <vxe-column field="accept_time" :title="t('cmdb.ad.acceptTime')" sortable :width="columns.length ? '150px' : undefined" :min-width="columns.length ? undefined : '150px'" fixed="right"></vxe-column>
              <vxe-column :title="t('operation')" :width="columns.length ? '100px' : undefined" :min-width="columns.length ? undefined : '100px'" align="center" fixed="right">
                <template #default="{ row }">
                  <a-space>
                    <a-tooltip :title="t('cmdb.ad.accept')">
                      <a v-if="!row.is_accept" @click="accept(row)"><CheckCircleOutlined /></a>
                    </a-tooltip>
                    <a-tooltip :title="t('cmdb.ad.viewRawData')">
                      <a @click="viewADC(row)"><EyeOutlined /></a>
                    </a-tooltip>
                    <a :style="{ color: 'red' }" @click="deleteADC(row)"><DeleteOutlined /></a>
                  </a-space>
                </template>
              </vxe-column>
              <template #empty>
                <div>
                  <img :style="{ width: '200px' }" :src="dataEmptyImg" />
                  <div>{{ t('noData') }}</div>
                </div>
              </template>
            </vxe-table>
          </a-spin>

          <a-modal v-model:open="logModalVisible" :footer="null" :width="596">
            <div class="log-modal-title">
              <span>{{ t('cmdb.ad.log') }}</span>
              <a class="log-config-toggle" :title="t('cmdb.ad.logConfig')" @click="showLogConfig = !showLogConfig">
                <SettingOutlined :class="{ 'log-config-icon-active': showLogConfig }" />
              </a>
            </div>
            <div v-if="showLogConfig" class="log-config-area">
              <span class="log-config-label">{{ t('cmdb.ad.execLogTypes') }}:</span>
              <a-checkbox-group v-model:value="execLogTypes" :disabled="logConfigSaving" @change="handleLogTypesChange">
                <a-checkbox value="add">add</a-checkbox>
                <a-checkbox value="update">update</a-checkbox>
                <a-checkbox value="delete">delete</a-checkbox>
                <a-checkbox value="accept">accept</a-checkbox>
                <a-checkbox value="sync">sync</a-checkbox>
              </a-checkbox-group>
            </div>
            <p ref="logModelText" class="log-modal-text">
              <span v-for="(item, index) in logTextArray" :key="index" class="log-modal-text-item">
                {{ item }}
              </span>
            </p>
            <div v-if="logTextArray.length" class="log-modal-footer">
              <a-button type="danger" size="small" :loading="logClearing" @click="clearLogs">
                {{ t('cmdb.ad.clearLog') }}
              </a-button>
            </div>
          </a-modal>
          </div>

          <RawDataModal ref="rawDataModalRef" />
        </div>
      </template>
    </SplitPane>
  </div>
</template>

<style lang="less" scoped>
.two-column-layout {
  margin-bottom: -24px;
  width: 100%;

  .two-column-layout-sidebar {
    height: 100%;
    overflow: hidden;
    background-color: #f7f8fa;
    border-right: 1px solid #e8eaed;
    padding: 12px 8px;

    &:hover {
      overflow: auto;
    }
  }

  .two-column-layout-main {
    height: 100%;
    padding: 12px;
    background-color: #fff;
    overflow-y: auto;
    border-radius: @border-radius-box;
  }
}

.cmdb-adc {
  .cmdb-adc-group {
    &:not(:last-child) {
      margin-bottom: 12px;
    }

    &-title {
      margin-bottom: 8px;
      padding: 6px 12px;
      font-weight: 600;
      font-size: 13px;
      color: #666;
    }

    &-count {
      font-size: 12px;
      font-weight: 500;
      color: @text-color_3;
      background: #e8eaed;
      padding: 2px 6px;
      border-radius: 10px;
      margin-left: 4px;
    }
  }

  .cmdb-adc-side-item {
    width: 100%;
    display: flex;
    align-items: center;
    padding: 6px 12px;
    margin: 0 4px 6px 4px;
    cursor: pointer;
    border-radius: 6px;
    height: 36px;
    position: relative;
    transition: all 0.2s ease;

    &::before {
      content: "";
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: @primary-color;
      border-radius: 0 2px 2px 0;
      opacity: 0;
      transition: opacity 0.2s ease;
    }

    .cmdb-adc-side-icon {
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #fff;
      border: 1px solid #e8eaed;
      border-radius: 6px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      flex-shrink: 0;
      transition: transform 0.2s ease;

      img {
        max-height: 20px;
        max-width: 20px;
      }
    }

    .cmdb-adc-side-name {
      margin-left: 8px;
      text-wrap: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 14px;
      color: @text-color_1;
      transition: color 0.2s ease;
      flex: 1;
    }

    &:hover {
      background-color: @primary-color_7;
      transform: translateX(2px);

      .cmdb-adc-side-icon {
        transform: scale(1.05);
      }
    }
  }

  .cmdb-adc-side-item-selected {
    background-color: @primary-color_6;
    box-shadow: 0 1px 3px fade(@primary-color, 10%);

    &::before {
      opacity: 1;
    }

    .cmdb-adc-side-name {
      color: @primary-color;
      font-weight: 600;
    }

    .cmdb-adc-side-icon {
      box-shadow: 0 2px 4px fade(@primary-color, 20%);
    }
  }

  .discovery-ci-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 16px;

    :deep(.ant-input-search) {
      width: 260px;

      .ant-input {
        border-radius: 6px;
        border: 1px solid #e8eaed;
        transition: all 0.2s ease;

        &:hover {
          border-color: #c3cdd7;
        }

        &:focus {
          border-color: @primary-color;
          box-shadow: 0 0 0 2px fade(@primary-color, 10%);
        }
      }
    }

    .ops-list-batch-action {
      margin-left: auto;
    }
  }

  .discovery-ci-log {
    margin-left: auto;
  }

  .checkbox-hover-table {
    :deep(.vxe-table--body-wrapper) {
      .vxe-checkbox--label {
        display: inline;
        padding-left: 0px !important;
        color: #bfbfbf;
      }

      .vxe-icon-checkbox-unchecked {
        display: none;
      }

      .vxe-icon-checkbox-checked ~ .vxe-checkbox--label {
        display: none;
      }

      .vxe-cell--checkbox {
        &:hover {
          .vxe-icon-checkbox-unchecked {
            display: inline;
          }

          .vxe-checkbox--label {
            display: none;
          }
        }
      }
    }
  }
}

.log-modal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-right: 24px;
  font-size: 14px;
  font-weight: 500;
}

.log-config-toggle {
  color: @text-color_3;
  font-size: 14px;
  transition: color 0.2s;

  &:hover {
    color: @primary-color;
  }
}

.log-config-icon-active {
  color: @primary-color;
}

.log-config-area {
  margin-top: 12px;
  padding: 10px 14px;
  background: #fafafa;
  border: 1px solid @border-color-base;
  border-radius: 4px;

  .log-config-label {
    display: block;
    margin-bottom: 6px;
    font-size: 12px;
    color: @text-color_3;
  }

  :deep(.ant-checkbox-group) {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 16px;

    .ant-checkbox-wrapper {
      margin-right: 0;
    }
  }
}

.log-modal-text {
  margin-top: 14px;
  padding: 12px;
  width: 100%;
  height: 312px;
  overflow: auto;
  border: solid 1px @border-color-base;
  background-color: #2f333d;

  &-item {
    color: #c5c8c6;
    width: 100%;
    display: block;
    white-space: pre-wrap;
    word-break: break-all;
  }
}

.log-modal-footer {
  margin-top: 12px;
  text-align: right;
}
</style>
