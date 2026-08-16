<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { TableColumnsType } from 'ant-design-vue'
import { AppstoreOutlined, DeleteOutlined, EditOutlined, EyeOutlined, StopOutlined } from '@ant-design/icons-vue'
import { getTriggers, deleteTrigger, applyTrigger, cancelTrigger } from '@/modules/acl/api/trigger'
import { searchRole } from '@/modules/acl/api/role'
import { searchResourceType } from '@/modules/acl/api/resource'
import TriggerForm from './module/triggerForm.vue'
import TriggerPattern from './module/triggerPattern.vue'

interface RoleRow {
  id: number
  name: string
  uid?: number
  [key: string]: unknown
}

interface ResourceTypeRow {
  id: number
  name: string
  [key: string]: unknown
}

interface PermRow {
  id: number
  name: string
}

interface TriggerRow {
  id: number
  name: string
  wildcard: string
  resource_type_id: number
  uid: number[]
  users: string[]
  roles: number[]
  permissions: string[]
  enabled: boolean
  [key: string]: unknown
}

const { t } = useI18n()
const route = useRoute()

const roles = ref<RoleRow[]>([])
const searchName = ref('')
const resourceTypeList = ref<ResourceTypeRow[]>([])
const triggers = ref<TriggerRow[]>([])
const filterTriggers = ref<TriggerRow[]>([])
const id2perms = ref<Record<number, PermRow[]>>({})

const triggerFormRef = ref<{ handleEdit: (record: TriggerRow | null) => void }>()
const triggerPatternRef = ref<{ open: (params: Record<string, unknown>) => void }>()

const windowHeight = ref(window.innerHeight)
const scrollY = computed(() => Math.max(windowHeight.value - 185, 200))

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

const columns = computed<TableColumnsType<TriggerRow>>(() => [
  {
    title: t('name'),
    dataIndex: 'name',
    key: 'name',
    width: 150,
    fixed: 'left',
    ellipsis: true,
    sorter: (a, b) => (a.name || '').localeCompare(b.name || ''),
  },
  { title: t('acl.resource'), dataIndex: 'wildcard', key: 'wildcard', width: 250 },
  { title: t('acl.resourceType'), dataIndex: 'resource_type_id', key: 'resource_type_id', width: 120 },
  { title: t('acl.creator'), dataIndex: 'users', key: 'users', width: 150 },
  { title: t('acl.allRole'), dataIndex: 'roles', key: 'roles', width: 150 },
  { title: t('acl.permission'), dataIndex: 'permissions', key: 'permissions', width: 250 },
  { title: t('status'), dataIndex: 'enabled', key: 'enabled', width: 100 },
  { title: t('operation'), dataIndex: 'action', key: 'action', width: 120, fixed: 'right' },
])

function getResourceTypeName(id: number): string {
  const found = resourceTypeList.value.find((item) => item.id === id)
  return found ? found.name : 'unkown'
}

function getRoleNames(row: TriggerRow): string[] {
  return (row.roles || []).map((id) => {
    const found = roles.value.find((role) => role.id === Number(id))
    return found ? found.name : 'unknown'
  })
}

function loadTriggers() {
  searchName.value = ''
  getTriggers({ app_id: appId() }).then((res) => {
    const data = res as unknown as TriggerRow[]
    triggers.value = data
    filterTriggers.value = data
  })
}

function loadRoles() {
  searchRole({ app_id: appId(), page_size: 9999 }).then((res) => {
    const data = res as unknown as { roles: RoleRow[] }
    roles.value = data.roles || []
  })
}

function loadResourceTypeList() {
  searchResourceType({ app_id: appId(), page_size: 9999 }).then((res) => {
    const data = res as unknown as { groups: ResourceTypeRow[]; id2perms: Record<number, PermRow[]> }
    resourceTypeList.value = data.groups || []
    id2perms.value = data.id2perms || {}
  })
}

function handleCreateTrigger() {
  triggerFormRef.value?.handleEdit(null)
}

function handleEditTrigger(record: TriggerRow) {
  triggerFormRef.value?.handleEdit(record)
}

function handleDeleteTrigger(record: TriggerRow) {
  Modal.confirm({
    title: t('warning'),
    content: t('acl.confirmDeleteTrigger'),
    onOk() {
      deleteTrigger(record.id).then(() => {
        message.success(t('deleteSuccess'))
        loadTriggers()
      })
    },
  })
}

function handleApplyTrigger(record: TriggerRow) {
  Modal.confirm({
    title: t('acl.ruleApply'),
    content: t('acl.triggerTip1'),
    onOk() {
      applyTrigger(record.id).then(() => {
        message.success(t('operateSuccess'))
      })
    },
  })
}

function handleCancelTrigger(record: TriggerRow) {
  Modal.confirm({
    title: t('acl.ruleApply'),
    content: t('acl.triggerTip2'),
    onOk() {
      cancelTrigger(record.id).then(() => {
        message.success(t('operateSuccess'))
      })
    },
  })
}

function handlePattern(row: TriggerRow) {
  const { wildcard, uid, resource_type_id } = row
  triggerPatternRef.value?.open({
    resource_type_id,
    app_id: appId(),
    owner: uid,
    pattern: wildcard,
  })
}

function filter() {
  if (searchName.value) {
    const lower = searchName.value.toLowerCase()
    filterTriggers.value = triggers.value.filter((item) => item.name.toLowerCase().includes(lower))
  } else {
    filterTriggers.value = triggers.value
  }
}

function handleResize() {
  windowHeight.value = window.innerHeight
}

watch(
  () => route.name,
  () => {
    loadTriggers()
  }
)

watch(
  searchName,
  (val) => {
    if (!val) {
      filter()
    }
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('resize', handleResize)
  loadRoles()
  loadResourceTypeList()
  loadTriggers()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="acl-trigger">
    <div class="acl-trigger-header">
      <a-button type="primary" @click="handleCreateTrigger">{{ t('acl.addTrigger') }}</a-button>
      <a-input-search
        v-model:value="searchName"
        class="ops-input"
        :style="{ display: 'inline', marginLeft: '10px', width: '200px' }"
        :placeholder="`${t('search')} | ${t('name')}`"
        allow-clear
        @search="filter"
      />
    </div>

    <a-table
      :columns="columns"
      :data-source="filterTriggers"
      :pagination="false"
      :scroll="{ x: 1300, y: scrollY }"
      row-key="id"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'wildcard'">
          <div style="word-break: break-word">
            <span>{{ record.wildcard }}</span>
          </div>
        </template>
        <template v-else-if="column.key === 'resource_type_id'">
          {{ getResourceTypeName(record.resource_type_id) }}
        </template>
        <template v-else-if="column.key === 'users'">
          <span v-for="(u, index) in record.users" :key="index">
            {{ u }}<a-divider v-if="index < record.users.length - 1" type="vertical" />
          </span>
        </template>
        <template v-else-if="column.key === 'roles'">
          <span v-if="getRoleNames(record).length <= 1">
            <span v-for="(name, index) in getRoleNames(record)" :key="index">{{ name }}</span>
          </span>
          <a-tooltip v-else>
            <template #title>
              <span v-for="(name, index) in getRoleNames(record)" :key="index">
                <span>{{ name }}</span>
                <a-divider v-if="index < getRoleNames(record).length - 1" type="vertical" />
              </span>
            </template>
            <span>{{ getRoleNames(record)[0] }}...</span>
          </a-tooltip>
        </template>
        <template v-else-if="column.key === 'permissions'">
          <a-tag v-for="(p, index) in record.permissions" :key="index">{{ p }}</a-tag>
        </template>
        <template v-else-if="column.key === 'enabled'">
          <a-tag v-if="record.enabled" color="#2db7f5">{{ t('acl.enable') }}</a-tag>
          <a-tag v-else color="grey">{{ t('acl.disable') }}</a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-tooltip :title="t('acl.apply')">
              <a :style="{ color: '#0f9d58' }" @click="handleApplyTrigger(record)"><AppstoreOutlined /></a>
            </a-tooltip>
            <a-tooltip :title="t('cancel')">
              <a :style="{ color: 'orange' }" @click="handleCancelTrigger(record)"><StopOutlined /></a>
            </a-tooltip>
            <a-tooltip :title="t('acl.viewMatchResult')">
              <a :style="{ color: 'purple' }" @click="handlePattern(record)"><EyeOutlined /></a>
            </a-tooltip>
            <a @click="handleEditTrigger(record)"><EditOutlined /></a>
            <a :style="{ color: 'red' }" @click="handleDeleteTrigger(record)"><DeleteOutlined /></a>
          </a-space>
        </template>
      </template>
    </a-table>

    <TriggerForm
      ref="triggerFormRef"
      :roles="roles"
      :resource-type-list="resourceTypeList"
      :id2perms="id2perms"
      @refresh="loadTriggers"
    />
    <TriggerPattern ref="triggerPatternRef" :roles="roles" />
  </div>
</template>

<style scoped>
.acl-trigger {
  border-radius: 4px;
  background-color: #fff;
  height: calc(100vh - 64px);
  margin-bottom: -24px;
  padding: 20px;
}
.acl-trigger-header {
  width: 100%;
  display: inline-flex;
  margin-bottom: 20px;
  align-items: center;
}
</style>
