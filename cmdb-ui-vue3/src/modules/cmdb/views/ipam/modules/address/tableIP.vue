<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { DeleteOutlined, EditOutlined, PlusOutlined, RetweetOutlined } from '@ant-design/icons-vue'
import { STATUS_COLOR, STATUS_LABEL, ADDRESS_STATUS } from './constants'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import CIDetailDrawer from '@/modules/cmdb/views/ci/modules/ciDetailDrawer.vue'

const props = withDefaults(
  defineProps<{
    columns?: any[]
    allTableData?: any[]
    referenceShowAttrNameMap?: Record<string, string>
    referenceCIIdMap?: Record<string, Record<string, any>>
    columnWidth?: Record<string, number>
    addressCITypeId?: number | null
  }>(),
  {
    columns: () => [],
    allTableData: () => [],
    referenceShowAttrNameMap: () => ({}),
    referenceCIIdMap: () => ({}),
    columnWidth: () => ({}),
    addressCITypeId: null,
  }
)

const emit = defineEmits<{
  (e: 'openAssign', data: any): void
  (e: 'recycle', ip: string): void
  (e: 'selectChange', ips: string[]): void
}>()

const { t } = useI18n()

const xTableRef = ref<any>()
const detailRef = ref<InstanceType<typeof CIDetailDrawer>>()

const page = ref(1)
const pageSize = ref(50)
const pageSizeOptions = ['50', '100', '200']

const windowHeight = computed(() => window.innerHeight)
const tableHeight = computed(() => `${windowHeight.value - 270}px`)

const tableData = computed(() => {
  const start = (page.value - 1) * pageSize.value
  const end = start + pageSize.value
  return cloneDeep(props.allTableData.slice(start, end))
})

watch(
  () => props.allTableData,
  () => {
    page.value = 1
  }
)

function getVxetableRef(): any {
  return xTableRef.value || null
}

function getRowSeq(row: Record<string, any>): number {
  return getVxetableRef()?.getRowSeq?.(row)
}

function handlePageSizeChange(_current: number, nextPageSize: number) {
  pageSize.value = nextPageSize
  page.value = 1
}

function changePage(nextPage: number) {
  page.value = nextPage
}

function assignAddress(data: any) {
  emit('openAssign', data)
}

function clickRecycle(data: any) {
  emit('recycle', data.ip)
}

function getCheckedTableData(clear = true): any[] {
  const tableRef = getVxetableRef()
  let data = cloneDeep([...(tableRef?.getCheckboxReserveRecords() || []), ...(tableRef?.getCheckboxRecords(true) || [])])
  if (!data.length) {
    const { fullData } = tableRef?.getTableData() || {}
    data = cloneDeep(fullData || [])
  }

  if (clear) {
    clearCheckbox()
  }

  return data
}

function clearCheckbox() {
  const tableRef = getVxetableRef()
  if (tableRef) {
    tableRef.clearCheckboxRow()
    tableRef.clearCheckboxReserve()
  }
}

function getReferenceAttrValue(id: any, col: Record<string, any>): string {
  const ci = props.referenceCIIdMap?.[col?.reference_type_id]?.[id]
  if (!ci) {
    return id
  }

  const attrName = props.referenceShowAttrNameMap?.[col.reference_type_id]
  return ci?.[attrName] || id
}

function getChoiceValueLabel(col: Record<string, any>, colValue: any): string {
  const found = col?.choice_value?.find((item: any) => String(item[0]) === String(colValue))
  if (found) {
    return found?.[1]?.label || ''
  }
  return ''
}

function onSelectChange() {
  const xTable = getVxetableRef()
  const records = [...(xTable?.getCheckboxRecords() || []), ...(xTable?.getCheckboxReserveRecords() || [])]
  const ips = records.map((item: any) => item.ip)
  emit('selectChange', ips)
}

function onSelectRangeEnd({ records }: { records: any[] }) {
  const ips = records?.map?.((item: any) => item.ip) || []
  emit('selectChange', ips)
}

function openRelation(row: any) {
  if (row._id) {
    detailRef.value?.create(row._id, 'tab_2')
  }
}

defineExpose({ getCheckedTableData, clearCheckbox, getVxetableRef })
</script>

<template>
  <div class="ip-table">
    <vxe-table
      ref="xTableRef"
      size="small"
      show-overflow
      show-header-overflow
      highlight-hover-row
      :data="tableData"
      :row-config="{ useKey: true, keyField: 'ip' }"
      :column-config="{ resizable: true }"
      :checkbox-config="{ highlight: true, reserve: true, range: true }"
      :height="tableHeight"
      class="ops-unstripe-table checkbox-hover-table"
      @checkbox-change="onSelectChange"
      @checkbox-all="onSelectChange"
      @checkbox-range-end="onSelectRangeEnd"
    >
      <vxe-column align="center" type="checkbox" width="60">
        <template #default="{ row }">
          {{ getRowSeq(row) }}
        </template>
      </vxe-column>

      <vxe-column
        v-for="col in columns"
        :key="col.field"
        :title="col.title"
        :field="col.field"
        :width="columnWidth[col.field] || undefined"
      >
        <template
          v-if="col.field === '_ip_status' || col.is_link || col.is_reference || col.is_choice"
          #default="{ row }"
        >
          <div v-if="col.field === '_ip_status'" class="ip-table-status">
            <div
              class="ip-table-status-dot"
              :style="{
                backgroundColor: `${STATUS_COLOR[row._ip_status]}22`
              }"
            >
              <div
                class="ip-table-status-dot-content"
                :style="{
                  backgroundColor: STATUS_COLOR[row._ip_status]
                }"
              ></div>
            </div>
            <div class="ip-table-status-text">
              {{ t(STATUS_LABEL[row._ip_status]) }}
            </div>
          </div>
          <template v-if="col.is_reference && row[col.field]">
            <a
              v-for="ciId in (col.is_list ? row[col.field] : [row[col.field]])"
              :key="ciId"
              :href="`/cmdb/cidetail/${col.reference_type_id}/${ciId}`"
              target="_blank"
            >
              {{ getReferenceAttrValue(ciId, col) }}
            </a>
          </template>
          <template v-else-if="col.is_link && row[col.field]">
            <a
              v-for="(linkItem, linkIndex) in (col.is_list ? row[col.field] : [row[col.field]])"
              :key="linkIndex"
              :href="
                linkItem.startsWith('http') || linkItem.startsWith('https')
                  ? `${linkItem}`
                  : `http://${linkItem}`
              "
              target="_blank"
            >
              {{ getChoiceValueLabel(col, linkItem) || linkItem }}
            </a>
          </template>
          <template v-else-if="col.is_choice && row[col.field]">
            <span
              v-for="value in (col.is_list ? row[col.field] : [row[col.field]])"
              :key="value"
              class="column-default-choice"
            >
              {{ getChoiceValueLabel(col, value) || value }}
            </span>
          </template>
        </template>
      </vxe-column>

      <vxe-column :title="t('operation')" width="80" fixed="right">
        <template #default="{ row }">
          <div class="ip-table-operation">
            <template v-if="[ADDRESS_STATUS.ONLINE_ASSIGNED, ADDRESS_STATUS.OFFLINE_ASSIGNED].includes(row._ip_status)">
              <a-tooltip :title="t('cmdb.ipam.editAssignAddress')">
                <a @click="assignAddress(row)"><EditOutlined /></a>
              </a-tooltip>
              <a-tooltip :title="t('cmdb.ipam.recycle')">
                <a @click="clickRecycle(row)"><DeleteOutlined /></a>
              </a-tooltip>
            </template>
            <a-tooltip v-else :title="t('cmdb.ipam.assign')">
              <a @click="assignAddress(row)"><PlusOutlined /></a>
            </a-tooltip>

            <a-tooltip v-if="row._ip_status !== ADDRESS_STATUS.OFFLINE_UNASSIGNED" :title="t('cmdb.ci.viewRelation')">
              <a @click="openRelation(row)">
                <RetweetOutlined />
              </a>
            </a-tooltip>
          </div>
        </template>
      </vxe-column>
    </vxe-table>

    <div class="ip-table-pagination">
      <a-pagination
        show-size-changer
        :current="page"
        size="small"
        :total="allTableData.length"
        show-quick-jumper
        :page-size="pageSize"
        :page-size-options="pageSizeOptions"
        :show-total="
          (total: number, range: number[]) =>
            t('pagination.total', {
              range0: range[0],
              range1: range[1],
              total,
            })
        "
        @show-size-change="handlePageSizeChange"
        @change="changePage"
      />
    </div>

    <CIDetailDrawer ref="detailRef" :type-id="addressCITypeId" />
  </div>
</template>

<style lang="less" scoped>
.ip-table {
  &-status {
    display: flex;
    align-items: center;

    &-dot {
      width: 12px;
      height: 12px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;

      &-content {
        width: 6px;
        height: 6px;
        border-radius: 6px;
      }
    }

    &-text {
      margin-left: 4px;
      font-size: 12px;
      font-weight: 400;
      color: #4e5969;
    }
  }

  &-operation {
    display: flex;
    align-items: center;
    column-gap: 12px;
  }

  &-pagination {
    text-align: right;
    margin-top: 12px;
  }
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
</style>
