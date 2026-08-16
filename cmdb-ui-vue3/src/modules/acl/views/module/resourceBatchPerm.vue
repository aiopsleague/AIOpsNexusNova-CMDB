<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { FormInstance } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { searchRole } from '@/modules/acl/api/role'
import {
  getResourceTypePerms,
  setBatchRoleResourceByResourceName,
  setBatchRoleResourceRevokeByResourceName,
} from '@/modules/acl/api/permission'

interface RoleOption {
  id?: number
  name?: string
}

interface PermOption {
  name: string
}

const { t } = useI18n()
const route = useRoute()

const formRef = ref<FormInstance>()
const visible = ref(false)
const resourceTypeId = ref<number | undefined>(undefined)
const roleType = ref(true)
const allRoles = ref<RoleOption[]>([])
const allPerms = ref<PermOption[]>([])

const form = reactive({
  roleIdList: [] as number[],
  permName: [] as string[],
  resourceNames: '',
})

const rules = {
  roleIdList: [{ required: true, type: 'array' as const, message: t('acl.role_placeholder2') }],
  permName: [{ required: true, type: 'array' as const, message: t('acl.permission_placeholder') }],
  resourceNames: [{ required: true, message: t('acl.resourceBatchTips') }],
}

const roleOptions = computed(() => allRoles.value.map((r) => ({ value: r.id, label: r.name || '' })))
const permOptions = computed(() => allPerms.value.map((p) => ({ value: p.name, label: p.name })))

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function open(currentTypeId: number) {
  visible.value = true
  resourceTypeId.value = currentTypeId
  loadRoles(1)
  loadPerm(currentTypeId)
}

function resetForm() {
  formRef.value?.clearValidate()
  form.roleIdList = []
  form.permName = []
  form.resourceNames = ''
}

function handleClose() {
  resetForm()
  roleType.value = true
  visible.value = false
}

function handleRoleTypeChange(target: boolean) {
  loadRoles(Number(target))
}

function loadRoles(isUserRole: number) {
  searchRole({ page_size: 9999, app_id: appId(), user_role: isUserRole }).then((res) => {
    const data = res as unknown as { roles: RoleOption[] }
    allRoles.value = data.roles || []
  })
}

function loadPerm(rTypeId: number) {
  getResourceTypePerms(rTypeId).then((res) => {
    const data = res as unknown as PermOption[]
    allPerms.value = data || []
  })
}

async function doBatch(grant: boolean) {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    const resourceNames = form.resourceNames.split('\n')
    for (const roleId of form.roleIdList) {
      const payload = {
        resource_names: resourceNames,
        perms: form.permName,
        resource_type_id: resourceTypeId.value,
      }
      const req = grant
        ? setBatchRoleResourceByResourceName(roleId, payload)
        : setBatchRoleResourceRevokeByResourceName(roleId, payload)
      await req
      message.success(t('operateSuccess'))
    }
    resetForm()
  } catch {
    // validation failed
  }
}

function handleSubmit() {
  doBatch(true)
}

function handleRevoke() {
  doBatch(false)
}

defineExpose({ open })
</script>

<template>
  <CustomDrawer
    v-model:open="visible"
    :title="t('acl.convenient')"
    width="500px"
    :mask-closable="false"
    :closable="true"
    @close="handleClose"
  >
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

      <a-form-item :label="t('acl.resourceName')" name="resourceNames">
        <a-textarea
          v-model:value="form.resourceNames"
          :auto-size="{ minRows: 4 }"
          :placeholder="t('acl.resourceBatchTips')"
        />
      </a-form-item>

      <div class="custom-drawer-bottom-action">
        <a-button type="danger" ghost @click="handleRevoke">{{ t('acl.revoke') }}</a-button>
        <a-button type="primary" @click="handleSubmit">{{ t('grant') }}</a-button>
      </div>
    </a-form>
  </CustomDrawer>
</template>
