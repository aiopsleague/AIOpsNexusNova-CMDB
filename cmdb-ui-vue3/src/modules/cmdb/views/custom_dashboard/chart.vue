<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { useAppStore } from '@/stores/app'
import { toThousands } from '../../utils/helper'
import {
  category_1_bar_options,
  category_1_line_options,
  category_1_pie_options,
  category_2_bar_options,
  category_2_pie_options,
} from './chartOptions'
import { getCITypeAttributesByTypeIds } from '../../api/CITypeAttr'
import CIIcon from '@/modules/cmdb/components/ciIcon/index.vue'

const props = withDefaults(
  defineProps<{
    ciTypes?: any[]
    chartId?: number
    data?: number | object | any[]
    category?: number
    options?: Record<string, any>
    editable?: boolean
    typeId?: number | number[] | null
    isPreview?: boolean
  }>(),
  {
    ciTypes: () => [],
    chartId: 0,
    data: 0,
    category: 0,
    options: () => ({}),
    editable: false,
    typeId: null,
    isPreview: false,
  }
)

const { t } = useI18n()
const appStore = useAppStore()

const containerEl = ref<HTMLElement | null>(null)
const chartEl = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const columns = ref<string[]>([])
const tableHeight = ref<string | number>('')
const tableData = ref<any[]>([])
const keyLength = ref(0)
const attributes = ref<any[]>([])
const columnName = ref<string[]>([])
const keyColumns = computed(() => Array.from({ length: keyLength.value }, (_, i) => i))

const ciType = computed(() => {
  if (props.typeId || props.options?.type_ids) {
    const find = props.ciTypes.find(
      (item) => item.id === props.typeId || item.id === props.options?.type_ids[0]
    )
    return find || null
  }
  return null
})

function getEchartsTheme(): string | undefined {
  const theme = document.documentElement.getAttribute('data-theme')
  return theme === 'dark' ? 'dark' : undefined
}

function handleThemeChange() {
  if (!chart || !chartEl.value) return
  const option = chart.getOption()
  chart.dispose()
  chart = echarts.init(chartEl.value, getEchartsTheme())
  chart.setOption(option, true)
}

function setChart() {
  if (!chart) {
    chart = echarts.init(chartEl.value as HTMLElement, getEchartsTheme())
  }
  if (props.category === 1 && props.options.chartType === 'bar') {
    chart.setOption(category_1_bar_options(props.data, props.options), true)
  }
  if (props.category === 1 && props.options.chartType === 'line') {
    chart.setOption(category_1_line_options(props.data, props.options), true)
  }
  if (props.category === 1 && props.options.chartType === 'pie') {
    chart.setOption(category_1_pie_options(props.data, props.options), true)
  }
  if (props.category === 2 && ['bar', 'line'].includes(props.options.chartType)) {
    chart.setOption(category_2_bar_options(props.data, props.options, props.options.chartType), true)
  }
  if (props.category === 2 && props.options.chartType === 'pie') {
    chart.setOption(category_2_pie_options(props.data, props.options), true)
  }
}

function resizeChart() {
  nextTick(() => {
    if (chart) {
      chart.resize()
    }
  })
}

defineExpose({ resizeChart })

function formatTableData(dataList: any[], data: any, obj: Record<string, any>) {
  Object.keys(data).forEach((k) => {
    if (typeof data[k] === 'number') {
      dataList.push({ ...obj, [`key${Object.keys(obj).length}`]: k, value: data[k] })
    } else {
      formatTableData(dataList, data[k], { ...obj, [`key${Object.keys(obj).length}`]: k })
    }
  })
}

function mergeRowMethod({ row, rowIndex, column, visibleData }: any): { rowspan: number; colspan: number } | undefined {
  const fields = ['key0', 'key1', 'key2']
  const cellValue = row[column.field]
  if (cellValue && fields.includes(column.field)) {
    const prevRow = visibleData[rowIndex - 1]
    let nextRow = visibleData[rowIndex + 1]
    if (prevRow && prevRow[column.field] === cellValue) {
      return { rowspan: 0, colspan: 0 }
    } else {
      let countRowspan = 1
      while (nextRow && nextRow[column.field] === cellValue) {
        nextRow = visibleData[++countRowspan + rowIndex]
      }
      if (countRowspan > 1) {
        return { rowspan: countRowspan, colspan: 1 }
      }
    }
  }
  return undefined
}

watch(
  () => props.data,
  (newValue) => {
    if (props.category === 1 || props.category === 2) {
      if (props.options.chartType !== 'table' && Object.prototype.toString.call(newValue) === '[object Object]') {
        if (props.isPreview) {
          nextTick(() => {
            setChart()
          })
        } else {
          setChart()
        }
      }
    }
    if (props.options.chartType === 'table') {
      nextTick(() => {
        const dom = containerEl.value
        tableHeight.value = dom ? dom.offsetHeight : ''
      })
      if (props.options.ret) {
        const excludeKeys = ['_X_ROW_KEY', 'ci_type', 'ci_type_alias', 'unique', 'unique_alias', '_id', '_type']
        if (newValue && (newValue as any[]).length) {
          columns.value = Object.keys((newValue as any[])[0]).filter((keys) => !excludeKeys.includes(keys))
          tableData.value = newValue as any[]
        }
      } else {
        getCITypeAttributesByTypeIds({ type_ids: props.options?.type_ids.join(',') }).then((res) => {
          attributes.value = res.attributes
          const dataList: any[] = []
          keyLength.value = props.options?.attr_ids?.length ?? 0
          const columnNames: string[] = []
          props.options.attr_ids.forEach((attr: number) => {
            const find = attributes.value.find((item) => item.id === attr)
            columnNames.push(find?.alias || find?.name)
          })
          columnName.value = columnNames
          formatTableData(dataList, props.data, {})
          tableData.value = dataList
        })
      }
    }
  },
  { immediate: true, deep: true }
)

watch(
  () => appStore.sidebar,
  () => {
    setTimeout(() => {
      resizeChart()
    }, 200)
  }
)

onMounted(() => {
  window.addEventListener('resize', resizeChart)
  window.addEventListener('ops:theme-change', handleThemeChange)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  window.removeEventListener('ops:theme-change', handleThemeChange)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<template>
  <div
    :id="`cmdb-dashboard-${chartId}-${editable}-${isPreview}`"
    ref="containerEl"
    :style="{ width: '100%', height: 'calc(100% - 2.2vw)' }"
  >
    <div
      v-if="options.chartType === 'count'"
      :style="{ color: options.fontColor || '#fff' }"
      class="cmdb-dashboard-grid-item-chart"
    >
      <div v-if="options.showIcon && ciType" class="cmdb-dashboard-grid-item-chart-icon">
        <CIIcon :icon="ciType.icon" :title="ciType.name" />
      </div>
      <span :style="{ ...options.fontConfig }">{{ toThousands(data as number) }}</span>
    </div>
    <vxe-table
      v-if="options.chartType === 'table'"
      :max-height="tableHeight"
      :data="tableData"
      :stripe="!!options.ret"
      size="mini"
      class="ops-stripe-table"
      :span-method="mergeRowMethod"
      :border="!options.ret"
      show-overflow
    >
      <template v-if="options.ret">
        <vxe-column v-for="col in columns" :key="col" :title="col" :field="col" show-header-overflow>
          <template #default="{ row }">
            <span>{{ row[col] }}</span>
          </template>
        </vxe-column>
      </template>
      <template v-else>
        <vxe-column
          v-for="index in keyColumns"
          :key="`key${index}`"
          :title="columnName[index]"
          :field="`key${index}`"
          show-header-overflow
        >
          <template #default="{ row }">
            <span>{{ row[`key${index}`] }}</span>
          </template>
        </vxe-column>
        <vxe-column field="value" :title="t('cmdb.custom_dashboard.quantity')" show-header-overflow></vxe-column>
      </template>
    </vxe-table>
    <div
      v-else-if="category === 1 || category === 2"
      :id="`cmdb-dashboard-${chartId}-${editable}`"
      ref="chartEl"
      class="cmdb-dashboard-grid-item-chart"
    ></div>
  </div>
</template>

<style lang="less" scoped>
.cmdb-dashboard-grid-item-chart {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  > span {
    font-size: 50px;
    font-weight: 700;
  }
  .cmdb-dashboard-grid-item-chart-icon {
    > i {
      font-size: 40px;
    }
    > img {
      width: 40px;
    }
    > span {
      display: inline-block;
      width: 40px;
      height: 40px;
      font-size: 50px;
      text-align: center;
      line-height: 50px;
    }
  }
}
</style>
