<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { CheckFn } from './types'

const props = defineProps<{ check: CheckFn }>()

const emit = defineEmits<{ (e: 'update', name: string, value: string, from?: string): void }>()

const radioValue = ref(1)
const cycle01 = ref(1)
const cycle02 = ref(2)
const average01 = ref(0)
const average02 = ref(1)
const checkboxList = ref<Array<string | number>>([])

const cycleTotal = computed(() => `${cycle01.value}-${cycle02.value}`)
const averageTotal = computed(() => `${average01.value}/${average02.value}`)
const checkboxString = computed(() => {
  const str = checkboxList.value.join()
  return str === '' ? '*' : str
})

function radioChange() {
  switch (radioValue.value) {
    case 1:
      emit('update', 'second', '*', 'second')
      emit('update', 'min', '*', 'second')
      break
    case 2:
      emit('update', 'second', cycle01.value + '-' + cycle02.value)
      break
    case 3:
      emit('update', 'second', average01.value + '/' + average02.value)
      break
    case 4:
      emit('update', 'second', checkboxString.value)
      break
  }
}

watch(radioValue, radioChange)
watch([cycle01, cycle02], ([c1, c2]) => {
  cycle01.value = props.check(c1, 0, 59)
  cycle02.value = props.check(c2, 0, 59)
  if (radioValue.value === 2) emit('update', 'second', cycleTotal.value)
})
watch([average01, average02], ([a1, a2]) => {
  average01.value = props.check(a1, 0, 59)
  average02.value = props.check(a2, 1, 59)
  if (radioValue.value === 3) emit('update', 'second', averageTotal.value)
})
watch(checkboxList, () => {
  if (radioValue.value === 4) emit('update', 'second', checkboxString.value)
})

defineExpose({ radioValue, cycle01, cycle02, average01, average02, checkboxList })
</script>

<template>
  <a-form size="small">
    <a-radio-group v-model:value="radioValue" style="width: 100%">
      <a-form-item>
        <a-radio :value="1">秒，允许的通配符[, - * /]</a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="2">
          周期从
          <a-input-number v-model:value="cycle01" :min="0" :max="60" /> -
          <a-input-number v-model:value="cycle02" :min="0" :max="60" /> 秒
        </a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="3">
          从
          <a-input-number v-model:value="average01" :min="0" :max="60" /> 秒开始，每
          <a-input-number v-model:value="average02" :min="0" :max="60" /> 秒执行一次
        </a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="4">
          指定
          <a-select
            v-model:value="checkboxList"
            mode="multiple"
            allow-clear
            placeholder="可多选"
            style="width: 100%"
          >
            <a-select-option v-for="item in 60" :key="item" :value="item - 1">{{ item - 1 }}</a-select-option>
          </a-select>
        </a-radio>
      </a-form-item>
    </a-radio-group>
  </a-form>
</template>
