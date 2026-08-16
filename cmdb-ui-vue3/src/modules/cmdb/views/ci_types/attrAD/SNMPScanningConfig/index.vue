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
    :label-col="labelCol"
    :wrapper-col="{ span: 6 }"
    class="attr-ad-form"
  >
    <a-form-item
      :label="t('cmdb.ciType.initialNode')"
      :extra="t('cmdb.ciType.snmpFormTip4')"
    >
      <a-input
        v-model:value="formData.initial_node"
        :placeholder="t('cmdb.ciType.defaultGateway')"
      />
    </a-form-item>

    <a-form-item
      :label="t('cmdb.ciType.recursiveOrNot')"
      :extra="t('cmdb.ciType.snmpFormTip5')"
    >
      <a-switch v-model:checked="formData.recursive_scan" />
    </a-form-item>

    <a-form-item
      :label="t('cmdb.ciType.maximumDepth')"
      :extra="t('cmdb.ciType.snmpFormTip6')"
    >
      <a-input-number
        v-model:value="formData.max_depth"
        :min="0"
        :precision="0"
      />
    </a-form-item>
  </a-form>
</template>
