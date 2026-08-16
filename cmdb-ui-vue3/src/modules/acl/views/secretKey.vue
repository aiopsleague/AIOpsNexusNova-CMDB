<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { getSecret, updateSecret } from '@/modules/acl/api/secretKey'

const { t } = useI18n()

const form = ref<{ key: string; secret: string }>({ key: '', secret: '' })
const visible = ref(false)

const displayForm = computed(() => ({
  key: visible.value ? form.value.key : form.value.key.replace(/./g, '*'),
  secret: visible.value ? form.value.secret : form.value.secret.replace(/./g, '*'),
}))

function loadSecret() {
  getSecret().then((res) => {
    const data = res as unknown as { key: string; secret: string }
    form.value = { key: data.key, secret: data.secret }
  })
}

function handleReset() {
  Modal.confirm({
    title: t('reset'),
    content: t('acl.confirmResetSecret'),
    onOk() {
      return updateSecret({}).then((res) => {
        message.success(t('operateSuccess'))
        const data = res as unknown as { key: string; secret: string }
        form.value = { key: data.key, secret: data.secret }
      })
    },
  })
}

function toggleVisible() {
  visible.value = !visible.value
}

onMounted(loadSecret)
</script>

<template>
  <div class="acl-secret-key">
    <a-form :model="displayForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 12 }">
      <a-form-item label="Key">
        <a-input :value="displayForm.key" disabled />
      </a-form-item>
      <a-form-item label="Secret">
        <a-input :value="displayForm.secret" disabled />
      </a-form-item>
      <a-form-item label=" " :colon="false">
        <a-space>
          <a-button type="primary" @click="toggleVisible">{{ visible ? t('hide') : t('view') }}</a-button>
          <a-button type="danger" ghost @click="handleReset">{{ t('reset') }}</a-button>
        </a-space>
      </a-form-item>
    </a-form>
  </div>
</template>

<style scoped>
.acl-secret-key {
  background-color: #fff;
  padding: 24px;
  border-radius: 4px;
  height: calc(100% + 24px);
}
.acl-secret-key :deep(.ant-input[disabled]) {
  color: rgba(0, 0, 0, 0.5);
}
</style>
