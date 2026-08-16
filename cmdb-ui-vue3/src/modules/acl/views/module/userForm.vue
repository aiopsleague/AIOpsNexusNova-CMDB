<script setup lang="ts">
import { reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { addUser, updateUserById } from '@/modules/acl/api/user'

interface UserFormRecord {
  uid?: number
  username?: string
  nickname?: string
  password?: string
  department?: string
  catalog?: string
  email?: string
  mobile?: string
  block?: boolean
}

const { t } = useI18n()

const props = defineProps<{ handleOk?: () => void }>()

const formRef = ref<FormInstance>()
const visible = ref(false)

const form = reactive({
  id: undefined as number | undefined,
  username: '',
  nickname: '',
  password: '',
  department: '',
  catalog: '',
  email: '',
  mobile: '',
  block: false,
})

const rules = {
  username: [{ required: true, message: t('acl.username_placeholder') }],
  password: [{ required: true, message: t('acl.password_placeholder') }],
  email: [
    { type: 'email' as const, message: t('acl.email_placeholder') },
    { required: true, message: t('acl.email_placeholder') },
  ],
  mobile: [{ pattern: /^1\d{10}$/, message: t('acl.mobileTips') }],
}

function resetForm() {
  form.id = undefined
  form.username = ''
  form.nickname = ''
  form.password = ''
  form.department = ''
  form.catalog = ''
  form.email = ''
  form.mobile = ''
  form.block = false
}

function handleCreate() {
  resetForm()
  visible.value = true
}

function handleEdit(record: UserFormRecord) {
  resetForm()
  form.id = record.uid
  form.username = record.username || ''
  form.nickname = record.nickname || ''
  form.password = record.password || ''
  form.department = record.department || ''
  form.catalog = record.catalog || ''
  form.email = record.email || ''
  form.mobile = record.mobile || ''
  form.block = !!record.block
  visible.value = true
}

function handleClose() {
  formRef.value?.clearValidate()
  visible.value = false
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    const values = (await formRef.value.validate()) as Record<string, unknown>
    if (form.id) {
      await updateUserById(form.id, { ...values, id: form.id })
      message.success(t('updateSuccess'))
    } else {
      await addUser(values)
      message.success(t('addSuccess'))
    }
    props.handleOk?.()
    handleClose()
  } catch {
    // validation failed
  }
}

defineExpose({ handleCreate, handleEdit })
</script>

<template>
  <CustomDrawer v-model:open="visible" :title="t('acl.addUser')" :closable="false" placement="right" width="500px">
    <a-form ref="formRef" :model="form" :rules="rules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
      <a-form-item :label="t('acl.username')" name="username">
        <a-input v-model:value="form.username" :placeholder="t('acl.username_placeholder')" />
      </a-form-item>

      <a-form-item :label="t('acl.nickname')" name="nickname">
        <a-input v-model:value="form.nickname" :placeholder="t('acl.nickname_placeholder')" />
      </a-form-item>

      <a-form-item :label="t('acl.password')" name="password">
        <a-input v-model:value="form.password" type="password" :placeholder="t('acl.password_placeholder')" />
      </a-form-item>

      <a-form-item :label="t('acl.department')" name="department">
        <a-input v-model:value="form.department" />
      </a-form-item>

      <a-form-item :label="t('acl.group')" name="catalog">
        <a-input v-model:value="form.catalog" />
      </a-form-item>

      <a-form-item :label="t('acl.email')" name="email">
        <a-input v-model:value="form.email" :placeholder="t('acl.email_placeholder')" />
      </a-form-item>

      <a-form-item :label="t('acl.mobile')" name="mobile">
        <a-input v-model:value="form.mobile" />
      </a-form-item>

      <a-form-item :label="t('acl.isBlock')" name="block">
        <a-switch v-model:checked="form.block" />
      </a-form-item>

      <div class="custom-drawer-bottom-action">
        <a-button @click="handleClose">{{ t('cancel') }}</a-button>
        <a-button type="primary" @click="handleSubmit">{{ t('confirm') }}</a-button>
      </div>
    </a-form>
  </CustomDrawer>
</template>
