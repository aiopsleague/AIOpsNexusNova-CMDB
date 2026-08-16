<script setup lang="ts">
import { inject, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const statistics = inject<() => Record<string, any>>('statistics', () => ({}))

const leftEl = ref<HTMLElement | null>(null)
const rightEl = ref<HTMLElement | null>(null)
let chart1: echarts.ECharts | null = null
let chart2: echarts.ECharts | null = null

function getEchartsTheme(): string | undefined {
  const theme = document.documentElement.getAttribute('data-theme')
  return theme === 'dark' ? 'dark' : undefined
}

const summaryCounter = ref<Array<[string, number]>>([])

function handleThemeChange() {
  if (chart1 && leftEl.value) {
    const option = chart1.getOption()
    chart1.dispose()
    chart1 = echarts.init(leftEl.value, getEchartsTheme())
    chart1.setOption(option)
  }
  if (chart2 && rightEl.value) {
    const option = chart2.getOption()
    chart2.dispose()
    chart2 = echarts.init(rightEl.value, getEchartsTheme())
    chart2.setOption(option)
  }
}

function setChart() {
  if (!chart1) {
    chart1 = echarts.init(leftEl.value as HTMLElement, getEchartsTheme())
  }
  if (!chart2) {
    chart2 = echarts.init(rightEl.value as HTMLElement, getEchartsTheme())
  }
  chart1.setOption({
    color: '#3ba1ff',
    grid: {
      left: 0,
      right: 0,
      top: 50,
      bottom: 0,
      containLabel: true,
    },
    tooltip: {
      trigger: 'item',
    },
    xAxis: {
      type: 'category',
      data: summaryCounter.value.map((item) => item[0]),
      axisLabel: {
        fontSize: 10,
      },
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: false,
      },
    },
    series: [
      {
        data: summaryCounter.value.map((item) => item[1]),
        type: 'bar',
      },
    ],
  })
  chart2.setOption({
    grid: {
      left: 0,
      right: 0,
      top: 50,
      bottom: 0,
      containLabel: true,
    },
    tooltip: {
      trigger: 'item',
    },
    series: [
      {
        type: 'funnel',
        width: '80%',
        height: '90%',
        left: '20%',
        top: '10%',
        sort: 'ascending',
        label: {
          position: 'left',
        },
        data: summaryCounter.value
          .filter((item) => item[1])
          .map((item) => {
            return { value: item[1], name: item[0] }
          }),
      },
    ],
  })
}

watch(
  () => statistics().summary_counter,
  (newValue) => {
    if (newValue && newValue.length) {
      summaryCounter.value = newValue
      setChart()
    }
  },
  { immediate: true, deep: true }
)

onMounted(() => {
  window.addEventListener('ops:theme-change', handleThemeChange)
})

onBeforeUnmount(() => {
  window.removeEventListener('ops:theme-change', handleThemeChange)
  if (chart1) {
    chart1.dispose()
    chart1 = null
  }
  if (chart2) {
    chart2.dispose()
    chart2 = null
  }
})
</script>

<template>
  <a-row>
    <a-col :span="14">
      <div ref="leftEl" :style="{ height: '300px' }"></div>
    </a-col>
    <a-col :span="10">
      <div ref="rightEl" :style="{ height: '300px' }"></div>
    </a-col>
  </a-row>
</template>

<style></style>
