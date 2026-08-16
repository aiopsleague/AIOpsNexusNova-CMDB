<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { DeleteOutlined, EyeOutlined, InfoCircleOutlined, UsergroupAddOutlined } from '@ant-design/icons-vue'
import type { TableColumnsType } from 'ant-design-vue'
import Pager from '@/components/Pager/index.vue'
import {
  deleteResourceById,
  searchResource,
  searchResourceType,
  getResourceGroups,
  deleteResourceGroup,
} from '@/modules/acl/api/resource'
import ResourceForm from './module/resourceForm.vue'
import ResourceGroupModal from './module/resourceGroupModal.vue'
import ResourceGroupMember from './module/resourceGroupMember.vue'
import ResourcePermForm from './module/resourcePermForm.vue'
import ResourcePermManageForm from './module/resourcePermManageForm.vue'
import ResourceBatchPerm from './module/resourceBatchPerm.vue'

interface ResourceRow {
  id: number
  name: string
  user?: string
  created_at?: string
  updated_at?: string
  [key: string]: unknown
}

interface ResourceTypeRow {
  id?: number
  name?: string
  [key: string]: unknown
}

const { t } = useI18n()
const route = useRoute()

const loading = ref(false)
const tableData = ref<ResourceRow[]>([])
const isGroup = ref(false)
const allResourceTypes = ref<ResourceTypeRow[]>([])
const currentType = ref<ResourceTypeRow>({ id: 0 })
const activeKey = ref<string | number | undefined>(undefined)
const searchName = ref('')
const selectedRowKeys = ref<(string | number)[]>([])
const selectedRows = ref<ResourceRow[]>([])

const pageSizeOptions = [20, 50, 100, 200]
const tablePage = reactive({
  total: 0,
  currentPage: 1,
  pageSize: 50,
})

const windowHeight = ref(window.innerHeight)
const scrollY = computed(() => Math.max(windowHeight.value - 250, 200))

const resourceFormRef = ref<{ handleCreate: (type: ResourceTypeRow) => void }>()
const resourceGroupModalRef = ref<{ handleEdit: (record: ResourceRow) => void }>()
const resourceGroupMemberRef = ref<{ handleEdit: (record: ResourceRow) => void }>()
const resourcePermFormRef = ref<{ handlePerm: (record: ResourceRow, group: boolean) => void }>()
const resourcePermManageFormRef = ref<{
  editPerm: (record: ResourceRow | ResourceRow[], group: boolean, grantOrRevoke?: 'grant' | 'revoke') => void
}>()
const resourceBatchPermRef = ref<{ open: (currentTypeId: number) => void }>()

const columns = computed<TableColumnsType<ResourceRow>>(() => [
  {
    title: isGroup.value ? t('acl.groupName') : t('acl.resourceName'),
    dataIndex: 'name',
    key: 'name',
    width: 150,
    fixed: 'left',
  },
  { title: t('acl.creator'), dataIndex: 'user', key: 'user', width: 120 },
  { title: t('created_at'), dataIndex: 'created_at', key: 'created_at', width: 180, align: 'center' },
  { title: t('updated_at'), dataIndex: 'updated_at', key: 'updated_at', width: 180, align: 'center' },
  { title: t('operation'), dataIndex: 'action', key: 'action', width: 200, fixed: 'right', align: 'center' },
])

const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: (string | number)[], rows: ResourceRow[]) => {
    selectedRowKeys.value = keys
    selectedRows.value = rows
  },
}))

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function searchData() {
  loading.value = true
  const param = {
    app_id: appId(),
    resource_type_id: currentType.value.id,
    page_size: tablePage.pageSize,
    page: tablePage.currentPage,
    q: searchName.value,
  }
  const fetcher = isGroup.value ? getResourceGroups(param) : searchResource(param)
  fetcher
    .then((res) => {
      const data = res as unknown as {
        numfound: number
        page: number
        resources?: ResourceRow[]
        groups?: ResourceRow[]
      }
      tablePage.total = data.numfound
      tablePage.currentPage = data.page
      tableData.value = (isGroup.value ? data.groups : data.resources) || []
      loading.value = false
    })
    .catch(() => {
      loading.value = false
    })
}

async function getAllResourceTypes() {
  const res = await searchResourceType({ page_size: 9999, app_id: appId() })
  const data = res as unknown as { groups: ResourceTypeRow[] }
  allResourceTypes.value = data.groups || []
  if (allResourceTypes.value.length) {
    activeKey.value = allResourceTypes.value[0].id
    loadCurrentType(allResourceTypes.value[0].id)
  }
}

function loadCurrentType(rtypeId: string | number | undefined) {
  searchName.value = ''
  clearSelection()
  tablePage.currentPage = 1
  if (rtypeId != null) {
    const found = allResourceTypes.value.find((item) => String(item.id) === String(rtypeId))
    if (found) currentType.value = found
  }
  searchData()
}

function clearSelection() {
  selectedRowKeys.value = []
  selectedRows.value = []
}

function handleCreate() {
  resourceFormRef.value?.handleCreate(currentType.value)
}

function handleDisplayMember(record: ResourceRow) {
  resourceGroupMemberRef.value?.handleEdit(record)
}

function handleGroupEdit(record: ResourceRow) {
  resourceGroupModalRef.value?.handleEdit(record)
}

function handleDelete(record: ResourceRow) {
  deleteResource(record.id)
}

function deleteResource(id: number) {
  const doDelete = isGroup.value ? deleteResourceGroup(id) : deleteResourceById(id, { app_id: appId() })
  doDelete.then(() => {
    message.success(t('deleteSuccess'))
    handleOk()
  })
}

function handleOk() {
  tablePage.currentPage = 1
  searchData()
}

function handleSearch() {
  tablePage.currentPage = 1
  searchData()
}

function handleIsGroupChange() {
  searchName.value = ''
  tablePage.currentPage = 1
  clearSelection()
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

function handlePerm(record: ResourceRow) {
  resourcePermFormRef.value?.handlePerm(record, isGroup.value)
}
function handlePermManage(record: ResourceRow) {
  resourcePermManageFormRef.value?.editPerm(record, isGroup.value)
}
function handleBatchPerm() {
  resourcePermManageFormRef.value?.editPerm(selectedRows.value, isGroup.value)
}
function handleBatchRevoke() {
  resourcePermManageFormRef.value?.editPerm(selectedRows.value, isGroup.value, 'revoke')
}
function handleBatchPermOpen() {
  resourceBatchPermRef.value?.open(currentType.value.id as number)
}
function closePerm() {
  clearSelection()
}

function handleResize() {
  windowHeight.value = window.innerHeight
}

watch(
  () => route.name,
  () => {
    isGroup.value = false
    tablePage.total = 0
    tablePage.currentPage = 1
    tablePage.pageSize = 50
    getAllResourceTypes()
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
  getAllResourceTypes()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="acl-resources">
    <div v-if="allResourceTypes.length">
      <a-tabs v-model:active-key="activeKey" @change="loadCurrentType">
        <a-tab-pane v-for="rtype in allResourceTypes" :key="rtype.id" :tab="rtype.name" />
      </a-tabs>

      <div class="acl-resources-header">
        <a-space>
          <a-button type="primary" @click="handleCreate">{{ t('acl.addResource') }}</a-button>
          <a-input-search
            v-model:value="searchName"
            class="ops-input"
            allow-clear
            :placeholder="`${t('search')} | ${t('acl.resource')}`"
            @search="handleSearch"
          />

          <div v-if="selectedRows.length" class="ops-list-batch-action">
            <a @click="handleBatchPerm">{{ t('grant') }}</a>
            <a-divider type="vertical" />
            <a @click="handleBatchRevoke">{{ t('acl.revoke') }}</a>
            <span>{{ t('selectRows', { rows: selectedRows.length }) }}</span>
          </div>
        </a-space>

        <a-space>
          <a-button type="primary" ghost @click="handleBatchPermOpen">{{ t('acl.convenient') }}</a-button>
          <a-switch v-model:checked="isGroup" :un-checked-children="t('acl.group2')" @change="handleIsGroupChange" />
        </a-space>
      </div>

      <a-spin :spinning="loading">
        <a-table
          :columns="columns"
          :data-source="tableData"
          :pagination="false"
          :scroll="{ x: 900, y: scrollY }"
          :row-selection="rowSelection"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <template v-if="isGroup">
                <a @click="handleDisplayMember(record)">{{ t('acl.member') }}</a>
                <a-divider type="vertical" />
                <a @click="handleGroupEdit(record)">{{ t('edit') }}</a>
                <a-divider type="vertical" />
              </template>
              <a-tooltip :title="t('acl.viewAuth')">
                <a @click="handlePerm(record)"><EyeOutlined /></a>
              </a-tooltip>
              <a-divider type="vertical" />
              <a-tooltip :title="t('grant')">
                <a :style="{ color: '#4bbb13' }" @click="handlePermManage(record)"><UsergroupAddOutlined /></a>
              </a-tooltip>
              <a-divider type="vertical" />
              <a-popconfirm
                :title="t('confirmDelete')"
                :ok-text="t('yes')"
                :cancel-text="t('no')"
                @confirm="handleDelete(record)"
              >
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
    </div>

    <div v-else class="acl-resources-empty">
      <InfoCircleOutlined style="font-size: 50px; margin-bottom: 20px; color: orange" />
      <h3>{{ t('acl.addTypeTips') }}</h3>
    </div>

    <ResourceForm ref="resourceFormRef" :handle-ok="handleOk" />
    <ResourcePermForm ref="resourcePermFormRef" />
    <ResourcePermManageForm ref="resourcePermManageFormRef" :group-type-message="currentType" @close="closePerm" />
    <ResourceGroupModal ref="resourceGroupModalRef" />
    <ResourceGroupMember ref="resourceGroupMemberRef" />
    <ResourceBatchPerm ref="resourceBatchPermRef" />
  </div>
</template>

<style scoped>
.acl-resources {
  border-radius: 4px;
  background-color: #fff;
  height: calc(100vh - 64px);
  margin-bottom: -24px;
  padding: 8px 20px 20px 20px;
}
.acl-resources-header {
  width: 100%;
  display: inline-flex;
  margin-bottom: 20px;
  align-items: center;
  justify-content: space-between;
}
.acl-resources-header :deep(.ant-switch) {
  margin-left: auto;
}
.acl-resources-empty {
  text-align: center;
  margin-top: 20%;
}
</style>
