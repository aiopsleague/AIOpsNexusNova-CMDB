<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { CopyOutlined } from '@ant-design/icons-vue'
import type { TableColumnsType } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { searchPermResourceByRoleId } from '@/modules/acl/api/permission'
import { searchResourceType } from '@/modules/acl/api/resource'

interface ResourceTypeOption {
  id?: number
  name?: string
}

interface ResourceRow {
  id?: number
  name: string
  permissions?: string[]
}

const { t } = useI18n()
const route = useRoute()

const visible = ref(false)
const rid = ref(0)
const records = ref<ResourceRow[]>([])
const resourceTypes = ref<ResourceTypeOption[]>([])
const typeSelected = ref<number | null>(null)
const filterName = ref('')

const windowHeight = ref(window.innerHeight)
const scrollY = computed(() => Math.max(windowHeight.value - 220, 200))

const filteredRecords = computed(() => {
  if (!filterName.value) return records.value
  const lower = filterName.value.toLowerCase()
  return records.value.filter((item) => (item.name || '').toLowerCase().includes(lower))
})

const columns = computed<TableColumnsType<ResourceRow>>(() => [
  { title: t('acl.resourceName'), dataIndex: 'name', key: 'name', width: '30%' },
  { title: t('acl.permissionList'), dataIndex: 'permissions', key: 'permissions', width: '70%' },
])

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function loadResourceTypes() {
  resourceTypes.value = []
  searchResourceType({ app_id: appId() }).then((res) => {
    const data = res as unknown as { groups: ResourceTypeOption[] }
    resourceTypes.value = data.groups || []
    typeSelected.value = resourceTypes.value.length > 0 ? resourceTypes.value[0].id ?? null : null
  })
}

function refresh() {
  if (typeSelected.value == null) return
  searchPermResourceByRoleId(rid.value, {
    resource_type_id: typeSelected.value,
    app_id: appId(),
  }).then((res) => {
    const data = res as unknown as { resources: ResourceRow[] }
    records.value = data.resources || []
  })
}

function loadUserResource(record: { id: number }) {
  visible.value = true
  rid.value = record.id
  refresh()
}

async function copyResourceName() {
  const val = filteredRecords.value.map((item) => item.name).join('\n')
  try {
    await navigator.clipboard.writeText(val)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = val
    document.body.appendChild(textarea)
    textarea.select()
    textarea.setSelectionRange(0, val.length)
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }
  message.success(t('copySuccess'))
}

function handleResize() {
  windowHeight.value = window.innerHeight
}

watch(
  () => route.name,
  () => {
    resourceTypes.value = []
    loadResourceTypes()
  }
)

onMounted(() => {
  window.addEventListener('resize', handleResize)
  loadResourceTypes()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

defineExpose({ loadUserResource })
</script>

<template>
  <CustomDrawer
    v-model:open="visible"
    width="800px"
    placement="left"
    :title="t('acl.resourceList')"
    :has-footer="false"
  >
    <a-form-item :label="t('acl.resourceType')" :label-col="{ span: 4 }" :wrapper-col="{ span: 14 }">
      <a-select v-model:value="typeSelected" style="width: 100%" @change="refresh">
        <a-select-option v-for="type in resourceTypes" :key="type.id" :value="type.id">
          {{ type.name }}
        </a-select-option>
      </a-select>
    </a-form-item>

    <div class="resource-user-form-toolbar">
      <a-input-search
        v-model:value="filterName"
        :placeholder="t('acl.resourceName')"
        allow-clear
        style="width: 300px"
      />
      <a-tooltip :title="t('acl.copyResource')">
        <a-button type="link" @click="copyResourceName"><CopyOutlined /></a-button>
      </a-tooltip>
    </div>

    <a-table
      :columns="columns"
      :data-source="filteredRecords"
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
  </CustomDrawer>
</template>

<style scoped>
.resource-user-form-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
</style>
