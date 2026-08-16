<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { TableColumnsType } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import {
  getResourcePerms,
  deleteRoleResourcePerm,
  getResourceGroupPerms,
  deleteRoleResourceGroupPerm,
  deleteRoleResourceGroupPerm2,
} from '@/modules/acl/api/permission'

interface PermItem {
  rid: number
  name: string
}

interface UserItem {
  nickname: string
}

interface ResPermRow {
  name: string
  perms: PermItem[]
  users: UserItem[]
}

interface ResourceRecord {
  id: number
  resource_type_id: number
}

const { t } = useI18n()
const route = useRoute()

const isGroup = ref(false)
const visible = ref(false)
const currentRecord = ref<ResourceRecord>({ id: 0, resource_type_id: 0 })
const resPerms = ref<ResPermRow[]>([])
const filterName = ref('')

const windowHeight = ref(window.innerHeight)
const scrollY = computed(() => Math.max(windowHeight.value - 150, 200))

const columns = computed<TableColumnsType<ResPermRow>>(() => [
  { title: t('acl.role'), dataIndex: 'name', key: 'name', width: '20%' },
  { title: t('acl.subordinateUsers'), dataIndex: 'users', key: 'users', width: '35%' },
  { title: t('acl.permissionList'), dataIndex: 'perms', key: 'perms', width: '35%' },
  { title: t('acl.batchOperate'), dataIndex: 'operate', key: 'operate' },
])

const filteredResPerms = computed(() => {
  if (!filterName.value) return resPerms.value
  const lower = filterName.value.toLowerCase()
  return resPerms.value.filter((item) => (item.name || '').toLowerCase().includes(lower))
})

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function handlePerm(r: ResourceRecord, group: boolean) {
  isGroup.value = group
  visible.value = true
  currentRecord.value = r
  getResPerms(r.id)
}

function normalizePerms(res: unknown): ResPermRow[] {
  const data = res as Record<string, { perms?: PermItem[]; users?: UserItem[] }>
  const result: ResPermRow[] = []
  for (const key in data) {
    result.push({ name: key, perms: data[key].perms || [], users: data[key].users || [] })
  }
  return result
}

function getResPerms(resId: number) {
  const req = isGroup.value ? getResourceGroupPerms(resId) : getResourcePerms(resId)
  req.then((res) => {
    resPerms.value = normalizePerms(res)
  })
}

function handleClearAll(row: ResPermRow) {
  const rid = row.perms[0]?.rid
  if (rid == null) return
  const params = { perms: [], app_id: appId() }
  const req = isGroup.value
    ? deleteRoleResourceGroupPerm2(rid, currentRecord.value.id, params)
    : deleteRoleResourcePerm(rid, currentRecord.value.id, params)
  req.then(() => {
    message.success(t('deleteSuccess'))
    getResPerms(currentRecord.value.id)
  })
}

function deletePerm(roleID: number, permName: string) {
  const params = { perms: [permName], app_id: appId() }
  const req = isGroup.value
    ? deleteRoleResourceGroupPerm(roleID, currentRecord.value.id, params)
    : deleteRoleResourcePerm(roleID, currentRecord.value.id, params)
  req.then(() => {
    message.success(t('deleteSuccess'))
  })
}

function handleResize() {
  windowHeight.value = window.innerHeight
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

defineExpose({ handlePerm })
</script>

<template>
  <CustomDrawer
    v-model:open="visible"
    :title="t('acl.permissionList')"
    width="80%"
    placement="left"
    :has-footer="false"
  >
    <div class="resource-perm-toolbar">
      <a-input-search
        v-model:value="filterName"
        :placeholder="t('acl.role')"
        allow-clear
        style="width: 300px"
      />
    </div>
    <a-table
      :columns="columns"
      :data-source="filteredResPerms"
      :pagination="false"
      :scroll="{ y: scrollY }"
      row-key="name"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'users'">
          <a-tag v-for="u in record.users || []" :key="u.nickname" color="green">{{ u.nickname }}</a-tag>
        </template>
        <template v-else-if="column.key === 'perms'">
          <a-tag
            v-for="perm in record.perms || []"
            :key="perm.name"
            closable
            color="cyan"
            @close="deletePerm(perm.rid, perm.name)"
          >
            {{ perm.name }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'operate'">
          <a-button size="small" type="danger" @click="handleClearAll(record)">
            {{ t('clear') }}
          </a-button>
        </template>
      </template>
    </a-table>
  </CustomDrawer>
</template>

<style scoped>
.resource-perm-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
</style>
