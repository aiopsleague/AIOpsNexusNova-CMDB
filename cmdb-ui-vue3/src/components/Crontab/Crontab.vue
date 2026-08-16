<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import CrontabSecond from './Crontab-Second.vue'
import CrontabMin from './Crontab-Min.vue'
import CrontabHour from './Crontab-Hour.vue'
import CrontabDay from './Crontab-Day.vue'
import CrontabMouth from './Crontab-Mouth.vue'
import CrontabWeek from './Crontab-Week.vue'
import CrontabYear from './Crontab-Year.vue'
import { cronValidate } from './utils'
import type { CronValue } from './types'

const props = defineProps<{
  expression?: string
  hideComponent?: string[]
  defaultExpression?: string
  hasFooter?: boolean
}>()

const emit = defineEmits<{
  (e: 'fill', value: string): void
  (e: 'hide'): void
  (e: 'error', message: string): void
}>()

const tabTitles = [
  { value: 'second', label: '秒' },
  { value: 'min', label: '分钟' },
  { value: 'hour', label: '小时' },
  { value: 'day', label: '日' },
  { value: 'month', label: '月' },
  { value: 'week', label: '周' },
  { value: 'year', label: '年' },
]

const contabValueObj = ref<CronValue>({
  second: '*',
  min: '*',
  hour: '*',
  day: '*',
  mouth: '*',
  week: '?',
  year: '',
})

// Child component instances (used to reverse-parse an expression into the UI).
interface CronChild {
  radioValue: number
  cycle01: number
  cycle02: number
  average01: number
  average02: number
  checkboxList: Array<string | number>
  workday?: number
  weekday?: number
}

const cronsecond = ref<CronChild | null>(null)
const cronmin = ref<CronChild | null>(null)
const cronhour = ref<CronChild | null>(null)
const cronday = ref<CronChild | null>(null)
const cronmouth = ref<CronChild | null>(null)
const cronweek = ref<CronChild | null>(null)
const cronyear = ref<CronChild | null>(null)

function getChild(name: string): CronChild | null {
  const map: Record<string, CronChild | null> = {
    second: cronsecond.value,
    min: cronmin.value,
    hour: cronhour.value,
    day: cronday.value,
    mouth: cronmouth.value,
    week: cronweek.value,
    year: cronyear.value,
  }
  return map[name] ?? null
}

function shouldHide(key: string): boolean {
  if (props.hideComponent && props.hideComponent.includes(key)) return false
  return true
}

function resolveExp(expression: string) {
  if (expression) {
    const arr = expression.split(' ')
    if (arr.length >= 6) {
      const obj: CronValue = {
        second: arr[0],
        min: arr[1],
        hour: arr[2],
        day: arr[3],
        mouth: arr[4],
        week: arr[5],
        year: arr[6] ? arr[6] : '',
      }
      contabValueObj.value = { ...obj }
      for (const key of Object.keys(obj) as Array<keyof CronValue>) {
        if (obj[key]) changeRadio(key, obj[key])
      }
    }
  }
}

function updateContabValue(name: string, value: string, from?: string) {
  contabValueObj.value[name as keyof CronValue] = value
  if (from && from !== name) {
    changeRadio(name, value)
  }
}

function changeRadio(name: string, value: string) {
  const arr = ['second', 'min', 'hour', 'mouth']
  const child = getChild(name)
  if (!child) return

  let insVlaue = 1
  if (arr.includes(name)) {
    if (value === '*') {
      insVlaue = 1
    } else if (value.indexOf('-') > -1) {
      const indexArr = value.split('-')
      child.cycle01 = isNaN(Number(indexArr[0])) ? 0 : Number(indexArr[0])
      child.cycle02 = Number(indexArr[1])
      insVlaue = 2
    } else if (value.indexOf('/') > -1) {
      const indexArr = value.split('/')
      child.average01 = isNaN(Number(indexArr[0])) ? 0 : Number(indexArr[0])
      child.average02 = Number(indexArr[1])
      insVlaue = 3
    } else {
      insVlaue = 4
      child.checkboxList = value.split(',').map((v) => Number(v))
    }
  } else if (name === 'day') {
    if (value === '*') {
      insVlaue = 1
    } else if (value === '?') {
      insVlaue = 2
    } else if (value.indexOf('-') > -1) {
      const indexArr = value.split('-')
      child.cycle01 = isNaN(Number(indexArr[0])) ? 0 : Number(indexArr[0])
      child.cycle02 = Number(indexArr[1])
      insVlaue = 3
    } else if (value.indexOf('/') > -1) {
      const indexArr = value.split('/')
      child.average01 = isNaN(Number(indexArr[0])) ? 0 : Number(indexArr[0])
      child.average02 = Number(indexArr[1])
      insVlaue = 4
    } else if (value.indexOf('W') > -1) {
      const indexArr = value.split('W')
      child.workday = isNaN(Number(indexArr[0])) ? 0 : Number(indexArr[0])
      insVlaue = 5
    } else if (value === 'L') {
      insVlaue = 6
    } else {
      child.checkboxList = value.split(',')
      insVlaue = 7
    }
  } else if (name === 'week') {
    if (value === '*') {
      insVlaue = 1
    } else if (value === '?') {
      insVlaue = 2
    } else if (value.indexOf('-') > -1) {
      const indexArr = value.split('-')
      child.cycle01 = isNaN(Number(indexArr[0])) ? 0 : Number(indexArr[0])
      child.cycle02 = Number(indexArr[1])
      insVlaue = 3
    } else if (value.indexOf('#') > -1) {
      const indexArr = value.split('#')
      child.average01 = isNaN(Number(indexArr[0])) ? 1 : Number(indexArr[0])
      child.average02 = Number(indexArr[1])
      insVlaue = 4
    } else if (value.indexOf('L') > -1) {
      const indexArr = value.split('L')
      child.weekday = isNaN(Number(indexArr[0])) ? 1 : Number(indexArr[0])
      insVlaue = 5
    } else {
      child.checkboxList = value.split(',')
      insVlaue = 6
    }
  } else if (name === 'year') {
    if (value === '') {
      insVlaue = 1
    } else if (value === '*') {
      insVlaue = 2
    } else if (value.indexOf('-') > -1) {
      insVlaue = 3
    } else if (value.indexOf('/') > -1) {
      insVlaue = 4
    } else {
      child.checkboxList = value.split(',')
      insVlaue = 5
    }
  }
  child.radioValue = insVlaue
}

function checkNumber(value: number, minLimit: number, maxLimit: number): number {
  let v = Math.floor(value)
  if (v < minLimit) {
    v = minLimit
  } else if (v > maxLimit) {
    v = maxLimit
  }
  return v
}

function hidePopup() {
  emit('hide')
}

function submitFill() {
  const result = cronValidate(contabValueString.value)
  if (typeof result !== 'boolean') {
    message.warning(result)
    emit('error', result)
    return
  }
  emit('fill', displayContabValueString.value)
  hidePopup()
}

function clearCron() {
  resolveExp(props.defaultExpression || '* * * * * ?')
}

const contabValueString = computed(() => {
  const obj = contabValueObj.value
  return (
    obj.second +
    ' ' +
    obj.min +
    ' ' +
    obj.hour +
    ' ' +
    obj.day +
    ' ' +
    obj.mouth +
    ' ' +
    obj.week +
    (obj.year === '' ? '' : ' ' + obj.year)
  )
})

// Strip the leading "second" field and normalize `?` to `*` for display.
const displayContabValueString = computed(() => {
  const temp = contabValueString.value.substring(2)
  return temp.replace(/\?/g, '*')
})

const displayTabTitles = computed(() => {
  return tabTitles.filter((item) => !(props.hideComponent ?? []).includes(item.value))
})

watch(
  () => props.expression,
  (val) => {
    if (!val) {
      clearCron()
      return
    }
    resolveExp(val)
  },
  { immediate: true }
)

onMounted(() => {
  if (props.expression) {
    resolveExp(props.expression)
  } else {
    clearCron()
  }
})
</script>

<template>
  <div :style="{ width: '490px' }">
    <a-tabs type="card" class="ops-crontab">
      <a-tab-pane v-if="shouldHide('second')" key="second" tab="秒">
        <CrontabSecond ref="cronsecond" :check="checkNumber" @update="updateContabValue" />
      </a-tab-pane>
      <a-tab-pane v-if="shouldHide('min')" key="min" tab="分钟">
        <CrontabMin ref="cronmin" :check="checkNumber" :cron="contabValueObj" @update="updateContabValue" />
      </a-tab-pane>
      <a-tab-pane v-if="shouldHide('hour')" key="hour" tab="小时">
        <CrontabHour ref="cronhour" :check="checkNumber" :cron="contabValueObj" @update="updateContabValue" />
      </a-tab-pane>
      <a-tab-pane v-if="shouldHide('day')" key="day" tab="日">
        <CrontabDay ref="cronday" :check="checkNumber" :cron="contabValueObj" @update="updateContabValue" />
      </a-tab-pane>
      <a-tab-pane v-if="shouldHide('mouth')" key="mouth" tab="月">
        <CrontabMouth ref="cronmouth" :check="checkNumber" :cron="contabValueObj" @update="updateContabValue" />
      </a-tab-pane>
      <a-tab-pane v-if="shouldHide('week')" key="week" tab="周">
        <CrontabWeek ref="cronweek" :check="checkNumber" :cron="contabValueObj" @update="updateContabValue" />
      </a-tab-pane>
      <a-tab-pane v-if="shouldHide('year')" key="year" tab="年">
        <CrontabYear ref="cronyear" :check="checkNumber" :cron="contabValueObj" @update="updateContabValue" />
      </a-tab-pane>
    </a-tabs>

    <div class="popup-main">
      <div class="popup-result">
        <p class="title">时间表达式</p>
        <div style="padding: 12px">
          <table>
            <thead>
              <th v-for="item of displayTabTitles" :key="item.value" width="40">{{ item.label }}</th>
              <th>crontab完整表达式</th>
            </thead>
            <tbody>
              <td v-if="shouldHide('second')">
                <span class="square">{{ contabValueObj.second }}</span>
              </td>
              <td v-if="shouldHide('min')">
                <span class="square">{{ contabValueObj.min }}</span>
              </td>
              <td v-if="shouldHide('hour')">
                <span class="square">{{ contabValueObj.hour }}</span>
              </td>
              <td v-if="shouldHide('day')">
                <span class="square">{{ contabValueObj.day === '?' ? '*' : contabValueObj.day }}</span>
              </td>
              <td v-if="shouldHide('mouth')">
                <span class="square">{{ contabValueObj.mouth }}</span>
              </td>
              <td v-if="shouldHide('week')">
                <span class="square">{{ contabValueObj.week === '?' ? '*' : contabValueObj.week }}</span>
              </td>
              <td v-if="shouldHide('year')">
                <span class="square">{{ contabValueObj.year }}</span>
              </td>
              <td>
                <span class="rectangle">{{ displayContabValueString }}</span>
              </td>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <div v-if="hasFooter" class="pop_btn">
      <a-space>
        <a-button size="small" type="primary" @click="submitFill">确定</a-button>
        <a-button size="small" danger @click="clearCron">重置</a-button>
        <a-button size="small" @click="hidePopup">取消</a-button>
      </a-space>
    </div>
  </div>
</template>

<style scoped>
.pop_btn {
  text-align: right;
  margin-top: 24px;
}
.popup-main {
  position: relative;
  margin: 16px auto;
  background: #fff;
  border-radius: 8px;
  font-size: 12px;
  overflow: hidden;
  box-shadow: 0px 8px 16px rgba(160, 181, 235, 0.25);
}
.popup-result {
  border-radius: 8px;
}
.popup-result .title {
  background: #fff;
  font-weight: 400;
  font-size: 14px;
  color: #2f54eb;
  background-color: #f0f5ff;
  margin: 0px;
  box-sizing: border-box;
  padding-left: 12px;
}
.popup-result table {
  text-align: center;
  width: 100%;
  margin: 0 auto;
}
.popup-result table span {
  display: block;
  width: 100%;
  font-family: arial;
  line-height: 26px;
  height: 26px;
  white-space: nowrap;
  overflow: hidden;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}
.popup-result table span.square {
  width: 40px;
  box-sizing: border-box;
}
.popup-result table span.rectangle {
  width: 247px;
}
</style>
