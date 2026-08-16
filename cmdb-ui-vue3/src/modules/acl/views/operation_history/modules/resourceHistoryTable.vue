<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TableColumnsType } from 'ant-design-vue'
import Pager from '@/components/Pager/index.vue'
import SearchForm from '../../module/searchForm.vue'
import { searchResourceHistory } from '@/modules/acl/api/history'
import { searchUser } from '@/modules/acl/api/user'
import { searchResource } from '@/modules/acl/api/resource'
import { searchApp } from '@/modules/acl/api/app'

interface OptionItem {
  [name: string]: number
}

const { t } = useI18n()

const searchFormRef = ref<{ queryParams: Record<string, unknown> }>()

const loading = ref(true)
const checked = ref(false)
const isExpand = ref(false)
const app_id = ref<string | undefined>(undefined)
const resourcesPage = ref(1)
const resourcesNum = ref(0)
const tableData = ref<any[]>([])

const allResources = ref<OptionItem[]>([])
const allUsers = ref<OptionItem[]>([])
const allUsersMap = ref<Map<number, string>>(new Map())

const colorMap: Record<string, string> = {
  create: 'green',
  update: 'orange',
  delete: 'red',
}

const queryParams = ref<Record<string, any>>({
  page: 1,
  page_size: 50,
  scope: 'resource',
  start: '',
  end: '',
})

const resourceTableAttrList = ref<any[]>([
  {
    alias: t('acl.date'),
    is_choice: false,
    name: 'datetime',
    value_type: '3',
  },
  {
    alias: t('acl.app'),
    is_choice: true,
    name: 'app_id',
    value_type: '2',
    choice_value: [],
  },
  {
    alias: t('acl.operator'),
    is_choice: true,
    name: 'operate_uid',
    value_type: '2',
    choice_value: [],
  },
  {
    alias: t('acl.resourceName'),
    is_choice: true,
    name: 'link_id',
    value_type: '2',
    choice_value: [],
  },
  {
    alias: t('operation'),
    is_choice: true,
    name: 'operate_type',
    value_type: '2',
    choice_value: [{ [t('create')]: 'create' }, { [t('update')]: 'update' }, { [t('delete')]: 'delete' }],
  },
])

const windowHeight = ref(window.innerHeight)
const windowHeightMinus = computed(() => (isExpand.value ? 374 : 310))
const scrollY = computed(() => Math.max(windowHeight.value - windowHeightMinus.value, 200))

const operateTypeMap = computed<Record<string, string>>(() => ({
  create: t('create'),
  update: t('update'),
  delete: t('delete'),
}))

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
      item.originResource_ids = item?.extra?.resource_ids?.origin
      item.currentResource_ids = item?.extra?.resource_ids?.current
      handleChangeDescription(item, item.operate_type)
      item.operate_uid = allUsersMap.value.get(item.operate_uid)
    })
    tableData.value = res.data
  } finally {
    loading.value = false
  }
}

async function getAllApps() {
  const res = (await searchApp()) as unknown as { apps: Array<{ id: number; name: string }> }
  const apps: OptionItem[] = []
  res.apps.forEach((item) => {
    apps.push({ [item.name]: item.id })
  })
  resourceTableAttrList.value[1].choice_value = apps
}

async function getAllUsers() {
  const res = (await searchUser({ page_size: 10000, app_id: 'acl' })) as unknown as {
    users: Array<{ uid: number; nickname: string }>
  }
  const users: OptionItem[] = []
  const usersMap = new Map<number, string>()
  res.users.forEach((item) => {
    users.push({ [item.nickname]: item.uid })
    usersMap.set(item.uid, item.nickname)
  })
  allUsers.value = users
  allUsersMap.value = usersMap
  resourceTableAttrList.value[2].choice_value = users
}

async function getAllResources(appId?: string, page?: number, value?: string) {
  if (!appId) {
    resourceTableAttrList.value[3].choice_value = []
    return
  }
  const res = (await searchResource({ page, page_size: 50, app_id: appId, q: value })) as unknown as {
    resources: Array<{ id: number; name: string }>
    numfound: number
  }
  resourcesNum.value = res.numfound
  const resources = allResources.value
  res.resources.forEach((item) => {
    resources.push({ [item.name]: item.id })
  })
  allResources.value = resources
  resourceTableAttrList.value[3].choice_value = resources
}

function loadMoreResources(name: string, value?: string) {
  if (name === 'link_id' && allResources.value.length < resourcesNum.value) {
    resourcesPage.value += 1
    getAllResources(app_id.value, resourcesPage.value, value)
  }
}

function resourceClear() {
  resourcesPage.value = 1
  allResources.value = []
  getAllResources(app_id.value, 1)
}

let fetchTimer: ReturnType<typeof setTimeout> | undefined
function fetchResources(value: string) {
  if (fetchTimer) clearTimeout(fetchTimer)
  fetchTimer = setTimeout(() => {
    allResources.value = []
    if (!app_id.value) {
      resourceTableAttrList.value[3].choice_value = []
      return
    }
    resourcesPage.value = 1
    if (value === '') {
      getAllResources(app_id.value, 1)
      return
    }
    doFetchResources(value)
  }, 800)
}

async function doFetchResources(value: string) {
  const resources: OptionItem[] = []
  const res = (await searchResource({ page: 1, page_size: 50, app_id: app_id.value, q: value })) as unknown as {
    resources: Array<{ id: number; name: string }>
    numfound: number
  }
  resourcesNum.value = res.numfound
  res.resources.forEach((item) => {
    resources.push({ [item.name]: item.id })
  })
  allResources.value = resources
  resourceTableAttrList.value[3].choice_value = resources
}

function handleExpandChange(expand: boolean) {
  isExpand.value = expand
}

function handleSearch(params: Record<string, any>) {
  queryParams.value = { ...queryParams.value, ...params, scope: checked.value ? 'resource_group' : 'resource' }
  getTable(queryParams.value)
}

function searchFormReset() {
  checked.value = false
  queryParams.value = {
    page: 1,
    page_size: 50,
    scope: checked.value ? 'resource_group' : 'resource',
  }
  resourcesPage.value = 1
  resourcesNum.value = 0
  getTable(queryParams.value)
}

function onSwitchChange(val: boolean) {
  checked.value = val
  queryParams.value.scope = val ? 'resource_group' : 'resource'
  queryParams.value.page = 1
  getTable(queryParams.value)
}

async function searchFormChange(params: Record<string, any>) {
  if (app_id.value !== params.app_id) {
    app_id.value = params.app_id
    allResources.value = []
    resourcesPage.value = 1
    resourcesNum.value = 0
    await getAllResources(app_id.value, resourcesPage.value)
  }
  if (params.app_id === undefined) {
    app_id.value = undefined
    if (searchFormRef.value) searchFormRef.value.queryParams.link_id = undefined
    allResources.value = []
    resourcesPage.value = 1
    resourcesNum.value = 0
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
  () => resourceTableAttrList.value[3]?.choice_value,
  () => {
    if (searchFormRef.value) searchFormRef.value.queryParams.link_id = undefined
  }
)

onMounted(() => {
  window.addEventListener('resize', handleResize)
  Promise.all([getAllApps(), getAllUsers()]).then(() => getTable(queryParams.value))
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (fetchTimer) clearTimeout(fetchTimer)
})
</script>

<template>
  <div>
    <SearchForm
      ref="searchFormRef"
      :attr-list="resourceTableAttrList"
      :has-switch="true"
      :switch-value="t('acl.group2')"
      @on-switch-change="onSwitchChange"
      @expand-change="handleExpandChange"
      @search="handleSearch"
      @search-form-reset="searchFormReset"
      @search-form-change="searchFormChange"
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
