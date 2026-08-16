<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { CheckFn, CronValue } from './types'

const props = defineProps<{ check: CheckFn; cron: CronValue }>()

const emit = defineEmits<{ (e: 'update', name: string, value: string, from?: string): void }>()

const fullYear = ref(0)
const radioValue = ref(1)
const cycle01 = ref(0)
const cycle02 = ref(0)
const average01 = ref(0)
const average02 = ref(1)
const checkboxList = ref<Array<string | number>>([])

const cycleTotal = computed(() => `${cycle01.value}-${cycle02.value}`)
const averageTotal = computed(() => `${average01.value}/${average02.value}`)
const checkboxString = computed(() => checkboxList.value.join())

function radioChange() {
  if (props.cron.mouth === '*') {
    emit('update', 'mouth', '0', 'year')
  }
  if (props.cron.day === '*') {
    emit('update', 'day', '0', 'year')
  }
  if (props.cron.hour === '*') {
    emit('update', 'hour', '0', 'year')
  }
  if (props.cron.min === '*') {
    emit('update', 'min', '0', 'year')
  }
  if (props.cron.second === '*') {
    emit('update', 'second', '0', 'year')
  }
  switch (radioValue.value) {
    case 1:
      emit('update', 'year', '')
      break
    case 2:
      emit('update', 'year', '*')
      break
    case 3:
      emit('update', 'year', cycle01.value + '-' + cycle02.value)
      break
    case 4:
      emit('update', 'year', average01.value + '/' + average02.value)
      break
    case 5:
      emit('update', 'year', checkboxString.value)
      break
  }
}

watch(radioValue, radioChange)
watch([cycle01, cycle02], ([c1, c2]) => {
  cycle01.value = props.check(c1, fullYear.value, fullYear.value + 100)
  cycle02.value = props.check(c2, fullYear.value + 1, fullYear.value + 101)
  if (radioValue.value === 3) emit('update', 'year', cycleTotal.value)
})
watch([average01, average02], ([a1, a2]) => {
  average01.value = props.check(a1, fullYear.value, fullYear.value + 100)
  average02.value = props.check(a2, 1, 10)
  if (radioValue.value === 4) emit('update', 'year', averageTotal.value)
})
watch(checkboxList, () => {
  if (radioValue.value === 5) emit('update', 'year', checkboxString.value)
})

onMounted(() => {
  fullYear.value = Number(new Date().getFullYear())
})

defineExpose({ radioValue, cycle01, cycle02, average01, average02, checkboxList })
</script>

<template>
  <a-form size="small">
    <a-radio-group v-model:value="radioValue" style="width: 100%">
      <a-form-item>
        <a-radio :value="1">不填，允许的通配符[, - * /]</a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="2">每年</a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="3">
          周期从
          <a-input-number v-model:value="cycle01" :min="fullYear" /> -
          <a-input-number v-model:value="cycle02" :min="fullYear" />
        </a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="4">
          从
          <a-input-number v-model:value="average01" :min="fullYear" /> 年开始，每
          <a-input-number v-model:value="average02" :min="fullYear" /> 年执行一次
        </a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="5">
          指定
          <a-select
            v-model:value="checkboxList"
            mode="multiple"
            allow-clear
            placeholder="可多选"
            style="width: 100%"
          >
            <a-select-option v-for="item in 9" :key="item" :value="item - 1 + fullYear">{{ item - 1 + fullYear }}</a-select-option>
          </a-select>
        </a-radio>
      </a-form-item>
    </a-radio-group>
  </a-form>
</template>
