<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { CheckOutlined, DeleteOutlined, EditOutlined, FileSearchOutlined, TeamOutlined } from '@ant-design/icons-vue'
import type { TableColumnsType } from 'ant-design-vue'
import Pager from '@/components/Pager/index.vue'
import { deleteRoleById, searchRole } from '@/modules/acl/api/role'
import RoleForm from './module/roleForm.vue'
import ResourceUserForm from './module/resourceUserForm.vue'
import UsersUnderRoleForm from './module/usersUnderRoleForm.vue'

interface RoleRow {
  id: number
  name: string
  uid?: number | null
  is_app_admin?: boolean
  [key: string]: unknown
}

interface ParentRole {
  id: number
  name: string
}

const { t } = useI18n()
const route = useRoute()

const loading = ref(false)
const is_all = ref(String(route.name) === 'acl_roles')
const searchName = ref('')
const tableData = ref<RoleRow[]>([])
const allRoles = ref<RoleRow[]>([])
const id2parents = ref<Record<number, ParentRole[]>>({})

const tablePage = reactive({
  total: 0,
  currentPage: 1,
  pageSize: 50,
})
const pageSizeOptions = [20, 50, 100, 200]

const roleFormRef = ref<{
  handleCreate: () => void
  handleEdit: (record: RoleRow) => void
}>()
const resourceUserFormRef = ref<{ loadUserResource: (record: { id: number }) => void }>()
const usersUnderRoleFormRef = ref<{ handleProcessRole: (rid: number) => void }>()

const windowHeight = ref(window.innerHeight)
const scrollY = computed(() => Math.max(windowHeight.value - 200, 200))

const columns = computed<TableColumnsType<RoleRow>>(() => [
  {
    title: t('acl.role'),
    dataIndex: 'name',
    key: 'name',
    width: 150,
    fixed: 'left',
    sorter: (a, b) => (a.name || '').localeCompare(b.name || ''),
  },
  {
    title: t('admin'),
    dataIndex: 'is_app_admin',
    key: 'is_app_admin',
    width: 100,
    align: 'center',
  },
  {
    title: t('acl.inheritedFrom'),
    dataIndex: 'id',
    key: 'id',
    width: 150,
  },
  {
    title: t('acl.visualRole'),
    dataIndex: 'uid',
    key: 'uid',
    width: 120,
    align: 'center',
    filters: [
      { text: t('yes'), value: 1 },
      { text: t('no'), value: 0 },
    ],
    filterMultiple: false,
    onFilter: (value, record) => (Number(value) === 1 ? !record.uid : !!record.uid),
  },
  {
    title: t('operation'),
    dataIndex: 'action',
    key: 'action',
    width: 120,
    fixed: 'right',
    align: 'center',
  },
])

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function initData() {
  searchRole({ app_id: appId(), page_size: 9999 }).then((res) => {
    const data = res as unknown as { roles: RoleRow[] }
    allRoles.value = data.roles || []
  })
}

function loadData() {
  loading.value = true
  const { currentPage, pageSize } = tablePage
  searchRole({
    app_id: appId(),
    page_size: pageSize,
    page: currentPage,
    is_all: is_all.value,
    q: searchName.value,
  })
    .then((res) => {
      const data = res as unknown as {
        roles: RoleRow[]
        id2parents: Record<number, ParentRole[]>
        numfound: number
      }
      tableData.value = data.roles || []
      id2parents.value = data.id2parents || {}
      tablePage.total = data.numfound || 0
      loading.value = false
    })
    .catch(() => {
      loading.value = false
    })
}

function handleOk() {
  loadData()
  initData()
}

function handleSearch() {
  tablePage.currentPage = 1
  loadData()
}

function handleCreate() {
  roleFormRef.value?.handleCreate()
}

function handleEdit(record: RoleRow) {
  roleFormRef.value?.handleEdit(record)
}

function handleDisplayUserResource(record: RoleRow) {
  resourceUserFormRef.value?.loadUserResource({ id: record.id })
}

function handleDisplayUserUnderRole(record: RoleRow) {
  usersUnderRoleFormRef.value?.handleProcessRole(record.id)
}

function handleDelete(record: RoleRow) {
  deleteRole(record.id)
}

function deleteRole(id: number) {
  deleteRoleById(id, { app_id: appId() }).then(() => {
    message.success(t('deleteSuccess'))
    handleOk()
  })
}

function onPageChange(page: number) {
  tablePage.currentPage = page
  loadData()
}

function onSizeChange(size: number) {
  tablePage.pageSize = size
  tablePage.currentPage = 1
  loadData()
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
    tableData.value = []
    allRoles.value = []
    loadData()
    initData()
  }
)

watch(searchName, (val) => {
  if (!val) {
    tablePage.currentPage = 1
    loadData()
  }
})

watch(is_all, () => {
  tablePage.currentPage = 1
  loadData()
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
  initData()
  loadData()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="acl-roles">
    <div class="acl-roles-header">
      <a-button type="primary" @click="handleCreate">{{ t('acl.addVisualRole') }}</a-button>
      <a-input-search
        v-model:value="searchName"
        class="ops-input"
        allow-clear
        :style="{ display: 'inline', marginLeft: '10px', width: '200px' }"
        :placeholder="`${t('search')} | ${t('acl.role')}`"
        @search="handleSearch"
      ></a-input-search>
      <a-checkbox v-model:checked="is_all">{{ t('acl.allRole') }}</a-checkbox>
    </div>
    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="tableData"
        :pagination="false"
        :scroll="{ x: 800, y: scrollY }"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'is_app_admin'">
            <CheckOutlined v-if="record.is_app_admin" />
          </template>
          <template v-else-if="column.key === 'id'">
            <a-tag v-for="role in id2parents[record.id] || []" :key="role.id" color="cyan">{{ role.name }}</a-tag>
          </template>
          <template v-else-if="column.key === 'uid'">
            {{ record.uid ? t('no') : t('yes') }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip v-if="route.name !== 'acl_roles'" :title="t('acl.resourceList')">
                <a @click="handleDisplayUserResource(record)"><FileSearchOutlined /></a>
              </a-tooltip>
              <a-tooltip v-if="!record.uid" :title="t('acl.userList')">
                <a @click="handleDisplayUserUnderRole(record)"><TeamOutlined /></a>
              </a-tooltip>
              <a @click="handleEdit(record)"><EditOutlined /></a>
              <a-popconfirm :title="t('confirmDelete')" :ok-text="t('yes')" :cancel-text="t('no')" @confirm="handleDelete(record)">
                <a style="color: red"><DeleteOutlined /></a>
              </a-popconfirm>
            </a-space>
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

    <RoleForm ref="roleFormRef" :all-roles="allRoles" :id2parents="id2parents" :handle-ok="handleOk" />
    <ResourceUserForm ref="resourceUserFormRef" />
    <UsersUnderRoleForm ref="usersUnderRoleFormRef" :all-roles="allRoles" />
  </div>
</template>

<style scoped>
.acl-roles {
  border-radius: 4px;
  background-color: #fff;
  height: calc(100vh - 64px);
  margin-bottom: -24px;
  padding: 20px;
}
.acl-roles-header {
  width: 100%;
  display: inline-flex;
  margin-bottom: 20px;
  align-items: center;
}
.acl-roles-header :deep(.ant-checkbox-wrapper) {
  margin-left: auto;
}
</style>
