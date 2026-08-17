<script setup lang="ts">
import { computed, inject, onMounted, onUpdated, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { FilterFilled } from '@ant-design/icons-vue'
import SearchForm from './searchForm.vue'
import OperateTypeTag from '../components/OperateTypeTag.vue'
import { getCITypesTable, getUsers } from '@/modules/cmdb/api/history'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { getRelationTypes } from '@/modules/cmdb/api/relationType'
import { deepCompare } from '@/modules/cmdb/utils/objectDiff'
import { useOperationHistory } from '../composables/useOperationHistory'
import { PAGINATION_CONFIG } from '../constants'

const { t, locale } = useI18n()
const { handleError, applyFilter } = useOperationHistory()
const reload = inject<(() => void) | null>('reload', null)

const xTableRef = ref<any>()

const loading = ref(true)
const relationTypeList = ref<Map<number, string> | null>(null)
const typeList = ref<Map<number, string> | null>(null)
const userList = ref<Map<number, string>>(new Map())
const pageSizeOptions = PAGINATION_CONFIG.PAGE_SIZE_OPTIONS.map(String)
const isExpand = ref(false)
const current = ref(1)
const pageSize = ref(50)
const numfound = ref(0)
const tableData = ref<any[]>([])
const queryParams = ref<Record<string, any>>({
  page: 1,
  page_size: PAGINATION_CONFIG.DEFAULT_PAGE_SIZE,
  type_id: undefined,
  operate_type: undefined,
})
const ciTypeChoices = ref<Array<Record<string, any>>>([])

const windowHeight = computed(() => window.innerHeight)
const windowHeightMinus = computed(() => (isExpand.value ? 446 : 381))

const operateTypeMap = computed(
  () =>
    new Map<string, string>([
      ['0', t('cmdb.history.addCIType')],
      ['1', t('cmdb.history.updateCIType')],
      ['2', t('cmdb.history.deleteCIType')],
      ['3', t('cmdb.history.addAttribute')],
      ['4', t('cmdb.history.updateAttribute')],
      ['5', t('cmdb.history.deleteAttribute')],
      ['6', t('cmdb.history.addTrigger')],
      ['7', t('cmdb.history.updateTrigger')],
      ['8', t('cmdb.history.deleteTrigger')],
      ['9', t('cmdb.history.addUniqueConstraint')],
      ['10', t('cmdb.history.updateUniqueConstraint')],
      ['11', t('cmdb.history.deleteUniqueConstraint')],
      ['12', t('cmdb.history.addRelation')],
      ['13', t('cmdb.history.deleteRelation')],
      ['14', t('cmdb.history.addReconciliation')],
      ['15', t('cmdb.history.updateReconciliation')],
      ['16', t('cmdb.history.deleteReconciliation')],
    ])
)

const typeTableAttrList = computed(() => [
  {
    alias: t('cmdb.ciType.ciType'),
    is_choice: true,
    name: 'type_id',
    value_type: '2',
    choice_value: ciTypeChoices.value,
  },
  {
    alias: t('operation'),
    is_choice: true,
    name: 'operate_type',
    value_type: '2',
    choice_value: [
      { [t('cmdb.history.addCIType')]: 0 },
      { [t('cmdb.history.updateCIType')]: 1 },
      { [t('cmdb.history.deleteCIType')]: 2 },
      { [t('cmdb.history.addAttribute')]: 3 },
      { [t('cmdb.history.updateAttribute')]: 4 },
      { [t('cmdb.history.deleteAttribute')]: 5 },
      { [t('cmdb.history.addTrigger')]: 6 },
      { [t('cmdb.history.updateTrigger')]: 7 },
      { [t('cmdb.history.deleteTrigger')]: 8 },
      { [t('cmdb.history.addUniqueConstraint')]: 9 },
      { [t('cmdb.history.updateUniqueConstraint')]: 10 },
      { [t('cmdb.history.deleteUniqueConstraint')]: 11 },
      { [t('cmdb.history.addRelation')]: 12 },
      { [t('cmdb.history.deleteRelation')]: 13 },
      { [t('cmdb.history.addReconciliation')]: 14 },
      { [t('cmdb.history.updateReconciliation')]: 15 },
      { [t('cmdb.history.deleteReconciliation')]: 16 },
    ],
  },
])

watch(current, (val) => {
  queryParams.value.page = val
})

watch(pageSize, (val) => {
  queryParams.value.page_size = val
})

watch(locale, () => {
  reload?.()
})

onMounted(async () => {
  await Promise.all([getRelationTypeList(), getTypes(), getUserList()])
  await getTable(queryParams.value)
})

onUpdated(() => {
  const el = xTableRef.value?.$el
  if (el) {
    const wrapper = el.querySelector('.vxe-table--body-wrapper')
    if (wrapper) {
      wrapper.scrollTop = 0
    }
  }
})

async function getTable(params: Record<string, any>) {
  try {
    loading.value = true
    const res = await getCITypesTable(params)
    res.result.forEach((item: any) => {
      handleChangeDescription(item, item.operate_type)
      item.operate_type = handleOperateType(item.operate_type)
      item.type_id = handleTypeId(item.type_id)
      item.uid = handleUID(item.uid)
    })
    tableData.value = res.result
    pageSize.value = res.page_size
    current.value = res.page
    numfound.value = res.numfound
  } finally {
    loading.value = false
  }
}

async function getTypes() {
  try {
    const res = await getCITypes()
    const typesArr: Array<Record<string, any>> = []
    const typesMap = new Map<number, string>()
    res.ci_types.forEach((item: any) => {
      if (item.alias) {
        typesMap.set(item.id, item.alias)
        typesArr.push({ [item.alias]: item.id })
      }
    })
    typeList.value = typesMap
    ciTypeChoices.value = typesArr
  } catch (error) {
    handleError(error, 'fetch CI types')
  }
}

async function getUserList() {
  try {
    const res = await getUsers({})
    const userListMap = new Map<number, string>()
    res.forEach((item: any) => {
      userListMap.set(item.uid, item.nickname)
    })
    userList.value = userListMap
  } catch (error) {
    handleError(error, 'fetch users')
  }
}

async function getRelationTypeList() {
  try {
    const res = await getRelationTypes()
    const relationTypeMap = new Map<number, string>()
    res.forEach((item: any) => {
      relationTypeMap.set(item.id, item.name)
    })
    relationTypeList.value = relationTypeMap
  } catch (error) {
    handleError(error, 'fetch relation types')
  }
}

function onChange(pageNum: number) {
  current.value = pageNum
  getTable(queryParams.value)
}

function onShowSizeChange(_current: number, size: number) {
  current.value = 1
  pageSize.value = size
  getTable(queryParams.value)
}

function handleExpandChange(expand: boolean) {
  isExpand.value = expand
}

function handleSearch(params: Record<string, any>) {
  current.value = 1
  queryParams.value = params
  getTable(params)
}

function searchFormReset() {
  queryParams.value = {
    page: 1,
    page_size: PAGINATION_CONFIG.DEFAULT_PAGE_SIZE,
    type_id: undefined,
    operate_type: undefined,
  }
  getTable(queryParams.value)
}

function handleOperateType(operate_type: string) {
  return operateTypeMap.value.get(operate_type)
}

function handleTypeId(typeIdValue: number) {
  return typeList.value?.get(typeIdValue) ? typeList.value.get(typeIdValue) : typeIdValue
}

function handleUID(uid: number) {
  return userList.value.get(uid)
}

function handleRelationType(relation_type_id: number) {
  return relationTypeList.value?.get(relation_type_id)
}

function handleChangeDescription(item: any, operate_type: string) {
  switch (operate_type) {
    // add CIType
    case '0': {
      item.changeDescription = `${t('cmdb.history.addCIType')}: ${item.change.alias}`
      break
    }
    // update CIType
    case '1': {
      item.changeArr = []
      const diffs = deepCompare({
        obj1: item?.change?.old,
        obj2: item?.change?.new,
        ignoreKeys: ['updated_at'],
      })
      for (const val of diffs) {
        const str = ` [ ${val.path} :  ${val.value1} -> ${val.value2} ] `
        item.changeDescription += str
        item.changeArr.push(str)
      }
      if (!item.changeDescription) item.changeDescription = t('cmdb.history.noModifications')
      break
    }
    // delete CIType
    case '2': {
      item.changeDescription = `${t('cmdb.history.deleteCIType')}: ${item.change.alias}`
      break
    }
    // add Attribute
    case '3': {
      item.changeDescription = `${t('cmdb.history.attr')}：${item.change.alias}`
      break
    }
    // update Attribute
    case '4': {
      item.changeArr = []
      const diffs = deepCompare({
        obj1: item?.change?.old,
        obj2: item?.change?.new,
        ignoreKeys: ['updated_at'],
      })
      for (const val of diffs) {
        const str = ` [ ${val.path} :  ${val.value1} -> ${val.value2} ] `
        item.changeDescription += str
        item.changeArr.push(str)
      }
      if (!item.changeDescription) item.changeDescription = t('cmdb.history.noModifications')
      break
    }
    // delete Attribute
    case '5': {
      item.changeDescription = `${t('delete')}：${item.change.alias}`
      break
    }
    // add trigger
    case '6': {
      item.changeDescription = `${t('cmdb.history.addTrigger')}：${item?.change?.option?.name || ''}`
      break
    }
    // update trigger
    case '7': {
      item.changeArr = []
      const diffs = deepCompare({
        obj1: item?.change?.old,
        obj2: item?.change?.new,
        directDeepKeys: ['notifies'],
        ignoreKeys: ['updated_at'],
      })
      for (const val of diffs) {
        const str = ` [ ${val.path} :  ${val.value1} -> ${val.value2} ] `
        item.changeDescription += str
        item.changeArr.push(str)
      }
      if (!item.changeDescription) item.changeDescription = t('cmdb.history.noModifications')
      break
    }
    // delete trigger
    case '8': {
      item.changeDescription = `${t('cmdb.history.deleteTrigger')}：${item?.change?.option?.name || ''}`
      break
    }
    // add unique constraint
    case '9': {
      item.changeDescription = `${t('cmdb.history.attrId')}：[${item.change.attr_ids}]`
      break
    }
    // update unique constraint
    case '10': {
      item.changeArr = []
      const oldVal = item.change.old.attr_ids
      const newVal = item.change.new.attr_ids
      const str = `${t('cmdb.history.attrId')}：[${oldVal}] -> [${newVal}]`
      item.changeDescription = str
      item.changeArr.push(str)
      break
    }
    // delete unique constraint
    case '11': {
      item.changeDescription = `${t('cmdb.history.attrId')}：[${item.change.attr_ids}]`
      break
    }
    // add relation
    case '12': {
      item.changeDescription = `${t('new')}：${item.change.parent.alias} -> ${handleRelationType(
        item.change.relation_type_id
      )} -> ${item.change.child.alias}`
      break
    }
    // delete relation
    case '13': {
      item.changeDescription = `${t('delete')}：${item.change.parent_id.alias} -> ${handleRelationType(
        item.change.relation_type_id
      )} -> ${item.change.child.alias}`
      break
    }
    case '14': {
      item.changeDescription = `${t('cmdb.history.addReconciliation')}: ${item.change.name || item.change.alias}`
      break
    }
    case '15': {
      item.changeArr = []
      const diffs = deepCompare({
        obj1: item?.change?.old,
        obj2: item?.change?.new,
        directDeepKeys: ['notifies'],
        ignoreKeys: ['updated_at'],
      })
      for (const val of diffs) {
        const str = ` [ ${val.path} :  ${val.value1} -> ${val.value2} ] `
        item.changeDescription += str
        item.changeArr.push(str)
      }
      if (!item.changeDescription) item.changeDescription = t('cmdb.history.updateReconciliation')
      break
    }
    case '16': {
      item.changeDescription = `${t('cmdb.history.deleteReconciliation')}: ${item.change.name || item.change.alias}`
      break
    }
  }
}

function filterOperate() {
  applyFilter(queryParams.value, getTable)
}

function filterOperateReset() {
  applyFilter(queryParams.value, getTable, { operate_type: undefined })
}

async function handleExport(params: Record<string, any>) {
  const hide = message.loading(t('loading'), 0)
  try {
    const res = await getCITypesTable({
      ...params,
      page: queryParams.value.page,
      page_size: queryParams.value.page_size,
    })
    hide()

    if (!res.result || res.result.length === 0) {
      message.warning(t('noData'))
      return
    }

    res.result.forEach((item: any) => {
      handleChangeDescription(item, item.operate_type)
      item.operate_type = handleOperateType(item.operate_type)
      item.type_id = handleTypeId(item.type_id)
      item.uid = handleUID(item.uid)
      if (item.operate_type.includes(t('update'))) {
        item.changeDescription = item.changeArr.join(';')
      }
    })

    await xTableRef.value?.getVxetableRef()?.exportData({
      filename: `${t('cmdb.history.ciTypeChange')}_${new Date().toISOString().split('T')[0]}`,
      sheetName: 'Sheet1',
      type: 'xlsx',
      types: ['xlsx'],
      isMerge: true,
      isColgroup: true,
      data: res.result,
    })

    message.success(t('exportSuccess'))
  } catch (error) {
    hide()
    handleError(error, 'export')
  }
}
</script>

<template>
  <div class="operation-history-table">
    <search-form
      :attr-list="typeTableAttrList"
      @expand-change="handleExpandChange"
      @search="handleSearch"
      @search-form-reset="searchFormReset"
      @export="handleExport"
    ></search-form>
    <vxe-table
      ref="xTableRef"
      :loading="loading"
      resizable
      :data="tableData"
      :max-height="`${windowHeight - windowHeightMinus}px`"
      :row-config="{ keyField: '_XID', isHover: true }"
      size="small"
      stripe
      class="ops-stripe-table"
    >
      <vxe-column field="created_at" width="165" :title="t('cmdb.history.opreateTime')"></vxe-column>
      <vxe-column field="user" width="120" :title="t('cmdb.history.user')"></vxe-column>
      <vxe-column field="operate_type" width="140" :title="t('operation')">
        <template #header="{ column }">
          <span>{{ column.title }}</span>
          <a-popover trigger="click" placement="bottom">
            <FilterFilled class="filter" :class="{ active: queryParams.operate_type !== undefined }" />
            <template #content>
              <div class="filter-content">
                <a-select
                  v-model:value="queryParams.operate_type"
                  :placeholder="t('cmdb.history.filterOperate')"
                  show-search
                  option-filter-prop="label"
                  style="width: 200px"
                  allow-clear
                >
                  <a-select-option
                    v-for="(choice, index) in typeTableAttrList[1].choice_value"
                    :key="index"
                    :value="Object.values(choice)[0]"
                    :label="Object.keys(choice)[0]"
                  >
                    {{ Object.keys(choice)[0] }}
                  </a-select-option>
                </a-select>
                <a-button type="link" class="filterButton" @click="filterOperate">
                  {{ t('cmdb.history.filter') }}
                </a-button>
                <a-button type="link" class="filterResetButton" @click="filterOperateReset">
                  {{ t('reset') }}
                </a-button>
              </div>
            </template>
          </a-popover>
        </template>
        <template #default="{ row }">
          <operate-type-tag :operate-type="row.operate_type" />
        </template>
      </vxe-column>
      <vxe-column field="type_id" :title="t('cmdb.ciType.ciType')" width="150">
        <template #default="{ row }">
          {{ row.operate_type === t('cmdb.history.deleteCIType') ? row.change.alias : row.type_id }}
        </template>
      </vxe-column>
      <vxe-column field="changeDescription" :title="t('desc')" min-width="200">
        <template #default="{ row }">
          <div v-if="row.changeDescription === t('cmdb.history.noUpdate')" class="change-text">
            {{ row.changeDescription }}
          </div>
          <template v-else-if="row.operate_type.includes(t('update'))">
            <div v-for="(tag, index) in row.changeArr" :key="index" class="change-text update-text">
              {{ tag }}
            </div>
          </template>
          <div v-else-if="row.operate_type.includes(t('new'))" class="change-text new-text">
            {{ row.changeDescription }}
          </div>
          <div v-else-if="row.operate_type.includes(t('delete'))" class="change-text delete-text">
            {{ row.changeDescription }}
          </div>
        </template>
      </vxe-column>
    </vxe-table>
    <a-row class="row" justify="end">
      <a-col>
        <a-pagination
          v-model:current="current"
          size="small"
          :page-size-options="pageSizeOptions"
          :total="numfound"
          show-size-changer
          :page-size="pageSize"
          :show-total="(total: number) => t('cmdb.history.totalItems', { total })"
          @change="onChange"
          @show-size-change="onShowSizeChange"
        ></a-pagination>
      </a-col>
    </a-row>
  </div>
</template>

<style lang="less" scoped>
@import '../styles/table.less';

.row {
  margin-top: 5px;
}
</style>
