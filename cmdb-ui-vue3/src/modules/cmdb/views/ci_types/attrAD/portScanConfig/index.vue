<script setup lang="ts">
import { computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'

const props = withDefaults(
  defineProps<{
    value?: Record<string, any>
  }>(),
  {
    value: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'change', value: Record<string, any>): void
}>()

const { t } = useI18n()

const provide_labelCol = inject<() => any>('provide_labelCol')

const formData = computed({
  get: () => props.value,
  set: (newValue) => emit('change', newValue),
})

const labelCol = computed(() => provide_labelCol?.())
</script>

<template>
  <a-form
    :model="formData"
    label-align="right"
    :label-col="labelCol"
    :wrapper-col="{ span: 6 }"
    class="attr-ad-form"
  >
    <a-form-item :extra="`${t('cmdb.ciType.example')}: 192.168.0.0/16`" :label="t('cmdb.ciType.portScanLabel1')">
      <a-input v-model:value="formData.cidr" />
    </a-form-item>
    <a-form-item :extra="`${t('cmdb.ciType.example')}: 8000-8800`" :label="t('cmdb.ciType.portScanLabel2')">
      <a-input v-model:value="formData.ports" />
    </a-form-item>
    <a-form-item :extra="`${t('cmdb.ciType.example')}: 0x1234`" :label="t('cmdb.ciType.portScanLabel3')">
      <a-input v-model:value="formData.enable_cidr" />
    </a-form-item>
  </a-form>
</template>
