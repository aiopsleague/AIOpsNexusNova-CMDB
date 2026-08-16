<script setup lang="ts">
import { reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { FormInstance } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { addResourceType, updateResourceTypeById } from '@/modules/acl/api/resource'

interface ResourceTypeRecord {
  id?: number
  name?: string
  description?: string
  perms?: string[]
}

const { t } = useI18n()
const route = useRoute()

const props = defineProps<{ handleOk?: () => void }>()

const formRef = ref<FormInstance>()
const visible = ref(false)

// Permission choices are kept as a checkbox group (legacy behavior).
const plainOptions = ['1', '2']
const perms = ref<string[]>(['1'])
const indeterminate = ref(true)
const checkAll = ref(false)

const form = reactive({
  id: undefined as number | undefined,
  name: '',
  description: '',
})

const rules = {
  name: [{ required: true, message: t('acl.resourceNameInput') }],
}

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function onPermChange(checked: string[]) {
  indeterminate.value = !!checked.length && checked.length < plainOptions.length
  checkAll.value = checked.length === plainOptions.length
}

function onCheckAllChange(e: { target: { checked: boolean } }) {
  perms.value = e.target.checked ? plainOptions : []
  indeterminate.value = false
  checkAll.value = e.target.checked
}

function resetForm() {
  form.id = undefined
  form.name = ''
  form.description = ''
  perms.value = ['1']
  indeterminate.value = true
  checkAll.value = false
}

function handleCreate() {
  resetForm()
  visible.value = true
}

function onClose() {
  formRef.value?.clearValidate()
  resetForm()
  visible.value = false
}

function handleEdit(record: ResourceTypeRecord) {
  resetForm()
  visible.value = true
  form.id = record.id
  form.name = record.name || ''
  form.description = record.description || ''
  perms.value = record.perms || []
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    const values = (await formRef.value.validate()) as Record<string, unknown>
    const payload = { ...values, id: form.id, app_id: appId(), perms: perms.value }
    if (form.id) {
      await updateResourceTypeById(form.id, payload)
      message.success(t('updateSuccess'))
    } else {
      await addResourceType(payload)
      message.success(t('addSuccess'))
    }
    props.handleOk?.()
    onClose()
  } catch {
    // validation failed
  }
}

defineExpose({ handleCreate, handleEdit })
</script>

<template>
  <CustomDrawer
    v-model:open="visible"
    :closable="false"
    :title="t('acl.addResourceType')"
    placement="right"
    width="30%"
  >
    <a-form ref="formRef" :model="form" :rules="rules">
      <a-form-item :label="t('acl.typeName')" name="name">
        <a-input v-model:value="form.name" />
      </a-form-item>

      <a-form-item :label="t('desc')" name="description">
        <a-textarea v-model:value="form.description" :placeholder="t('acl.descInput')" :rows="4" />
      </a-form-item>

      <a-form-item :label="t('acl.permission')">
        <div :style="{ borderBottom: '1px solid #E9E9E9' }">
          <a-checkbox :indeterminate="indeterminate" :checked="checkAll" @change="onCheckAllChange">
            {{ t('checkAll') }}
          </a-checkbox>
        </div>
        <br />
        <a-checkbox-group v-model:value="perms" :options="plainOptions" @change="onPermChange" />
      </a-form-item>

      <div class="custom-drawer-bottom-action">
        <a-button @click="onClose">{{ t('cancel') }}</a-button>
        <a-button type="primary" @click="handleSubmit">{{ t('confirm') }}</a-button>
      </div>
    </a-form>
  </CustomDrawer>
</template>
