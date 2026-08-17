<script setup lang="ts">
import { computed, inject, onMounted, onUpdated, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { FilterFilled, ArrowRightOutlined } from '@ant-design/icons-vue'
import SearchForm from './searchForm.vue'
import Pager from '@/components/Pager/index.vue'
import OperateTypeTag from '../components/OperateTypeTag.vue'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { getRelationTable, getUsers } from '@/modules/cmdb/api/history'
import { getRelationTypes } from '@/modules/cmdb/api/relationType'
import { useOperationHistory } from '../composables/useOperationHistory'
import { PAGINATION_CONFIG } from '../constants'

const { t, locale } = useI18n()
const { handleError, applyFilter, createMergeRowMethod } = useOperationHistory()
const reload = inject<(() => void) | null>('reload', null)

const xTableRef = ref<any>()

const loading = ref(true)
const isExpand = ref(false)
const tableData = ref<any[]>([])
const relationTypeList = ref<Map<number, string> | null>(null)
const total = ref(0)
const userList = ref<Array<Record<string, any>>>([])
const queryParams = ref<Record<string, any>>({
  page: 1,
  page_size: PAGINATION_CONFIG.DEFAULT_PAGE_SIZE,
  start: '',
  end: '',
  username: '',
  first_ci_id: undefined,
  second_ci_id: undefined,
  operate_type: undefined,
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

const relationTableAttrList = computed(() => [
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
    alias: t('cmdb.history.sourceCI'),
    is_choice: false,
    name: 'first_ci_id',
    value_type: '2',
    choice_value: [],
  },
  {
    alias: t('cmdb.history.targetCI'),
    is_choice: false,
    name: 'second_ci_id',
    value_type: '2',
    choice_value: [],
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
])

watch(locale, () => {
  reload?.()
})

onMounted(async () => {
  await Promise.all([getRelationTypeList(), getUserList(), getTypes()])
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
    const res = await getRelationTable(params)
    const tempArr: any[] = []
    res.records.forEach((item: any) => {
      item[1].forEach((subItem: any) => {
        subItem.operate_type = handleOperateType(subItem.operate_type)
        subItem.relation_type_id = handleRelationType(subItem.relation_type_id)
        subItem.first = res.cis[String(subItem.first_ci_id)]
        subItem.second = res.cis[String(subItem.second_ci_id)]
        const tempObj = Object.assign(subItem, item[0])
        tempArr.push(tempObj)
      })
    })
    total.value = res.total
    tableData.value = tempArr
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
    await getCITypes()
  } catch (error) {
    handleError(error, 'fetch CI types')
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
    first_ci_id: undefined,
    second_ci_id: undefined,
    operate_type: undefined,
  }
  getTable(queryParams.value)
}

function handleOperateType(operate_type: string) {
  return operateTypeMap.value.get(operate_type)
}

function handleRelationType(relation_type_id: number) {
  return relationTypeList.value?.get(relation_type_id)
}

function mergeRowMethod({ row, _rowIndex, column, visibleData }: any) {
  const fields = ['created_at', 'user']
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
    const res = await getRelationTable({
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
      item[1].forEach((subItem: any) => {
        subItem.operate_type = handleOperateType(subItem.operate_type)
        subItem.relation_type_id = handleRelationType(subItem.relation_type_id)
        subItem.first = res.cis[String(subItem.first_ci_id)]
        subItem.second = res.cis[String(subItem.second_ci_id)]

        const tempObj = Object.assign(subItem, item[0])
        tempObj.changeDescription = getExportChangeDescription(tempObj)

        data.push(tempObj)
      })
    })

    await xTableRef.value?.getVxetableRef()?.exportData({
      filename: `${t('cmdb.history.relationChange')}_${new Date().toISOString().split('T')[0]}`,
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

function getExportChangeDescription(item: any) {
  const first = item.first
    ? `${item.first.ci_type_alias}${
        item.first.unique_alias && item.first[item.first.unique]
          ? `（${item.first.unique_alias}：${item.first[item.first.unique]}）`
          : ''
      }`
    : ''
  const second = item.second
    ? `${item.second.ci_type_alias}${
        item.second.unique_alias && item.second[item.second.unique]
          ? `（${item.second.unique_alias}：${item.second[item.second.unique]}）`
          : ''
      }`
    : ''
  let center = ''
  if (item.changeDescription === t('cmdb.history.noUpdate')) {
    center = item.relation_type_id
  } else if (item.operate_type.includes(t('update'))) {
    center = item.changeArr.join(';')
  } else if (item.operate_type.includes(t('new'))) {
    center = item.relation_type_id
  } else if (item.operate_type.includes(t('delete'))) {
    center = item.relation_type_id
  }

  return `${first || ''} => ${center || ''} => ${second || ''}`
}
</script>

<template>
  <div class="operation-history-table">
    <search-form
      :attr-list="relationTableAttrList"
      @expand-change="handleExpandChange"
      @search="handleSearch"
      @search-form-reset="searchFormReset"
      @export="handleExport"
    ></search-form>
    <vxe-table
      ref="xTableRef"
      :loading="loading"
      size="small"
      show-overflow="tooltip"
      show-header-overflow="tooltip"
      resizable
      :data="tableData"
      :max-height="`${windowHeight - windowHeightOffset}px`"
      :row-config="{ keyField: '_XID' }"
      :scroll-y="{ enabled: false }"
      :span-method="mergeRowMethod"
      stripe
      class="ops-stripe-table"
    >
      <vxe-column field="created_at" width="165" :title="t('cmdb.history.opreateTime')"></vxe-column>
      <vxe-column field="user" width="120" :title="t('cmdb.history.user')">
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
      <vxe-column field="operate_type" width="90" :title="t('operation')">
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
                    v-for="(choice, index) in relationTableAttrList[4].choice_value"
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
      <vxe-column field="changeDescription" min-width="200" :title="t('desc')">
        <template #default="{ row }">
          <div class="relation-description">
            <span v-if="row && row.first" class="ci-info source-ci">
              <span class="ci-type">{{ row.first.ci_type_alias }}</span>
              <span v-if="row.first.unique_alias && row.first[row.first.unique]" class="ci-detail">
                {{ row.first.unique_alias }}: {{ row.first[row.first.unique] }}
              </span>
            </span>

            <span class="relation-arrow">
              <ArrowRightOutlined />
            </span>

            <span class="relation-type">
              <a-tag v-if="row.changeDescription === t('cmdb.history.noUpdate')" color="default">
                {{ row.relation_type_id }}
              </a-tag>
              <template v-else-if="row.operate_type.includes(t('update'))">
                <a-tag v-for="(tag, index) in row.changeArr" :key="index" color="orange">
                  {{ tag }}
                </a-tag>
              </template>
              <a-tag v-else-if="row.operate_type.includes(t('new'))" color="green">
                {{ row.relation_type_id }}
              </a-tag>
              <a-tag v-else-if="row.operate_type.includes(t('delete'))" color="red">
                {{ row.relation_type_id }}
              </a-tag>
            </span>

            <span class="relation-arrow">
              <ArrowRightOutlined />
            </span>

            <span v-if="row && row.second" class="ci-info target-ci">
              <span class="ci-type">{{ row.second.ci_type_alias }}</span>
              <span v-if="row.second.unique_alias && row.second[row.second.unique]" class="ci-detail">
                {{ row.second.unique_alias }}: {{ row.second[row.second.unique] }}
              </span>
            </span>
          </div>
        </template>
      </vxe-column>
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

.relation-description {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  line-height: 22px;

  .ci-info {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    background: #f5f5f5;
    border-radius: 2px;
    border: 1px solid #d9d9d9;
    font-size: 13px;

    .ci-type {
      color: rgba(0, 0, 0, 0.85);
      font-weight: 600;
    }

    .ci-detail {
      color: rgba(0, 0, 0, 0.65);
      font-size: 12px;

      &:before {
        content: '(';
        margin-right: 2px;
      }

      &:after {
        content: ')';
        margin-left: 2px;
      }
    }

    &.source-ci {
      border-left: 3px solid @primary-color;
    }

    &.target-ci {
      border-left: 3px solid #52c41a;
    }
  }

  .relation-arrow {
    color: #8c8c8c;
    font-size: 14px;
    margin: 0 4px;
  }

  .relation-type {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;
  }
}
</style>
