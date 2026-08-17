<script setup lang="ts">
import { computed, inject, onMounted, onUpdated, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { FilterFilled } from '@ant-design/icons-vue'
import Pager from '@/components/Pager/index.vue'
import SearchForm from './searchForm.vue'
import OperateTypeTag from '../components/OperateTypeTag.vue'
import { getCIHistoryTable, getUsers } from '@/modules/cmdb/api/history'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { useOperationHistory } from '../composables/useOperationHistory'
import { PAGINATION_CONFIG } from '../constants'

const { t, locale } = useI18n()
const { handleError, applyFilter, createMergeRowMethod } = useOperationHistory()
const reload = inject<(() => void) | null>('reload', null)

const childRef = ref<InstanceType<typeof SearchForm>>()
const xTableRef = ref<any>()

const typeId = ref<number | undefined>(undefined)
const loading = ref(true)
const typeList = ref<Map<number, string> | null>(null)
const userList = ref<Array<Record<string, any>>>([])
const attrList = ref<Array<Record<string, any>>>([])
const tableData = ref<any[]>([])
const total = ref(0)
const isExpand = ref(false)
const queryParams = ref<Record<string, any>>({
  page: 1,
  page_size: PAGINATION_CONFIG.DEFAULT_PAGE_SIZE,
})
const PAGE_SIZE_OPTIONS = PAGINATION_CONFIG.PAGE_SIZE_OPTIONS

const windowHeight = computed(() => window.innerHeight)
const windowHeightOffset = computed(() => (isExpand.value ? 446 : 381))

const operateTypeMap = computed(
  () =>
    new Map<string, string>([
      ['0', t('new')],
      ['1', t('delete')],
      ['2', t('update')],
    ])
)

const ciTypeChoices = computed(() => {
  if (!typeList.value) return []
  const choices: Array<Record<string, any>> = []
  typeList.value.forEach((alias, id) => {
    choices.push({ [alias]: id })
  })
  return choices
})

const attrChoices = computed(() => attrList.value || [])

const ciTableAttrList = computed(() => [
  {
    alias: t('cmdb.ciType.date'),
    is_choice: false,
    name: 'datetime',
    value_type: '3',
  },
  {
    alias: t('cmdb.history.user'),
    is_choice: true,
    name: 'username',
    value_type: '2',
    choice_value: userList.value,
  },
  {
    alias: t('cmdb.ciType.ciType'),
    is_choice: true,
    name: 'type_id',
    value_type: '2',
    choice_value: ciTypeChoices.value,
  },
  {
    alias: t('cmdb.history.attribute'),
    is_choice: true,
    name: 'attr_id',
    value_type: '2',
    choice_value: attrChoices.value,
  },
  {
    alias: t('operation'),
    is_choice: true,
    name: 'operate_type',
    value_type: '2',
    choice_value: [
      { [t('new')]: 0 },
      { [t('delete')]: 1 },
      { [t('update')]: 2 },
    ],
  },
  {
    alias: 'CI ID',
    is_choice: false,
    name: 'ci_id',
    value_type: '2',
  },
])

watch(locale, () => {
  reload?.()
})

watch(attrList, () => {
  if (childRef.value) {
    delete childRef.value.queryParams.attr_id
  }
})

onMounted(async () => {
  attrList.value = []
  await Promise.all([getUserList(), getTypes()])
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

function uniqBy(list: any[], key: string): any[] {
  const seen = new Set()
  return list.filter((item) => {
    const val = item[key]
    if (seen.has(val)) return false
    seen.add(val)
    return true
  })
}

async function getTable(params: Record<string, any>) {
  try {
    loading.value = true
    const res = await getCIHistoryTable(params)
    const tempArr: any[] = []
    res.records.forEach((item: any) => {
      item[0].type_id = handleTypeId(item[0].type_id)
      item[1].forEach((subItem: any) => {
        subItem.operate_type = handleOperateType(subItem.operate_type)
        const tempObj = Object.assign(subItem, item[0])
        tempArr.push(tempObj)
      })
    })
    tableData.value = tempArr
    total.value = res.total
  } catch (error) {
    handleError(error, 'fetch data')
  } finally {
    loading.value = false
  }
}

async function getUserList() {
  try {
    const res = await getUsers({})
    const users = uniqBy(res || [], 'nickname')
    userList.value = users.map((x: any) => {
      const username = x.nickname
      return { [username]: username }
    })
  } catch (error) {
    handleError(error, 'fetch users')
  }
}

async function getTypes() {
  try {
    const res = await getCITypes()
    const typesMap = new Map<number, string>()
    res.ci_types.forEach((item: any) => {
      if (item.alias) {
        typesMap.set(item.id, item.alias)
      }
    })
    typeList.value = typesMap
  } catch (error) {
    handleError(error, 'fetch CI types')
  }
}

async function getAttrs(typeIdValue: number | undefined) {
  if (!typeIdValue) {
    attrList.value = []
    return
  }
  try {
    const res = await getCITypeAttributesById(typeIdValue)
    const attrsArr: Array<Record<string, any>> = []
    res.attributes.forEach((item: any) => {
      if (item.alias) {
        attrsArr.push({ [item.alias]: item.id })
      }
    })
    attrList.value = attrsArr
  } catch (error) {
    handleError(error, 'fetch attributes')
  }
}

function onShowSizeChange(size: number) {
  queryParams.value.page_size = size
  queryParams.value.page = 1
  getTable(queryParams.value)
}

function onChange(pageNum: number) {
  queryParams.value.page = pageNum
  getTable(queryParams.value)
}

function handleExpandChange(expand: boolean) {
  isExpand.value = expand
}

function handleSearch(params: Record<string, any>) {
  queryParams.value = params
  getTable(params)
}

function searchFormReset() {
  queryParams.value = {
    page: 1,
    page_size: PAGINATION_CONFIG.DEFAULT_PAGE_SIZE,
    start: '',
    end: '',
    username: '',
    ci_id: undefined,
    attr_id: undefined,
    operate_type: undefined,
  }
  attrList.value = []
  getTable(queryParams.value)
}

function handleOperateType(operate_type: string) {
  return operateTypeMap.value.get(operate_type)
}

function handleTypeId(typeIdValue: number) {
  return typeList.value?.get(typeIdValue) ? typeList.value.get(typeIdValue) : typeIdValue
}

function searchFormChange(params: Record<string, any>) {
  if (typeId.value !== params.type_id) {
    typeId.value = params.type_id
    getAttrs(params.type_id)
  }
  if (params.type_id === undefined) {
    typeId.value = undefined
    if (childRef.value) {
      childRef.value.queryParams.attr_id = undefined
    }
  }
}

function mergeRowMethod({ row, _rowIndex, column, visibleData }: any) {
  const fields = ['created_at', 'user', 'type_id', 'show_attr_value']
  return createMergeRowMethod(fields)({ row, _rowIndex, column, visibleData })
}

function filterUser() {
  applyFilter(queryParams.value, getTable)
}

function filterUserReset() {
  applyFilter(queryParams.value, getTable, { username: '' })
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
    const res = await getCIHistoryTable({
      ...params,
      page: queryParams.value.page,
      page_size: queryParams.value.page_size,
    })
    hide()

    if (!res.records || res.records.length === 0) {
      message.warning(t('noData'))
      return
    }

    const data: any[] = []
    res.records.forEach((item: any) => {
      item[0].type_id = handleTypeId(item[0].type_id)
      item[1].forEach((subItem: any) => {
        subItem.operate_type = handleOperateType(subItem.operate_type)
        subItem.new = subItem.new || ''
        subItem.old = subItem.old || ''
        const tempObj = Object.assign(subItem, item[0])
        data.push(tempObj)
      })
    })

    await xTableRef.value?.getVxetableRef()?.exportData({
      filename: `${t('cmdb.history.ciChange')}_${new Date().toISOString().split('T')[0]}`,
      sheetName: 'Sheet1',
      type: 'xlsx',
      types: ['xlsx'],
      isMerge: true,
      isColgroup: true,
      data,
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
      ref="childRef"
      :attr-list="ciTableAttrList"
      @expand-change="handleExpandChange"
      @search="handleSearch"
      @search-form-reset="searchFormReset"
      @search-form-change="searchFormChange"
      @export="handleExport"
    ></search-form>
    <vxe-table
      ref="xTableRef"
      :row-config="{ keyField: '_XID' }"
      :loading="loading"
      border
      size="small"
      show-overflow="tooltip"
      show-header-overflow="tooltip"
      resizable
      :data="tableData"
      :max-height="`${windowHeight - windowHeightOffset}px`"
      :span-method="mergeRowMethod"
      :scroll-y="{ enabled: false }"
      class="ops-unstripe-table"
    >
      <vxe-column field="created_at" min-width="160" :title="t('cmdb.history.opreateTime')"></vxe-column>
      <vxe-column field="user" min-width="120" :title="t('cmdb.history.user')">
        <template #header="{ column }">
          <span>{{ column.title }}</span>
          <a-popover trigger="click" placement="bottom">
            <FilterFilled class="filter" :class="{ active: queryParams.username }" />
            <template #content>
              <div class="filter-content">
                <a-input
                  v-model:value="queryParams.username"
                  :placeholder="t('cmdb.history.userTips')"
                  size="small"
                  style="width: 200px"
                  allow-clear
                />
                <a-button type="link" class="filterButton" @click="filterUser">
                  {{ t('cmdb.history.filter') }}
                </a-button>
                <a-button type="link" class="filterResetButton" @click="filterUserReset">
                  {{ t('reset') }}
                </a-button>
              </div>
            </template>
          </a-popover>
        </template>
      </vxe-column>
      <vxe-column field="type_id" min-width="120" :title="t('cmdb.ciType.ciType')"></vxe-column>
      <vxe-column field="show_attr_value" min-width="120" :title="t('cmdb.ci.instance')"></vxe-column>
      <vxe-column field="operate_type" min-width="100" :title="t('operation')">
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
                    v-for="(choice, index) in ciTableAttrList[4].choice_value"
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
      <vxe-column field="attr_alias" min-width="120" :title="t('cmdb.history.attribute')"></vxe-column>
      <vxe-column :cell-type="'string'" field="old" min-width="200" :title="t('cmdb.history.old')"></vxe-column>
      <vxe-column :cell-type="'string'" field="new" min-width="200" :title="t('cmdb.history.new')"></vxe-column>
    </vxe-table>
    <pager
      :current-page="queryParams.page"
      :page-size="queryParams.page_size"
      :page-sizes="PAGE_SIZE_OPTIONS"
      :total="total"
      :is-loading="loading"
      @change="onChange"
      @show-size-change="onShowSizeChange"
    ></pager>
  </div>
</template>

<style lang="less" scoped>
@import '../styles/table.less';
</style>
