<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { addApp, updateApp, getApp } from '@/modules/acl/api/app'

interface AppFormInput {
  id?: number
  name?: string
  description?: string
}

const { t } = useI18n()

const emit = defineEmits<{ (e: 'refresh'): void }>()

const formRef = ref<FormInstance>()
const visible = ref(false)
const mode = ref<'create' | 'update'>('create')

const form = reactive({
  id: undefined as number | undefined,
  name: '',
  description: '',
  app_id: '',
  secret_key: '',
})

const rules = {
  name: [{ required: true, message: t('acl.appNameInput') }],
  description: [{ required: true, message: t('acl.descInput') }],
}

const title = computed(() => (mode.value === 'update' ? t('acl.updateApp') : t('acl.addApp')))

function open(ele?: AppFormInput) {
  visible.value = true
  if (ele) {
    mode.value = 'update'
    form.id = ele.id
    form.name = ele.name || ''
    form.description = ele.description || ''
    getApp(ele.id as number).then((res) => {
      const data = res as unknown as { app_id: string; secret_key: string }
      form.app_id = data.app_id
      form.secret_key = data.secret_key
    })
  } else {
    mode.value = 'create'
    form.id = undefined
    form.name = ''
    form.description = ''
    form.app_id = ''
    form.secret_key = ''
  }
}

function handleClose() {
  formRef.value?.clearValidate()
  visible.value = false
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    const values = (await formRef.value.validate()) as Record<string, unknown>
    const payload = { ...values, app_id: form.app_id, secret_key: form.secret_key }
    if (form.id) {
      await updateApp(form.id, payload)
      message.success(t('updateSuccess'))
    } else {
      await addApp(payload)
      message.success(t('addSuccess'))
    }
    handleClose()
    emit('refresh')
  } catch {
    // validation failed
  }
}

defineExpose({ open })
</script>

<template>
  <CustomDrawer v-model:open="visible" :title="title" :closable="false" width="500">
    <a-form ref="formRef" :model="form" :rules="rules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
      <a-form-item :label="t('acl.app')" name="name">
        <a-input v-model:value="form.name" />
      </a-form-item>
      <a-form-item :label="t('desc')" name="description">
        <a-input v-model:value="form.description" />
      </a-form-item>
      <a-form-item label="AppId">
        <a-input v-model:value="form.app_id" :disabled="mode === 'update'" />
      </a-form-item>
      <a-form-item label="SecretKey">
        <a-input v-model:value="form.secret_key" :disabled="mode === 'update'" />
      </a-form-item>
      <div class="custom-drawer-bottom-action">
        <a-button @click="handleClose">{{ t('cancel') }}</a-button>
        <a-button type="primary" @click="handleSubmit">{{ t('submit') }}</a-button>
      </div>
    </a-form>
  </CustomDrawer>
</template>
