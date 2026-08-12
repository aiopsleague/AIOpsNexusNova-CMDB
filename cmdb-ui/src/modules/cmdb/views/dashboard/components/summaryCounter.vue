<template>
  <a-row>
    <a-col :span="14">
      <div id="summary-counter-left" :style="{ height: '300px' }"></div>
    </a-col>
    <a-col :span="10">
      <div id="summary-counter-right" :style="{ height: '300px' }"></div>
    </a-col>
  </a-row>
</template>

<script>
import * as echarts from 'echarts'
import { getEchartsTheme } from '@/utils/echarts-theme'
export default {
  name: 'SummaryCounter',
  inject: ['statistics'],
  data() {
    return {
      chart1: null,
      chart2: null,
    }
  },
  computed: {
    summary_counter() {
      return this.statistics().summary_counter
    },
  },
  watch: {
    summary_counter: {
      immediate: true,
      deep: true,
      handler(newValue) {
        if (newValue && newValue.length) {
          this.setChart()
        }
      },
    },
  },
  mounted() {
    window.addEventListener('ops:theme-change', this.handleThemeChange)
  },
  beforeDestroy() {
    window.removeEventListener('ops:theme-change', this.handleThemeChange)
    if (this.chart1) {
      this.chart1.dispose()
      this.chart1 = null
    }
    if (this.chart2) {
      this.chart2.dispose()
      this.chart2 = null
    }
  },
  methods: {
    handleThemeChange() {
      const el1 = document.getElementById('summary-counter-left')
      const el2 = document.getElementById('summary-counter-right')
      if (this.chart1 && el1) {
        const option = this.chart1.getOption()
        this.chart1.dispose()
        this.chart1 = echarts.init(el1, getEchartsTheme())
        this.chart1.setOption(option)
      }
      if (this.chart2 && el2) {
        const option = this.chart2.getOption()
        this.chart2.dispose()
        this.chart2 = echarts.init(el2, getEchartsTheme())
        this.chart2.setOption(option)
      }
    },
    setChart() {
      if (!this.chart1) {
        this.chart1 = echarts.init(document.getElementById('summary-counter-left'), getEchartsTheme())
      }
      if (!this.chart2) {
        this.chart2 = echarts.init(document.getElementById('summary-counter-right'), getEchartsTheme())
      }
      this.chart1.setOption({
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
          data: this.summary_counter.map((item) => item[0]),
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
            data: this.summary_counter.map((item) => item[1]),
            type: 'bar',
          },
        ],
      })
      this.chart2.setOption({
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
            data: this.summary_counter
              .filter((item) => item[1])
              .map((item) => {
                return { value: item[1], name: item[0] }
              }),
          },
        ],
      })
    },
  },
}
</script>

<style></style>
