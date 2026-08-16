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
  allResourceTypes: OptionItem[]
  allUsers: OptionItem[]
  allRoles: OptionItem[]
  allRolesMap: Map<number, string>
  allUsersMap: Map<number, string>
  allResourceTypesMap: Map<number, string>
}>()

const { t } = useI18n()
const route = useRoute()

const loading = ref(true)
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
  scope: 'resource_type',
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
    alias: t('acl.resourceType'),
    is_choice: true,
    name: 'link_id',
    value_type: '2',
    choice_value: props.allResourceTypes,
  },
])

const columns = computed<TableColumnsType>(() => [
  { title: t('acl.operateTime'), dataIndex: 'created_at', key: 'created_at', width: 144 },
  { title: t('acl.operator'), dataIndex: 'operate_uid', key: 'operate_uid', width: 130 },
  { title: t('operation'), dataIndex: 'operate_type', key: 'operate_type', width: 100 },
  { title: t('acl.resourceTypeName'), dataIndex: 'link_id', key: 'link_id' },
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
      item.operate_uid = props.allUsersMap.get(item.operate_uid)
    })
    tableData.value = res.data
  } finally {
    loading.value = false
  }
}

function handleSearch(params: Record<string, any>) {
  queryParams.value = { ...queryParams.value, ...params, app_id: appId(), scope: 'resource_type' }
  getTable(queryParams.value)
}

function searchFormReset() {
  queryParams.value = {
    page: 1,
    page_size: 50,
    app_id: appId(),
    scope: 'resource_type',
  }
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
      item.changeDescription = `${t('acl.addResourceType')}：${item.current.name}\n${t('desc')}：${
        item.current.description
      }\n${t('acl.permission')}: ${item.extra.permission_ids.current}`
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
      const currentPerms = item.extra.permission_ids.current
      const originPerms = item.extra.permission_ids.origin
      if (!isEqual(currentPerms, originPerms)) {
        item.changeDescription += ` 【 permission_ids : ${originPerms} -> ${currentPerms} 】 `
      }
      if (!item.changeDescription) item.changeDescription = t('acl.noChange')
      break
    }
    case 'delete': {
      item.changeDescription = `${t('acl.deleteResourceType')}${item.origin.name}\n${t('desc')}: ${
        item.origin.description
      }\n${t('acl.permission')}: ${item.extra.permission_ids.origin}`
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
    <SearchForm :attr-list="resourceTableAttrList" @search="handleSearch" @search-form-reset="searchFormReset" />
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
