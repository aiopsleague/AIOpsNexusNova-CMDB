<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { TableColumnsType } from 'ant-design-vue'
import Pager from '@/components/Pager/index.vue'
import SearchForm from './searchForm.vue'
import { searchTriggerHistory } from '@/modules/acl/api/history'

interface OptionItem {
  [name: string]: number
}

const props = defineProps<{
  allUsers: OptionItem[]
  allRoles: OptionItem[]
  allTriggers: OptionItem[]
  allRolesMap: Map<number, string>
  allTriggersMap: Map<number, string>
  allUsersMap: Map<number, string>
  allResourceTypesMap: Map<number, string>
}>()

const { t } = useI18n()
const route = useRoute()

const loading = ref(true)
const tableData = ref<any[]>([])

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
  app_id: appId(),
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
  trigger_apply: t('acl.apply'),
  trigger_cancel: t('cancel'),
}))

const triggerTableAttrList = computed(() => [
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
    choice_value: [
      { [t('create')]: 'create' },
      { [t('update')]: 'update' },
      { [t('delete')]: 'delete' },
      { [t('acl.apply')]: 'trigger_apply' },
      { [t('cancel')]: 'trigger_cancel' },
    ],
  },
  {
    alias: t('acl.trigger'),
    is_choice: true,
    name: 'trigger_id',
    value_type: '2',
    choice_value: props.allTriggers,
  },
])

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
    const res = (await searchTriggerHistory(handleQueryParams(params))) as unknown as { data: any[] }
    res.data.forEach((item) => {
      handleChangeDescription(item, item.operate_type)
      item.trigger_id = props.allTriggersMap.get(item.trigger_id)
      item.operate_uid = props.allUsersMap.get(item.operate_uid)
    })
    tableData.value = res.data
  } finally {
    loading.value = false
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

function handleSearch(params: Record<string, any>) {
  queryParams.value = { ...queryParams.value, ...params }
  queryParams.value.app_id = appId()
  getTable(queryParams.value)
}

function searchFormReset() {
  queryParams.value = {
    page: 1,
    page_size: 50,
    app_id: appId(),
  }
  getTable(queryParams.value)
}

function handleChangeDescription(item: any, operateType: string) {
  const roleNames = (roles: string) =>
    roles
      .slice(1, roles.length - 1)
      .split(', ')
      .map((i) => props.allRolesMap.get(Number(i)))
      .join('，')
  switch (operateType) {
    case 'create': {
      const newStr = roleNames(item.current.roles)
      item.changeDescription = `${t('acl.addTrigger')}: ${item.current.name}\n${t('acl.resourceType')}: ：${props.allResourceTypesMap.get(
        item.current.resource_type_id
      )}，this.$t('acl.resourceName')：${item.current.wildcard}，${t('acl.role2')}: [${newStr}]\n${t(
        'acl.permission'
      )}: ${item.current.permissions}\n${t('status')}: ${item.current.enabled}`
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
            item.changeDescription += ` 【 ${key} : ${oldVal} -> ${newVal} 】 `
          }
        }
      }
      if (!item.changeDescription) item.changeDescription = t('acl.noChange')
      break
    }
    case 'delete': {
      const newStr = roleNames(item.origin.roles)
      item.changeDescription = `${t('acl.deleteTrigger')}: ${item.origin.name}\n${t('acl.resourceType')}: ：${props.allResourceTypesMap.get(
        item.origin.resource_type_id
      )}，this.$t('acl.resourceName')：${item.origin.wildcard}，${t('acl.role2')}: [${newStr}]\n${t(
        'acl.permission'
      )}: ${item.origin.permissions}\n${t('status')}: ${item.origin.enabled}`
      break
    }
    case 'trigger_apply': {
      const newStr = roleNames(item.current.roles)
      item.changeDescription = `${t('acl.applyTrigger')}: ${item.current.name}\n${t('acl.resourceType')}: ：${props.allResourceTypesMap.get(
        item.current.resource_type_id
      )}，this.$t('acl.resourceName')：${item.current.wildcard}，${t('acl.role2')}: [${newStr}]\n${t(
        'acl.permission'
      )}: ${item.current.permissions}\n${t('status')}: ${item.current.enabled}`
      break
    }
    case 'trigger_cancel': {
      const newStr = roleNames(item.current.roles)
      item.changeDescription = `${t('acl.cancelTrigger')}: ${item.current.name}\n${t('acl.resourceType')}: ：${props.allResourceTypesMap.get(
        item.current.resource_type_id
      )}，this.$t('acl.resourceName')：${item.current.wildcard}，${t('acl.role2')}: [${newStr}]\n${t(
        'acl.permission'
      )}: ${item.current.permissions}\n${t('status')}: ${item.current.enabled}`
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
    <SearchForm :attr-list="triggerTableAttrList" @search-form-reset="searchFormReset" @search="handleSearch" />
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
