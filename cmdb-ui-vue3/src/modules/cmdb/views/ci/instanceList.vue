<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, nextTick, onMounted, provide, ref, watch } from 'vue'
import {
  InfoCircleOutlined,
  MoreOutlined,
  PlusOutlined,
  SettingOutlined,
  StarOutlined,
  UserAddOutlined,
} from '@ant-design/icons-vue'
import { message, Modal, notification } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { searchCI, deleteCI as deleteCIById, updateCI } from '@/modules/cmdb/api/ci'
import { getSubscribeAttributes, subscribeCIType, subscribeTreeView } from '@/modules/cmdb/api/preference'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { CIBaselineRollback } from '@/modules/cmdb/api/history'
import { roleHasPermissionToGrant } from '@/modules/acl/api/permission'
import { searchResourceType } from '@/modules/acl/api/resource'
import { getCITableColumns, cloneDeep } from '@/modules/cmdb/utils/helper'
import CMDBGrant from '@/modules/cmdb/components/cmdbGrant/index.vue'
import SearchForm from '@/modules/cmdb/components/searchForm/SearchForm.vue'
import PreferenceSearch from '@/modules/cmdb/components/preferenceSearch/preferenceSearch.vue'
import CITable from '@/modules/cmdb/components/ciTable/index.vue'
import BatchDownload from '@/modules/cmdb/components/batchDownload/batchDownload.vue'
import QRCodeBatchExport from '@/modules/cmdb/components/QRCodeBatchExport/index.vue'
import CreateInstanceForm from './modules/CreateInstanceForm.vue'
import CiDetailDrawer from './modules/ciDetailDrawer.vue'
import EditAttrsPopover from './modules/editAttrsPopover.vue'
import MetadataDrawer from './modules/MetadataDrawer.vue'
import CiRollbackForm from './modules/ciRollbackForm.vue'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    typeId?: number
    CIType?: Record<string, any>
    autoSub?: Record<string, any>
  }>(),
  {
    typeId: undefined,
    CIType: () => ({}),
    autoSub: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'unSubscribe'): void
}>()

const searchRef = ref<any>()
const xTableRef = ref<InstanceType<typeof CITable>>()
const cmdbGrantRef = ref<InstanceType<typeof CMDBGrant>>()
const preferenceSearchRef = ref<any>()
const createRef = ref<InstanceType<typeof CreateInstanceForm>>()
const ciDetailDrawerRef = ref<InstanceType<typeof CiDetailDrawer>>()
const batchDownloadRef = ref<InstanceType<typeof BatchDownload>>()
const qrcodeBatchExportRef = ref<InstanceType<typeof QRCodeBatchExport>>()
const metadataDrawerRef = ref<InstanceType<typeof MetadataDrawer>>()
const ciRollbackFormRef = ref<InstanceType<typeof CiRollbackForm>>()

const loading = ref(false)
const currentPage = ref(1)
const pageSizeOptions = ref(['50', '100', '200', '100000'])
const pageSize = ref(50)
const totalNumber = ref(0)
const loadTip = ref('')

const preferenceAttrList = ref<any[]>([])
const instanceList = ref<any[]>([])
const columns = ref<any[]>([])
const selectedRowKeys = ref<any[]>([])
const initialInstanceList = ref<any[]>([])
const sortByTable = ref<string | undefined>(undefined)

const attrList = ref<any[]>([])
const attributes = ref<Record<string, any>>({})
const resourceType = ref<Record<string, any>>({})

const initialPasswordValue = ref<Record<string, string>>({})
const passwordValue = ref<Record<string, string>>({})
const visible = ref(false)

const tableHeight = computed(() => window.innerHeight - 240)

provide('handleSearch', handleSearch)
provide('setPreferenceSearchCurrent', setPreferenceSearchCurrent)
provide('attrList', () => attrList.value)
provide('attributes', () => attributes.value)
provide('filterCompPreferenceSearch', () => ({ type_id: props.typeId }))
provide('resource_type', () => resourceType.value)

function getTableRef(): any {
  return xTableRef.value?.getVxetableRef() || null
}

async function getAttributeList() {
  await getCITypeAttributesById(props.typeId as number).then((res) => {
    attrList.value = res.attributes
    attributes.value = res
  })
}

function handleSearch() {
  getTableRef()?.clearSort()
  sortByTable.value = undefined
  if (currentPage.value === 1) {
    reloadData()
  } else {
    currentPage.value = 1
  }
}

function setPreferenceSearchCurrent(id: number | null = null) {
  if (preferenceSearchRef.value) {
    preferenceSearchRef.value.currentPreferenceSearch = id
  }
}

function reloadData() {
  loadTableData()
}

async function loadTableData(sortBy?: string) {
  try {
    loading.value = true
    const fuzzySearch = searchRef.value?.fuzzySearch
    const expression = searchRef.value?.expression || ''
    const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
    const regSort = /(?<=sort=).+/g

    const exp = expression.match(regQ) ? expression.match(regQ)[0] : null
    let sort
    if (sortBy) {
      sort = sortBy
    } else {
      sort = expression.match(regSort) ? expression.match(regSort)[0] : undefined
    }
    const res = await searchCI({
      q: `_type:${props.typeId}${exp ? `,${exp}` : ''}${fuzzySearch ? `,*${fuzzySearch}*` : ''}`,
      count: pageSize.value,
      page: currentPage.value,
      sort,
    })
    totalNumber.value = res['numfound']
    columns.value = getColumns(res.result, preferenceAttrList.value)
    columns.value.forEach((col) => {
      if (col.is_password) {
        initialPasswordValue.value[col.field] = ''
        passwordValue.value[col.field] = ''
      }
    })
    const jsonAttrList = attrList.value.filter((attr) => attr.value_type === '6')
    instanceList.value = res['result'].map((item: any) => {
      jsonAttrList.forEach((jsonAttr) => {
        item[jsonAttr.name] = item[jsonAttr.name] ? JSON.stringify(item[jsonAttr.name]) : ''
      })
      return { ...cloneDeep(item) }
    })
    initialInstanceList.value = cloneDeep(instanceList.value)
    getTableRef()?.refreshColumn()
  } finally {
    loading.value = false
  }
}

function getColumns(data: any[], attrList: any[]) {
  const el = document.getElementById('ciIndex')
  const width = el ? el.clientWidth - 50 : 1600
  return getCITableColumns(data, attrList, width)
}

async function loadPreferenceAttrList() {
  const subscribed = await getSubscribeAttributes(props.typeId as number)
  preferenceAttrList.value = subscribed.attributes
}

function onSelectChange(records: any[]) {
  selectedRowKeys.value = records.map((i) => i.ci_id || i._id)
}

function onShowSizeChange(_current: number, nextPageSize: number) {
  pageSize.value = nextPageSize
  if (currentPage.value === 1) {
    reloadData()
  } else {
    currentPage.value = 1
  }
}

function columnDrop() {
  // TODO: wire up Sortable (column drag reorder not yet ported)
}

function handleMenuClick(e: { key: string }) {
  if (e.key === 'grant') {
    visible.value = false
  }
}

function handlePerm() {
  roleHasPermissionToGrant({
    app_id: 'cmdb',
    resource_type_name: 'CIType',
    perm: 'grant',
    resource_name: props.CIType.name,
  }).then((res: any) => {
    if (res.result) {
      searchResourceType({ page_size: 9999, app_id: 'cmdb' }).then((resourceRes: any) => {
        resourceType.value = { groups: resourceRes.groups, id2perms: resourceRes.id2perms }
        cmdbGrantRef.value?.open({
          name: props.CIType.name,
          cmdbGrantType: 'ci',
          CITypeId: props.typeId,
        })
      })
    } else {
      message.error(t('noPermission'))
    }
  })
}

function unsubscribe() {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.preference.confirmcancelSub2', {
      name: `${props.CIType.alias || props.CIType.name}`,
    }),
    onOk: () => {
      const promises = [subscribeCIType(props.typeId as number, ''), subscribeTreeView(props.typeId as number, '')]
      Promise.all(promises).then(() => {
        message.success(t('cmdb.preference.cancelSubSuccess'))
        emit('unSubscribe')
      })
    },
  })
}

function handleCITypeConfig() {
  const { id, name } = props.CIType || {}
  if (id && name) {
    roleHasPermissionToGrant({
      app_id: 'cmdb',
      resource_type_name: 'CIType',
      perm: 'config',
      resource_name: name,
    }).then((res: any) => {
      if (res?.result) {
        const storageId = `null%${id}%${name}`
        localStorage.setItem('ops_cityps_currentId', storageId)
        localStorage.setItem('ops_model_config_tab_key', '1')
        window.open('/cmdb/ci_types', '_blank')
      } else {
        message.error(t('noPermission'))
      }
    })
  }
}

function openMetadata() {
  if (props.typeId) {
    metadataDrawerRef.value?.open(props.typeId)
  }
}

function openUpdate() {
  createRef.value?.handleOpen(true, 'update')
}

function openBatchQRCode() {
  const showAttrName = attrList.value.find((attr) => attr?.id === props.CIType?.show_id)?.name || ''
  const uniqueAttrName = attrList.value.find((attr) => attr?.id === props.CIType?.unique_id)?.name || ''

  const ciList = selectedRowKeys.value.map((ciId) => {
    const item = instanceList.value.find((i) => i._id === ciId) || {}
    const label = item?.[showAttrName] || item?.[uniqueAttrName] || `CI ${ciId}`

    return {
      ciId,
      typeId: props.typeId,
      label,
    }
  })

  qrcodeBatchExportRef.value?.open(ciList)
}

function openBatchDownload() {
  batchDownloadRef.value?.open({
    preferenceAttrList: preferenceAttrList.value.filter((attr) => !attr?.is_reference),
    ciTypeName: props.CIType.alias || props.CIType.name,
  })
}

function batchRollback() {
  nextTick(() => {
    ciRollbackFormRef.value?.onOpen(true)
  })
}

function batchDelete() {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete'),
    onOk() {
      batchDeleteAsync()
    },
  })
}

async function batchDeleteAsync() {
  let successNum = 0
  let errorNum = 0
  loading.value = true
  loadTip.value = t('cmdb.ci.batchDeleting')
  const floor = Math.ceil(selectedRowKeys.value.length / 6)
  for (let i = 0; i < floor; i++) {
    const itemList = selectedRowKeys.value.slice(6 * i, 6 * i + 6)
    const promises = itemList.map((x) => deleteCIById(x, false))
    await Promise.allSettled(promises)
      .then((res) => {
        res.forEach((r) => {
          if (r.status === 'fulfilled') {
            successNum += 1
          } else {
            errorNum += 1
          }
        })
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
  getTableRef()?.clearCheckboxRow()
  getTableRef()?.clearCheckboxReserve()
  if (currentPage.value === 1) {
    loadTableData()
  } else {
    currentPage.value = 1
  }
}

function batchUpdate(values: Record<string, any>) {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ci.batchUpdateConfirm'),
    onOk() {
      batchUpdateAsync(values)
    },
  })
}

async function batchUpdateAsync(values: Record<string, any>) {
  let successNum = 0
  let errorNum = 0
  loading.value = true
  loadTip.value = t('cmdb.ci.batchUpdateInProgress') + '...'
  const payload: Record<string, any> = {}
  Object.keys(values).forEach((key) => {
    payload[key] = values[key] === undefined || values[key] === null ? null : values[key]
  })
  createRef.value?.handleClose()
  const key = 'updatable'
  let errorMsg = ''
  for (let i = 0; i < selectedRowKeys.value.length; i++) {
    await updateCI(selectedRowKeys.value[i], payload, false)
      .then(() => {
        successNum += 1
      })
      .catch((error) => {
        errorMsg = errorMsg + '\n' + `${selectedRowKeys.value[i]}:${error.response?.data?.message ?? ''}`
        notification.warning({
          key,
          message: t('warning'),
          description: errorMsg,
          duration: 0,
          style: { whiteSpace: 'break-spaces', overflow: 'auto', maxHeight: window.innerHeight - 80 + 'px' },
        })
        errorNum += 1
      })
      .finally(() => {
        loadTip.value = t('cmdb.ci.batchUpdateInProgress2', {
          total: selectedRowKeys.value.length,
          successNum,
          errorNum,
        })
      })
  }
  loading.value = false
  loadTip.value = ''
  selectedRowKeys.value = []
  getTableRef()?.clearCheckboxRow()
  getTableRef()?.clearCheckboxReserve()
  reloadData()
}

async function batchRollbackAsync(params: Record<string, any>) {
  const mask = document.querySelector('.ant-drawer-mask') as HTMLElement | null
  const oldValue = mask?.style.zIndex
  if (mask) {
    mask.style.zIndex = '2'
  }
  let successNum = 0
  let errorNum = 0
  loading.value = true
  loadTip.value = t('cmdb.ci.rollbackingTips')
  const floor = Math.ceil(selectedRowKeys.value.length / 6)
  for (let i = 0; i < floor; i++) {
    const itemList = selectedRowKeys.value.slice(6 * i, 6 * i + 6)
    const promises = itemList.map((x) => CIBaselineRollback(x, params))
    await Promise.allSettled(promises)
      .then((res) => {
        res.forEach((r) => {
          if (r.status === 'fulfilled') {
            successNum += 1
          } else {
            errorNum += 1
          }
        })
      })
      .finally(() => {
        loadTip.value = t('cmdb.ci.batchRollbacking', {
          total: selectedRowKeys.value.length,
          successNum,
          errorNum,
        })
      })
  }
  loading.value = false
  loadTip.value = ''
  if (mask) {
    mask.style.zIndex = oldValue || ''
  }
  selectedRowKeys.value = []
  getTableRef()?.clearCheckboxRow()
  getTableRef()?.clearCheckboxReserve()
  if (currentPage.value === 1) {
    loadTableData()
  } else {
    currentPage.value = 1
  }
}

function batchDownload({ filename, type, checkedKeys, exportQRCode }: any) {
  const jsonAttrList: string[] = []
  checkedKeys.forEach((key: string) => {
    const _find = attrList.value.find((attr) => attr.name === key)
    if (_find && _find.value_type === '6') jsonAttrList.push(key)
  })
  const data = cloneDeep([
    ...(getTableRef()?.getCheckboxReserveRecords() || []),
    ...(getTableRef()?.getCheckboxRecords(true) || []),
  ])

  const tableRef = getTableRef()
  // The ExcelJS-based QR-code embedding is unavailable in the Vue 3 shell, so the
  // QR export option falls back to a plain data export.
  void exportQRCode

  tableRef?.exportData({
    filename,
    type,
    columnFilterMethod({ column }: any) {
      return checkedKeys.includes(column.property)
    },
    data: [
      ...data.map((item: any) => {
        jsonAttrList.forEach((jsonAttr) => (item[jsonAttr] = item[jsonAttr] ? JSON.stringify(item[jsonAttr]) : ''))
        return { ...item }
      }),
    ],
  })
  selectedRowKeys.value = []
  tableRef?.clearCheckboxRow()
  tableRef?.clearCheckboxReserve()
}

function deleteCI(record: any) {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete'),
    onOk() {
      deleteCIById(record.ci_id || record._id).then(() => {
        message.success(t('deleteSuccess'))
        reloadData()
      })
    },
  })
}

function openDetail(id: any, activeTabKey?: string, ciDetailRelationKey?: string) {
  void ciDetailRelationKey
  ciDetailDrawerRef.value?.create(id, activeTabKey)
}

function refreshAfterEditAttrs() {
  loadPreferenceAttrList().then(() => loadTableData())
}

function getQAndSort() {
  const fuzzySearch = searchRef.value?.fuzzySearch || ''
  const expression = searchRef.value?.expression || ''
  preferenceSearchRef.value?.savePreference({ fuzzySearch, expression })
}

function setParamsFromPreferenceSearch(item: any) {
  const { fuzzySearch, expression } = item.option
  if (searchRef.value) {
    searchRef.value.fuzzySearch = fuzzySearch
    searchRef.value.expression = expression
  }
  selectedRowKeys.value = []
  getTableRef()?.clearCheckboxRow()
  getTableRef()?.clearCheckboxReserve()
  getTableRef()?.clearSort()
  sortByTable.value = undefined
  nextTick(() => {
    if (currentPage.value === 1) {
      loadTableData()
    } else {
      currentPage.value = 1
    }
  })
}

function copyExpression() {
  const expression = searchRef.value?.expression || ''
  const fuzzySearch = searchRef.value?.fuzzySearch

  const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
  const exp = expression.match(regQ) ? expression.match(regQ)[0] : null
  const text = `q=_type:${props.typeId}${exp ? `,${exp}` : ''}${fuzzySearch ? `,*${fuzzySearch}*` : ''}`
  navigator.clipboard
    .writeText(text)
    .then(() => {
      message.success(t('copySuccess'))
    })
    .catch(() => {
      message.error(t('cmdb.ci.copyFailed'))
    })
}

watch(currentPage, () => {
  loadTableData(sortByTable.value)
})

onMounted(async () => {
  loading.value = true
  await getAttributeList()
  await loadPreferenceAttrList()
  await loadTableData()
  loading.value = false

  setTimeout(() => {
    columnDrop()
  }, 1000)
})
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <div id="ciIndex" class="cmdb-ci">
    <a-spin :tip="loadTip" :spinning="loading">
      <div class="cmdb-views-header">
        <span>
          <span class="cmdb-views-header-title">{{ CIType.alias || CIType.name }}</span>
          <span
            class="cmdb-views-header-metadata"
            @click="openMetadata"
          >
            <InfoCircleOutlined />{{ t('cmdb.ci.attributeDesc') }}
          </span>
        </span>
        <a-space>
          <a-button type="primary" class="ops-button-ghost" ghost @click="createRef?.handleOpen(true, 'create')">
            <template #icon><PlusOutlined /></template>
            {{ t('create') }}
          </a-button>
          <EditAttrsPopover :type-id="typeId" class="operation-icon" @refresh="refreshAfterEditAttrs">
            <a-button type="primary" ghost class="ops-button-ghost">
              <template #icon><SettingOutlined /></template>{{ t('cmdb.configTable') }}
            </a-button>
          </EditAttrsPopover>
          <a-dropdown>
            <a-button type="primary" ghost class="ops-button-ghost"><MoreOutlined /></a-button>
            <template #overlay>
              <a-menu @click="handleMenuClick">
                <a-menu-item key="grant" @click="handlePerm">
                  <UserAddOutlined />
                  {{ t('grant') }}
                </a-menu-item>
                <a-menu-item v-if="!autoSub.enabled" key="cancelSub" @click="unsubscribe">
                  <StarOutlined />
                  {{ t('cmdb.preference.cancelSub') }}
                </a-menu-item>
                <a-menu-item key="citypeConfig" @click="handleCITypeConfig">
                  {{ t('cmdb.menu.citypeManage') }}
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </a-space>
      </div>
      <div class="cmdb-ci-main">
        <SearchForm
          ref="searchRef"
          :preference-attr-list="preferenceAttrList"
          :type-id="typeId"
          :selected-row-keys="selectedRowKeys"
          @refresh="handleSearch"
          @copy-expression="copyExpression"
        >
          <PreferenceSearch
            ref="preferenceSearchRef"
            v-show="!selectedRowKeys.length"
            @get-q-and-sort="getQAndSort"
            @set-params-from-preference-search="setParamsFromPreferenceSearch"
          />
          <div class="ops-list-batch-action" v-show="!!selectedRowKeys.length">
            <span @click="openUpdate">{{ t('update') }}</span>
            <a-divider type="vertical" />
            <span @click="openBatchQRCode">{{ t('cmdb.ci.qrcodeExport') }}</span>
            <a-divider type="vertical" />
            <span @click="openBatchDownload">{{ t('download') }}</span>
            <a-divider type="vertical" />
            <span @click="batchDelete">{{ t('delete') }}</span>
            <a-divider type="vertical" />
            <span @click="batchRollback">{{ t('cmdb.ci.rollback') }}</span>
            <span>{{ t('cmdb.ci.selectRows', { rows: selectedRowKeys.length }) }}</span>
          </div>
        </SearchForm>

        <CiDetailDrawer ref="ciDetailDrawerRef" :type-id="typeId" />

        <CITable
          ref="xTableRef"
          :id="`cmdb-ci-${typeId}`"
          :loading="loading"
          :attr-list="preferenceAttrList"
          :columns="columns"
          :password-value="passwordValue"
          :data="instanceList"
          :height="tableHeight"
          @on-select-change="onSelectChange"
          @open-detail="openDetail"
          @delete-c-i="deleteCI"
        />

        <div :style="{ textAlign: 'right', marginTop: '4px' }">
          <a-pagination
            show-size-changer
            :current="currentPage"
            size="small"
            :total="totalNumber"
            show-quick-jumper
            :page-size="pageSize"
            :page-size-options="pageSizeOptions"
            @show-size-change="onShowSizeChange"
            :show-total="(total: number, range: number[]) => t('pagination.total', { range0: range[0], range1: range[1], total })"
            @change="(page: number) => (currentPage = page)"
          />
        </div>

        <CreateInstanceForm
          ref="createRef"
          :type-id-from-prop="typeId"
          @reload="reloadData"
          @submit="batchUpdate"
        />
        <BatchDownload ref="batchDownloadRef" @batch-download="batchDownload" />
        <CiRollbackForm ref="ciRollbackFormRef" :ci-ids="selectedRowKeys" @batch-rollback-async="batchRollbackAsync" />
        <QRCodeBatchExport ref="qrcodeBatchExportRef" />
        <MetadataDrawer ref="metadataDrawerRef" />
        <CMDBGrant ref="cmdbGrantRef" resource-type="CIType" app_id="cmdb" />
      </div>
    </a-spin>
  </div>
</template>

<style lang="less">
.cmdb-views-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;

  &-title {
    font-size: 18px;
    font-weight: 600;
    color: @text-color_1;
  }

  &-metadata {
    margin-left: 8px;
    color: @text-color_3;
    cursor: pointer;
  }
}

.ops-list-batch-action {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;

  span {
    cursor: pointer;
    color: @primary-color;
  }
}
</style>

<style lang="less" scoped>
.cmdb-ci {
  background-color: #fff;
  padding: 20px;
  border-radius: @border-radius-box;
  height: calc(100vh - 64px);
  overflow: auto;
  margin-bottom: -24px;
}
</style>
