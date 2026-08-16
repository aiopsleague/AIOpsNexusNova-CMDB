<script setup lang="ts">
import { ref, useAttrs, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  AppstoreOutlined,
  DeleteOutlined,
  HolderOutlined,
  RetweetOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons-vue'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { searchCI } from '@/modules/cmdb/api/ci'
import dataEmptyImg from '@/assets/data_empty.png'
import JsonEditor from '../JsonEditor/jsonEditor.vue'
import PasswordField from '../passwordField/index.vue'
import CIReferenceAttr from '@/components/ciReferenceAttr/index.vue'
import CiFileField from '@/modules/cmdb/components/CiFileField.vue'

/**
 * Core CI instance data table. Wraps vxe-table with inline editing, choice /
 * reference / file / password / JSON column rendering, checkbox range selection
 * and a JSON editor dialog. The parent accesses the underlying vxe-table
 * instance through the exposed `getVxetableRef()` method.
 */
const props = withDefaults(
  defineProps<{
    // table ID
    id?: string
    // table loading flag
    loading?: boolean
    // CI attribute list (used to resolve per-cell font options)
    attrList?: any[]
    // table columns
    columns?: any[]
    // per-field password edit buffers
    passwordValue?: Record<string, any>
    // loading tip text
    loadingTip?: string
    // whether to show the checkbox column
    showCheckbox?: boolean
    // whether to show the delete action
    showDelete?: boolean
    // table data
    data?: any[]
    // remote sort configuration
    sortConfig?: Record<string, any>
    // whether to show the operation column
    showOperation?: boolean
  }>(),
  {
    id: '',
    loading: false,
    attrList: () => [],
    columns: () => [],
    passwordValue: () => ({}),
    loadingTip: '',
    showCheckbox: true,
    showDelete: true,
    data: () => [],
    sortConfig: () => ({ remote: true, trigger: 'cell' }),
    showOperation: true,
  }
)

const emit = defineEmits<{
  (e: 'onSelectChange', records: any[]): void
  (e: 'openDetail', id: any, activeTabKey?: string, ciDetailRelationKey?: string): void
  (e: 'deleteCI', row: any): void
}>()

const { t } = useI18n()
const attrs = useAttrs()

const xTableRef = ref<any>()
const jsonEditorRef = ref<InstanceType<typeof JsonEditor>>()

const referenceShowAttrNameMap = ref<Record<string, string>>({})
const referenceCIIdMap = ref<Record<string, Record<string, any>>>({})

// Range-select state (ported from the legacy OpsTable wrapper).
let lastSelected: any[] = []
let currentSelected: any[] = []

/** Whether an attribute is a long-text field. */
function isLongText(attr: Record<string, any>): boolean {
  return (
    attr.value_type === '2' &&
    attr.is_index === false &&
    !attr.is_link &&
    !attr.is_file &&
    !attr.is_password
  )
}

/** Simple deep-equality for JSON-serializable rows (drop-in for lodash.isEqual). */
function isEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

function getVxetableRef(): any {
  return xTableRef.value || null
}

function combinedRecords(xTable: any): any[] {
  return [...xTable.getCheckboxRecords(), ...xTable.getCheckboxReserveRecords()]
}

function onSelectChange() {
  const xTable = getVxetableRef()
  if (!xTable) return
  emit('onSelectChange', combinedRecords(xTable))
}

function onSelectRangeStart() {
  const xTable = getVxetableRef()
  if (!xTable) return
  lastSelected = [...xTable.getCheckboxRecords(), ...xTable.getCheckboxReserveRecords()]
}

function onSelectRangeChange(e: { records: any[] }) {
  const xTable = getVxetableRef()
  if (!xTable) return
  xTable.setCheckboxRow(lastSelected, true)
  currentSelected = e.records
}

function onSelectRangeEnd() {
  const xTable = getVxetableRef()
  if (!xTable) return
  const isAllSelected = currentSelected.every((item: any) => {
    const idx = lastSelected.findIndex((ele: any) => isEqual(ele, item))
    return idx > -1
  })
  if (isAllSelected) {
    xTable.setCheckboxRow(currentSelected, false)
  }
  currentSelected = []
  lastSelected = []
  emit('onSelectChange', combinedRecords(xTable))
}

function getCellStyle(params: { row: Record<string, any>; column: Record<string, any> }): Record<string, any> | undefined {
  const { row, column } = params
  const property = column.property
  const found = props.attrList.find((attr) => attr.name === property)
  if (
    found &&
    found.option &&
    found.option.fontOptions &&
    row[property] !== undefined &&
    row[property] !== null
  ) {
    return { ...found.option.fontOptions }
  }
  return undefined
}

function getColumnsEditRender(col: Record<string, any>): Record<string, any> {
  const editRender: Record<string, any> = { ...col.editRender }

  if (col.is_file) {
    editRender.enabled = false
  }

  if (col.value_type === '6') {
    editRender.events = { focus: handleFocusJson }
  }

  return editRender
}

function handleFocusJson({ column, row }: { column: Record<string, any>; row: Record<string, any> }) {
  jsonEditorRef.value?.open(column, row)
}

function jsonEditorOk(row: any, column: any, jsonData: any) {
  props.data.forEach((item) => {
    if (item._id === row._id) {
      item[column.property] = JSON.stringify(jsonData)
    }
  })
  getVxetableRef()?.refreshColumn()
}

function getChoiceValueStyle(col: Record<string, any>, colValue: any): Record<string, any> {
  const found = col.filters?.find((item: any[]) => String(item[0]) === String(colValue))
  if (found) {
    return found[1]?.style || {}
  }
  return {}
}

function getChoiceValueIcon(col: Record<string, any>, colValue: any): Record<string, any> {
  const found = col.filters?.find((item: any[]) => String(item[0]) === String(colValue))
  if (found) {
    return found[1]?.icon || {}
  }
  return {}
}

function getChoiceValueLabel(col: Record<string, any>, colValue: any): string {
  const found = col?.filters?.find((item: any[]) => String(item[0]) === String(colValue))
  if (found) {
    return found[1]?.label || ''
  }
  return ''
}

/** Open the CI detail page. */
function openDetail(id: any, activeTabKey?: string, ciDetailRelationKey?: string) {
  emit('openDetail', id, activeTabKey, ciDetailRelationKey)
}

function deleteCI(row: any) {
  emit('deleteCI', row)
}

function getRowSeq(row: Record<string, any>): number {
  return getVxetableRef()?.getRowSeq(row)
}

async function handleReferenceShowAttrName(columns: any[]) {
  const needRequiredCITypeIds =
    columns?.filter((col) => col?.is_reference && col?.reference_type_id).map((col) => col.reference_type_id) || []
  if (!needRequiredCITypeIds.length) {
    referenceShowAttrNameMap.value = {}
    return
  }

  const res = await getCITypes({ type_ids: needRequiredCITypeIds.join(',') })

  const map: Record<string, string> = {}
  res.ci_types.forEach((ciType: Record<string, any>) => {
    map[ciType.id] = ciType?.show_name || ciType?.unique_name || ''
  })

  referenceShowAttrNameMap.value = map
}

async function handleReferenceCIIdMap() {
  const referenceTypeCol =
    props.columns.filter((col) => col?.is_reference && col?.reference_type_id) || []
  if (!props.data?.length || !referenceTypeCol?.length) {
    referenceCIIdMap.value = {}
    return
  }

  const map: Record<string, Record<string, any>> = {}
  props.data.forEach((row) => {
    referenceTypeCol.forEach((col) => {
      const ids = Array.isArray(row[col.field]) ? row[col.field] : row[col.field] ? [row[col.field]] : []
      if (ids.length) {
        if (!map[col.reference_type_id]) {
          map[col.reference_type_id] = {}
        }
        ids.forEach((id: any) => {
          map[col.reference_type_id][id] = {}
        })
      }
    })
  })

  if (!Object.keys(map).length) {
    referenceCIIdMap.value = {}
    return
  }

  const allRes = await Promise.all(
    Object.keys(map).map((key) => {
      return searchCI({
        q: `_type:${key},_id:(${Object.keys(map[key]).join(';')})`,
        count: 9999,
      })
    })
  )

  allRes.forEach((res: any) => {
    res.result.forEach((item: Record<string, any>) => {
      if (map?.[item._type]?.[item._id]) {
        map[item._type][item._id] = item
      }
    })
  })

  referenceCIIdMap.value = map
}

function getReferenceAttrValue(id: any, col: Record<string, any>): string {
  const ci = referenceCIIdMap.value?.[col?.reference_type_id]?.[id]
  if (!ci) {
    return id
  }

  const attrName = referenceShowAttrNameMap.value?.[col.reference_type_id]
  return ci?.[attrName] || id
}

function getInitReferenceSelectOption(value: any, col: Record<string, any>): any[] {
  const ids = Array.isArray(value) ? value : value ? [value] : []
  if (!ids.length) {
    return []
  }

  const map = referenceCIIdMap.value?.[col?.reference_type_id]
  const attrName = referenceShowAttrNameMap.value?.[col?.reference_type_id]

  return (Array.isArray(value) ? value : [value]).map((id: any) => {
    return {
      key: id,
      title: map?.[id]?.[attrName] || id,
    }
  })
}

function showCustomEditComponent(col: Record<string, any>): boolean {
  if (isLongText(col)) {
    return true
  }

  return col.is_choice || col.is_password || col.is_bool || col.is_reference
}

// Recompute reference display names / values when columns or data change.
watch(
  () => props.columns,
  (newVal) => {
    handleReferenceShowAttrName(newVal)
  },
  { immediate: true, deep: true }
)

watch(
  () => {
    const referenceTypeCol =
      props.columns?.filter((col) => col?.is_reference && col?.reference_type_id) || []
    if (!props.data?.length || !referenceTypeCol?.length) {
      return []
    }

    const ids: any[] = []
    props.data.forEach((row) => {
      referenceTypeCol.forEach((col) => {
        if (row[col.field]) {
          ids.push(...(Array.isArray(row[col.field]) ? row[col.field] : [row[col.field]]))
        }
      })
    })

    return [...new Set(ids)]
  },
  () => {
    handleReferenceCIIdMap()
  },
  { immediate: true, deep: true }
)

defineExpose({ getVxetableRef })
</script>

<template>
  <div class="ci-table-wrap">
    <vxe-table
      :id="id"
      ref="xTableRef"
      v-bind="attrs"
      border
      keep-source
      show-overflow
      resizable
      size="small"
      :data="data"
      :loading="loading"
      :row-config="{ useKey: true, keyField: '_id' }"
      show-header-overflow
      highlight-hover-row
      :checkbox-config="{ reserve: true, highlight: true, range: true }"
      :edit-config="{ trigger: 'dblclick', mode: 'row', showIcon: false }"
      :sort-config="sortConfig"
      :column-config="{ useKey: true }"
      :cell-style="getCellStyle"
      :scroll-y="{ enabled: true, gt: 20 }"
      :scroll-x="{ enabled: true, gt: 20 }"
      :custom-config="{ storage: true }"
      class="ops-unstripe-table checkbox-hover-table"
      @checkbox-change="onSelectChange"
      @checkbox-all="onSelectChange"
      @checkbox-range-start="onSelectRangeStart"
      @checkbox-range-change="onSelectRangeChange"
      @checkbox-range-end="onSelectRangeEnd"
    >
      <vxe-column
        v-if="showCheckbox"
        align="center"
        type="checkbox"
        width="60"
        fixed="left"
      >
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
        :edit-render="getColumnsEditRender(col)"
        :cell-type="col.value_type === '2' ? 'string' : 'auto'"
        :fixed="col.is_fixed ? 'left' : ''"
      >
        <template #header>
          <span class="vxe-handle">
            <HolderOutlined class="header-move-icon" />
            <span>{{ col.title }}</span>
          </span>
        </template>
        <template v-if="showCustomEditComponent(col)" #edit="{ row }">
          <CIReferenceAttr
            v-if="col.is_reference"
            :reference-type-id="col.reference_type_id"
            :is-list="col.is_list"
            :reference-show-attr-name="referenceShowAttrNameMap[col.reference_type_id] || ''"
            :init-select-option="getInitReferenceSelectOption(row[col.field], col)"
            :value="row[col.field]"
            @change="(val) => { row[col.field] = val }"
          />
          <a-switch v-else-if="col.is_bool" v-model:checked="row[col.field]" />
          <!-- eslint-disable-next-line vue/no-mutating-props -->
          <vxe-input v-else-if="col.is_password" v-model="passwordValue[col.field]" />

          <a-textarea
            v-else-if="isLongText(col)"
            :value="col.is_list && Array.isArray(row[col.field]) ? row[col.field].join(',') : row[col.field]"
            :style="{ resize: 'none' }"
            :rows="1"
            @input="(e: any) => {
              row[col.field] = e.target.value
            }"
          />

          <a-select
            v-if="col.is_choice"
            v-model:value="row[col.field]"
            :get-popup-container="(trigger: HTMLElement) => trigger.parentElement"
            :style="{ width: '100%', height: '32px' }"
            :placeholder="t('placeholder2')"
            :show-arrow="false"
            :mode="col.is_list ? 'multiple' : undefined"
            class="ci-table-edit-select"
            allow-clear
            show-search
          >
            <a-select-option
              v-for="(choice, idx) in col.filters"
              :key="'edit_' + col.field + idx"
              :value="choice[0]"
            >
              <span
                :style="{
                  ...(choice[1] ? choice[1].style : {}),
                  display: 'inline-flex',
                  alignItems: 'center'
                }"
              >
                <template v-if="choice[1] && choice[1].icon && choice[1].icon.name">
                  <img
                    v-if="choice[1].icon.id && choice[1].icon.url"
                    :src="`/api/common-setting/v1/file/${choice[1].icon.url}`"
                    :style="{ maxHeight: '13px', maxWidth: '13px', marginRight: '5px' }"
                  />
                  <AppstoreOutlined
                    v-else
                    :style="{ color: choice[1].icon.color, marginRight: '5px' }"
                  />
                </template>
                <a-tooltip placement="topLeft" :title="choice[1] ? choice[1].label || choice[0] : choice[0]">
                  <span>{{ choice[1] ? choice[1].label || choice[0] : choice[0] }}</span>
                </a-tooltip>
              </span>
            </a-select-option>
          </a-select>
        </template>
        <template
          v-if="col.value_type === '6' || col.is_link || col.is_password || col.is_choice || col.is_reference || col.is_file"
          #default="{ row }"
        >
          <template v-if="col.is_reference">
            <a
              v-for="ciId in (col.is_list ? row[col.field] : [row[col.field]])"
              :key="ciId"
              :href="`/cmdb/cidetail/${col.reference_type_id}/${ciId}`"
              target="_blank"
            >
              {{ getReferenceAttrValue(ciId, col) }}
            </a>
          </template>
          <span v-else-if="col.value_type === '6' && row[col.field]">{{ row[col.field] }}</span>
          <template v-else-if="col.is_link && row[col.field]">
            <a
              v-for="(item, linkIndex) in (col.is_list ? row[col.field] : [row[col.field]])"
              :key="linkIndex"
              :href="
                item.startsWith('http') || item.startsWith('https')
                  ? `${item}`
                  : `http://${item}`
              "
              target="_blank"
            >
              {{ getChoiceValueLabel(col, item) || item }}
            </a>
          </template>
          <PasswordField
            v-else-if="col.is_password && row[col.field]"
            :ci_id="row._id"
            :attr_id="col.attr_id"
          />
          <CiFileField
            v-else-if="col.is_file"
            :value="row[col.field]"
            :is-list="col.is_list"
            :is-edit="false"
            :attr-id="col.attr_id"
            :ci-id="row.ci_id || row._id"
            :attr-name="col.field"
            @input="(val) => { row[col.field] = val }"
          />
          <template v-else-if="col.is_choice">
            <span
              v-for="value in (col.is_list ? row[col.field] : [row[col.field]])"
              :key="value"
              :style="getChoiceValueStyle(col, value)"
              class="column-default-choice"
            >
              <img
                v-if="getChoiceValueIcon(col, value).id && getChoiceValueIcon(col, value).url"
                :src="`/api/common-setting/v1/file/${getChoiceValueIcon(col, value).url}`"
                :style="{ maxHeight: '13px', maxWidth: '13px', marginRight: '5px' }"
              />
              <AppstoreOutlined
                v-else-if="getChoiceValueIcon(col, value).name"
                :style="{ color: getChoiceValueIcon(col, value).color, marginRight: '5px' }"
              />
              {{ getChoiceValueLabel(col, value) || value }}
            </span>
          </template>
        </template>
      </vxe-column>
      <vxe-column v-if="showOperation" align="left" field="operate" fixed="right" width="80">
        <template #header>
          <span>{{ t('operation') }}</span>
        </template>
        <template #default="{ row }">
          <a-space>
            <a @click="openDetail(row.ci_id || row._id)">
              <UnorderedListOutlined />
            </a>
            <a-tooltip :title="t('cmdb.ci.viewRelation')">
              <a @click="openDetail(row.ci_id || row._id, 'tab_2', '2')">
                <RetweetOutlined />
              </a>
            </a-tooltip>
            <a v-if="showDelete" :style="{ color: 'red' }" @click="deleteCI(row)">
              <DeleteOutlined />
            </a>
          </a-space>
        </template>
      </vxe-column>
      <template #empty>
        <div v-if="loading" class="ci-table-loading">
          {{ loadingTip || t('loading') }}
        </div>
        <div v-else>
          <img :style="{ width: '200px' }" :src="dataEmptyImg" />
          <div>{{ t('noData') }}</div>
        </div>
      </template>
      <template #loading>
        <div class="ci-table-loading">{{ loadingTip || t('loading') }}</div>
      </template>
    </vxe-table>

    <JsonEditor ref="jsonEditorRef" @json-editor-ok="jsonEditorOk" />
  </div>
</template>

<style lang="less" scoped>
.ci-table-wrap {
  .ci-table-loading {
    width: 100%;
    line-height: 200px;
  }

  .header-move-icon {
    width: 17px;
    height: 17px;
    display: none;
    position: absolute;
    left: -3px;
    top: 12px;
  }

  .column-default-choice {
    border-radius: 4px;
    padding: 1px 5px;
    margin: 2px;
    vertical-align: bottom;
    display: inline-flex;
    align-items: center;
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
