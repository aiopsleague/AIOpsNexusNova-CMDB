<script setup lang="ts">
import { computed, onMounted, provide, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Modal } from 'ant-design-vue'
import {
  DeleteOutlined,
  EditOutlined,
  MenuOutlined,
  PlusCircleOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue'
import { GridLayout, GridItem } from 'grid-layout-plus'
import ChartForm from './chartForm.vue'
import Chart from './chart.vue'
import { getCustomDashboard, deleteCustomDashboard, batchUpdateCustomDashboard } from '../../api/customDashboard'
import { getCITypes } from '../../api/CIType'
import { getStatistics } from '../../api/statistics'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import CIIcon from '@/modules/cmdb/components/ciIcon/index.vue'
import emptyImage from '@/assets/data_empty.png'

withDefaults(
  defineProps<{
    editable?: boolean
  }>(),
  {
    editable: false,
  }
)

const { t } = useI18n()

const layout = ref<any[]>([])
const ciTypes = ref<any[]>([])
const totalData = ref<Record<string, any>>({})
const chartFormRef = ref<{ open: (type: 'add' | 'edit', item?: Record<string, any>) => void }>()

const windowHeight = computed(() => window.innerHeight)

// Store chart component instances keyed by dashboard item id, so they can be
// resized after the grid layout changes.
const chartRefs = new Map<number, { resizeChart: () => void }>()

function setChartRef(id: number, el: any) {
  if (el) {
    chartRefs.set(id, el)
  } else {
    chartRefs.delete(id)
  }
}

provide('layout', () => layout.value)

function isEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

async function getLayout() {
  const res = await getCustomDashboard()
  layout.value = res.map((item: any) => {
    return {
      ...item,
      i: item.id,
      x: (item.options || {}).x || 0,
      y: (item.options || {}).y || 0,
      w: (item.options || {}).w || 4,
      h: (item.options || {}).h || 5,
    }
  })
  if (layout.value && layout.value.length) {
    getStatistics().then((res1) => {
      totalData.value = res1
    })
  }
}

function openChartForm(type: 'add' | 'edit' = 'add', item: Record<string, any> = {}) {
  chartFormRef.value?.open(type, item)
}

function refresh(id?: number) {
  if (id) {
    setTimeout(() => {
      chartRefs.get(id)?.resizeChart()
    }, 100)
  } else {
    getLayout()
  }
}

function deleteChart(item: any) {
  Modal.confirm({
    title: '警告',
    content: '确认删除？',
    onOk() {
      deleteCustomDashboard(item.id).then(() => {
        getLayout()
      })
    },
  })
}

function layoutUpdatedEvent(newLayout: any[]) {
  const id2options: Record<string, any> = {}
  newLayout.forEach((item) => {
    const oldOptions = cloneDeep(item.options)
    const newOptions = { ...cloneDeep(item.options), x: item.x, y: item.y, w: item.w, h: item.h }
    if (!isEqual(oldOptions, newOptions)) {
      id2options[item.id] = newOptions
    }
  })
  if (JSON.stringify(id2options) !== '{}') {
    batchUpdateCustomDashboard({ id2options }).then(async () => {
      await getLayout()
      Object.keys(id2options).forEach((key) => {
        chartRefs.get(Number(key))?.resizeChart()
      })
    })
  }
}

function getCiType(item: any) {
  if (item.type_id || item.options?.type_ids) {
    const find = ciTypes.value.find((type) => type.id === item.type_id || type.id === item.options?.type_ids[0])
    return find || null
  }
  return null
}

onMounted(() => {
  getCITypes().then((res) => {
    ciTypes.value = res.ci_types
  })
  getLayout()
})
</script>

<template>
  <div
    :style="{
      height: `${windowHeight - 40}px`,
      overflowY: 'auto',
      overflowX: 'hidden',
      position: 'relative',
      margin: '-24px',
    }"
  >
    <template v-if="layout && layout.length">
      <div v-if="editable">
        <a-button
          :style="{ marginLeft: '22px', marginTop: '20px', backgroundColor: '#D6E9FF', boxShadow: 'none' }"
          type="primary"
          ghost
          class="ops-button-ghost"
          @click="openChartForm('add', { options: { w: 3 } })"
        >
          <template #icon><PlusCircleOutlined /></template>{{ t('cmdb.custom_dashboard.newChart') }}
        </a-button>
      </div>
      <GridLayout
        v-model:layout="layout"
        :col-num="12"
        :row-height="30"
        :is-draggable="editable"
        :is-resizable="editable"
        :is-mirrored="false"
        :margin="[22, 22]"
        @layout-updated="layoutUpdatedEvent"
      >
        <GridItem
          v-for="item in layout"
          :key="item.i"
          class="cmdb-dashboard-grid-item"
          :x="item.x"
          :y="item.y"
          :w="item.w"
          :h="item.h"
          :i="item.i"
          :style="{
            background:
              item.options.chartType === 'count'
                ? Array.isArray(item.options.bgColor)
                  ? `linear-gradient(to bottom, ${item.options.bgColor[0]} 0%, ${item.options.bgColor[1]} 100%)`
                  : item.options.bgColor
                : '#fff',
          }"
        >
          <div class="cmdb-dashboard-grid-item-title">
            <template v-if="item.options.chartType !== 'count' && item.options.showIcon && getCiType(item)">
              <CIIcon :icon="getCiType(item).icon" :title="getCiType(item).name" />
            </template>
            <span :style="{ color: item.options.chartType === 'count' ? item.options.fontColor : '#000' }">{{
              item.options.name
            }}</span>
          </div>
          <a-dropdown v-if="editable">
            <a
              class="cmdb-dashboard-grid-item-operation"
              :style="{
                color: item.options.chartType === 'count' ? item.options.fontColor : '',
              }"
              ><MenuOutlined
            /></a>
            <template #overlay>
              <a-menu>
                <a-menu-item>
                  <a @click="() => openChartForm('edit', item)"
                    ><EditOutlined style="margin-right: 5px" />{{ t('edit') }}</a
                  >
                </a-menu-item>
                <a-menu-item>
                  <a @click="deleteChart(item)"><DeleteOutlined style="margin-right: 5px" />{{ t('delete') }}</a>
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
          <Chart
            :ref="(el) => setChartRef(item.id, el)"
            :chart-id="item.id"
            :data="totalData[item.id]"
            :category="item.category"
            :options="item.options"
            :editable="editable"
            :ci-types="ciTypes"
            :type-id="item.type_id"
          />
        </GridItem>
      </GridLayout>
    </template>
    <div v-else class="dashboard-empty">
      <a-empty :image="emptyImage" description=""></a-empty>
      <a-button v-if="editable" size="small" type="primary" @click="openChartForm('add', { options: { w: 3 } })">
        <template #icon><PlusOutlined /></template>
        {{ t('cmdb.menu.customDashboard') }}
      </a-button>
      <span v-else>{{ t('cmdb.custom_dashboard.noCustomDashboard') }}</span>
    </div>
    <ChartForm ref="chartFormRef" :ci-types="ciTypes" @refresh="refresh" />
  </div>
</template>

<style lang="less" scoped>
.dashboard-empty {
  margin-top: 200px;
  text-align: center;
}
.cmdb-dashboard-grid-item {
  border-radius: 2px;
  padding: 6px 12px;
  .cmdb-dashboard-grid-item-title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 700;
    color: #000000;
  }
  .cmdb-dashboard-grid-item-operation {
    position: absolute;
    right: 12px;
    top: 6px;
  }
  .cmdb-dashboard-grid-item-chart-type {
    position: absolute;
    top: 6px;
    right: 24px;
  }
}
</style>

<style lang="less">
.cmdb-dashboard-grid-item-title {
  display: flex;
  align-items: center;
  > i {
    font-size: 16px;
    margin-right: 5px;
  }
  > img {
    width: 16px;
    margin-right: 5px;
  }
  > span:not(:last-child) {
    display: inline-block;
    width: 16px;
    height: 16px;
    line-height: 16px;
    font-size: 16px;
    text-align: center;
    margin-right: 5px;
  }
}
</style>
