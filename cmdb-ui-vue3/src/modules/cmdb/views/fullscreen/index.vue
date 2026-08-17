<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import AssetsCard from './assetsCard.vue'
import ProcessLine from './processLine.vue'

const assetsList = [
  {
    name: '硬盘',
    image: 'harddisk',
    list: [
      { first: '大小', second: '个数' },
      { first: '200', second: '10' },
      { first: '100', second: '20' },
      { first: '50', second: '30' },
    ],
    unit: 'G',
  },
  {
    name: '网卡',
    image: 'netcard',
    list: [
      { first: '速率', second: '个数' },
      { first: '200', second: '10' },
      { first: '100', second: '20' },
      { first: '50', second: '30' },
    ],
    unit: 'M',
  },
  {
    name: '虚拟机',
    image: 'virtual',
    list: [
      { first: '系统', second: '个数' },
      { first: 'Febra', second: '10' },
      { first: 'Windows', second: '20' },
      { first: 'Cimax', second: '30' },
    ],
    unit: '',
  },
  {
    name: '内存',
    image: 'memory',
    list: [
      { first: '大小', second: '个数' },
      { first: '80', second: '10' },
      { first: '40', second: '20' },
      { first: '20', second: '30' },
    ],
    unit: 'G',
  },
]

const applicationList = [
  { name: 'IQ', number: 50 },
  { name: 'Service', number: 25 },
  { name: 'Disk', number: 25 },
]

const businessList = [
  { name: 'IT1', number: 50 },
  { name: 'IT2', number: 100 },
  { name: 'IT3', number: 150 },
]

const resourceServerList = [
  { name: 'IT1', core_2: 3, core_4: 6, core_8: 4 },
  { name: 'IT2', core_2: 6, core_4: 4, core_8: 3 },
  { name: 'IT3', core_2: 4, core_4: 3, core_8: 6 },
]

const resourceProductList = [
  { name: 'IT1', data: { IQ: 5, Service: 3 } },
  { name: 'IT2', data: { IQ: 2, Service: 3 } },
  { name: 'IT3', data: { IQ: 2, Service: 4 } },
]

const maxResourceProduct = 5

const isFullscreen = ref(false)

let chart1: echarts.ECharts | null = null
let chart2: echarts.ECharts | null = null

const applicationTotal = applicationList.reduce((prev, item) => prev + item.number, 0)
const businessTotal = businessList.reduce((prev, item) => prev + item.number, 0)

function getEchartsTheme(): string | undefined {
  const theme = document.documentElement.getAttribute('data-theme')
  return theme === 'dark' ? 'dark' : undefined
}

function handleThemeChange() {
  const el1 = document.getElementById('pie-box')
  const el2 = document.getElementById('line-box')
  if (chart1 && el1) {
    const option = chart1.getOption()
    chart1.dispose()
    chart1 = echarts.init(el1, getEchartsTheme())
    chart1.setOption(option)
  }
  if (chart2 && el2) {
    const option = chart2.getOption()
    chart2.dispose()
    chart2 = echarts.init(el2, getEchartsTheme())
    chart2.setOption(option)
  }
}

function handleFullscreen() {
  const element = document.documentElement
  if (isFullscreen.value) {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    } else if ((document as any).webkitCancelFullScreen) {
      ;(document as any).webkitCancelFullScreen()
    } else if ((document as any).mozCancelFullScreen) {
      ;(document as any).mozCancelFullScreen()
    } else if ((document as any).msExitFullscreen) {
      ;(document as any).msExitFullscreen()
    }
  } else {
    if (element.requestFullscreen) {
      element.requestFullscreen()
    } else if ((element as any).webkitRequestFullScreen) {
      ;(element as any).webkitRequestFullScreen()
    } else if ((element as any).mozRequestFullScreen) {
      ;(element as any).mozRequestFullScreen()
    } else if ((element as any).msRequestFullscreen) {
      ;(element as any).msRequestFullscreen()
    }
  }
  isFullscreen.value = !isFullscreen.value
}

function resizeChart() {
  nextTick(() => {
    if (chart1) {
      chart1.resize()
    }
    if (chart2) {
      chart2.resize()
    }
  })
}

function calculateEchart(number = 12) {
  return Math.round((number * window.innerWidth) / 1912)
}

onMounted(() => {
  window.addEventListener('ops:theme-change', handleThemeChange)
  nextTick(() => {
    handleFullscreen()
    chart1 = echarts.init(document.getElementById('pie-box') as HTMLElement, getEchartsTheme())
    chart2 = echarts.init(document.getElementById('line-box') as HTMLElement, getEchartsTheme())

    chart1.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
      },
      legend: {
        show: false,
        top: '5%',
        left: 'center',
      },
      grid: {
        top: 0,
        right: 0,
        bottom: 0,
        left: 0,
      },
      series: [
        {
          name: 'Access From',
          type: 'pie',
          radius: ['50%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 0,
            borderColor: 'rgba(0, 45, 77, 1)',
            borderWidth: 2,
          },
          label: {
            show: true,
            color: '#fff',
            fontSize: calculateEchart(12),
          },
          emphasis: {},
          labelLine: {
            show: true,
          },
          data: [
            { value: 1048, name: '鲁证期货', itemStyle: { color: 'rgba(0, 128, 255, 1)' } },
            { value: 735, name: '光大期货', itemStyle: { color: 'rgba(0, 249, 255, 1)' } },
            { value: 580, name: '中泰期货', itemStyle: { color: 'rgba(255, 246, 124, 1)' } },
          ],
        },
      ],
    })
    chart2.setOption({
      grid: {
        top: '20%',
        right: '10%',
        bottom: '10%',
        left: '8%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
        axisLabel: {
          show: false,
        },
        axisTick: {
          show: false,
        },
      },
      yAxis: {
        type: 'value',
        splitLine: {
          show: false,
        },
        axisLine: {
          show: false,
        },
        axisLabel: {
          color: '#8FABBF',
          fontSize: calculateEchart(12),
        },
      },
      legend: {
        data: ['2021', '2022'],
        right: 0,
        top: '10%',
        textStyle: {
          color: 'rgba(255, 255, 255, 0.8)',
          fontSize: calculateEchart(12),
        },
        itemWidth: calculateEchart(25),
        itemHeight: calculateEchart(14),
      },
      series: [
        {
          name: '2021',
          data: [150, 230, 224, 218, 135, 147, 260, 200, 200, 300, 100, 225],
          type: 'line',
          symbol: 'circle',
          symbolSize: calculateEchart(5),
          lineStyle: {
            color: 'rgba(68,176,255,1)',
          },
          itemStyle: {
            color: 'rgba(144,202,255,1)',
          },
          areaStyle: {
            opacity: 0.8,
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: 'rgb(75, 100, 233)',
                },
                {
                  offset: 1,
                  color: 'rgb(0, 170, 181)',
                },
              ],
              global: false,
            },
          },
        },
        {
          name: '2022',
          data: [20, 200, 300, 100, 225, 169, 157, 150, 230, 224, 218, 135],
          type: 'line',
          symbol: 'circle',
          symbolSize: calculateEchart(5),
          lineStyle: {
            color: 'rgba(147,255,216,1)',
          },
          itemStyle: {
            color: 'rgba(128,255,249,1)',
          },
          areaStyle: {
            opacity: 0.8,
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: 'rgb(39,255,203)',
                },
                {
                  offset: 1,
                  color: 'rgb(3,71,128)',
                },
              ],
              global: false,
            },
          },
        },
      ],
    })
    window.addEventListener('resize', resizeChart)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
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
  <!-- eslint-disable vue/attributes-order -->
  <div class="cmdb-fullscreen">
    <div class="cmdb-fullscreen-left">
      <div class="cmdb-fullscreen-wrapper short-title">
        <span class="title" :style="{ left: '2.2em' }">券商部署</span>
        <div id="pie-box" class="pie-box"></div>
      </div>
      <div class="cmdb-fullscreen-wrapper short-title">
        <span class="title" :style="{ left: '1.6em' }">服务器上架</span>
        <div id="line-box" class="line-box"></div>
      </div>
      <div class="cmdb-fullscreen-wrapper long-title">
        <span class="title" :style="{ left: '1.5em' }">应用占服务器个数</span>
        <div class="line-wrapper-application">
          <ProcessLine
            v-for="item in applicationList"
            :key="item.name"
            :total="applicationTotal"
            :number="item.number"
            :name="item.name"
            type="application"
          />
        </div>
      </div>
      <div class="cmdb-fullscreen-wrapper long-title">
        <span class="title" :style="{ left: '1em' }">事业部占服务器个数</span>
        <div class="line-wrapper-businesss">
          <ProcessLine
            v-for="item in businessList"
            :key="item.name"
            :total="businessTotal"
            :number="item.number"
            :name="item.name"
            type="business"
          />
        </div>
      </div>
    </div>
    <div class="cmdb-fullscreen-right">
      <div class="cmdb-fullscreen-right-bottom">
        <div class="cmdb-fullscreen-wrapper first long-wrapper">
          <span class="title" :style="{ left: '2.2em' }">公司资产</span>
          <AssetsCard v-for="item in assetsList" :key="item.name">
            <template #image1>
              <img :src="`../../assets/fullscreen/assets_${item.image}_top.png`" />
            </template>
            <template #image2>
              <img :src="`../../assets/fullscreen/assets_${item.image}_bottom.png`" />
            </template>
            <template #name>
              <span>{{ item.name }}</span>
            </template>
            <template #data>
              <div class="assets-card-right-data">
                <div class="assets-card-right-data-content" v-for="(data, index) in item.list" :key="`data_${index}`">
                  <span
                    >{{ data.first }}<span v-if="item.unit && index" class="unit">{{ item.unit }}</span></span
                  >
                  <span>{{ data.second }}</span>
                </div>
              </div>
            </template>
          </AssetsCard>
        </div>
        <div class="cmdb-fullscreen-wrapper second short-title">
          <span class="title" :style="{ left: '2.8em' }">资源配置</span>
          <div class="resource">
            <div class="resource-server">
              <div class="inner-box">
                <div v-for="item in resourceServerList" :key="item.name">
                  <div class="inner-box-bar">
                    <div class="inner-box-bar-inner">
                      <div
                        class="inner-box-bar-core core_8"
                        :style="{
                          height: `${(item.core_8 * 100) / (item.core_2 + item.core_4 + item.core_8)}%`,
                        }"
                      ></div>
                      <div
                        class="inner-box-bar-core core_4"
                        :style="{
                          height: `${(item.core_4 * 100) / (item.core_2 + item.core_4 + item.core_8)}%`,
                        }"
                      ></div>
                      <div
                        class="inner-box-bar-core core_2"
                        :style="{
                          height: `${(item.core_2 * 100) / (item.core_2 + item.core_4 + item.core_8)}%`,
                        }"
                      ></div>
                    </div>
                  </div>
                  <div class="inner-subtitle">{{ item.name }}</div>
                </div>
                <div class="inner-box-legend">
                  <div class="inner-subtitle legend core_8">8核</div>
                  <div class="inner-subtitle legend core_4">4核</div>
                  <div class="inner-subtitle legend core_2">2核</div>
                </div>
              </div>
              <div class="inner-title">服务器 按事业部分类</div>
            </div>
            <div class="resource-product">
              <div class="inner-box">
                <div class="inner-box-product" v-for="item in resourceProductList" :key="item.name">
                  <div class="inner-box-cylinder">
                    <div
                      v-for="product in Object.keys(item.data)"
                      :key="product"
                      :class="`inner-box-cylinder-${product}`"
                      :style="{
                        '--custom-height': `${((item.data as Record<string, number>)[`${product}`] * 100) / maxResourceProduct}%`,
                      }"
                    >
                      <div class="inner-box-cylinder-dot"><img src="../../assets/fullscreen/resource_dot.png" /></div>
                    </div>
                  </div>
                  <div class="inner-subtitle">{{ item.name }}</div>
                </div>
                <div class="inner-box-legend">
                  <div class="inner-subtitle product-legend IQ">IQ</div>
                  <div class="inner-subtitle product-legend Service">Service</div>
                </div>
              </div>
              <div class="inner-title">产品 按事业部分类</div>
            </div>
          </div>
        </div>
      </div>
      <div class="cmdb-fullscreen-total">
        <span>全区总台数</span>
        <span
          class="cmdb-fullscreen-total-number"
          v-for="(number, index) in [0, 0, 2, 1, 0]"
          :key="`${number}_${index}`"
        >
          {{ number }}
        </span>
      </div>
      <div class="cmdb-fullscreen-server">
        <img :style="{ width: '1.3125em', height: '2.875em' }" src="../../assets/fullscreen/server_icon.png" />
        <span>服务器数目</span>
        <div class="cmdb-fullscreen-server-outer">
          <div class="cmdb-fullscreen-server-inner"><span>100</span><br /><span>中国</span></div>
          <div class="cmdb-fullscreen-server-inner"><span>50</span><br /><span>印度</span></div>
          <div class="cmdb-fullscreen-server-inner"><span>20</span><br /><span>新加坡</span></div>
          <div class="cmdb-fullscreen-server-inner"><span>20</span><br /><span>美国</span></div>
          <div class="cmdb-fullscreen-server-inner"><span>20</span><br /><span>德国</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
@import './index.less';
</style>
