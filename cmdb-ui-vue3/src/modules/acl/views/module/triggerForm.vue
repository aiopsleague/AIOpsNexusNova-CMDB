<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { EyeOutlined } from '@ant-design/icons-vue'
import type { FormInstance } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { addTrigger, updateTrigger } from '@/modules/acl/api/trigger'
import TriggerPattern from './triggerPattern.vue'

interface RoleOption {
  id: number
  name: string
  uid?: number
  [key: string]: unknown
}

interface ResourceTypeOption {
  id: number
  name: string
  [key: string]: unknown
}

interface PermOption {
  id: number
  name: string
}

interface TriggerRecord {
  id: number
  name: string
  wildcard: string
  resource_type_id: number
  uid: number[]
  roles: number[]
  permissions: string[]
  enabled: boolean
  [key: string]: unknown
}

const { t } = useI18n()
const route = useRoute()

const props = defineProps<{
  roles: RoleOption[]
  resourceTypeList: ResourceTypeOption[]
  id2perms: Record<number, PermOption[]>
}>()

const emit = defineEmits<{ (e: 'refresh'): void }>()

const formRef = ref<FormInstance>()
const triggerPatternRef = ref<{ open: (params: Record<string, unknown>) => void }>()

const visible = ref(false)
const triggerId = ref<number | null>(null)
const selectResourceTypePerms = ref<PermOption[]>([])

const form = reactive({
  name: '',
  wildcard: '',
  uid: [] as number[],
  resource_type_id: undefined as number | undefined,
  roles: [] as number[],
  permissions: [] as string[],
  enabled: true,
})

const rules = {
  name: [{ required: true, message: t('acl.triggerNameInput') }],
  resource_type_id: [{ required: true, message: t('acl.pleaseSelectType') }],
  roles: [{ required: true, message: t('acl.role_placeholder2') }],
  permissions: [{ required: true, message: t('acl.permission_placeholder') }],
}

const uidOptions = computed(() =>
  props.roles.filter((role) => role.uid != null).map((role) => ({ value: role.uid, label: role.name }))
)

const roleOptions = computed(() => props.roles.map((role) => ({ value: role.id, label: role.name })))

const resourceTypeOptions = computed(() =>
  props.resourceTypeList.map((rt) => ({ value: rt.id, label: rt.name }))
)

const permOptions = computed(() => selectResourceTypePerms.value.map((perm) => ({ value: perm.name, label: perm.name })))

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function resetForm() {
  form.name = ''
  form.wildcard = ''
  form.uid = []
  form.resource_type_id = undefined
  form.roles = []
  form.permissions = []
  form.enabled = true
  selectResourceTypePerms.value = []
}

function handleEdit(record: TriggerRecord | null) {
  resetForm()
  formRef.value?.clearValidate()
  visible.value = true
  if (record) {
    triggerId.value = record.id
    form.name = record.name
    form.wildcard = record.wildcard
    form.uid = record.uid || []
    form.resource_type_id = record.resource_type_id
    form.permissions = record.permissions || []
    form.enabled = !!record.enabled
    form.roles = (record.roles || []).map((x) => Number(x))
    selectResourceTypePerms.value = props.id2perms[record.resource_type_id] || []
  } else {
    triggerId.value = null
  }
}

function handleClose() {
  visible.value = false
}

function handleRTChange(value: number) {
  selectResourceTypePerms.value = props.id2perms[value] || []
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    const payload = {
      name: form.name,
      wildcard: form.wildcard,
      uid: form.uid,
      resource_type_id: form.resource_type_id,
      roles: form.roles,
      permissions: form.permissions,
      enabled: form.enabled,
      app_id: appId(),
    }
    if (triggerId.value) {
      await updateTrigger(triggerId.value, payload)
      message.success(t('updateSuccess'))
    } else {
      await addTrigger(payload)
      message.success(t('addSuccess'))
    }
    visible.value = false
    emit('refresh')
  } catch {
    // validation failed
  }
}

function handlePattern() {
  if (!formRef.value) return
  formRef.value
    .validate(['wildcard', 'uid', 'resource_type_id'])
    .then(() => {
      triggerPatternRef.value?.open({
        resource_type_id: form.resource_type_id,
        app_id: appId(),
        owner: form.uid,
        pattern: form.wildcard,
      })
    })
    .catch(() => {
      // validation failed
    })
}

defineExpose({ handleEdit })
</script>

<template>
  <CustomDrawer
    v-model:open="visible"
    :title="`${triggerId ? t('update') : t('create')}${t('acl.trigger')}`"
    :closable="false"
    placement="right"
    width="500px"
    :mask-closable="false"
  >
    <a-form ref="formRef" :model="form" :rules="rules" :label-col="{ span: 6 }" :wrapper-col="{ span: 15 }">
      <a-form-item :label="t('name')" name="name">
        <a-input v-model:value="form.name" size="large" />
      </a-form-item>

      <a-form-item :label="t('acl.resourceName')" name="wildcard">
        <a-input v-model:value="form.wildcard" size="large" :placeholder="t('acl.triggerTips1')" />
      </a-form-item>

      <a-form-item :label="t('acl.creator')" name="uid">
        <a-select
          v-model:value="form.uid"
          mode="multiple"
          :options="uidOptions"
          :placeholder="t('placeholder2')"
          :style="{ width: '100%' }"
          show-search
          option-filter-prop="label"
        />
      </a-form-item>

      <a-form-item :label="t('acl.resourceType')" name="resource_type_id">
        <a-select
          v-model:value="form.resource_type_id"
          :options="resourceTypeOptions"
          :placeholder="t('placeholder2')"
          :style="{ width: '100%' }"
          @change="handleRTChange"
        />
        <a-tooltip :title="t('acl.viewMatchResult')">
          <a class="trigger-form-pattern" @click="handlePattern"><EyeOutlined /></a>
        </a-tooltip>
      </a-form-item>

      <a-form-item :label="t('acl.role2')" name="roles">
        <a-select
          v-model:value="form.roles"
          mode="multiple"
          :options="roleOptions"
          :placeholder="t('placeholder2')"
          :style="{ width: '100%' }"
          show-search
          option-filter-prop="label"
        />
      </a-form-item>

      <a-form-item :label="t('acl.permission')" name="permissions">
        <a-select
          v-model:value="form.permissions"
          mode="multiple"
          :options="permOptions"
          :placeholder="t('placeholder2')"
          :style="{ width: '100%' }"
        />
      </a-form-item>

      <a-form-item :label="`${t('acl.enable')} / ${t('acl.disable')}`">
        <a-switch v-model:checked="form.enabled" />
      </a-form-item>
    </a-form>

    <div class="custom-drawer-bottom-action">
      <a-button @click="handleClose">{{ t('cancel') }}</a-button>
      <a-button type="primary" @click="handleSubmit">{{ t('submit') }}</a-button>
    </div>

    <TriggerPattern ref="triggerPatternRef" :roles="roles" />
  </CustomDrawer>
</template>

<style scoped>
.trigger-form-pattern {
  position: absolute;
  right: -20px;
}
</style>
