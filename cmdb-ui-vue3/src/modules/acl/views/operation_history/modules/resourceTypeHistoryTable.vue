<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TableColumnsType } from 'ant-design-vue'
import Pager from '@/components/Pager/index.vue'
import SearchForm from '../../module/searchForm.vue'
import { searchResourceHistory } from '@/modules/acl/api/history'
import { searchUser } from '@/modules/acl/api/user'
import { searchResourceType } from '@/modules/acl/api/resource'
import { searchApp } from '@/modules/acl/api/app'

interface OptionItem {
  [name: string]: number
}

const { t } = useI18n()

const searchFormRef = ref<{ queryParams: Record<string, unknown> }>()

const loading = ref(true)
const isExpand = ref(false)
const app_id = ref<string | undefined>(undefined)
const tableData = ref<any[]>([])

const allUsersMap = ref<Map<number, string>>(new Map())

const colorMap: Record<string, string> = {
  create: 'green',
  update: 'orange',
  delete: 'red',
}

const queryParams = ref<Record<string, any>>({
  page: 1,
  page_size: 50,
  scope: 'resource_type',
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
    alias: t('acl.resourceType'),
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
  { title: t('acl.resourceTypeName'), dataIndex: 'link_id', key: 'link_id', width: 159 },
  { title: t('desc'), dataIndex: 'changeDescription', key: 'changeDescription' },
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
  allUsersMap.value = usersMap
  resourceTableAttrList.value[2].choice_value = users
}

async function getAllResourceTypes(appId?: string) {
  if (!appId) {
    resourceTableAttrList.value[3].choice_value = []
    return
  }
  const res = (await searchResourceType({ page: 1, page_size: 9999, app_id: appId })) as unknown as {
    groups: Array<{ id: number; name: string }>
  }
  const resourceTypes: OptionItem[] = []
  res.groups.forEach((item) => {
    resourceTypes.push({ [item.name]: item.id })
  })
  resourceTableAttrList.value[3].choice_value = resourceTypes
}

function handleExpandChange(expand: boolean) {
  isExpand.value = expand
}

function handleSearch(params: Record<string, any>) {
  queryParams.value = { ...queryParams.value, ...params, scope: 'resource_type' }
  getTable(queryParams.value)
}

function searchFormReset() {
  queryParams.value = {
    page: 1,
    page_size: 50,
    scope: 'resource_type',
  }
  getTable(queryParams.value)
}

async function searchFormChange(params: Record<string, any>) {
  if (app_id.value !== params.app_id) {
    app_id.value = params.app_id
    await getAllResourceTypes(app_id.value)
  }
  if (params.app_id === undefined) {
    app_id.value = undefined
    if (searchFormRef.value) searchFormRef.value.queryParams.link_id = undefined
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
      const description = item.current?.description === undefined ? t('acl.none') : item.current?.description
      const permission =
        item.extra.permission_ids?.current === undefined ? t('acl.none') : item.extra.permission_ids?.current
      item.changeDescription = `${t('acl.addResourceType')}：${item.current.name}\n${t('desc')}：${description}\n${t(
        'acl.permission'
      )}：${permission}`
      break
    }
    case 'update': {
      item.changeDescription = ''
      for (const key in item.origin) {
        const newVal = item.current[key]
        const oldVal = item.origin[key]
        if (!isEqual(newVal, oldVal) && key !== 'updated_at' && key !== 'deleted_at' && key !== 'created_at') {
          if (oldVal === null || oldVal === '') {
            item.changeDescription += ` 【 ${key} : -> ${newVal} 】 \n`
          } else {
            item.changeDescription += ` 【 ${key} : ${oldVal} -> ${newVal} 】 \n`
          }
        }
      }
      const currentPerms =
        item.extra.permission_ids?.current === undefined ? t('acl.none') : item.extra.permission_ids?.current
      const originPerms =
        item.extra.permission_ids?.origin === undefined ? t('acl.none') : item.extra.permission_ids?.origin
      if (!isEqual(currentPerms, originPerms)) {
        item.changeDescription += ` 【 permission_ids : ${originPerms} -> ${currentPerms} 】 `
      }
      if (!item.changeDescription) item.changeDescription = t('acl.noChange')
      break
    }
    case 'delete': {
      const description = item.origin?.description === undefined ? t('acl.none') : item.origin?.description
      const permission =
        item.extra.permission_ids?.origin === undefined ? t('acl.none') : item.extra.permission_ids?.origin
      item.changeDescription = `${t('acl.deleteResourceType')}: ${item.origin.name}\n${t('desc')}：${description}\n${t(
        'acl.permission'
      )}: ${permission}`
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
})
</script>

<template>
  <div>
    <SearchForm
      ref="searchFormRef"
      :attr-list="resourceTableAttrList"
      @search="handleSearch"
      @search-form-reset="searchFormReset"
      @search-form-change="searchFormChange"
      @expand-change="handleExpandChange"
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
        <template v-else-if="column.key === 'changeDescription'">
          <p>{{ record.changeDescription }}</p>
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
