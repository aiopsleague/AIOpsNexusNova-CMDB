<script setup lang="ts">
import { computed, provide, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { searchCI } from '@/modules/cmdb/api/ci'
import { getSubscribeAttributes } from '@/modules/cmdb/api/preference'
import { batchUpdateCIRelationChildren, batchUpdateCIRelationParents } from '@/modules/cmdb/api/CIRelation'
import { getCITableColumns } from '@/modules/cmdb/utils/helper'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { SUB_NET_CITYPE_NAME, SCOPE_CITYPE_NAME, ADDRESS_CITYPE_NAME } from '@/modules/cmdb/views/ipam/constants'
import SearchForm from '@/modules/cmdb/components/searchForm/SearchForm.vue'
import CreateInstanceForm from '@/modules/cmdb/views/ci/modules/CreateInstanceForm.vue'

const { t } = useI18n()

const emit = defineEmits<{ (e: 'reload'): void }>()

const xTable = ref<any>()
const searchForm = ref<InstanceType<typeof SearchForm>>()
const createInstanceForm = ref<InstanceType<typeof CreateInstanceForm>>()

const visible = ref(false)
const currentPage = ref(1)
const totalNumber = ref(0)
const tableData = ref<any[]>([])
const columns = ref<any[]>([])
const ciObj = ref<Record<string, any>>({})
const ciId = ref<string | number | null>(null)
const addTypeId = ref<number | null>(null)
const loading = ref(false)
const type = ref<'children' | 'parent'>('children')
const preferenceAttrList = ref<any[]>([])
const ancestor_ids = ref<unknown>(undefined)
const attrList = ref<any[]>([])
const showCreateBtn = ref(true) // Whether to show the create button.

const referenceShowAttrNameMap = ref<Record<string, string>>({})
const referenceCIIdMap = ref<Record<string, Record<string, any>>>({})

const tableHeight = computed(() => window.innerHeight - 250)

provide(
  'attrList',
  () => attrList.value
)

async function openModal(
  _ciObj: Record<string, any>,
  _ciId: string | number,
  addType: { id: number; name: string },
  _type: 'children' | 'parent',
  _ancestor_ids: unknown = undefined
) {
  visible.value = true
  ciObj.value = _ciObj
  ciId.value = _ciId
  addTypeId.value = addType.id
  type.value = _type
  ancestor_ids.value = _ancestor_ids
  showCreateBtn.value = ![SUB_NET_CITYPE_NAME, SCOPE_CITYPE_NAME, ADDRESS_CITYPE_NAME].includes(addType.name)

  await getSubscribeAttributes(addTypeId.value).then((res) => {
    preferenceAttrList.value = res.attributes // All subscribed columns.
    handleReferenceShowAttrName()
  })
  getCITypeAttributesById(addTypeId.value).then((res) => {
    attrList.value = res.attributes
  })
  getTableData(true)
}

async function getTableData(isInit: boolean) {
  if (addTypeId.value) {
    await fetchData(isInit)
  }
}

async function fetchData(isInit: boolean) {
  loading.value = true
  let fuzzySearch = ''
  let exp: string | null = null
  if (!isInit) {
    fuzzySearch = searchForm.value?.fuzzySearch ?? ''
    const expression = searchForm.value?.expression || ''
    const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g

    exp = expression.match(regQ) ? expression.match(regQ)![0] : null
  }

  await searchCI({
    q: `_type:${addTypeId.value}${exp ? `,${exp}` : ''}${fuzzySearch ? `,*${fuzzySearch}*` : ''}`,
    count: 50,
    page: currentPage.value,
  })
    .then((res: any) => {
      tableData.value = res.result
      totalNumber.value = res.numfound
      columns.value = getColumns(res.result, preferenceAttrList.value)
      const _table = xTable.value
      if (_table) {
        _table.refreshColumn()
      }
      loading.value = false

      handleReferenceCIIdMap()
    })
    .catch(() => {
      loading.value = false
    })
}

function getColumns(data: any[], attrListParam: any[]) {
  const modalDom = document.getElementById('add-table-modal')
  if (modalDom) {
    const width = modalDom.clientWidth - 50
    return getCITableColumns(data, attrListParam, width)
  }
  return []
}

async function handleReferenceShowAttrName() {
  const needRequiredCITypeIds =
    preferenceAttrList.value
      ?.filter((attr) => attr?.is_reference && attr?.reference_type_id)
      .map((attr) => attr.reference_type_id) || []
  if (!needRequiredCITypeIds.length) {
    referenceShowAttrNameMap.value = {}
    return
  }

  const res = await getCITypes({ type_ids: needRequiredCITypeIds.join(',') })

  const map: Record<string, string> = {}
  res.ci_types.forEach((ciType: any) => {
    map[ciType.id] = ciType?.show_name || ciType?.unique_name || ''
  })

  referenceShowAttrNameMap.value = map
}

async function handleReferenceCIIdMap() {
  const referenceTypeCol =
    preferenceAttrList.value.filter((attr) => attr?.is_reference && attr?.reference_type_id) || []
  if (!tableData.value?.length || !referenceTypeCol?.length) {
    referenceCIIdMap.value = {}
    return
  }

  const map: Record<string, Record<string, any>> = {}
  tableData.value.forEach((row) => {
    referenceTypeCol.forEach((col) => {
      const ids = Array.isArray(row[col.name]) ? row[col.name] : row[col.name] ? [row[col.name]] : []
      if (ids.length) {
        if (!map?.[col.reference_type_id]) {
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
    res.result.forEach((item: any) => {
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

function onSelectChange() {}

function handleClose() {
  const _table = xTable.value
  if (_table) {
    _table.clearCheckboxRow()
  }

  currentPage.value = 1
  visible.value = false
  showCreateBtn.value = true
}

async function handleOk() {
  const _table = xTable.value
  const selectRecordsCurrent = _table?.getCheckboxRecords?.() || []
  const selectRecordsReserved = _table?.getCheckboxReserveRecords?.() || []

  const ciIds = [...selectRecordsCurrent, ...selectRecordsReserved].map((record: any) => record._id)
  if (ciIds.length) {
    if (type.value === 'children') {
      await batchUpdateCIRelationChildren(ciIds, [ciId.value], ancestor_ids.value)
    } else {
      await batchUpdateCIRelationParents(ciIds, [ciId.value])
    }
    setTimeout(() => {
      message.success(t('addSuccess'))
      handleClose()
      emit('reload')
    }, 500)
  } else {
    handleClose()
    emit('reload')
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchData(false)
}

function handleChangePage(page: number) {
  currentPage.value = page
  fetchData(false)
}

function getChoiceValueLabel(col: Record<string, any>, colValue: any): string {
  const _find = col.filters.find((item: any[]) => String(item[0]) === String(colValue))
  if (_find) {
    return _find[1]?.label || ''
  }
  return ''
}

defineExpose({ openModal })

</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <a-modal
    v-model:open="visible"
    width="90%"
    :closable="false"
    :centered="true"
    :mask-closable="false"
    destroy-on-close
    @cancel="handleClose"
    @ok="handleOk"
  >
    <div :style="{ width: '100%' }" id="add-table-modal">
      <a-spin :spinning="loading">
        <SearchForm
          ref="searchForm"
          :type-id="addTypeId"
          :preference-attr-list="preferenceAttrList"
          @refresh="handleSearch"
        >
          <a-button
            v-if="showCreateBtn"
            @click="() => createInstanceForm?.handleOpen(true, 'create')"
            type="primary"
            size="small"
          >
            {{ t('create') }}
          </a-button>
        </SearchForm>
        <vxe-table
          ref="xTable"
          :data="tableData"
          :height="tableHeight"
          :row-config="{ keyField: '_id' }"
          highlight-hover-row
          :checkbox-config="{ reserve: true, highlight: true, range: true }"
          @checkbox-change="onSelectChange"
          @checkbox-all="onSelectChange"
          show-overflow="tooltip"
          show-header-overflow="tooltip"
          :scroll-y="{ enabled: true, gt: 50 }"
          :scroll-x="{ enabled: true, gt: 0 }"
          class="ops-stripe-table"
        >
          <vxe-column align="center" type="checkbox" width="60" fixed="left"></vxe-column>
          <vxe-column
            v-for="col in columns"
            :key="col.field"
            :title="col.title"
            :field="col.field"
            :width="col.width"
            :sortable="col.sortable"
          >
            <template v-if="col.is_reference" #default="{ row }">
              <a
                v-for="id in col.is_list ? row[col.field] : [row[col.field]]"
                :key="id"
                :href="`/cmdb/cidetail/${col.reference_type_id}/${id}`"
                target="_blank"
              >
                {{ getReferenceAttrValue(id, col) }}
              </a>
            </template>
            <template v-else-if="col.is_choice" #default="{ row }">
              <span v-for="value in col.is_list ? row[col.field] : [row[col.field]]" :key="value">
                {{ getChoiceValueLabel(col, value) || value }}
              </span>
            </template>
            <template v-else-if="col.value_type == '6'" #default="{ row }">
              <span v-if="col.value_type == '6' && row[col.field]">{{ JSON.stringify(row[col.field]) }}</span>
            </template>
          </vxe-column>
        </vxe-table>
        <a-pagination
          v-model:current="currentPage"
          size="small"
          :total="totalNumber"
          show-quick-jumper
          :page-size="50"
          :show-total="
            (total: number, range: number[]) =>
              t('pagination.total', {
                range0: range[0],
                range1: range[1],
                total,
              })
          "
          :style="{ textAlign: 'right', marginTop: '10px' }"
          @change="handleChangePage"
        />
      </a-spin>
    </div>
    <CreateInstanceForm
      ref="createInstanceForm"
      :type-id-from-relation="addTypeId ?? undefined"
      @reload="
        () => {
          currentPage = 1
          getTableData(true)
        }
      "
    />
  </a-modal>
</template>

<style lang="less" scoped></style>
