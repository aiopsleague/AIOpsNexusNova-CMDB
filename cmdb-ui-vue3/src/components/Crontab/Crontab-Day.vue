<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { CheckFn, CronValue } from './types'

const props = defineProps<{ check: CheckFn; cron: CronValue }>()

const emit = defineEmits<{ (e: 'update', name: string, value: string, from?: string): void }>()

const radioValue = ref(1)
const workday = ref(1)
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
  switch (radioValue.value) {
    case 1:
      emit('update', 'day', '*', 'day')
      emit('update', 'week', '?', 'day')
      break
    case 2:
      emit('update', 'day', '?')
      emit('update', 'week', '*')
      break
    case 3:
      emit('update', 'day', cycle01.value + '-' + cycle02.value)
      break
    case 4:
      emit('update', 'day', average01.value + '/' + average02.value)
      break
    case 5:
      emit('update', 'day', workday.value + 'W')
      break
    case 6:
      emit('update', 'day', 'L')
      break
    case 7:
      emit('update', 'day', checkboxString.value)
      break
  }
}

watch(radioValue, radioChange)
watch([cycle01, cycle02], ([c1, c2]) => {
  cycle01.value = props.check(c1, 1, 31)
  cycle02.value = props.check(c2, 1, 31)
  if (radioValue.value === 3) emit('update', 'day', cycleTotal.value)
})
watch([average01, average02], ([a1, a2]) => {
  average01.value = props.check(a1, 1, 31)
  average02.value = props.check(a2, 1, 31)
  if (radioValue.value === 4) emit('update', 'day', averageTotal.value)
})
watch(workday, (w) => {
  workday.value = props.check(w, 1, 31)
  if (radioValue.value === 5) emit('update', 'day', workday.value + 'W')
})
watch(checkboxList, () => {
  if (radioValue.value === 7) emit('update', 'day', checkboxString.value)
})

defineExpose({ radioValue, workday, cycle01, cycle02, average01, average02, checkboxList })
</script>

<template>
  <a-form size="small">
    <a-radio-group v-model:value="radioValue" style="width: 100%">
      <a-form-item>
        <a-radio :value="1">日，允许的通配符[, - * / L M]</a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="2">不指定</a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="3">
          周期从
          <a-input-number v-model:value="cycle01" :min="0" :max="31" /> -
          <a-input-number v-model:value="cycle02" :min="0" :max="31" /> 日
        </a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="4">
          从
          <a-input-number v-model:value="average01" :min="0" :max="31" /> 号开始，每
          <a-input-number v-model:value="average02" :min="0" :max="31" /> 日执行一次
        </a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="5">
          每月
          <a-input-number v-model:value="workday" :min="0" :max="31" /> 号最近的那个工作日
        </a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="6">本月最后一天</a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="7">
          指定
          <a-select
            v-model:value="checkboxList"
            mode="multiple"
            allow-clear
            placeholder="可多选"
            style="width: 100%"
          >
            <a-select-option v-for="item in 31" :key="item" :value="item">{{ item }}</a-select-option>
          </a-select>
        </a-radio>
      </a-form-item>
    </a-radio-group>
  </a-form>
</template>
