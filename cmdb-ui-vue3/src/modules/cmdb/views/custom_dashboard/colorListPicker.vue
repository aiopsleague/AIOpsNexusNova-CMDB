<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string | string[] | null
  }>(),
  {
    modelValue: null,
  }
)

const emit = defineEmits<{ (e: 'update:modelValue', value: string | string[]): void }>()

const list = [
  '#5DADF2,#86DFB7,#5A6F96,#7BD5FF,#FFB980,#4D58D6,#D9B6E9,#8054FF',
  '#9BA1F9,#0F2BA8,#A2EBFE,#4982F6,#FEB09C,#6C78E8,#FFDDAB,#4D66BD',
]

const currentColor = computed<string | string[] | null>({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val as string | string[]),
})
</script>

<template>
  <a-select v-model:value="currentColor">
    <a-select-option v-for="i in list" :key="i" :value="i">
      <div>
        <span v-for="color in i.split(',')" :key="color" :style="{ backgroundColor: color }" class="color-box"></span>
      </div>
    </a-select-option>
  </a-select>
</template>

<style lang="less" scoped>
.color-box {
  display: inline-block;
  width: 40px;
  height: 10px;
}
</style>
