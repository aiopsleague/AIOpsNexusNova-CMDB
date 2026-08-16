<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { TableColumnsType } from 'ant-design-vue'
import Pager from '@/components/Pager/index.vue'
import SearchForm from './searchForm.vue'
import { searchResourceHistory } from '@/modules/acl/api/history'

interface OptionItem {
  [name: string]: number
}

const props = defineProps<{
  allResources: OptionItem[]
  allUsers: OptionItem[]
  allRoles: OptionItem[]
  allRolesMap: Map<number, string>
  allUsersMap: Map<number, string>
  allResourcesMap: Map<number, string>
}>()

const emit = defineEmits<{
  (e: 'loadMoreResources', value?: string): void
  (e: 'reloadResources'): void
  (e: 'fetchResources', value: string): void
  (e: 'resourceClear'): void
}>()

const { t } = useI18n()
const route = useRoute()

const loading = ref(true)
const checked = ref(false)
const tableData = ref<any[]>([])

const colorMap: Record<string, string> = {
  create: 'green',
  update: 'orange',
  delete: 'red',
}

const queryParams = ref<Record<string, any>>({
  page: 1,
  page_size: 50,
  app_id: appId(),
  scope: 'resource',
  start: '',
  end: '',
})

const windowHeight = ref(window.innerHeight)
const scrollY = computed(() => Math.max(windowHeight.value - 310, 200))

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

const operateTypeMap = computed<Record<string, string>>(() => ({
  create: t('create'),
  update: t('update'),
  delete: t('delete'),
}))

const resourceTableAttrList = computed(() => [
  {
    alias: t('acl.date'),
    is_choice: false,
    name: 'datetime',
    value_type: '3',
  },
  {
    alias: t('acl.operator'),
    is_choice: true,
    name: 'operate_uid',
    value_type: '2',
    choice_value: props.allUsers,
  },
  {
    alias: t('operation'),
    is_choice: true,
    name: 'operate_type',
    value_type: '2',
    choice_value: [{ [t('create')]: 'create' }, { [t('update')]: 'update' }, { [t('delete')]: 'delete' }],
  },
  {
    alias: t('acl.resourceName'),
    is_choice: true,
    name: 'link_id',
    value_type: '2',
    choice_value: props.allResources,
  },
])

const columns = computed<TableColumnsType>(() => [
  { title: t('acl.operateTime'), dataIndex: 'created_at', key: 'created_at', width: 144 },
  { title: t('acl.operator'), dataIndex: 'operate_uid', key: 'operate_uid', width: 130 },
  { title: t('operation'), dataIndex: 'operate_type', key: 'operate_type', width: 100 },
  { title: t('acl.resourceName'), dataIndex: 'link_id', key: 'link_id' },
  { title: t('desc'), dataIndex: 'description', key: 'description' },
  { title: t('acl.source'), dataIndex: 'source', key: 'source', width: 100 },
])

const tableDataLength = computed(() => tableData.value.length)

function isEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

async function getTable(params: Record<string, any>) {
  try {
    loading.value = true
    const res = (await searchResourceHistory(handleQueryParams(params))) as unknown as { data: any[] }
    res.data.forEach((item) => {
      item.originResource_ids = item?.extra?.resource_ids?.origin.map((subItem: number) =>
        props.allResourcesMap.get(Number(subItem))
      )
      item.currentResource_ids = item?.extra?.resource_ids?.current.map((subItem: number) =>
        props.allResourcesMap.get(Number(subItem))
      )
      handleChangeDescription(item, item.operate_type)
      item.operate_uid = props.allUsersMap.get(item.operate_uid)
    })
    tableData.value = res.data
  } finally {
    loading.value = false
  }
}

function loadMoreResources(name: string, value?: string) {
  if (name === 'link_id') {
    emit('loadMoreResources', value)
  }
}

function resourceClear() {
  emit('resourceClear')
}

function fetchResources(value: string) {
  if (value === '') {
    emit('reloadResources')
    return
  }
  emit('fetchResources', value)
}

function handleSearch(params: Record<string, any>) {
  queryParams.value = {
    ...queryParams.value,
    ...params,
    app_id: appId(),
    scope: checked.value ? 'resource_group' : 'resource',
  }
  getTable(queryParams.value)
}

function searchFormReset() {
  checked.value = false
  queryParams.value = {
    page: 1,
    page_size: 50,
    app_id: appId(),
    scope: checked.value ? 'resource_group' : 'resource',
  }
  getTable(queryParams.value)
}

function onSwitchChange(val: boolean) {
  checked.value = val
  queryParams.value.scope = val ? 'resource_group' : 'resource'
  queryParams.value.page = 1
  getTable(queryParams.value)
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

function handleQueryParams(params: Record<string, any>): Record<string, any> {
  const qp = { ...params }
  let flag = false
  let q = qp.q ? qp.q : ''
  for (const key in qp) {
    if (key !== 'page' && key !== 'page_size' && key !== 'app_id' && key !== 'q' && key !== 'start' && key !== 'end' && qp[key] !== undefined) {
      flag = true
      if (q) q += `,${key}:${qp[key]}`
      else q += `${key}:${qp[key]}`
      delete qp[key]
    }
  }
  return flag ? { ...qp, q } : qp
}

function handleTagColor(operateType: string): string {
  return colorMap[operateType]
}

function handleChangeDescription(item: any, operateType: string) {
  switch (operateType) {
    case 'create': {
      item.description = `${t('acl.newResource')}${item.current.name}`
      break
    }
    case 'update': {
      item.description = ''
      for (const key in item.origin) {
        const newVal = item.current[key]
        const oldVal = item.origin[key]
        if (!isEqual(newVal, oldVal) && key !== 'updated_at' && key !== 'deleted_at' && key !== 'created_at') {
          if (oldVal === null) {
            item.description += ` 【 ${key} : -> ${newVal} 】 `
          } else {
            item.description += ` 【 ${key} : ${oldVal} -> ${newVal} 】 `
          }
        }
      }
      const originResourceIds = item.originResource_ids
      const currentResourceIds = item.currentResource_ids
      if (!isEqual(originResourceIds, currentResourceIds)) {
        if (originResourceIds.length === 0) {
          item.description += ` 【 resource_ids : ${t('new')} ${currentResourceIds} 】 `
        } else {
          item.description += ` 【 resource_ids : ${originResourceIds} -> ${currentResourceIds} 】 `
        }
      }
      if (!item.description) item.description = t('acl.noChange')
      break
    }
    case 'delete': {
      item.description = `${t('acl.deleteResource')}${item.origin.name}`
      break
    }
  }
}

function handleResize() {
  windowHeight.value = window.innerHeight
}

watch(
  () => route.name,
  async () => {
    queryParams.value.app_id = appId()
    await getTable(queryParams.value)
  }
)

onMounted(() => {
  window.addEventListener('resize', handleResize)
  getTable(queryParams.value)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div>
    <SearchForm
      :attr-list="resourceTableAttrList"
      :has-switch="true"
      :switch-value="t('acl.group2')"
      @on-switch-change="onSwitchChange"
      @search="handleSearch"
      @search-form-reset="searchFormReset"
      @load-more-data="loadMoreResources"
      @fetch-data="fetchResources"
      @resource-clear="resourceClear"
    />
    <a-table
      :columns="columns"
      :data-source="tableData"
      :loading="loading"
      :pagination="false"
      :scroll="{ x: 900, y: scrollY }"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'operate_type'">
          <a-tag :color="handleTagColor(record.operate_type)">{{ operateTypeMap[record.operate_type] }}</a-tag>
        </template>
        <template v-else-if="column.key === 'link_id'">
          <span>{{ record.current.name || record.origin.name }}</span>
        </template>
        <template v-else-if="column.key === 'description'">
          <p>{{ record.description }}</p>
        </template>
      </template>
    </a-table>
    <Pager
      :current-page="queryParams.page"
      :page-size="queryParams.page_size"
      :page-sizes="[50, 100, 200]"
      :total="tableDataLength"
      :is-loading="loading"
      :style="{ marginTop: '10px' }"
      @change="onChange"
      @show-size-change="onShowSizeChange"
    />
  </div>
</template>

<style scoped>
.row {
  margin-top: 5px;
}
.ant-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}
p {
  margin-bottom: 0;
}
</style>
