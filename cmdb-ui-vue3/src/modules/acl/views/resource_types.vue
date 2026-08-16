<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import type { TableColumnsType } from 'ant-design-vue'
import type { Permission } from '@/types'
import Pager from '@/components/Pager/index.vue'
import { deleteResourceTypeById, searchResourceType } from '@/modules/acl/api/resource'
import ResourceTypeForm from './module/resourceTypeForm.vue'

interface ResourceTypeRow {
  id: number
  name: string
  description?: string
  perms?: string[]
}

const { t } = useI18n()
const route = useRoute()

const loading = ref(false)
const groups = ref<ResourceTypeRow[]>([])
const id2perms = ref<Record<number, Permission[]>>({})
const searchName = ref('')

const pageSizeOptions = [20, 50, 100, 200]
const tablePage = reactive({
  total: 0,
  currentPage: 1,
  pageSize: 50,
})

const resourceTypeFormRef = ref<{
  open: (record?: { id?: number; name?: string; description?: string; perms?: string[] }) => void
}>()

const windowHeight = ref(window.innerHeight)
const scrollY = computed(() => Math.max(windowHeight.value - 200, 200))

const columns = computed<TableColumnsType<ResourceTypeRow>>(() => [
  { title: t('acl.resourceType'), dataIndex: 'name', key: 'name', width: 175, fixed: 'left' },
  { title: t('desc'), dataIndex: 'description', key: 'description', width: 175 },
  { title: t('acl.permission'), dataIndex: 'id', key: 'permission', width: 300 },
  { title: t('operation'), dataIndex: 'action', key: 'action', width: 100, fixed: 'right' },
])

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function searchData() {
  loading.value = true
  const params = {
    app_id: appId(),
    page_size: tablePage.pageSize,
    page: tablePage.currentPage,
    q: searchName.value,
  }
  searchResourceType(params).then((res) => {
    const data = res as unknown as {
      numfound: number
      page: number
      groups: ResourceTypeRow[]
      id2perms: Record<number, Permission[]>
    }
    tablePage.total = data.numfound
    tablePage.currentPage = data.page
    groups.value = data.groups || []
    id2perms.value = data.id2perms || {}
    loading.value = false
  })
}

function handleSearch() {
  tablePage.currentPage = 1
  searchData()
}

function handleCreate() {
  resourceTypeFormRef.value?.open()
}

function handleEdit(record: ResourceTypeRow) {
  const permList = id2perms.value[record.id]
  const perms = permList ? permList.map((p) => p.name) : []
  resourceTypeFormRef.value?.open({
    id: record.id,
    name: record.name,
    description: record.description,
    perms,
  })
}

function handleDelete(record: ResourceTypeRow) {
  deleteResourceType(record.id)
}

function deleteResourceType(id: number) {
  deleteResourceTypeById(id).then(() => {
    message.success(t('deleteSuccess'))
    handleOk()
  })
}

function handleOk() {
  searchData()
}

function onPageChange(page: number) {
  tablePage.currentPage = page
  searchData()
}

function onSizeChange(size: number) {
  tablePage.pageSize = size
  tablePage.currentPage = 1
  searchData()
}

function handleResize() {
  windowHeight.value = window.innerHeight
}

watch(
  () => route.name,
  () => {
    tablePage.total = 0
    tablePage.currentPage = 1
    tablePage.pageSize = 50
    searchData()
  }
)

watch(searchName, (val) => {
  if (!val) {
    tablePage.currentPage = 1
    searchData()
  }
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
  searchData()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="acl-resource-types">
    <div class="acl-resource-types-header">
      <a-button type="primary" style="margin-right: 0.3rem" @click="handleCreate">
        {{ t('acl.addResourceType') }}
      </a-button>
      <a-input-search
        v-model:value="searchName"
        class="ops-input"
        :style="{ display: 'inline', marginLeft: '10px', width: '200px' }"
        :placeholder="`${t('search')} | ${t('acl.resourceType')}`"
        allow-clear
        @search="handleSearch"
      />
    </div>
    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="groups"
        :pagination="false"
        :scroll="{ x: 750, y: scrollY }"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'permission'">
            <a-tag v-for="perm in id2perms[record.id] || []" :key="perm.id" color="cyan">{{ perm.name }}</a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a @click="handleEdit(record)"><EditOutlined /></a>
            <a-divider type="vertical" />
            <a-popconfirm :title="t('confirmDelete')" @confirm="handleDelete(record)">
              <a style="color: red"><DeleteOutlined /></a>
            </a-popconfirm>
          </template>
        </template>
      </a-table>
      <Pager
        :current-page="tablePage.currentPage"
        :page-size="tablePage.pageSize"
        :page-sizes="pageSizeOptions"
        :total="tablePage.total"
        :is-loading="loading"
        @change="onPageChange"
        @show-size-change="onSizeChange"
      />
    </a-spin>

    <resource-type-form ref="resourceTypeFormRef" :handle-ok="handleOk" />
  </div>
</template>

<style scoped>
.acl-resource-types {
  border-radius: 4px;
  background-color: #fff;
  height: calc(100vh - 64px);
  margin-bottom: -24px;
  padding: 20px;
}
.acl-resource-types-header {
  width: 100%;
  display: inline-flex;
  margin-bottom: 20px;
  align-items: center;
}
</style>
