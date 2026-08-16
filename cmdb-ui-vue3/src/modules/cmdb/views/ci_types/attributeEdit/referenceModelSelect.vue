<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getCITypes } from '@/modules/cmdb/api/CIType'

const props = withDefaults(
  defineProps<{
    modelValue?: any
    isLazyRequire?: boolean
    formItemLayout?: Record<string, any>
  }>(),
  {
    modelValue: '',
    isLazyRequire: true,
    formItemLayout: () => ({ labelCol: { span: 8 }, wrapperCol: { span: 15 } }),
  }
)

const emit = defineEmits<{ (e: 'update:modelValue', value: any): void }>()

const { t } = useI18n()

const isInit = ref(false)
const options = ref<{ value: string | number; label: string }[]>([])

const selectedValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

onMounted(() => {
  if (!props.isLazyRequire) {
    getSelectOptions()
  }
})

function handleDropdownVisibleChange(open: boolean) {
  if (!isInit.value && open) {
    getSelectOptions()
  }
}

async function getSelectOptions() {
  isInit.value = true
  const res = await getCITypes()

  options.value = res.ci_types.map((ciType: any) => {
    return {
      value: ciType.id,
      label: ciType?.alias || ciType?.name || '',
    }
  })
}
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <a-form-item
    name="reference_type_id"
    :label="t('cmdb.ciType.referenceModel')"
    :extra="t('cmdb.ciType.referenceModelTip1')"
    :label-col="formItemLayout.labelCol"
    :wrapper-col="formItemLayout.wrapperCol"
    :rules="[{ required: true, message: t('cmdb.ciType.referenceModelTip') }]"
  >
    <a-select
      allow-clear
      v-model:value="selectedValue"
      show-search
      option-filter-prop="title"
      @dropdown-visible-change="handleDropdownVisibleChange"
    >
      <a-select-option
        v-for="item in options"
        :key="item.value"
        :value="item.value"
        :title="item.label"
      >
        {{ item.label }}
      </a-select-option>
    </a-select>
  </a-form-item>
</template>
