<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TableColumnsType } from 'ant-design-vue'
import Pager from '@/components/Pager/index.vue'
import SearchForm from '../../module/searchForm.vue'
import { searchApp } from '@/modules/acl/api/app'
import { searchPermissionHistory } from '@/modules/acl/api/history'
import { searchRole } from '@/modules/acl/api/role'
import { searchUser } from '@/modules/acl/api/user'
import { searchResource, searchResourceType } from '@/modules/acl/api/resource'

interface OptionItem {
  [name: string]: number
}

const { t } = useI18n()

const searchFormRef = ref<{ queryParams: Record<string, unknown> }>()

const app_id = ref<string | undefined>(undefined)
const isExpand = ref(false)
const loading = ref(true)
const resourcesPage = ref(1)
const resourcesNum = ref(0)
const tableData = ref<any[]>([])

const allRoles = ref<OptionItem[]>([])
const allUsers = ref<OptionItem[]>([])
const allResourceTypes = ref<OptionItem[]>([])
const allResources = ref<OptionItem[]>([])

const allUsersMap = ref<Map<number, string>>(new Map())

const queryParams = ref<Record<string, any>>({
  page: 1,
  page_size: 50,
  start: '',
  end: '',
})

const permissionTableAttrList = ref<any[]>([
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
    alias: t('user'),
    is_choice: true,
    name: 'rid',
    value_type: '2',
    choice_value: [],
  },
  {
    alias: t('acl.resourceType'),
    is_choice: true,
    name: 'resource_type_id',
    value_type: '2',
    choice_value: [],
  },
  {
    alias: t('acl.resource'),
    is_choice: true,
    name: 'resource_id',
    value_type: '2',
    choice_value: [],
  },
  {
    alias: t('operation'),
    is_choice: true,
    name: 'operate_type',
    value_type: '2',
    choice_value: [{ [t('grant')]: 'grant' }, { [t('acl.cancel')]: 'revoke' }],
  },
])

const windowHeight = ref(window.innerHeight)
const windowHeightMinus = computed(() => (isExpand.value ? 374 : 310))
const scrollY = computed(() => Math.max(windowHeight.value - windowHeightMinus.value, 200))

const operateTypeMap = computed<Record<string, string>>(() => ({
  grant: t('grant'),
  revoke: t('acl.cancel'),
}))

const columns = computed<TableColumnsType>(() => [
  { title: t('acl.operateTime'), dataIndex: 'created_at', key: 'created_at', width: 144 },
  { title: t('acl.operator'), dataIndex: 'operate_uid', key: 'operate_uid', width: 130 },
  { title: t('operation'), dataIndex: 'operate_type', key: 'operate_type', width: 100 },
  { title: t('user'), dataIndex: 'rid', key: 'rid' },
  { title: t('acl.resourceType'), dataIndex: 'resource_type_id', key: 'resource_type_id' },
  { title: t('acl.resource'), dataIndex: 'resource_ids', key: 'resource_ids' },
  { title: t('acl.permission'), dataIndex: 'permission_ids', key: 'permission_ids' },
  { title: t('acl.source'), dataIndex: 'source', key: 'source', width: 100 },
])

const tableDataLength = computed(() => tableData.value.length)

async function getTable(params: Record<string, any>) {
  try {
    loading.value = true
    const res = (await searchPermissionHistory(handleQueryParams(params))) as unknown as {
      data: any[]
      id2groups: Record<string, { name: string }>
      id2perms: Record<string, { name: string }>
      id2resources: Record<string, { name: string }>
      id2roles: Record<string, { name: string }>
      id2resource_types: Record<string, { name: string }>
    }
    const { data, id2groups, id2perms, id2resources, id2roles, id2resource_types } = res
    data.forEach((item) => {
      item.rid = id2roles[item.rid].name
      item.operate_uid = allUsersMap.value.get(item.operate_uid)
      if (id2resource_types[item.resource_type_id]) {
        item.resource_type_id = id2resource_types[item.resource_type_id].name
      }
      item.resource_ids.forEach((subItem: number, index: number) => {
        item.resource_ids[index] = id2resources[subItem].name
      })
      item.group_ids.forEach((subItem: number, index: number) => {
        item.group_ids[index] = id2groups[subItem].name
      })
      item.permission_ids.forEach((subItem: number, index: number) => {
        item.permission_ids[index] = id2perms[subItem].name
      })
    })
    tableData.value = data
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
  permissionTableAttrList.value[1].choice_value = apps
}

async function getAllRoles(appId?: string) {
  if (!appId) {
    permissionTableAttrList.value[3].choice_value = []
    return
  }
  const res = (await searchRole({ page_size: 9999, app_id: appId })) as unknown as {
    roles: Array<{ id: number; name: string }>
  }
  const roles: OptionItem[] = []
  res.roles.forEach((item) => {
    roles.push({ [item.name]: item.id })
  })
  allRoles.value = roles
  permissionTableAttrList.value[3].choice_value = roles
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
  permissionTableAttrList.value[2].choice_value = users
}

async function getAllResourceTypes(appId?: string) {
  if (!appId) {
    permissionTableAttrList.value[4].choice_value = []
    return
  }
  const res = (await searchResourceType({ page_size: 9999, page: 1, app_id: appId })) as unknown as {
    groups: Array<{ id: number; name: string }>
  }
  const resourceTypes: OptionItem[] = []
  res.groups.forEach((item) => {
    resourceTypes.push({ [item.name]: item.id })
  })
  allResourceTypes.value = resourceTypes
  permissionTableAttrList.value[4].choice_value = resourceTypes
}

async function getAllResources(appId?: string, page?: number, value?: string) {
  if (!appId) {
    permissionTableAttrList.value[5].choice_value = []
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
  permissionTableAttrList.value[5].choice_value = resources
}

function loadMoreResources(name: string, value?: string) {
  if (name === 'resource_id' && allResources.value.length < resourcesNum.value) {
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
      permissionTableAttrList.value[5].choice_value = []
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
  permissionTableAttrList.value[5].choice_value = resources
}

function searchFormReset() {
  queryParams.value = { page: 1, page_size: 50 }
  resourcesPage.value = 1
  resourcesNum.value = 0
  getTable(queryParams.value)
}

function handleSearch(params: Record<string, any>) {
  queryParams.value = { ...queryParams.value, ...params }
  getTable(queryParams.value)
}

function handleExpandChange(expand: boolean) {
  isExpand.value = expand
}

async function searchFormChange(params: Record<string, any>) {
  if (app_id.value !== params.app_id) {
    app_id.value = params.app_id
    allResources.value = []
    resourcesPage.value = 1
    resourcesNum.value = 0
    await Promise.all([
      getAllRoles(app_id.value),
      getAllResourceTypes(app_id.value),
      getAllResources(app_id.value, resourcesPage.value),
    ])
  }
  if (params.app_id === undefined) {
    app_id.value = undefined
    clearStaleFields()
    allResources.value = []
    resourcesPage.value = 1
    resourcesNum.value = 0
  }
}

function clearStaleFields() {
  if (searchFormRef.value) {
    searchFormRef.value.queryParams.rid = undefined
    searchFormRef.value.queryParams.resource_type_id = undefined
    searchFormRef.value.queryParams.resource_id = undefined
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
  let q = ''
  for (const key in qp) {
    if (key !== 'page' && key !== 'page_size' && key !== 'app_id' && key !== 'start' && key !== 'end' && qp[key] !== undefined) {
      if (q) q += `,${key}:${qp[key]}`
      else q += `${key}:${qp[key]}`
      delete qp[key]
    }
  }
  return q ? { ...qp, q } : qp
}

function handleResize() {
  windowHeight.value = window.innerHeight
}

watch(
  () => permissionTableAttrList.value[3]?.choice_value,
  () => {
    clearStaleFields()
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
      :attr-list="permissionTableAttrList"
      @search="handleSearch"
      @expand-change="handleExpandChange"
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
      :scroll="{ x: 1100, y: scrollY }"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'created_at'">
          <span>{{ record.deleted_at || record.updated_at || record.created_at }}</span>
        </template>
        <template v-else-if="column.key === 'operate_type'">
          <a-tag :color="record.operate_type === 'grant' ? 'green' : 'red'">{{
            operateTypeMap[record.operate_type]
          }}</a-tag>
        </template>
        <template v-else-if="column.key === 'resource_ids'">
          <template v-if="(record.resource_ids || []).length > 0">
            <a-tooltip placement="top">
              <template #title>{{ record.resource_ids[0] }}</template>
              <a-tag
                v-for="(resource, index) in record.resource_ids"
                :key="'resources_' + resource + index"
                color="blue"
              >
                {{ resource }}
              </a-tag>
            </a-tooltip>
          </template>
          <template v-else-if="(record.group_ids || []).length > 0">
            <a-tag v-for="(group, index) in record.group_ids" :key="'groups_' + group + index" color="blue">
              {{ group }}
            </a-tag>
          </template>
        </template>
        <template v-else-if="column.key === 'permission_ids'">
          <a-tag v-for="(perm, index) in record.permission_ids || []" :key="'perms_' + perm + index">
            {{ perm }}
          </a-tag>
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
.ant-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
