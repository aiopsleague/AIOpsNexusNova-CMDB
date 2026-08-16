<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { CheckFn, CronValue } from './types'

const props = defineProps<{ check: CheckFn; cron: CronValue }>()

const emit = defineEmits<{ (e: 'update', name: string, value: string, from?: string): void }>()

const radioValue = ref(1)
const cycle01 = ref(1)
const cycle02 = ref(2)
const average01 = ref(1)
const average02 = ref(1)
const checkboxList = ref<Array<string | number>>([])

const cycleTotal = computed(() => `${cycle01.value}-${cycle02.value}`)
const averageTotal = computed(() => `${average01.value}/${average02.value}`)
const checkboxString = computed(() => {
  const str = checkboxList.value.join()
  return str === '' ? '*' : str
})

function radioChange() {
  if (radioValue.value === 1) {
    emit('update', 'mouth', '*')
  } else {
    if (props.cron.day === '*') {
      emit('update', 'day', '0', 'mouth')
    }
    if (props.cron.hour === '*') {
      emit('update', 'hour', '0', 'mouth')
    }
    if (props.cron.min === '*') {
      emit('update', 'min', '0', 'mouth')
    }
    if (props.cron.second === '*') {
      emit('update', 'second', '0', 'mouth')
    }
  }
  switch (radioValue.value) {
    case 2:
      emit('update', 'mouth', cycle01.value + '-' + cycle02.value)
      break
    case 3:
      emit('update', 'mouth', average01.value + '/' + average02.value)
      break
    case 4:
      emit('update', 'mouth', checkboxString.value)
      break
  }
}

watch(radioValue, radioChange)
watch([cycle01, cycle02], ([c1, c2]) => {
  cycle01.value = props.check(c1, 1, 12)
  cycle02.value = props.check(c2, 1, 12)
  if (radioValue.value === 2) emit('update', 'mouth', cycleTotal.value)
})
watch([average01, average02], ([a1, a2]) => {
  average01.value = props.check(a1, 1, 12)
  average02.value = props.check(a2, 1, 12)
  if (radioValue.value === 3) emit('update', 'mouth', averageTotal.value)
})
watch(checkboxList, () => {
  if (radioValue.value === 4) emit('update', 'mouth', checkboxString.value)
})

defineExpose({ radioValue, cycle01, cycle02, average01, average02, checkboxList })
</script>

<template>
  <a-form size="small">
    <a-radio-group v-model:value="radioValue" style="width: 100%">
      <a-form-item>
        <a-radio :value="1">月，允许的通配符[, - * /]</a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="2">
          周期从
          <a-input-number v-model:value="cycle01" :min="1" :max="12" /> -
          <a-input-number v-model:value="cycle02" :min="1" :max="12" /> 月
        </a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="3">
          从
          <a-input-number v-model:value="average01" :min="1" :max="12" /> 月开始，每
          <a-input-number v-model:value="average02" :min="1" :max="12" /> 月执行一次
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
            <a-select-option v-for="item in 12" :key="item" :value="item">{{ item }}</a-select-option>
          </a-select>
        </a-radio>
      </a-form-item>
    </a-radio-group>
  </a-form>
</template>
