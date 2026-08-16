<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { CheckFn, CronValue } from './types'

const props = defineProps<{ check: CheckFn; cron: CronValue }>()

const emit = defineEmits<{ (e: 'update', name: string, value: string, from?: string): void }>()

const radioValue = ref(2)
const weekday = ref(1)
const cycle01 = ref(1)
const cycle02 = ref(2)
const average01 = ref(1)
const average02 = ref(1)
const checkboxList = ref<Array<string | number>>([])
const weekList = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const cycleTotal = computed(() => `${cycle01.value}-${cycle02.value}`)
const averageTotal = computed(() => `${average01.value}#${average02.value}`)
const checkboxString = computed(() => {
  const str = checkboxList.value.join()
  return str === '' ? '*' : str
})

function radioChange() {
  if (radioValue.value !== 2) {
    emit('update', 'day', '?')
  }
  switch (radioValue.value) {
    case 1:
      emit('update', 'week', '*')
      break
    case 2:
      emit('update', 'week', '?')
      emit('update', 'day', '*')
      break
    case 3:
      emit('update', 'week', cycle01.value + '-' + cycle02.value)
      break
    case 4:
      emit('update', 'week', average01.value + '#' + average02.value)
      break
    case 5:
      emit('update', 'week', weekday.value + 'L')
      break
    case 6:
      emit('update', 'week', checkboxString.value)
      break
  }
}

watch(radioValue, radioChange)
watch([cycle01, cycle02], ([c1, c2]) => {
  cycle01.value = props.check(c1, 1, 7)
  cycle02.value = props.check(c2, 1, 7)
  if (radioValue.value === 3) emit('update', 'week', cycleTotal.value)
})
watch([average01, average02], ([a1, a2]) => {
  average01.value = props.check(a1, 1, 4)
  average02.value = props.check(a2, 1, 7)
  if (radioValue.value === 4) emit('update', 'week', averageTotal.value)
})
watch(weekday, (w) => {
  weekday.value = props.check(w, 1, 7)
  if (radioValue.value === 5) emit('update', 'week', weekday.value + 'L')
})
watch(checkboxList, () => {
  if (radioValue.value === 6) emit('update', 'week', checkboxString.value)
})

defineExpose({ radioValue, weekday, cycle01, cycle02, average01, average02, checkboxList })
</script>

<template>
  <a-form size="small">
    <a-radio-group v-model:value="radioValue" style="width: 100%">
      <a-form-item>
        <a-radio :value="1">周，允许的通配符[, - * / L #]</a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="2">不指定</a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="3">
          周期从星期
          <a-input-number v-model:value="cycle01" :min="1" :max="7" /> -
          <a-input-number v-model:value="cycle02" :min="1" :max="7" />
        </a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="4">
          第
          <a-input-number v-model:value="average01" :min="1" :max="4" /> 周的星期
          <a-input-number v-model:value="average02" :min="1" :max="7" />
        </a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="5">
          本月最后一个星期
          <a-input-number v-model:value="weekday" :min="1" :max="7" />
        </a-radio>
      </a-form-item>
      <a-form-item>
        <a-radio :value="6">
          指定
          <a-select
            v-model:value="checkboxList"
            mode="multiple"
            allow-clear
            placeholder="可多选"
            style="width: 100%"
          >
            <a-select-option v-for="(item, index) in weekList" :key="index" :value="index + 1">{{ item }}</a-select-option>
          </a-select>
        </a-radio>
      </a-form-item>
    </a-radio-group>
  </a-form>
</template>
