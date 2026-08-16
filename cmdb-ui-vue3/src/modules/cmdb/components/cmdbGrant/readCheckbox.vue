<script setup lang="ts">
import { computed, inject } from 'vue'

const props = withDefaults(
  defineProps<{
    value?: boolean
    valueKey?: string
    rid?: number
  }>(),
  {
    value: false,
    valueKey: 'read_attr',
    rid: 0,
  }
)

const emit = defineEmits<{
  (e: 'openReadGrantModal'): void
}>()

// Injected by GrantComp: () => Record<rid, { attr_filter / ci_filter }>.
const provideFilerPerimissions = inject<() => Record<string, any>>('filerPerimissions', () => ({}))

const filerPerimissions = computed(() => provideFilerPerimissions())

const filterKey = computed(() => {
  if (props.valueKey === 'read_attr') {
    return 'attr_filter'
  }
  return 'ci_filter'
})

const isHalfChecked = computed(() => {
  if (filerPerimissions.value[props.rid]) {
    const tempValue = filerPerimissions.value[props.rid][filterKey.value]
    return !!(tempValue && tempValue.length)
  }
  return false
})

function openReadGrantModal() {
  emit('openReadGrantModal')
}
</script>

<template>
  <div :class="{ 'read-checkbox': true, 'ant-checkbox-wrapper': isHalfChecked }" @click="openReadGrantModal">
    <a-tooltip
      v-if="value && isHalfChecked"
      :title="valueKey === 'read_ci' ? filerPerimissions[rid].name || '' : ''"
    >
      <div v-if="value && isHalfChecked" class="read-checkbox-half-checked ant-checkbox"></div>
    </a-tooltip>
    <a-checkbox v-else :checked="value" />
  </div>
</template>

<style scoped>
.read-checkbox .read-checkbox-half-checked {
  width: 16px;
  height: 16px;
  border: 1px solid #d9d9d9;
  border-radius: 2px;
  cursor: pointer;
  margin: 0;
  padding: 0;
  position: relative;
  overflow: hidden;
}
.read-checkbox .read-checkbox-half-checked::after {
  content: '';
  position: absolute;
  width: 0;
  height: 0;
  border-radius: 2px;
  border: 14px solid transparent;
  border-left-color: #2f54eb;
  transform: rotate(225deg);
  top: -16px;
  left: -17px;
}
</style>
