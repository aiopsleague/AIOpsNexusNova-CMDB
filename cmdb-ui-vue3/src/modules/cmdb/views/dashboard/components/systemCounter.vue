<script setup lang="ts">
import { inject, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const statistics = inject<() => Record<string, any>>('statistics', () => ({}))

const chartEl = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

function getEchartsTheme(): string | undefined {
  const theme = document.documentElement.getAttribute('data-theme')
  return theme === 'dark' ? 'dark' : undefined
}

const systemCounter = ref<Record<string, number>>({})

function handleThemeChange() {
  if (!chart || !chartEl.value) return
  const option = chart.getOption()
  chart.dispose()
  chart = echarts.init(chartEl.value, getEchartsTheme())
  chart.setOption(option)
}

function setChart() {
  if (!chart) {
    chart = echarts.init(chartEl.value as HTMLElement, getEchartsTheme())
  }
  const sum = Object.values(systemCounter.value).reduce((prev, curr) => prev + curr, 0)
  chart.setOption({
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
        name: 'Access From',
        type: 'pie',
        radius: '80%',
        data: Object.keys(systemCounter.value).map((item) => {
          return {
            value: systemCounter.value[item],
            name: item,
            label: {
              position: systemCounter.value[item] / sum < 0.2 ? 'outside' : 'inside',
              formatter: '{b}: {c}',
            },
          }
        }),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  })
}

watch(
  () => statistics().system_counter,
  (newValue) => {
    if (newValue && JSON.stringify(newValue) !== '{}') {
      systemCounter.value = newValue
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
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<template>
  <div ref="chartEl" :style="{ height: '300px' }"></div>
</template>

<style></style>
