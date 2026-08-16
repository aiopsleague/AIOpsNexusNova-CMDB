<script setup lang="ts">
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const statistics = inject<() => Record<string, any>>('statistics', () => ({}))

const chartEl = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null
const dimension = ref(0)

function getEchartsTheme(): string | undefined {
  const theme = document.documentElement.getAttribute('data-theme')
  return theme === 'dark' ? 'dark' : undefined
}

const windowHeight = computed(() => window.innerHeight)
const domHeight = computed(() => (windowHeight.value - 570 > 300 ? windowHeight.value - 570 : 300))

function setChart() {
  const counter = statistics().business_counter
  if (!counter || !counter.detail) return
  const business = Object.keys(counter.detail) as string[]

  if (!chart) {
    chart = echarts.init(chartEl.value as HTMLElement, getEchartsTheme())
    chart.on('updateAxisPointer', (event: any) => {
      const xAxisInfo = event.axesInfo?.[0]
      if (xAxisInfo) {
        const idx = xAxisInfo.value
        dimension.value = idx
        const valueIdx = idx + 1
        chart?.setOption({
          title: {
            subtext: `${business[idx]}`,
          },
          series: {
            id: 'pie',
            label: {
              formatter: `{b}: {@[${valueIdx}]} ({d}%)`,
            },
            encode: {
              value: valueIdx,
              tooltip: valueIdx,
            },
          },
        })
      }
    })
  }

  let resourceNames: string[] = []
  business.forEach((bu) => {
    resourceNames = [...resourceNames, ...Object.keys(counter.detail[bu])]
  })
  const resourceName = [...new Set(resourceNames)]
  const source: any[] = [['resource', ...business]]
  resourceName.forEach((r) => {
    const list: any[] = [r]
    business.forEach((bu) => {
      list.push(counter.detail[bu][r] || 0)
    })
    source.push(list)
  })

  chart.setOption({
    title: {
      subtext: `${business[dimension.value]}`,
      left: '8%',
    },
    legend: {
      type: 'scroll',
      left: 'center',
      bottom: 0,
    },
    tooltip: {
      trigger: 'axis',
      showContent: false,
    },
    dataset: {
      source,
    },
    xAxis: { type: 'category' },
    yAxis: { gridIndex: 0 },
    grid: { top: '10%', left: '30%', right: 0, bottom: '15%' },
    series: [
      ...resourceName.map(() => {
        return {
          type: 'line',
          smooth: true,
          seriesLayoutBy: 'row',
          emphasis: { focus: 'series' },
        }
      }),
      {
        type: 'pie',
        id: 'pie',
        radius: '50%',
        center: ['10%', '50%'],
        emphasis: {
          focus: 'self',
        },
        label: {
          formatter: `{b}: {@${business[dimension.value]}} ({d}%)`,
        },
        encode: {
          itemName: 'resource',
          value: business[dimension.value],
          tooltip: business[dimension.value],
        },
      },
    ],
  })
}

watch(
  () => statistics().business_counter,
  (newValue) => {
    if (newValue && JSON.stringify(newValue) !== '{}') {
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

function handleThemeChange() {
  if (!chart || !chartEl.value) return
  const option = chart.getOption()
  chart.dispose()
  chart = echarts.init(chartEl.value, getEchartsTheme())
  chart.setOption(option)
}
</script>

<template>
  <div>
    <div ref="chartEl" :style="{ height: `${domHeight}px` }"></div>
  </div>
</template>

<style></style>
