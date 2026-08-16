<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

// Computes the next few run times for a cron expression. Not currently wired
// into the main editor, but kept for parity with the legacy component.
const props = defineProps<{ ex: string }>()

const dayRule = ref('')
const dayRuleSup = ref<any>('')
const dateArr = ref<any[]>([])
const resultList = ref<string[]>([])
const isShow = ref(false)

// Recompute the run times whenever the expression changes.
function expressionChange() {
  isShow.value = false
  const ruleArr = props.ex.split(' ')
  let nums = 0
  const resultArr: string[] = []
  const nTime = new Date()
  const nYear = nTime.getFullYear()
  let nMouth = nTime.getMonth() + 1
  let nDay = nTime.getDate()
  let nHour = nTime.getHours()
  let nMin = nTime.getMinutes()
  let nSecond = nTime.getSeconds()

  getSecondArr(ruleArr[0])
  getMinArr(ruleArr[1])
  getHourArr(ruleArr[2])
  getDayArr(ruleArr[3])
  getMouthArr(ruleArr[4])
  getWeekArr(ruleArr[5])
  getYearArr(ruleArr[6], nYear)

  const sDate = dateArr.value[0]
  const mDate = dateArr.value[1]
  const hDate = dateArr.value[2]
  const DDate = dateArr.value[3]
  const MDate = dateArr.value[4]
  const YDate = dateArr.value[5]

  let sIdx = getIndex(sDate, nSecond)
  let mIdx = getIndex(mDate, nMin)
  let hIdx = getIndex(hDate, nHour)
  let DIdx = getIndex(DDate, nDay)
  let MIdx = getIndex(MDate, nMouth)
  const YIdx = getIndex(YDate, nYear)

  const resetSecond = () => {
    sIdx = 0
    nSecond = sDate[sIdx]
  }
  const resetMin = () => {
    mIdx = 0
    nMin = mDate[mIdx]
    resetSecond()
  }
  const resetHour = () => {
    hIdx = 0
    nHour = hDate[hIdx]
    resetMin()
  }
  const resetDay = () => {
    DIdx = 0
    nDay = DDate[DIdx]
    resetHour()
  }
  const resetMouth = () => {
    MIdx = 0
    nMouth = MDate[MIdx]
    resetDay()
  }

  if (nYear !== YDate[YIdx]) {
    resetMouth()
  }
  if (nMouth !== MDate[MIdx]) {
    resetDay()
  }
  if (nDay !== DDate[DIdx]) {
    resetHour()
  }
  if (nHour !== hDate[hIdx]) {
    resetMin()
  }
  if (nMin !== mDate[mIdx]) {
    resetSecond()
  }

  goYear: for (let Yi = YIdx; Yi < YDate.length; Yi++) {
    const YY = YDate[Yi]
    if (nMouth > MDate[MDate.length - 1]) {
      resetMouth()
      continue
    }
    goMouth: for (let Mi = MIdx; Mi < MDate.length; Mi++) {
      let MM: any = MDate[Mi]
      MM = MM < 10 ? '0' + MM : MM
      if (nDay > DDate[DDate.length - 1]) {
        resetDay()
        if (Mi === MDate.length - 1) {
          resetMouth()
          continue goYear
        }
        continue
      }
      goDay: for (let Di = DIdx; Di < DDate.length; Di++) {
        let DD: any = DDate[Di]
        let thisDD: any = DD < 10 ? '0' + DD : DD

        if (nHour > hDate[hDate.length - 1]) {
          resetHour()
          if (Di === DDate.length - 1) {
            resetDay()
            if (Mi === MDate.length - 1) {
              resetMouth()
              continue goYear
            }
            continue goMouth
          }
          continue
        }

        if (
          checkDate(YY + '-' + MM + '-' + thisDD + ' 00:00:00') !== true &&
          dayRule.value !== 'workDay' &&
          dayRule.value !== 'lastWeek' &&
          dayRule.value !== 'lastDay'
        ) {
          resetDay()
          continue goMouth
        }
        if (dayRule.value === 'lastDay') {
          if (checkDate(YY + '-' + MM + '-' + thisDD + ' 00:00:00') !== true) {
            while (DD > 0 && checkDate(YY + '-' + MM + '-' + thisDD + ' 00:00:00') !== true) {
              DD--
              thisDD = DD < 10 ? '0' + DD : DD
            }
          }
        } else if (dayRule.value === 'workDay') {
          if (checkDate(YY + '-' + MM + '-' + thisDD + ' 00:00:00') !== true) {
            while (DD > 0 && checkDate(YY + '-' + MM + '-' + thisDD + ' 00:00:00') !== true) {
              DD--
              thisDD = DD < 10 ? '0' + DD : DD
            }
          }
          const thisWeek = formatDate(new Date(YY + '-' + MM + '-' + thisDD + ' 00:00:00'), 'week')
          if (thisWeek === 0) {
            DD++
            thisDD = DD < 10 ? '0' + DD : DD
            if (checkDate(YY + '-' + MM + '-' + thisDD + ' 00:00:00') !== true) {
              DD -= 3
            }
          } else if (thisWeek === 6) {
            if (dayRuleSup.value !== 1) {
              DD--
            } else {
              DD += 2
            }
          }
        } else if (dayRule.value === 'weekDay') {
          const thisWeek = formatDate(new Date(YY + '-' + MM + '-' + DD + ' 00:00:00'), 'week')
          if (!dayRuleSup.value.includes(thisWeek)) {
            if (Di === DDate.length - 1) {
              resetDay()
              if (Mi === MDate.length - 1) {
                resetMouth()
                continue goYear
              }
              continue goMouth
            }
            continue
          }
        } else if (dayRule.value === 'assWeek') {
          const thisWeek = formatDate(new Date(YY + '-' + MM + '-' + DD + ' 00:00:00'), 'week')
          if (dayRuleSup.value[1] >= thisWeek) {
            DD = (dayRuleSup.value[0] - 1) * 7 + dayRuleSup.value[1] - thisWeek + 1
          } else {
            DD = dayRuleSup.value[0] * 7 + dayRuleSup.value[1] - thisWeek + 1
          }
        } else if (dayRule.value === 'lastWeek') {
          if (checkDate(YY + '-' + MM + '-' + thisDD + ' 00:00:00') !== true) {
            while (DD > 0 && checkDate(YY + '-' + MM + '-' + thisDD + ' 00:00:00') !== true) {
              DD--
              thisDD = DD < 10 ? '0' + DD : DD
            }
          }
          const thisWeek = formatDate(new Date(YY + '-' + MM + '-' + thisDD + ' 00:00:00'), 'week')
          if (dayRuleSup.value < thisWeek) {
            DD -= thisWeek - dayRuleSup.value
          } else if (dayRuleSup.value > thisWeek) {
            DD -= 7 - (dayRuleSup.value - thisWeek)
          }
        }
        DD = DD < 10 ? '0' + DD : DD

        goHour: for (let hi = hIdx; hi < hDate.length; hi++) {
          const hh = hDate[hi] < 10 ? '0' + hDate[hi] : hDate[hi]

          if (nMin > mDate[mDate.length - 1]) {
            resetMin()
            if (hi === hDate.length - 1) {
              resetHour()
              if (Di === DDate.length - 1) {
                resetDay()
                if (Mi === MDate.length - 1) {
                  resetMouth()
                  continue goYear
                }
                continue goMouth
              }
              continue goDay
            }
            continue
          }
          goMin: for (let mi = mIdx; mi < mDate.length; mi++) {
            const mm = mDate[mi] < 10 ? '0' + mDate[mi] : mDate[mi]

            if (nSecond > sDate[sDate.length - 1]) {
              resetSecond()
              if (mi === mDate.length - 1) {
                resetMin()
                if (hi === hDate.length - 1) {
                  resetHour()
                  if (Di === DDate.length - 1) {
                    resetDay()
                    if (Mi === MDate.length - 1) {
                      resetMouth()
                      continue goYear
                    }
                    continue goMouth
                  }
                  continue goDay
                }
                continue goHour
              }
              continue
            }
            for (let si = sIdx; si <= sDate.length - 1; si++) {
              const ss = sDate[si] < 10 ? '0' + sDate[si] : sDate[si]
              if (MM !== '00' && DD !== '00') {
                resultArr.push(YY + '-' + MM + '-' + DD + ' ' + hh + ':' + mm + ':' + ss)
                nums++
              }
              if (nums === 5) break goYear
              if (si === sDate.length - 1) {
                resetSecond()
                if (mi === mDate.length - 1) {
                  resetMin()
                  if (hi === hDate.length - 1) {
                    resetHour()
                    if (Di === DDate.length - 1) {
                      resetDay()
                      if (Mi === MDate.length - 1) {
                        resetMouth()
                        continue goYear
                      }
                      continue goMouth
                    }
                    continue goDay
                  }
                  continue goHour
                }
                continue goMin
              }
            }
          }
        }
      }
    }
  }
  if (resultArr.length === 0) {
    resultList.value = ['没有达到条件的结果！']
  } else {
    resultList.value = resultArr
    if (resultArr.length !== 5) {
      resultList.value.push('最近100年内只有上面' + resultArr.length + '条结果！')
    }
  }
  isShow.value = true
}

function getIndex(arr: number[], value: number): number {
  if (value <= arr[0] || value > arr[arr.length - 1]) {
    return 0
  }
  for (let i = 0; i < arr.length - 1; i++) {
    if (value > arr[i] && value <= arr[i + 1]) {
      return i + 1
    }
  }
  return 0
}

function getYearArr(rule: string, year: number) {
  dateArr.value[5] = getOrderArr(year, year + 100)
  if (rule !== undefined) {
    if (rule.indexOf('-') >= 0) {
      dateArr.value[5] = getCycleArr(rule, year + 100, false)
    } else if (rule.indexOf('/') >= 0) {
      dateArr.value[5] = getAverageArr(rule, year + 100)
    } else if (rule !== '*') {
      dateArr.value[5] = getAssignArr(rule)
    }
  }
}

function getMouthArr(rule: string) {
  dateArr.value[4] = getOrderArr(1, 12)
  if (rule.indexOf('-') >= 0) {
    dateArr.value[4] = getCycleArr(rule, 12, false)
  } else if (rule.indexOf('/') >= 0) {
    dateArr.value[4] = getAverageArr(rule, 12)
  } else if (rule !== '*') {
    dateArr.value[4] = getAssignArr(rule)
  }
}

function getWeekArr(rule: string) {
  if (dayRule.value === '' && dayRuleSup.value === '') {
    if (rule.indexOf('-') >= 0) {
      dayRule.value = 'weekDay'
      dayRuleSup.value = getCycleArr(rule, 7, false)
    } else if (rule.indexOf('#') >= 0) {
      dayRule.value = 'assWeek'
      const matchRule = rule.match(/[0-9]{1}/g) || []
      dayRuleSup.value = [Number(matchRule[0]), Number(matchRule[1])]
      dateArr.value[3] = [1]
      if (dayRuleSup.value[1] === 7) {
        dayRuleSup.value[1] = 0
      }
    } else if (rule.indexOf('L') >= 0) {
      dayRule.value = 'lastWeek'
      dayRuleSup.value = Number((rule.match(/[0-9]{1,2}/g) || ['0'])[0])
      dateArr.value[3] = [31]
      if (dayRuleSup.value === 7) {
        dayRuleSup.value = 0
      }
    } else if (rule !== '*' && rule !== '?') {
      dayRule.value = 'weekDay'
      dayRuleSup.value = getAssignArr(rule)
    }
    if (dayRule.value === 'weekDay') {
      for (let i = 0; i < dayRuleSup.value.length; i++) {
        if (dayRuleSup.value[i] === 7) {
          dayRuleSup.value[i] = 0
        }
      }
    }
  }
}

function getDayArr(rule: string) {
  dateArr.value[3] = getOrderArr(1, 31)
  dayRule.value = ''
  dayRuleSup.value = ''
  if (rule.indexOf('-') >= 0) {
    dateArr.value[3] = getCycleArr(rule, 31, false)
    dayRuleSup.value = 'null'
  } else if (rule.indexOf('/') >= 0) {
    dateArr.value[3] = getAverageArr(rule, 31)
    dayRuleSup.value = 'null'
  } else if (rule.indexOf('W') >= 0) {
    dayRule.value = 'workDay'
    dayRuleSup.value = Number((rule.match(/[0-9]{1,2}/g) || ['0'])[0])
    dateArr.value[3] = [dayRuleSup.value]
  } else if (rule.indexOf('L') >= 0) {
    dayRule.value = 'lastDay'
    dayRuleSup.value = 'null'
    dateArr.value[3] = [31]
  } else if (rule !== '*' && rule !== '?') {
    dateArr.value[3] = getAssignArr(rule)
    dayRuleSup.value = 'null'
  } else if (rule === '*') {
    dayRuleSup.value = 'null'
  }
}

function getHourArr(rule: string) {
  dateArr.value[2] = getOrderArr(0, 23)
  if (rule.indexOf('-') >= 0) {
    dateArr.value[2] = getCycleArr(rule, 24, true)
  } else if (rule.indexOf('/') >= 0) {
    dateArr.value[2] = getAverageArr(rule, 23)
  } else if (rule !== '*') {
    dateArr.value[2] = getAssignArr(rule)
  }
}

function getMinArr(rule: string) {
  dateArr.value[1] = getOrderArr(0, 59)
  if (rule.indexOf('-') >= 0) {
    dateArr.value[1] = getCycleArr(rule, 60, true)
  } else if (rule.indexOf('/') >= 0) {
    dateArr.value[1] = getAverageArr(rule, 59)
  } else if (rule !== '*') {
    dateArr.value[1] = getAssignArr(rule)
  }
}

function getSecondArr(rule: string) {
  dateArr.value[0] = getOrderArr(0, 59)
  if (rule.indexOf('-') >= 0) {
    dateArr.value[0] = getCycleArr(rule, 60, true)
  } else if (rule.indexOf('/') >= 0) {
    dateArr.value[0] = getAverageArr(rule, 59)
  } else if (rule !== '*') {
    dateArr.value[0] = getAssignArr(rule)
  }
}

function getOrderArr(min: number, max: number): number[] {
  const arr: number[] = []
  for (let i = min; i <= max; i++) {
    arr.push(i)
  }
  return arr
}

function getAssignArr(rule: string): number[] {
  const arr: number[] = []
  const assignArr = rule.split(',')
  for (let i = 0; i < assignArr.length; i++) {
    arr[i] = Number(assignArr[i])
  }
  arr.sort(compare)
  return arr
}

function getAverageArr(rule: string, limit: number): number[] {
  const arr: number[] = []
  const agArr = rule.split('/')
  let min = Number(agArr[0])
  const step = Number(agArr[1])
  while (min <= limit) {
    arr.push(min)
    min += step
  }
  return arr
}

function getCycleArr(rule: string, limit: number, status: boolean): number[] {
  const arr: number[] = []
  const cycleArr = rule.split('-')
  const min = Number(cycleArr[0])
  let max = Number(cycleArr[1])
  if (min > max) {
    max += limit
  }
  for (let i = min; i <= max; i++) {
    let add = 0
    if (status === false && i % limit === 0) {
      add = limit
    }
    arr.push(Math.round((i % limit) + add))
  }
  arr.sort(compare)
  return arr
}

function compare(value1: number, value2: number): number {
  if (value2 - value1 > 0) {
    return -1
  }
  return 1
}

function formatDate(value: number | Date, type?: string): any {
  const time = typeof value === 'number' ? new Date(value) : value
  const Y = time.getFullYear()
  const M = time.getMonth() + 1
  const D = time.getDate()
  const h = time.getHours()
  const m = time.getMinutes()
  const s = time.getSeconds()
  const week = time.getDay()
  if (type === undefined) {
    return (
      Y +
      '-' +
      (M < 10 ? '0' + M : M) +
      '-' +
      (D < 10 ? '0' + D : D) +
      ' ' +
      (h < 10 ? '0' + h : h) +
      ':' +
      (m < 10 ? '0' + m : m) +
      ':' +
      (s < 10 ? '0' + s : s)
    )
  } else if (type === 'week') {
    return week
  }
}

function checkDate(value: string): boolean {
  const time = new Date(value)
  const format = formatDate(time)
  return value === format
}

watch(
  () => props.ex,
  () => expressionChange()
)

onMounted(() => expressionChange())
</script>

<template>
  <div class="popup-result">
    <p class="title">最近5次运行时间</p>
    <ul class="popup-result-scroll">
      <template v-if="isShow">
        <li v-for="item in resultList" :key="item">{{ item }}</li>
      </template>
      <li v-else>计算结果中...</li>
    </ul>
  </div>
</template>

<style scoped>
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
.popup-result-scroll {
  font-size: 12px;
  line-height: 24px;
  height: 10em;
  overflow-y: auto;
  margin: 0;
  padding-left: 24px;
}
</style>
