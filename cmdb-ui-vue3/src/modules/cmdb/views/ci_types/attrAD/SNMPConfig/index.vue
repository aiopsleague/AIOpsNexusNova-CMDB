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

// Mirror the parent-provided value so the v-model in the template mutates the
// shared object directly, matching the legacy `model` component behaviour.
const formData = computed({
  get: () => props.value,
  set: (newValue) => emit('change', newValue),
})

const labelCol = computed(() => provide_labelCol?.())
</script>

<template>
  <a-form
    :model="formData"
    :label-col="labelCol"
    :wrapper-col="{ span: 6 }"
    class="attr-ad-form"
  >
    <a-form-item :label="t('cmdb.ciType.defaultVersion')">
      <a-select
        v-model:value="formData.version"
        allow-clear
      >
        <a-select-option value="1">
          v1
        </a-select-option>
        <a-select-option value="2c">
          v2c
        </a-select-option>
      </a-select>
    </a-form-item>

    <a-form-item :label="t('cmdb.ciType.defaultCommunity')">
      <a-input v-model:value="formData.community" />
    </a-form-item>

    <a-form-item
      :label="t('cmdb.ciType.timeout')"
      :extra="t('cmdb.ciType.snmpFormTip2')"
    >
      <a-input-number
        v-model:value="formData.timeout"
        :min="0"
        :precision="0"
      />
    </a-form-item>

    <a-form-item
      :label="t('cmdb.ciType.retryCount')"
      :extra="t('cmdb.ciType.snmpFormTip3')"
    >
      <a-input-number
        v-model:value="formData.retries"
        :min="0"
        :precision="0"
      />
    </a-form-item>
  </a-form>
</template>
