<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { TableColumnsType } from 'ant-design-vue'
import Pager from '@/components/Pager/index.vue'
import SearchForm from './searchForm.vue'
import { searchPermissionHistory } from '@/modules/acl/api/history'

interface OptionItem {
  [name: string]: number
}

const props = defineProps<{
  allResourceTypes: OptionItem[]
  allResources: OptionItem[]
  allUsers: OptionItem[]
  allRoles: OptionItem[]
  allRolesMap: Map<number, string>
  allUsersMap: Map<number, string>
  allResourceTypesMap: Map<number, string>
}>()

const emit = defineEmits<{
  (e: 'loadMoreResources', value?: string): void
  (e: 'reloadResources'): void
  (e: 'fetchResources', value: string): void
  (e: 'resourceClear'): void
}>()

const { t } = useI18n()
const route = useRoute()

const isExpand = ref(false)
const loading = ref(true)
const tableData = ref<any[]>([])

const queryParams = ref<Record<string, any>>({
  page: 1,
  page_size: 50,
  app_id: appId(),
  start: '',
  end: '',
})

const windowHeight = ref(window.innerHeight)
const windowHeightMinus = computed(() => (isExpand.value ? 374 : 310))
const scrollY = computed(() => Math.max(windowHeight.value - windowHeightMinus.value, 200))

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

const operateTypeMap = computed<Record<string, string>>(() => ({
  grant: t('grant'),
  revoke: t('acl.cancel'),
}))

const permissionTableAttrList = computed(() => [
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
    alias: t('user'),
    is_choice: true,
    name: 'rid',
    value_type: '2',
    choice_value: props.allRoles,
  },
  {
    alias: t('acl.resourceType'),
    is_choice: true,
    name: 'resource_type_id',
    value_type: '2',
    choice_value: props.allResourceTypes,
  },
  {
    alias: t('acl.resource'),
    is_choice: true,
    name: 'resource_id',
    value_type: '2',
    choice_value: props.allResources,
  },
  {
    alias: t('operation'),
    is_choice: true,
    name: 'operate_type',
    value_type: '2',
    choice_value: [{ [t('grant')]: 'grant' }, { [t('acl.cancel')]: 'revoke' }],
  },
])

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
    }
    const { data, id2groups, id2perms, id2resources, id2roles } = res
    data.forEach((item) => {
      item.operate_uid = props.allUsersMap.get(item.operate_uid)
      item.rid = id2roles[item.rid].name
      item.resource_type_id = props.allResourceTypesMap.get(item.resource_type_id)
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

function loadMoreResources(name: string, value?: string) {
  if (name === 'resource_id') {
    emit('loadMoreResources', value)
  }
}

function resourceClear() {
  emit('resourceClear')
}

let fetchTimer: ReturnType<typeof setTimeout> | undefined
function fetchResources(value: string) {
  if (fetchTimer) clearTimeout(fetchTimer)
  fetchTimer = setTimeout(() => {
    if (value === '') {
      emit('reloadResources')
      return
    }
    emit('fetchResources', value)
  }, 800)
}

// Build the q param out of filter fields, leaving pagination/app/date params intact.
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

function handleExpandChange(expand: boolean) {
  isExpand.value = expand
}

function searchFormReset() {
  queryParams.value = {
    page: 1,
    page_size: 50,
    app_id: appId(),
  }
  getTable(queryParams.value)
}

function handleSearch(params: Record<string, any>) {
  queryParams.value = { ...queryParams.value, ...params, app_id: appId() }
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
  if (fetchTimer) clearTimeout(fetchTimer)
})
</script>

<template>
  <div>
    <SearchForm
      :attr-list="permissionTableAttrList"
      @search="handleSearch"
      @expand-change="handleExpandChange"
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
