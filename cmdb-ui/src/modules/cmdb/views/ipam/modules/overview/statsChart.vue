<template>
  <div class="stats-chart">
    <div
      class="stats-chart-pie"
      ref="statsChartRef"
    ></div>
    <div class="stats-chart-ratio">
      {{ statsData.ratio }}%
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { getEchartsTheme } from '@/utils/echarts-theme'

export default {
  name: 'StatsChart',
  props: {
    statsData: {
      type: Object,
      default: () => {}
    }
  },
  watch: {
    statsData: {
      deep: true,
      immediate: true,
      handler(data) {
        this.updateChart(data)
      }
    }
  },
  mounted() {
    window.addEventListener('ops:theme-change', this.handleThemeChange)
  },
  beforeDestroy() {
    window.removeEventListener('ops:theme-change', this.handleThemeChange)
    if (this.chart) {
      this.chart.dispose()
      this.chart = null
    }
  },
  methods: {
    handleThemeChange() {
      if (!this.chart || !this.$refs.statsChartRef) return
      const option = this.chart.getOption()
      this.chart.dispose()
      this.chart = echarts.init(this.$refs.statsChartRef, getEchartsTheme())
      this.chart.setOption(option)
    },
    updateChart(data) {
      const option = {
        color: data?.chartColor || [],
        tooltip: {
          show: false
        },
        legend: {
          show: false,
        },
        series: [
          {
            type: 'pie',
            radius: ['60%', '85%'],
            data: data?.data?.map((item) => {
              return {
                name: this.$t(item?.label),
                value: item?.chartValue ?? item.value
              }
            }) || [],
            itemStyle: {
              borderColor: '#fff',
              borderWidth: 1
            },
            label: {
              show: false,
            },
          }
        ]
      }

      this.$nextTick(() => {
        if (!this.chart) {
          const el = this.$refs.statsChartRef
          this.chart = echarts.init(el, getEchartsTheme())
        }
        this.chart.setOption(option)
      })
    }
  }
}
</script>

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
