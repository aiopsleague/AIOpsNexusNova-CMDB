<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { TableColumnsType } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { useUserStore } from '@/stores/user'
import { searchApp } from '@/modules/acl/api/app'
import { searchRole } from '@/modules/acl/api/role'
import { searchResourceType } from '@/modules/acl/api/resource'
import { searchPermResourceByRoleId } from '@/modules/acl/api/permission'

interface AppRow {
  id: number
  name: string
}

interface ResourceTypeRow {
  id?: number
  name?: string
}

interface RoleRow {
  id?: number
  uid?: number
}

interface ResourceRow {
  id?: number
  name: string
  permissions?: string[]
}

interface UserRow {
  uid?: number
  nickname?: string
}

const { t } = useI18n()
const userStore = useUserStore()

const spinning = ref(false)
const visible = ref(false)
const user = ref<UserRow>({})
const roles = ref<RoleRow[]>([])
const apps = ref<AppRow[]>([])
const currentAppId = ref(0)
const currentResourceId = ref<string | number | undefined>(undefined)
const resourceTypes = ref<ResourceTypeRow[]>([])
const resources = ref<ResourceRow[]>([])
const filterName = ref('')

const windowHeight = ref(window.innerHeight)
const scrollY = computed(() => Math.max(windowHeight.value - 230, 200))

const displayApps = computed(() => {
  const perms = (userStore.roles?.permissions ?? []) as unknown as string[]
  if (perms.includes('acl_admin')) return apps.value
  return apps.value.filter((item) => perms.includes(`${item.name}_admin`))
})

const columns = computed<TableColumnsType<ResourceRow>>(() => [
  { title: t('acl.resourceName'), dataIndex: 'name', key: 'name', width: '30%' },
  { title: t('acl.permissionList'), dataIndex: 'permissions', key: 'permissions', width: '70%' },
])

const filteredResources = computed(() => {
  if (!filterName.value) return resources.value
  const lower = filterName.value.toLowerCase()
  return resources.value.filter((item) => (item.name || '').toLowerCase().includes(lower))
})

function collect(u: UserRow) {
  user.value = u
  visible.value = true
  setTimeout(() => {
    loadResource()
  }, 500)
}

async function loadRoles(appId: number) {
  const res = await searchRole({ app_id: appId, page_size: 9999, is_all: true })
  const data = res as unknown as { roles: RoleRow[] }
  roles.value = (data.roles || []).filter((item) => item.uid)
}

async function handleSwitchApp(appId: string | number) {
  currentAppId.value = Number(appId)
  await loadResourceTypes(Number(appId))
}

async function loadApps() {
  const res = await searchApp()
  const data = res as unknown as { apps: AppRow[] }
  apps.value = data.apps || []
  if (displayApps.value[0]) {
    currentAppId.value = displayApps.value[0].id
    await loadRoles(apps.value[0].id)
    await loadResourceTypes(displayApps.value[0].id)
  } else {
    message.info('No apps!')
  }
}

async function loadResourceTypes(appId: number) {
  const res = await searchResourceType({ app_id: appId, page_size: 9999 })
  const data = res as unknown as { groups: ResourceTypeRow[] }
  resourceTypes.value = data.groups || []
  currentResourceId.value = resourceTypes.value[0] && resourceTypes.value[0].id
  await loadResource()
}

async function loadResource() {
  spinning.value = true
  const fil = roles.value.filter((role) => role.uid === user.value.uid)
  if (!fil[0]) {
    spinning.value = false
    return
  }
  const res = await searchPermResourceByRoleId(fil[0].id ?? 0, {
    resource_type_id: currentResourceId.value,
    app_id: currentAppId.value,
  })
  const data = res as unknown as { resources: ResourceRow[] }
  resources.value = data.resources || []
  spinning.value = false
}

function handleResize() {
  windowHeight.value = window.innerHeight
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  loadApps()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

defineExpose({ collect })
</script>

<template>
  <CustomDrawer
    v-model:open="visible"
    :title="`${t('acl.summaryPermissions')}: ${user.nickname || ''}`"
    placement="left"
    width="100%"
    :has-footer="false"
  >
    <a-tabs @change="handleSwitchApp">
      <a-tab-pane
        v-for="app in displayApps"
        :key="app.id"
        :tab="app.name.slice(0, 1).toUpperCase() + app.name.slice(1)"
      >
        <a-tabs
          v-if="resourceTypes && resourceTypes.length"
          v-model:active-key="currentResourceId"
          :animated="false"
          @change="loadResource"
        >
          <a-tab-pane v-for="rType in resourceTypes" :key="rType.id" :tab="rType.name">
            <a-spin :spinning="spinning">
              <div class="perm-collect-toolbar">
                <a-input-search
                  v-model:value="filterName"
                  :placeholder="t('acl.resourceName')"
                  allow-clear
                  style="width: 300px"
                />
              </div>
              <a-table
                :columns="columns"
                :data-source="filteredResources"
                :pagination="false"
                :scroll="{ y: scrollY }"
                row-key="id"
                size="small"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'permissions'">
                    <a-tag v-for="(r, index) in record.permissions || []" :key="index" color="cyan">{{ r }}</a-tag>
                  </template>
                </template>
              </a-table>
            </a-spin>
          </a-tab-pane>
        </a-tabs>
      </a-tab-pane>
    </a-tabs>
  </CustomDrawer>
</template>

<style scoped>
.perm-collect-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
</style>
