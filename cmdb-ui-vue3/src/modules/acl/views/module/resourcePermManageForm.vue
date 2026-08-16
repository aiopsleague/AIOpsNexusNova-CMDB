<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { FormInstance } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { searchRole } from '@/modules/acl/api/role'
import {
  getResourceTypePerms,
  setRoleResourcePerm,
  setRoleResourceGroupPerm,
  setBatchRoleResourcePerm,
  setBatchRoleResourceGroupPerm,
  setBatchRoleResourceRevoke,
  setBatchRoleResourceGroupRevoke,
} from '@/modules/acl/api/permission'

interface RoleOption {
  id?: number
  name?: string
}

interface PermOption {
  name: string
}

interface ResourceRecord {
  id: number
  name?: string
  resource_type_id: number
}

const { t } = useI18n()
const route = useRoute()

defineProps<{ groupTypeMessage: Record<string, unknown> }>()

const emit = defineEmits<{ (e: 'close'): void }>()

const formRef = ref<FormInstance>()
const isGroup = ref(false)
const allRoles = ref<RoleOption[]>([])
const allPerms = ref<PermOption[]>([])
const visible = ref(false)
const instance = ref<ResourceRecord | ResourceRecord[]>({ id: 0, resource_type_id: 0 })
const type = ref<'grant' | 'revoke'>('grant')
const title = ref('')
const loading = ref(false)
const roleType = ref(false)

const form = reactive({
  roleIdList: [] as number[],
  permName: [] as string[],
})

const rules = {
  roleIdList: [{ required: true, type: 'array' as const, message: t('acl.role_placeholder2') }],
  permName: [{ required: true, type: 'array' as const, message: t('acl.permission_placeholder') }],
}

const roleOptions = computed(() => allRoles.value.map((r) => ({ value: r.id, label: r.name || '' })))
const permOptions = computed(() => allPerms.value.map((p) => ({ value: p.name, label: p.name })))

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function handleRoleTypeChange(target: boolean) {
  if (!target) {
    loadRoles(1)
  } else {
    loadRoles(0)
  }
}

function loadRoles(isUserRole: number) {
  searchRole({ page_size: 9999, app_id: appId(), user_role: isUserRole }).then((res) => {
    const data = res as unknown as { roles: RoleOption[] }
    allRoles.value = data.roles || []
  })
}

function loadPerm(resourceTypeId: number) {
  getResourceTypePerms(resourceTypeId).then((res) => {
    const data = res as unknown as PermOption[]
    allPerms.value = data || []
  })
}

function closeForm() {
  visible.value = false
  formRef.value?.clearValidate()
  form.roleIdList = []
  form.permName = []
  emit('close')
}

function editPerm(record: ResourceRecord | ResourceRecord[], group: boolean, grantOrRevoke: 'grant' | 'revoke' = 'grant') {
  isGroup.value = group
  visible.value = true
  instance.value = record
  type.value = grantOrRevoke
  if (Array.isArray(record)) {
    loadPerm(record[0].resource_type_id)
    title.value = grantOrRevoke === 'grant' ? t('acl.batchGrant') : t('acl.batchRevoke')
  } else {
    title.value = `${t('acl.editPerm')}${record.name || ''}`
    loadPerm(record.resource_type_id)
  }
}

function requestPerm(roleId: number, params: Record<string, unknown>, ids: number[], isBatch: boolean) {
  if (!isGroup.value) {
    if (isBatch) {
      return type.value === 'grant'
        ? setBatchRoleResourcePerm(roleId, { ...params, resource_ids: ids })
        : setBatchRoleResourceRevoke(roleId, { ...params, resource_ids: ids })
    }
    return setRoleResourcePerm(roleId, (instance.value as ResourceRecord).id, params)
  }
  if (isBatch) {
    return type.value === 'grant'
      ? setBatchRoleResourceGroupPerm(roleId, { ...params, group_ids: ids })
      : setBatchRoleResourceGroupRevoke(roleId, { ...params, group_ids: ids })
  }
  return setRoleResourceGroupPerm(roleId, (instance.value as ResourceRecord).id, params)
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    loading.value = true
    const isBatch = Array.isArray(instance.value)
    const ids = isBatch ? (instance.value as ResourceRecord[]).map((a) => a.id) : []
    const params = { perms: form.permName, app_id: appId() }
    await Promise.all(
      form.roleIdList.map((roleId) =>
        requestPerm(roleId, params, ids, isBatch).then(() => {
          message.success(t('operateSuccess'))
        })
      )
    )
  } catch {
    // validation failed
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRoles(1)
})

defineExpose({ editPerm })
</script>

<template>
  <CustomDrawer v-model:open="visible" :title="title" width="500px" :closable="false" @close="closeForm">
    <a-form ref="formRef" :model="form" :rules="rules">
      <a-form-item name="roleIdList">
        <template #label>
          <div style="display: inline-block">
            <span>{{ t('acl.roleList') }}</span>
            <a-divider type="vertical" />
            <a-switch
              v-model:checked="roleType"
              style="display: inline-block"
              :checked-children="t('user')"
              :un-checked-children="t('acl.virtual')"
              @change="handleRoleTypeChange"
            />
          </div>
        </template>
        <a-select
          v-model:value="form.roleIdList"
          mode="multiple"
          style="width: 100%"
          :options="roleOptions"
          :placeholder="t('acl.role_placeholder3')"
        />
      </a-form-item>

      <a-form-item :label="t('acl.permissionList')" name="permName">
        <a-select
          v-model:value="form.permName"
          mode="multiple"
          style="width: 100%"
          :options="permOptions"
          :placeholder="t('acl.permission_placeholder')"
        />
      </a-form-item>

      <div class="custom-drawer-bottom-action">
        <a-button @click="closeForm">{{ t('cancel') }}</a-button>
        <a-button type="primary" :loading="loading" @click="handleSubmit">{{ t('confirm') }}</a-button>
      </div>
    </a-form>
  </CustomDrawer>
</template>
