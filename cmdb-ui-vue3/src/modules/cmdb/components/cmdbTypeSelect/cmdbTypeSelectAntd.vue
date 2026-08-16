<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getCITypeGroupsConfig } from '@/modules/cmdb/api/ciTypeGroup'
import { cloneDeep } from '@/modules/cmdb/utils/helper'

const props = withDefaults(
  defineProps<{
    ciTypeGroup?: any[]
    placeholder?: string
  }>(),
  {
    ciTypeGroup: () => [],
    placeholder: '',
  }
)

const modelValue = defineModel<string | number | Array<string | number> | undefined>()
const emit = defineEmits<{ (e: 'change', value: any): void }>()

const { t } = useI18n()

const selectOptions = ref<any[]>([])

async function handleSelectOptions() {
  let rawCITypeGroup: any[] = []
  if (props.ciTypeGroup && props.ciTypeGroup.length) {
    rawCITypeGroup = props.ciTypeGroup
  } else {
    rawCITypeGroup = await getCITypeGroupsConfig({ need_other: true })
  }
  selectOptions.value = cloneDeep(rawCITypeGroup).filter((group) => group?.ci_types?.length)
}

function handleChange(value: any) {
  modelValue.value = value
  emit('change', value)
}

watch(
  () => props.ciTypeGroup,
  () => {
    handleSelectOptions()
  },
  { deep: true }
)

onMounted(() => {
  handleSelectOptions()
})
</script>

<template>
  <a-select
    :value="modelValue"
    v-bind="$attrs"
    style="width: 100%"
    show-search
    option-filter-prop="label"
    :placeholder="placeholder || t('placeholder2')"
    @change="handleChange"
  >
    <a-select-opt-group v-for="group in selectOptions" :key="group.id" :label="group.name || t('cmdb.common.other')">
      <a-select-option
        v-for="type in group.ci_types"
        :key="type.id"
        :value="type.id"
        :label="`${type.alias || type.name || t('cmdb.common.other')} ${type.name || ''}`"
      >
        {{ type.alias || type.name || t('cmdb.common.other') }}
        <span v-if="type.name" class="select-option-name">({{ type.name }})</span>
      </a-select-option>
    </a-select-opt-group>
  </a-select>
</template>

<style lang="less" scoped>
.select-option-name {
  font-size: 12px;
  color: #a5a9bc;
}
</style>
