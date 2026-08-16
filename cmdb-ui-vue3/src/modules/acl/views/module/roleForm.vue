<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { FormInstance } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { addRole, updateRoleById, delParentRole, addBatchParentRole } from '@/modules/acl/api/role'

interface RoleOption {
  id: number
  name?: string
}

interface ParentRole {
  id: number
  name: string
}

interface RoleRecord {
  id: number
  name: string
  is_app_admin?: boolean
}

const { t } = useI18n()
const route = useRoute()

const props = defineProps<{
  handleOk?: () => void
  allRoles: RoleOption[]
  id2parents: Record<number, ParentRole[]>
}>()

const formRef = ref<FormInstance>()
const visible = ref(false)
const drawerTitle = ref('')

const form = reactive({
  id: undefined as number | undefined,
  name: '',
  password: '',
  is_app_admin: false,
})

const rules = {
  name: [{ required: true, message: t('acl.role_placeholder1') }],
}

const selectedParents = ref<number[]>([])
const oldParents = ref<number[]>([])

const roleOptions = computed(() =>
  (props.allRoles || []).map((role) => ({ value: role.id, label: role.name || '' }))
)

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function resetForm() {
  form.id = undefined
  form.name = ''
  form.password = ''
  form.is_app_admin = false
  selectedParents.value = []
  oldParents.value = []
}

function handleCreate() {
  resetForm()
  formRef.value?.clearValidate()
  drawerTitle.value = t('acl.addRole')
  visible.value = true
}

function handleEdit(record: RoleRecord) {
  resetForm()
  formRef.value?.clearValidate()
  drawerTitle.value = `${t('edit')}: ${record.name}`
  visible.value = true
  form.id = record.id
  form.name = record.name || ''
  form.is_app_admin = !!record.is_app_admin
  const parents = props.id2parents[record.id]
  if (parents) {
    parents.forEach((item) => {
      selectedParents.value.push(item.id)
      oldParents.value.push(item.id)
    })
  }
}

function handleClose() {
  resetForm()
  formRef.value?.clearValidate()
  visible.value = false
}

// Sync parent role relations: remove deselected parents and add newly selected ones.
async function updateParents(id: number) {
  const appIdVal = appId()
  await Promise.all([
    ...oldParents.value
      .filter((item) => !selectedParents.value.includes(item))
      .map((item) => delParentRole(id, item, { app_id: appIdVal })),
    ...selectedParents.value
      .filter((item) => !oldParents.value.includes(item))
      .map((item) => addBatchParentRole(item, { child_ids: [id], app_id: appIdVal })),
  ])
}

async function updateRole(id: number, data: Record<string, unknown>) {
  await updateParents(id)
  await updateRoleById(id, { ...data, app_id: appId() })
  message.success(t('updateSuccess'))
  props.handleOk?.()
  handleClose()
}

async function createRole(data: Record<string, unknown>) {
  const res = (await addRole({ ...data, app_id: appId() })) as unknown as { id: number }
  message.success(t('addSuccess'))
  await updateParents(res.id)
  props.handleOk?.()
  handleClose()
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    const values = (await formRef.value.validate()) as Record<string, unknown>
    if (form.id) {
      await updateRole(form.id, values)
    } else {
      await createRole(values)
    }
  } catch {
    // validation failed
  }
}

defineExpose({ handleCreate, handleEdit })
</script>

<template>
  <CustomDrawer v-model:open="visible" :title="drawerTitle" :closable="false" placement="right" width="500px">
    <a-form ref="formRef" :model="form" :rules="rules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
      <a-form-item :label="t('acl.role')" name="name">
        <a-input v-model:value="form.name" :placeholder="t('acl.role_placeholder1')" />
      </a-form-item>

      <a-form-item v-if="appId() !== 'acl'" :label="t('acl.password')" name="password">
        <a-input v-model:value="form.password" :placeholder="t('acl.password')" />
      </a-form-item>

      <a-form-item :label="t('acl.inheritedFrom')">
        <a-select
          v-model:value="selectedParents"
          mode="multiple"
          :options="roleOptions"
          :placeholder="t('acl.selectedParents')"
          style="width: 100%"
          allow-clear
          show-search
          option-filter-prop="label"
        />
      </a-form-item>

      <a-form-item :label="t('acl.isAppAdmin')">
        <a-switch v-model:checked="form.is_app_admin" />
      </a-form-item>

      <div class="custom-drawer-bottom-action">
        <a-button @click="handleClose">{{ t('cancel') }}</a-button>
        <a-button type="primary" @click="handleSubmit">{{ t('confirm') }}</a-button>
      </div>
    </a-form>
  </CustomDrawer>
</template>
