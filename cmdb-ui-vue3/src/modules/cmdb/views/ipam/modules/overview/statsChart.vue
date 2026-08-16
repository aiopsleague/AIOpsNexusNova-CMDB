<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'

interface ChartDataItem {
  label?: string
  value?: number
  chartValue?: number
}

const props = withDefaults(
  defineProps<{
    statsData?: Record<string, any>
  }>(),
  {
    statsData: () => ({}),
  }
)

const { t } = useI18n()

const statsChartRef = ref<HTMLElement | null>(null)
let chart: echarts.EChartsType | null = null

/**
 * ECharts theme helper: the chart background stays transparent so it inherits
 * the page theme; the built-in 'dark' theme handles text/axis colors.
 */
function getEchartsTheme(): string | undefined {
  const theme = document.documentElement.getAttribute('data-theme')
  return theme === 'dark' ? 'dark' : undefined
}

function handleThemeChange() {
  if (!chart || !statsChartRef.value) return
  const option = chart.getOption()
  chart.dispose()
  chart = echarts.init(statsChartRef.value, getEchartsTheme())
  chart.setOption(option)
}

function updateChart(data: Record<string, any>) {
  const option: echarts.EChartsOption = {
    color: data?.chartColor || [],
    tooltip: {
      show: false,
    },
    legend: {
      show: false,
    },
    series: [
      {
        type: 'pie',
        radius: ['60%', '85%'],
        data:
          data?.data?.map((item: ChartDataItem) => {
            return {
              name: t(item?.label || ''),
              value: item?.chartValue ?? item.value,
            }
          }) || [],
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 1,
        },
        label: {
          show: false,
        },
      },
    ],
  }

  nextTick(() => {
    if (!chart) {
      chart = echarts.init(statsChartRef.value as HTMLElement, getEchartsTheme())
    }
    chart.setOption(option)
  })
}

watch(
  () => props.statsData,
  (data) => {
    updateChart(data)
  },
  { deep: true, immediate: true }
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
  <div class="stats-chart">
    <div ref="statsChartRef" class="stats-chart-pie"></div>
    <div class="stats-chart-ratio">
      {{ statsData.ratio }}%
    </div>
  </div>
</template>

<style lang="less" scoped>
.stats-chart {
  width: 60px;
  height: 60px;
  position: relative;

  &-pie {
    width: 100%;
    height: 100%;
  }

  &-ratio {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 2;

    font-size: 14px;
    font-weight: 700;
    color: #1D2129;
  }
}
</style>
