<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { CaretRightOutlined, ExportOutlined } from '@ant-design/icons-vue'
import ExcelJS from 'exceljs'
import FileSaver from 'file-saver'
import AttrDisplay from '@/modules/cmdb/views/resource_search_2/resourceSearch/components/attrDisplay.vue'
import BatchDownload from '@/modules/cmdb/components/batchDownload/batchDownload.vue'
import { cloneDeep } from '@/modules/cmdb/utils/helper'

const props = withDefaults(
  defineProps<{
    allTableData?: Record<string, any>
    tabActive?: string
    returnPath?: boolean
    isHideSearchCondition?: boolean
    referenceShowAttrNameMap?: Record<string, string>
    referenceCIIdMap?: Record<string, Record<string, any>>
    searchValue?: string
    isSearchLoading?: boolean
  }>(),
  {
    allTableData: () => ({}),
    tabActive: '',
    returnPath: false,
    isHideSearchCondition: false,
    referenceShowAttrNameMap: () => ({}),
    referenceCIIdMap: () => ({}),
    searchValue: '',
    isSearchLoading: false,
  }
)

const emit = defineEmits<{
  (e: 'updateTab', tab: string): void
}>()

const { t } = useI18n()

const xTableRef = ref<any>()
const batchDownloadRef = ref<InstanceType<typeof BatchDownload>>()

const windowHeight = computed(() => window.innerHeight)

const tableHeight = computed(() =>
  props.isHideSearchCondition ? windowHeight.value - 308 : windowHeight.value - 458
)

const tableData = computed(() => props.allTableData?.[props.tabActive] || {})

const tabList = computed(() => {
  const keys = Object.keys(props.allTableData) || []
  return keys.map((key) => {
    return {
      value: key,
      count: props.allTableData?.[key]?.count || 0,
    }
  })
})

function markSearchValue(text: unknown): string {
  if (!text || !props.searchValue) {
    return String(text)
  }
  const regex = new RegExp(`(${props.searchValue})`, 'gi')
  return String(text).replace(regex, `<span style="background-color: #D3EEFE; padding: 0 2px;">$1</span>`)
}

function clickTab(tab: string) {
  emit('updateTab', tab)
}

function getRowSeq(row: Record<string, any>): number {
  return xTableRef.value?.getRowSeq(row)
}

function getCellClassName({ columnIndex }: { columnIndex: number }): string {
  const pathLength = tableData.value?.pathList?.length
  if (columnIndex <= pathLength && props.returnPath) {
    return 'table-path-cell'
  }
  return ''
}

function getHeaderCellClassName({ columnIndex }: { columnIndex: number }): string {
  const pathLength = tableData.value?.pathList?.length
  if (columnIndex <= pathLength && props.returnPath) {
    return 'table-path-header-cell'
  }
  return ''
}

function handleExport() {
  const preferenceAttrList: any[] = []
  if (props.returnPath && tableData.value?.pathList?.length) {
    preferenceAttrList.push(
      ...tableData.value.pathList.map((path: any) => {
        return {
          name: path.id,
          alias: path.name,
        }
      })
    )
  }

  if (tableData.value?.ciAttr?.length) {
    const ciAttr = cloneDeep(tableData.value.ciAttr)
    ciAttr.forEach((attr: any) => {
      attr.alias = attr.alias || attr.name
    })
    preferenceAttrList.push(...ciAttr)
  }

  batchDownloadRef.value?.open({
    preferenceAttrList,
    ciTypeName: props.tabActive || '',
  })
}

function batchDownload(payload: Record<string, unknown>) {
  const { checkedKeys = [], filename } = payload as { checkedKeys: string[]; filename: string }
  const wb = new ExcelJS.Workbook()

  const tableRef = xTableRef.value
  let rows: any[] = cloneDeep([
    ...tableRef.getCheckboxReserveRecords(),
    ...tableRef.getCheckboxRecords(true),
  ])
  if (!rows.length) {
    const { fullData } = tableRef.getTableData()
    rows = cloneDeep(fullData)
  }

  const ws = wb.addWorksheet(props.tabActive)

  const pathColumns: any[] = []
  const targetColumns: any[] = []

  if (props.returnPath) {
    const pathFilter = tableData.value.pathList.filter((path: any) => checkedKeys.includes(path.id))
    pathFilter.forEach((path: any) => {
      pathColumns.push({ header: path.name || '', key: path.id, width: 20 })
    })
  }

  const attrMap = new Map<string, any>()
  const attrFilter = tableData.value.ciAttr.filter((attr: any) => checkedKeys.includes(attr.name))
  attrFilter.forEach((attr: any) => {
    attrMap.set(attr.name, attr)
    targetColumns.push({ header: attr.alias || attr.name || '', key: attr.name, width: 20 })
  })

  ws.columns = [...pathColumns, ...targetColumns]

  rows.forEach(({ pathCI, targetCI }: any) => {
    const row: Record<string, any> = {}
    if (props.returnPath) {
      pathColumns.forEach(({ key }: { key: string }) => {
        row[key] = pathCI?.[key] || ''
      })
    }
    targetColumns.forEach(({ key }: { key: string }) => {
      const value = targetCI?.[key] ?? null
      const attr = attrMap.get(key)
      if (attr.valueType === '6') {
        row[key] = value ? JSON.stringify(value) : value
      } else if (attr.is_list && Array.isArray(value)) {
        row[key] = value.join(',')
      } else {
        row[key] = value
      }
    })
    ws.addRow(row)
  })

  wb.xlsx.writeBuffer().then((buffer) => {
    const file = new Blob([buffer], { type: 'application/octet-stream' })
    FileSaver.saveAs(file, `${filename}.xlsx`)
  })

  tableRef.clearCheckboxRow()
  tableRef.clearCheckboxReserve()
}

function onSelectChange() {
  // Reserved for parity with the legacy implementation.
}
</script>

<template>
  <!-- eslint-disable vue/attributes-order, vue/no-v-html -->
  <div class="search-table">
    <div class="search-table-header">
      <div class="table-tab">
        <div
          v-for="tab in tabList"
          :key="tab.value"
          :class="['table-tab-item', tabActive === tab.value ? 'table-tab-item_active' : '']"
          @click="clickTab(tab.value)"
        >
          {{ tab.value }}
          (<span class="table-tab-item-count">{{ tab.count }}</span>)
        </div>
      </div>

      <a-button
        v-if="tableData.ciList && tableData.ciList.length"
        type="primary"
        class="ops-button-ghost search-table-export"
        ghost
        @click="handleExport"
      >
        <ExportOutlined />
        {{ t('export') }}
      </a-button>
    </div>

    <vxe-table
      ref="xTableRef"
      show-overflow
      :data="tableData.ciList"
      size="small"
      :height="`${tableHeight}px`"
      :cell-class-name="getCellClassName"
      :header-cell-class-name="getHeaderCellClassName"
      :checkbox-config="{ range: true }"
      :loading="isSearchLoading"
      :column-config="{ resizable: true }"
      :resizable-config="{ minWidth: 60 }"
      class="checkbox-hover-table"
      @checkbox-change="onSelectChange"
      @checkbox-all="onSelectChange"
      @checkbox-range-end="onSelectChange"
    >
      <vxe-column v-if="tableData.ciList && tableData.ciList.length" align="center" type="checkbox" width="60">
        <template #default="{ row }">
          {{ getRowSeq(row) }}
        </template>
      </vxe-column>

      <template v-if="returnPath && tableData.pathList && tableData.pathList.length">
        <vxe-column
          v-for="(path, index) in tableData.pathList"
          :key="`${path.id}-${index}`"
          class="table-path-column"
          :title="tableData.pathList[index].name"
          :field="path.id"
          :show-header-overflow="false"
          :width="index !== tableData.pathList.length - 1 ? 160 : 100"
        >
          <template #header>
            <div class="table-path-header">
              <span
                class="table-path-header-name"
                :style="{
                  maxWidth: tableData.pathList[index].relation ? '70px' : '100%',
                }"
              >
                <a-tooltip :title="tableData.pathList[index].name">
                  {{ tableData.pathList[index].name }}
                </a-tooltip>
              </span>
              <div class="table-path-header-right" v-if="tableData.pathList[index].relation">
                <span class="table-path-header-line">
                  <CaretRightOutlined class="table-path-header-line-arrow" />
                </span>
                <span class="table-path-header-relation">
                  <span class="table-path-header-relation-text">
                    <a-tooltip :title="tableData.pathList[index].relation">
                      {{ tableData.pathList[index].relation }}
                    </a-tooltip>
                  </span>
                </span>
              </div>
            </div>
          </template>
          <template #default="{ row, columnIndex }">
            <span v-if="columnIndex === 1" v-html="markSearchValue(row.pathCI[path.id])"></span>
            <span v-else>{{ row.pathCI[path.id] }}</span>
          </template>
        </vxe-column>
      </template>

      <template v-if="tableData.ciAttr && tableData.ciAttr.length">
        <vxe-column
          v-for="(attr, index) in tableData.ciAttr"
          :key="`${attr.name}_${index}`"
          :title="attr.alias || attr.name || ''"
          :field="attr.name"
          :width="attr.width"
          :show-header-overflow="true"
        >
          <template #default="{ row }">
            <AttrDisplay
              :attr="attr"
              :ci="row.targetCI"
              :reference-show-attr-name-map="referenceShowAttrNameMap"
              :reference-c-i-id-map="referenceCIIdMap"
            />
          </template>
        </vxe-column>
      </template>
    </vxe-table>

    <BatchDownload ref="batchDownloadRef" :show-file-type-select="false" @batch-download="batchDownload" />
  </div>
</template>

<style lang="less" scoped>
.search-table {
  width: 100%;

  &-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
  }

  &-export {
    flex-shrink: 0;
    margin-left: 12px;
  }

  .table-tab {
    display: flex;
    align-items: center;
    column-gap: 35px;
    padding-bottom: 6px;
    margin-bottom: 18px;
    max-width: 100%;
    overflow-x: auto;
    overflow-y: hidden;

    &-item {
      font-size: 14px;
      font-weight: 400;
      color: #4e5969;
      cursor: pointer;
      flex-shrink: 0;

      &-count {
        color: #2f54eb;
      }

      &_active {
        color: #2f54eb;
      }

      &:hover {
        color: #2f54eb;
      }
    }
  }

  .table-path-header {
    position: relative;
    display: flex;
    align-items: center;

    &-name {
      max-width: 80px;
      overflow: hidden;
      text-overflow: ellipsis;
      text-wrap: nowrap;
      position: relative;
      z-index: 1;
      flex-shrink: 0;
    }

    &-right {
      display: flex;
      align-items: center;
      width: 100%;
      margin-left: 10px;
      margin-right: -5px;
      position: relative;
    }

    &-line {
      width: 100%;
      height: 1px;
      position: relative;
      background-color: #cacdd9;
      z-index: 0;

      &-arrow {
        position: absolute;
        right: -6px;
        top: -6px;
        font-size: 12px;
        color: #cacdd9;
      }
    }

    &-relation {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background-color: #ffffff;
      border: solid 1px #e4e7ed;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 8px;
      border-radius: 22px;
      z-index: 2;
      max-width: 70px;
      width: fit-content;

      &-text {
        font-size: 12px;
        font-weight: 400;
        color: #a5a9bc;

        overflow: hidden;
        text-overflow: ellipsis;
        text-wrap: nowrap;
        width: 100%;
      }
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

  :deep(.table-path-header-cell) {
    background-color: #ebeff8 !important;

    .vxe-cell--title {
      width: 100%;
      overflow: visible;
    }
  }

  :deep(.table-path-cell) {
    background-color: #f9fbff;
  }

  :deep(.attr-display) {
    display: inline;
  }
}
</style>
