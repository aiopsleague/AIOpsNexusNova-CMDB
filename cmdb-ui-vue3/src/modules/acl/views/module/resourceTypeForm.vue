<script setup lang="ts">
import { reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { FormInstance } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { addResourceType, updateResourceTypeById } from '@/modules/acl/api/resource'

interface ResourceTypeFormInput {
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
const perms = ref<string[]>([])

const form = reactive({
  id: undefined as number | undefined,
  name: '',
  description: '',
})

const rules = {
  name: [{ required: true, message: t('acl.typeNameInput') }],
}

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function open(record?: ResourceTypeFormInput) {
  visible.value = true
  if (record) {
    form.id = record.id
    form.name = record.name || ''
    form.description = record.description || ''
    perms.value = record.perms || []
  } else {
    form.id = undefined
    form.name = ''
    form.description = ''
    perms.value = []
  }
}

function handleClose() {
  formRef.value?.clearValidate()
  form.id = undefined
  form.name = ''
  form.description = ''
  perms.value = []
  visible.value = false
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    const values = (await formRef.value.validate()) as Record<string, unknown>
    const payload = { ...values, app_id: appId(), perms: perms.value }
    if (form.id) {
      await updateResourceTypeById(form.id, payload)
      message.success(t('updateSuccess'))
    } else {
      await addResourceType(payload)
      message.success(t('addSuccess'))
    }
    props.handleOk?.()
    handleClose()
  } catch {
    // validation failed
  }
}

defineExpose({ open })
</script>

<template>
  <CustomDrawer
    v-model:open="visible"
    :title="t('acl.addResourceType')"
    :closable="false"
    placement="right"
    width="500px"
  >
    <a-form ref="formRef" :model="form" :rules="rules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
      <a-form-item :label="t('acl.typeName')" name="name">
        <a-input v-model:value="form.name" :placeholder="t('acl.typeName')" />
      </a-form-item>

      <a-form-item :label="t('desc')" name="description">
        <a-textarea v-model:value="form.description" :placeholder="t('acl.descInput')" :rows="4" />
      </a-form-item>

      <a-form-item :label="t('acl.permission')">
        <a-select v-model:value="perms" mode="tags" style="width: 100%" :placeholder="t('acl.permInput')" />
      </a-form-item>

      <div class="custom-drawer-bottom-action">
        <a-button @click="handleClose">{{ t('cancel') }}</a-button>
        <a-button type="primary" @click="handleSubmit">{{ t('confirm') }}</a-button>
      </div>
    </a-form>
  </CustomDrawer>
</template>
