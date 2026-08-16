<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, inject, provide, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import CiTypeGrant from './ciTypeGrant.vue'
import TypeRelationGrant from './typeRelationGrant.vue'
import RelationViewGrant from './relationViewGrant.vue'
import TopologyViewGrant from './topologyViewGrant.vue'
import GrantModal from './grantModal.vue'
import ReadGrantModal from './readGrantModal.vue'
import { searchResource } from '@/modules/acl/api/resource'
import { getResourcePerms } from '@/modules/acl/api/permission'
import { getCITypeGroupById, ciTypeFilterPermissions } from '@/modules/cmdb/api/CIType'
import { CI_DEFAULT_ATTR } from '@/modules/cmdb/constants'
import { useUserStore } from '@/stores/user'

const props = withDefaults(
  defineProps<{
    CITypeId?: number | null
    resourceTypeName?: string
    resourceType?: string
    app_id?: string
    cmdbGrantType?: string
    typeRelationIds?: Array<string | number> | null
    isModal?: boolean
  }>(),
  {
    CITypeId: null,
    resourceTypeName: '',
    resourceType: 'CIType',
    app_id: 'cmdb',
    cmdbGrantType: 'ci_type,ci',
    typeRelationIds: null,
    isModal: false,
  }
)

const { t } = useI18n()
const userStore = useUserStore()

// Injected by the parent view: () => resource type descriptor with `.groups`.
const resourceTypeFn = inject<() => any>('resource_type', () => ({ groups: [] }))

const tableData = ref<Record<string, any>[]>([])
const grantType = ref('')
const resourceId = ref<number | null>(null)
const attrGroup = ref<any[]>([])
const filerPerimissions = ref<Record<string, any>>({})
const loading = ref(false)
const addedRids = ref<Array<{ rid: string | number; name: string }>>([])

const grantModalRef = ref<InstanceType<typeof GrantModal>>()
const readGrantModalRef = ref<InstanceType<typeof ReadGrantModal>>()

const allEmployees = computed<any[]>(() => userStore.allEmployees as any[])
const allDepartments = computed<any[]>(() => userStore.allDepartments as any[])
const childResourceType = computed(() => resourceTypeFn())

// Provide to the grant sub-components.
provide('attrGroup', () => attrGroup.value)
provide('filerPerimissions', () => filerPerimissions.value)
provide('loading', () => loading.value)
provide('isModal', props.isModal)

function getAttrGroup() {
  getCITypeGroupById(props.CITypeId as number, { need_other: true }).then((res: any) => {
    attrGroup.value = res
  })
}

function getFilterPermissions() {
  ciTypeFilterPermissions(props.CITypeId as number).then((res: any) => {
    Object.keys(res).forEach((key) => {
      const attrFilter = res?.[key]?.attr_filter
      if (attrFilter?.length) {
        res[key].attr_filter = attrFilter.filter(
          (item: string) => ![CI_DEFAULT_ATTR.UPDATE_USER, CI_DEFAULT_ATTR.UPDATE_TIME].includes(item)
        )
      }
    })
    filerPerimissions.value = res
  })
}

async function init() {
  const found = childResourceType.value.groups.find((item: any) => item.name === props.resourceType)
  const resourceTypeId = found?.id ?? 0
  const res: any = await searchResource({
    app_id: props.app_id,
    resource_type_id: resourceTypeId,
    page_size: 9999,
  })
  const tempFind = res.resources.find((item: any) => item.name === props.resourceTypeName)
  resourceId.value = tempFind?.id || 0
  getTableData()
}

async function getTableData() {
  loading.value = true
  const table = (await getResourcePerms(resourceId.value as number, { need_users: 0 })) as Record<string, any>
  const perms: Record<string, any>[] = []
  for (const key in table) {
    const obj: Record<string, any> = {}
    obj.name = key
    table[key].perms.forEach((perm: any) => {
      obj[`${perm.name}`] = true
      obj.rid = perm?.rid ?? null
    })
    perms.push(obj)
  }
  tableData.value = perms
  loading.value = false
}

function grantDepart(grantTypeParam: string) {
  grantModalRef.value?.open('depart')
  grantType.value = grantTypeParam
}

function grantRole(grantTypeParam: string) {
  grantModalRef.value?.open('role')
  grantType.value = grantTypeParam
}

function handleOk(params: any, type: string) {
  const currentGrantType = grantType.value
  let rids: Array<{ rid: string | number; name: string }>
  if (type === 'depart') {
    rids = [
      ...params.department.map((rid: any) => {
        const found = allDepartments.value.find((dep: any) => dep.acl_rid === rid)
        return { rid, name: found?.department_name ?? rid }
      }),
      ...params.user.map((rid: any) => {
        const found = allEmployees.value.find((emp: any) => emp.acl_rid === rid)
        return { rid, name: found?.nickname ?? rid }
      }),
    ]
  } else {
    rids = [
      ...params.map((role: any) => {
        return { rid: role.id, name: role.name }
      }),
    ]
  }

  if (currentGrantType === 'ci_type') {
    tableData.value.unshift(
      ...rids.map(({ rid, name }) => {
        const found = tableData.value.find((item) => item.rid === rid)
        return { rid, name, conifg: false, grant: false, ...found }
      })
    )
  }
  if (currentGrantType === 'ci') {
    tableData.value.unshift(
      ...rids.map(({ rid, name }) => {
        const found = tableData.value.find((item) => item.rid === rid)
        return { rid, name, read_attr: false, read_ci: false, create: false, update: false, delete: false, ...found }
      })
    )
  }
  if (currentGrantType === 'type_relation') {
    tableData.value.unshift(
      ...rids.map(({ rid, name }) => {
        return { rid, name, create: false, grant: false, delete: false }
      })
    )
  }
  if (currentGrantType === 'relation_view') {
    tableData.value.unshift(
      ...rids.map(({ rid, name }) => {
        return { rid, name, read: false, grant: false }
      })
    )
  }
  if (currentGrantType === 'TopologyView') {
    tableData.value.unshift(
      ...rids.map(({ rid, name }) => {
        return { rid, name, read: false, update: false, delete: false, grant: false }
      })
    )
  }
  addedRids.value = rids
}

function openReadGrantModal(col: string, row: Record<string, any>) {
  readGrantModalRef.value?.open(col, row)
}

function updateTableDataRead(row: Record<string, any>, hasRead: boolean) {
  const idx = tableData.value.findIndex((item) => item.rid === row.rid)
  tableData.value[idx] = { ...tableData.value[idx], read: hasRead }
  getFilterPermissions()
}

watch(
  () => props.resourceTypeName,
  () => {
    init()
  },
  { immediate: true }
)

watch(
  () => props.CITypeId,
  () => {
    if (props.CITypeId && props.cmdbGrantType.includes('ci')) {
      getFilterPermissions()
      getAttrGroup()
    }
  },
  { immediate: true }
)

defineExpose({ getTableData })
</script>

<template>
  <div class="cmdb-grant">
    <template v-if="cmdbGrantType.includes('ci_type')">
      <div class="cmdb-grant-title">{{ t('cmdb.components.ciTypeGrant') }}</div>
      <div class="cmdb-grant-desc">{{ t('cmdb.components.ciTypeGrantDesc') }}</div>
      <CiTypeGrant
        :c-i-type-id="CITypeId"
        :table-data="tableData"
        grant-type="ci_type"
        :added-rids="addedRids"
        @grant-depart="grantDepart"
        @grant-role="grantRole"
        @get-table-data="getTableData"
      />
    </template>
    <template
      v-if="cmdbGrantType.includes('ci_type,ci') || (cmdbGrantType.includes('ci') && !cmdbGrantType.includes('ci_type'))"
    >
      <div class="cmdb-grant-title">{{ t('cmdb.components.ciGrant') }}</div>
      <div class="cmdb-grant-desc">{{ t('cmdb.components.ciGrantDesc') }}</div>
      <CiTypeGrant
        :c-i-type-id="CITypeId"
        :table-data="tableData"
        grant-type="ci"
        :added-rids="addedRids"
        @grant-depart="grantDepart"
        @grant-role="grantRole"
        @get-table-data="getTableData"
        @open-read-grant-modal="openReadGrantModal"
      />
    </template>
    <template v-if="cmdbGrantType.includes('type_relation')">
      <div class="cmdb-grant-title">{{ t('cmdb.components.relationGrant') }}</div>
      <TypeRelationGrant
        :type-relation-ids="typeRelationIds"
        :table-data="tableData"
        grant-type="type_relation"
        :added-rids="addedRids"
        @grant-depart="grantDepart"
        @grant-role="grantRole"
        @get-table-data="getTableData"
      />
    </template>
    <template v-if="cmdbGrantType.includes('relation_view')">
      <div class="cmdb-grant-title">{{ resourceTypeName }}{{ t('cmdb.components.perm') }}</div>
      <RelationViewGrant
        :resource-type-name="resourceTypeName"
        :table-data="tableData"
        grant-type="relation_view"
        :added-rids="addedRids"
        @grant-depart="grantDepart"
        @grant-role="grantRole"
        @get-table-data="getTableData"
      />
    </template>
    <template v-if="cmdbGrantType.includes('TopologyView')">
      <div class="cmdb-grant-title">{{ resourceTypeName }}{{ t('cmdb.components.perm') }}</div>
      <TopologyViewGrant
        :resource-type-name="resourceTypeName"
        :table-data="tableData"
        :view-id="CITypeId"
        grant-type="TopologyView"
        :added-rids="addedRids"
        @grant-depart="grantDepart"
        @grant-role="grantRole"
        @get-table-data="getTableData"
      />
    </template>

    <GrantModal ref="grantModalRef" @handle-ok="handleOk" />
    <ReadGrantModal ref="readGrantModalRef" :c-i-type-id="CITypeId" @update-table-data-read="updateTableDataRead" />
  </div>
</template>

<style scoped>
.cmdb-grant {
  position: relative;
  padding: 0 20px;
  overflow: auto;
}
.cmdb-grant-title {
  border-left: 4px solid #2f54eb;
  padding-left: 10px;
  margin-bottom: 8px;
}
.cmdb-grant-desc {
  color: #999;
  font-size: 12px;
  margin-bottom: 12px;
  padding-left: 14px;
}
</style>

<style>
.cmdb-grant .grant-button {
  padding: 6px 8px;
  color: #2f54eb;
  background-color: #f0f5ff;
  border-radius: 2px;
  cursor: pointer;
  margin: 15px 0;
  display: inline-block;
  transition: all 0.3s;
  z-index: 1;
}
.cmdb-grant .grant-table-row-focus {
  background-color: #b1c9ff;
}
</style>
