<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TableColumnsType } from 'ant-design-vue'
import Pager from '@/components/Pager/index.vue'
import SearchForm from '../../module/searchForm.vue'
import { searchTriggerHistory } from '@/modules/acl/api/history'
import { getTriggers } from '@/modules/acl/api/trigger'
import { searchUser } from '@/modules/acl/api/user'
import { searchApp } from '@/modules/acl/api/app'

interface OptionItem {
  [name: string]: number
}

const { t } = useI18n()

const searchFormRef = ref<{ queryParams: Record<string, unknown> }>()

const app_id = ref<string | undefined>(undefined)
const loading = ref(true)
const isExpand = ref(false)
const tableData = ref<any[]>([])

const allUsersMap = ref<Map<number, string>>(new Map())
const allTriggersMap = ref<Map<number, string>>(new Map())

const colorMap: Record<string, string> = {
  create: 'green',
  delete: 'red',
  update: 'orange',
  trigger_apply: 'green',
  trigger_cancel: 'red',
}

const queryParams = ref<Record<string, any>>({
  page: 1,
  page_size: 50,
  start: '',
  end: '',
})

const triggerTableAttrList = ref<any[]>([
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
    alias: t('acl.trigger'),
    is_choice: true,
    name: 'trigger_id',
    value_type: '2',
    choice_value: [],
  },
  {
    alias: t('operation'),
    is_choice: true,
    name: 'operate_type',
    value_type: '2',
    choice_value: [
      { [t('create')]: 'create' },
      { [t('update')]: 'update' },
      { [t('delete')]: 'delete' },
      { [t('acl.apply')]: 'trigger_apply' },
      { [t('cancel')]: 'trigger_cancel' },
    ],
  },
])

const windowHeight = ref(window.innerHeight)
const windowHeightMinus = computed(() => (isExpand.value ? 374 : 310))
const scrollY = computed(() => Math.max(windowHeight.value - windowHeightMinus.value, 200))

const operateTypeMap = computed<Record<string, string>>(() => ({
  create: t('create'),
  update: t('update'),
  delete: t('delete'),
  trigger_apply: t('acl.apply'),
  trigger_cancel: t('cancel'),
}))

const columns = computed<TableColumnsType>(() => [
  { title: t('acl.operateTime'), dataIndex: 'created_at', key: 'created_at', width: 144 },
  { title: t('acl.operator'), dataIndex: 'operate_uid', key: 'operate_uid', width: 130 },
  { title: t('operation'), dataIndex: 'operate_type', key: 'operate_type', width: 100 },
  { title: t('acl.trigger'), dataIndex: 'trigger_id', key: 'trigger_id', width: 250 },
  { title: t('desc'), dataIndex: 'changeDescription', key: 'changeDescription' },
])

const tableDataLength = computed(() => tableData.value.length)

function isEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

async function getTable(params: Record<string, any>) {
  try {
    loading.value = true
    const res = (await searchTriggerHistory(handleQueryParams(params))) as unknown as {
      data: any[]
      id2resource_types: Record<string, { name: string }>
      id2roles: Record<string, { name: string }>
    }
    const { data, id2resource_types, id2roles } = res
    data.forEach((item) => {
      handleChangeDescription(item, item.operate_type, id2resource_types, id2roles)
      item.trigger_id = allTriggersMap.value.get(item.trigger_id)
      item.operate_uid = allUsersMap.value.get(item.operate_uid)
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
  triggerTableAttrList.value[1].choice_value = apps
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
  triggerTableAttrList.value[2].choice_value = users
}

async function loadTriggers(appId?: string) {
  if (!appId) {
    triggerTableAttrList.value[3].choice_value = []
    return
  }
  const res = (await getTriggers({ app_id: appId })) as unknown as Array<{ id: number; name: string }>
  const triggers: OptionItem[] = []
  const triggersMap = new Map<number, string>()
  res.forEach((item) => {
    triggers.push({ [item.name]: item.id })
    triggersMap.set(item.id, item.name)
  })
  allTriggersMap.value = triggersMap
  triggerTableAttrList.value[3].choice_value = triggers
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
  queryParams.value = { ...queryParams.value, ...params }
  getTable(queryParams.value)
}

function searchFormReset() {
  queryParams.value = {
    page: 1,
    page_size: 50,
  }
  getTable(queryParams.value)
}

async function searchFormChange(params: Record<string, any>) {
  if (app_id.value !== params.app_id) {
    app_id.value = params.app_id
    await loadTriggers(app_id.value)
  }
  if (params.app_id === undefined) {
    app_id.value = undefined
    if (searchFormRef.value) searchFormRef.value.queryParams.trigger_id = undefined
  }
}

function roleNames(roles: string, id2roles: Record<string, { name: string }>) {
  return roles
    .slice(1, roles.length - 1)
    .split(', ')
    .map((i) => id2roles[i].name)
    .join('，')
}

function handleChangeDescription(
  item: any,
  operateType: string,
  id2resource_types: Record<string, { name: string }>,
  id2roles: Record<string, { name: string }>
) {
  switch (operateType) {
    case 'create': {
      const newStr = roleNames(item.current.roles, id2roles)
      const { name, resource_type_id, wildcard, permissions, enabled } = item.current
      item.changeDescription = `${t('acl.addTrigger')}:${name}\n${t('acl.resourceType')}: ${
        id2resource_types[resource_type_id].name
      }，this.$t('acl.resourceName')：${wildcard || ''}，${t('acl.role2')}:[${newStr}]\nthis.$t('acl.permssion')}: ${permissions}\n${t(
        'status'
      )}: ${enabled}`
      break
    }
    case 'update': {
      item.changeDescription = ''
      for (const key in item.origin) {
        const newVal = item.current[key]
        const oldVal = item.origin[key]
        if (!isEqual(newVal, oldVal) && key !== 'updated_at' && key !== 'deleted_at' && key !== 'created_at') {
          if (oldVal === null) {
            item.changeDescription += ` 【 ${key} : -> ${newVal} 】 `
          } else {
            item.changeDescription += ` 【 ${key} :${oldVal} -> ${newVal} 】 `
          }
        }
      }
      if (!item.changeDescription) item.changeDescription = t('acl.noChange')
      break
    }
    case 'delete': {
      const newStr = roleNames(item.origin.roles, id2roles)
      const { name, resource_type_id, wildcard, permissions, enabled } = item.origin
      item.changeDescription = `${t('acl.deleteTrigger')}: ${name}\n${t('acl.resourceType')}: ${
        id2resource_types[resource_type_id].name
      }，${t('acl.resourceName')}: ${wildcard || ''}，${t('acl.role2')}:[${newStr}]\nthis.$t('acl.permssion')}: ${permissions}\n${t(
        'status'
      )}: ${enabled}`
      break
    }
    case 'trigger_apply': {
      const newStr = roleNames(item.current.roles, id2roles)
      const { name, resource_type_id, wildcard, permissions, enabled } = item.current
      item.changeDescription = `${t('acl.applyTrigger')}: ${name}\n${t('acl.resourceType')}: ${
        id2resource_types[resource_type_id].name
      }，${t('acl.resourceName')}: ${wildcard || ''}，${t('acl.role2')}:[${newStr}]\nthis.$t('acl.permssion')}: ${permissions}\n${t(
        'status'
      )}: ${enabled}`
      break
    }
    case 'trigger_cancel': {
      const newStr = roleNames(item.current.roles, id2roles)
      const { name, resource_type_id, wildcard, permissions, enabled } = item.current
      item.changeDescription = `${t('acl.cancelTrigger')}: ${name}\n${t('acl.resourceType')}: ${
        id2resource_types[resource_type_id].name
      }，${t('acl.resourceName')}: ${wildcard || ''}，${t('acl.role2')}:[${newStr}]\nthis.$t('acl.permssion')}: ${permissions}\n${t(
        'status'
      )}: ${enabled}`
      break
    }
  }
}

function handleQueryParams(params: Record<string, any>): Record<string, any> {
  const qp = { ...params }
  let q = ''
  for (const key in qp) {
    if (key !== 'page' && key !== 'page_size' && key !== 'app_id' && key !== 'start' && key !== 'end' && qp[key] !== undefined) {
      if (q) {
        q += `,${key}:${qp[key]}`
      } else {
        q += `${key}:${qp[key]}`
      }
    }
  }
  return q ? { ...qp, q } : qp
}

function handleTagColor(operateType: string): string {
  return colorMap[operateType]
}

function handleResize() {
  windowHeight.value = window.innerHeight
}

watch(
  () => triggerTableAttrList.value[3]?.choice_value,
  () => {
    if (searchFormRef.value) searchFormRef.value.queryParams.trigger_id = undefined
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
      :attr-list="triggerTableAttrList"
      @search-form-reset="searchFormReset"
      @search="handleSearch"
      @expand-change="handleExpandChange"
      @search-form-change="searchFormChange"
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
        <template v-else-if="column.key === 'trigger_id'">
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
p {
  margin-bottom: 0;
}
.ant-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
