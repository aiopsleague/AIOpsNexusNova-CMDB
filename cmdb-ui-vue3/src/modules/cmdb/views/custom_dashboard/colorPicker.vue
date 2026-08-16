<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string | string[] | null
    colorList?: Array<string | string[]>
  }>(),
  {
    modelValue: null,
    colorList: () => [],
  }
)

const emit = defineEmits<{ (e: 'update:modelValue', value: string | string[]): void }>()

const currentColor = computed<string | string[] | null>({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val as string | string[]),
})

function isEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

function changeColor(item: string | string[]) {
  emit('update:modelValue', item)
}
</script>

<template>
  <div class="color-picker">
    <div
      v-for="item in colorList"
      :key="Array.isArray(item) ? item.join() : item"
      :style="{
        background: Array.isArray(item) ? `linear-gradient(to bottom, ${item[0]} 0%, ${item[1]} 100%)` : item,
      }"
      :class="{ 'color-picker-box': true, 'color-picker-box-selected': isEqual(currentColor, item) }"
      @click="changeColor(item)"
    ></div>
  </div>
</template>

<style lang="less" scoped>
.color-picker {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  .color-picker-box {
    width: 19px;
    height: 19px;
    border: 1px solid #dae2e7;
    border-radius: 1px;
    cursor: pointer;
  }
  .color-picker-box-selected {
    position: relative;
    &:after {
      content: '';
      position: absolute;
      width: 24px;
      height: 24px;
      border: 1px solid #43bbff;
      top: -3px;
      left: -3px;
    }
  }
}
</style>
