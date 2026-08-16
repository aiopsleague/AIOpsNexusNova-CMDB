<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import PermissionHistoryTable from './module/permissionHistoryTable.vue'
import RoleHistoryTable from './module/roleHistoryTable.vue'
import ResourceHistoryTable from './module/resourceHistoryTable.vue'
import ResourceTypeHistoryTable from './module/resourceTypeHistoryTable.vue'
import TriggerHistoryTable from './module/triggerHistoryTable.vue'
import { getTriggers } from '@/modules/acl/api/trigger'
import { searchRole } from '@/modules/acl/api/role'
import { searchUser } from '@/modules/acl/api/user'
import { searchResource, searchResourceType } from '@/modules/acl/api/resource'

interface OptionItem {
  [name: string]: number
}

const { t } = useI18n()
const route = useRoute()

const isLoaded = ref(false)
const resourcesNum = ref(0)
const resourcesPage = ref(1)

const allResourceTypes = ref<OptionItem[]>([])
const allResources = ref<OptionItem[]>([])
const allUsers = ref<OptionItem[]>([])
const allRoles = ref<OptionItem[]>([])
const allTriggers = ref<OptionItem[]>([])

const allRolesMap = ref<Map<number, string>>(new Map())
const allUsersMap = ref<Map<number, string>>(new Map())
const allResourceTypesMap = ref<Map<number, string>>(new Map())
const allResourcesMap = ref<Map<number, string>>(new Map())
const allTriggersMap = ref<Map<number, string>>(new Map())

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

async function initData() {
  await Promise.all([getAllRoles(), getAllUsers(), getAllResourceTypes(), getAllResources(1), loadTriggers()])
}

async function getAllRoles() {
  const res = (await searchRole({ app_id: appId(), page_size: 9999 })) as unknown as {
    roles: Array<{ id: number; name: string }>
  }
  const roles: OptionItem[] = []
  const rolesMap = new Map<number, string>()
  res.roles.forEach((item) => {
    roles.push({ [item.name]: item.id })
    rolesMap.set(item.id, item.name)
  })
  allRoles.value = roles
  allRolesMap.value = rolesMap
}

async function getAllUsers() {
  const res = (await searchUser({ page_size: 10000 })) as unknown as {
    users: Array<{ uid: number; nickname: string }>
  }
  const users: OptionItem[] = []
  const usersMap = new Map<number, string>()
  res.users.forEach((item) => {
    users.push({ [item.nickname]: item.uid })
    usersMap.set(item.uid, item.nickname)
  })
  allUsers.value = users
  allUsersMap.value = usersMap
}

async function getAllResourceTypes() {
  const res = (await searchResourceType({ app_id: appId(), page_size: 9999, page: 1 })) as unknown as {
    groups: Array<{ id: number; name: string }>
  }
  const resourceTypes: OptionItem[] = []
  const resourceTypesMap = new Map<number, string>()
  res.groups.forEach((item) => {
    resourceTypes.push({ [item.name]: item.id })
    resourceTypesMap.set(item.id, item.name)
  })
  allResourceTypes.value = resourceTypes
  allResourceTypesMap.value = resourceTypesMap
}

async function getAllResources(page = 1, value?: string) {
  const res = (await searchResource({ page, page_size: 50, app_id: appId(), q: value })) as unknown as {
    resources: Array<{ id: number; name: string }>
    numfound: number
  }
  resourcesNum.value = res.numfound
  const resources = allResources.value
  const resourcesMap = allResourcesMap.value
  res.resources.forEach((item) => {
    resources.push({ [item.name]: item.id })
    resourcesMap.set(item.id, item.name)
  })
  allResources.value = resources
  allResourcesMap.value = resourcesMap
}

function reloadResources() {
  resourcesPage.value = 1
  allResources.value = []
  allResourcesMap.value = new Map()
  getAllResources()
}

function loadMoreResources(value?: string) {
  if (allResources.value.length < resourcesNum.value) {
    resourcesPage.value += 1
    getAllResources(resourcesPage.value, value)
  }
}

function resourceClear() {
  resourcesPage.value = 1
  allResources.value = []
  getAllResources()
}

async function fetchResources(value: string) {
  const resources: OptionItem[] = []
  const resourcesMap = new Map<number, string>()
  const res = (await searchResource({ page: 1, page_size: 50, app_id: appId(), q: value })) as unknown as {
    resources: Array<{ id: number; name: string }>
    numfound: number
  }
  resourcesNum.value = res.numfound
  resourcesPage.value = 1
  res.resources.forEach((item) => {
    resources.push({ [item.name]: item.id })
    resourcesMap.set(item.id, item.name)
  })
  allResources.value = resources
  allResourcesMap.value = resourcesMap
}

async function loadTriggers() {
  const res = (await getTriggers({ app_id: appId() })) as unknown as Array<{ id: number; name: string }>
  const triggers: OptionItem[] = []
  const triggersMap = new Map<number, string>()
  res.forEach((item) => {
    triggers.push({ [item.name]: item.id })
    triggersMap.set(item.id, item.name)
  })
  allTriggers.value = triggers
  allTriggersMap.value = triggersMap
}

watch(
  () => route.name,
  async () => {
    isLoaded.value = false
    allResources.value = []
    resourcesPage.value = 1
    await initData()
    isLoaded.value = true
  }
)

onMounted(async () => {
  await initData()
  isLoaded.value = true
})
</script>

<template>
  <div class="acl-history">
    <a-tabs default-active-key="1">
      <a-tab-pane key="1" :tab="t('acl.permissionChange')">
        <PermissionHistoryTable
          v-if="isLoaded"
          :all-resource-types="allResourceTypes"
          :all-resources="allResources"
          :all-users="allUsers"
          :all-roles="allRoles"
          :all-roles-map="allRolesMap"
          :all-users-map="allUsersMap"
          :all-resource-types-map="allResourceTypesMap"
          @load-more-resources="loadMoreResources"
          @reload-resources="reloadResources"
          @fetch-resources="fetchResources"
          @resource-clear="resourceClear"
        />
      </a-tab-pane>
      <a-tab-pane key="2" :tab="t('acl.roleChange')">
        <RoleHistoryTable
          v-if="isLoaded"
          :all-users="allUsers"
          :all-roles="allRoles"
          :all-roles-map="allRolesMap"
          :all-users-map="allUsersMap"
        />
      </a-tab-pane>
      <a-tab-pane key="3" :tab="t('acl.resourceChange')">
        <ResourceHistoryTable
          v-if="isLoaded"
          :all-resources="allResources"
          :all-users="allUsers"
          :all-roles="allRoles"
          :all-roles-map="allRolesMap"
          :all-users-map="allUsersMap"
          :all-resources-map="allResourcesMap"
          @load-more-resources="loadMoreResources"
          @reload-resources="reloadResources"
          @fetch-resources="fetchResources"
          @resource-clear="resourceClear"
        />
      </a-tab-pane>
      <a-tab-pane key="4" :tab="t('acl.resourceTypeChange')">
        <ResourceTypeHistoryTable
          v-if="isLoaded"
          :all-resource-types="allResourceTypes"
          :all-users="allUsers"
          :all-roles="allRoles"
          :all-roles-map="allRolesMap"
          :all-users-map="allUsersMap"
          :all-resource-types-map="allResourceTypesMap"
        />
      </a-tab-pane>
      <a-tab-pane key="5" :tab="t('acl.triggerChange')">
        <TriggerHistoryTable
          v-if="isLoaded"
          :all-triggers="allTriggers"
          :all-users="allUsers"
          :all-roles="allRoles"
          :all-roles-map="allRolesMap"
          :all-users-map="allUsersMap"
          :all-triggers-map="allTriggersMap"
          :all-resource-types-map="allResourceTypesMap"
        />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<style scoped>
.acl-history {
  border-radius: 4px;
  height: calc(100vh - 64px);
  margin-bottom: -24px;
  padding: 24px;
  background-color: #fff;
}
</style>
