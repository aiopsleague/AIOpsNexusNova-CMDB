<script setup lang="ts">
import { computed, inject, nextTick, reactive, ref, type Component } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  BarChartOutlined,
  LineChartOutlined,
  NumberOutlined,
  PieChartOutlined,
  PlayCircleOutlined,
  TableOutlined,
} from '@ant-design/icons-vue'
import Chart from './chart.vue'
import { dashboardCategory } from './constant'
import { postCustomDashboard, putCustomDashboard, postCustomDashboardPreview } from '@/modules/cmdb/api/customDashboard'
import { getCITypeAttributesByTypeIds, getCITypeCommonAttributesByTypeIds } from '@/modules/cmdb/api/CITypeAttr'
import { getRecursive_level2children } from '@/modules/cmdb/api/CITypeRelation'
import { getCITypeGroupsConfig } from '@/modules/cmdb/api/ciTypeGroup'
import { getLastLayout } from '@/modules/cmdb/utils/helper'
import FilterComp from '@/components/CMDBFilterComp/index.vue'
import ColorPicker from './colorPicker.vue'
import ColorListPicker from './colorListPicker.vue'
import CMDBTypeSelectAntd from '@/modules/cmdb/components/cmdbTypeSelect/cmdbTypeSelectAntd.vue'
import CIIcon from '@/modules/cmdb/components/ciIcon/index.vue'

const props = withDefaults(
  defineProps<{
    ciTypes?: any[]
  }>(),
  {
    ciTypes: () => [],
  }
)

const emit = defineEmits<{ (e: 'refresh', id?: number): void }>()

const { t } = useI18n()

const layout = inject<() => any[]>('layout', () => [])

const formRef = ref<{ validate: () => Promise<any>; clearValidate: () => void }>()
const filterCompRef = ref<{ visibleChange: (open: boolean, isInitOne?: boolean) => void; handleSubmit: () => void }>()

const visible = ref(false)
const attributes = ref<any[]>([])
const type = ref<'add' | 'edit'>('add')

interface DashboardForm {
  category: number
  tableCategory: number
  name?: string
  type_id?: number
  type_ids?: number[]
  attr_ids?: number[]
  level?: number
  showIcon: boolean
}

const form = reactive<DashboardForm>({
  category: 0,
  tableCategory: 1,
  name: undefined,
  type_id: undefined,
  type_ids: undefined,
  attr_ids: undefined,
  level: undefined,
  showIcon: false,
})

const rules = {
  category: [{ required: true, trigger: 'change' }],
  name: [{ required: true, message: t('cmdb.custom_dashboard.titleTips') }],
  type_id: [{ required: true, message: t('cmdb.ciType.selectCIType'), trigger: 'change' }],
  type_ids: [{ required: true, message: t('cmdb.ciType.selectCIType'), trigger: 'change' }],
  attr_ids: [{ required: true, message: t('cmdb.ciType.selectCITypeAttributes'), trigger: 'change' }],
  level: [{ required: true, message: t('cmdb.custom_dashboard.levelTips') }],
  showIcon: [{ required: false }],
}

const item = ref<Record<string, any>>({})
const chartType = ref('count') // table, bar, line, pie, count
const width = ref(3)
const fontColor = ref('#ffffff')
const bgColor = ref<string | string[]>(['#6ABFFE', '#5375EB'])
const chartColor = ref('#5DADF2,#86DFB7,#5A6F96,#7BD5FF,#FFB980,#4D58D6,#D9B6E9,#8054FF')
const isShowPreview = ref(false)
const filterExp = ref<string | undefined>(undefined)
const previewData = ref<any>(null)
const barStack = ref('total')
const barDirection = ref('y')
const commonAttributes = ref<any[]>([])
const level2children = ref<Record<string, any[]>>({})
const isShadow = ref(false)
const changeCITypeRequestValue = ref<any>(null)
const CITypeGroup = ref<any[]>([])

const ciType = computed(() => {
  if (form.type_id || form.type_ids) {
    const find = props.ciTypes.find((ci) => ci.id === form.type_id || ci.id === form.type_ids?.[0])
    return find || null
  }
  return null
})

const chartTypeList = computed(() => [
  { value: 'count', label: t('cmdb.custom_dashboard.count') },
  { value: 'bar', label: t('cmdb.custom_dashboard.bar') },
  { value: 'line', label: t('cmdb.custom_dashboard.line') },
  { value: 'pie', label: t('cmdb.custom_dashboard.pie') },
  { value: 'table', label: t('cmdb.custom_dashboard.table') },
])

const categoryOptions = computed(() => dashboardCategory())

const chartTypeIcons: Record<string, Component> = {
  count: NumberOutlined,
  bar: BarChartOutlined,
  line: LineChartOutlined,
  pie: PieChartOutlined,
  table: TableOutlined,
}

async function open(openType: 'add' | 'edit', editItem: Record<string, any> = {}) {
  visible.value = true
  type.value = openType
  item.value = editItem
  const { category = 0, name, type_id, level } = editItem
  const options = (editItem.options || {}) as Record<string, any>
  const chartTypeValue = options.chartType || 'count'
  const fontColorValue = options.fontColor || '#ffffff'
  const bgColorValue = options.bgColor || ['#6ABFFE', '#5375EB']
  const widthValue = options.w
  const showIconValue = options.showIcon
  const typeIds = options.type_ids || []
  const attrIds = options.attr_ids || []
  const ret = options.ret || ''
  width.value = widthValue
  chartType.value = chartTypeValue
  filterExp.value = options.filter ?? ''
  chartColor.value = options.chartColor ?? '#5DADF2,#86DFB7,#5A6F96,#7BD5FF,#FFB980,#4D58D6,#D9B6E9,#8054FF'
  isShadow.value = options.isShadow ?? false

  if (chartTypeValue === 'count') {
    fontColor.value = fontColorValue
    bgColor.value = bgColorValue
  }

  if (typeIds?.length || type_id) {
    const requireTypeIds = type_id ? [type_id] : typeIds
    const res = await getCITypeAttributesByTypeIds({ type_ids: requireTypeIds.join(',') })
    attributes.value = res.attributes
  }

  if (typeIds && typeIds.length) {
    const res = await getCITypeAttributesByTypeIds({ type_ids: typeIds.join(',') })
    attributes.value = res.attributes
    if ((['bar', 'line', 'pie'].includes(chartTypeValue) && category === 1) || chartTypeValue === 'table') {
      barDirection.value = options.barDirection ?? 'y'
      barStack.value = options.barStack ?? 'total'
      const commonRes = await getCITypeCommonAttributesByTypeIds({ type_ids: typeIds.join(',') })
      commonAttributes.value = commonRes.attributes
    }
  }
  if (type_id) {
    getRecursive_level2children(type_id).then((res) => {
      level2children.value = res
    })
    const commonRes = await getCITypeCommonAttributesByTypeIds({ type_ids: type_id })
    commonAttributes.value = commonRes.attributes
  }
  nextTick(() => {
    filterCompRef.value?.visibleChange(true, false)
  })
  const defaultForm: DashboardForm = {
    category: 0,
    name: undefined,
    type_id: undefined,
    type_ids: undefined,
    attr_ids: undefined,
    level: undefined,
    showIcon: false,
    tableCategory: 1,
  }
  Object.assign(form, defaultForm, {
    category,
    name,
    type_id,
    type_ids: typeIds,
    attr_ids: attrIds,
    level,
    showIcon: showIconValue,
    tableCategory: ret === 'cis' ? 2 : 1,
  })
  getCITypeGroup()
}

function handleclose() {
  attributes.value = []
  formRef.value?.clearValidate()
  isShowPreview.value = false
  visible.value = false
}

async function getCITypeGroup() {
  CITypeGroup.value = await getCITypeGroupsConfig({ need_other: true })
}

function changeCIType(value: any) {
  form.attr_ids = []
  commonAttributes.value = []
  changeCITypeRequestValue.value = value
  if ((Array.isArray(value) && value.length) || (!Array.isArray(value) && value)) {
    getCITypeAttributesByTypeIds({ type_ids: Array.isArray(value) ? value.join(',') : value }).then((res) => {
      if (changeCITypeRequestValue.value === value) {
        attributes.value = res.attributes
      }
    })
  }
  if (!Array.isArray(value) && value) {
    getRecursive_level2children(value).then((res) => {
      if (changeCITypeRequestValue.value === value) {
        level2children.value = res
      }
    })
  }
  if ((['bar', 'line', 'pie'].includes(chartType.value) && form.category === 1) || chartType.value === 'table') {
    getCITypeCommonAttributesByTypeIds({ type_ids: Array.isArray(value) ? value.join(',') : value }).then((res) => {
      if (changeCITypeRequestValue.value === value) {
        commonAttributes.value = res.attributes
      }
    })
  }
}

async function handleok() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  const name = form.name
  const currentChartType = chartType.value
  const currentFontColor = fontColor.value
  const currentBgColor = bgColor.value
  filterCompRef.value?.handleSubmit()
  if (item.value.id) {
    const params: Record<string, any> = {
      ...form,
      options: {
        ...item.value.options,
        name,
        w: width.value,
        chartType: chartType.value,
        showIcon: form.showIcon,
        type_ids: form.type_ids,
        filter: filterExp.value,
        isShadow: isShadow.value,
      },
    }
    if (currentChartType === 'count') {
      params.options.fontColor = currentFontColor
      params.options.bgColor = currentBgColor
    }
    if (['bar', 'line', 'pie'].includes(currentChartType)) {
      if (form.category === 1) {
        params.options.attr_ids = form.attr_ids
      }
      params.options.chartColor = chartColor.value
    }
    if (currentChartType === 'bar') {
      params.options.barDirection = barDirection.value
      params.options.barStack = barStack.value
    }
    if (currentChartType === 'table') {
      params.options.attr_ids = form.attr_ids
      if (form.tableCategory === 2) {
        params.options.ret = 'cis'
      }
    }
    delete params.showIcon
    delete params.type_ids
    delete params.attr_ids
    delete params.tableCategory
    await putCustomDashboard(item.value.id, params)
    emit('refresh', item.value.id)
  } else {
    const { xLast, yLast, wLast } = getLastLayout(layout())
    const w = width.value
    const x = xLast + wLast + w > 12 ? 0 : xLast + wLast
    const y = xLast + wLast + w > 12 ? yLast + 1 : yLast
    const params: Record<string, any> = {
      ...form,
      options: {
        x,
        y,
        w,
        h: form.category === 0 ? 3 : 5,
        name,
        chartType: chartType.value,
        showIcon: form.showIcon,
        type_ids: form.type_ids,
        filter: filterExp.value,
        isShadow: isShadow.value,
      },
    }
    if (currentChartType === 'count') {
      params.options.fontColor = currentFontColor
      params.options.bgColor = currentBgColor
    }
    if (['bar', 'line', 'pie'].includes(currentChartType)) {
      if (form.category === 1) {
        params.options.attr_ids = form.attr_ids
      }
      params.options.chartColor = chartColor.value
    }
    if (currentChartType === 'bar') {
      params.options.barDirection = barDirection.value
      params.options.barStack = barStack.value
    }
    if (currentChartType === 'table') {
      params.options.attr_ids = form.attr_ids
      if (form.tableCategory === 2) {
        params.options.ret = 'cis'
      }
    }
    delete params.showIcon
    delete params.type_ids
    delete params.attr_ids
    delete params.tableCategory
    await postCustomDashboard(params)
  }
  handleclose()
  emit('refresh')
}

function changeChartType(chartTypeItem: { value: string }) {
  if (!(['bar', 'line', 'pie'].includes(chartType.value) && ['bar', 'line', 'pie'].includes(chartTypeItem.value))) {
    resetForm()
  }
  chartType.value = chartTypeItem.value
  isShowPreview.value = false
  if (chartTypeItem.value === 'count') {
    form.category = 0
  } else {
    form.category = 1
  }
}

async function showPreview() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  isShowPreview.value = false
  const name = form.name
  const currentChartType = chartType.value
  const currentFontColor = fontColor.value
  const currentBgColor = bgColor.value
  filterCompRef.value?.handleSubmit()
  const params: Record<string, any> = {
    ...form,
    options: {
      name,
      chartType: currentChartType,
      showIcon: form.showIcon,
      type_ids: form.type_ids,
      filter: filterExp.value,
      isShadow: isShadow.value,
    },
  }
  if (currentChartType === 'count') {
    params.options.fontColor = currentFontColor
    params.options.bgColor = currentBgColor
  }
  if (['bar', 'line', 'pie'].includes(currentChartType)) {
    if (form.category === 1) {
      params.options.attr_ids = form.attr_ids
    }
    params.options.chartColor = chartColor.value
  }
  if (currentChartType === 'bar') {
    params.options.barDirection = barDirection.value
    params.options.barStack = barStack.value
  }
  if (currentChartType === 'table') {
    params.options.attr_ids = form.attr_ids
    if (form.tableCategory === 2) {
      params.options.ret = 'cis'
    }
  }
  delete params.showIcon
  delete params.type_ids
  delete params.attr_ids
  delete params.tableCategory
  postCustomDashboardPreview(params).then((res) => {
    isShowPreview.value = true
    previewData.value = res.counter
  })
}

function setExpFromFilter(filterExpValue: string) {
  if (filterExpValue) {
    filterExp.value = `${filterExpValue}`
  } else {
    filterExp.value = undefined
  }
}

function resetForm() {
  form.type_id = undefined
  form.type_ids = []
  form.attr_ids = []
  formRef.value?.clearValidate()
}

function changeAttr(value: number[]) {
  if (value && value.length) {
    if (['line', 'pie'].includes(chartType.value)) {
      form.attr_ids = [value[value.length - 1]]
    }
    if (chartType.value === 'bar' && value.length > 2) {
      form.attr_ids = value.slice(value.length - 2, value.length)
    }
    if (chartType.value === 'table' && value.length > 3) {
      form.attr_ids = value.slice(value.length - 3, value.length)
    }
  }
}

function clickLevel2children(citype: any, level: number) {
  if (form.level !== level) {
    nextTick(() => {
      form.type_ids = [citype.id]
    })
  }
  form.level = level
}

defineExpose({ open })
</script>

<template>
  <a-modal
    v-model:open="visible"
    width="1200px"
    :title="`${type === 'add' ? t('cmdb.custom_dashboard.newChart') : t('cmdb.custom_dashboard.editChart')}`"
    :body-style="{ paddingTop: 0 }"
    @cancel="handleclose"
    @ok="handleok"
  >
    <div class="chart-wrapper">
      <div class="chart-left">
        <a-form ref="formRef" :model="form" :rules="rules" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
          <a-form-item :label="t('cmdb.custom_dashboard.title')" name="name">
            <a-input v-model:value="form.name" :placeholder="t('cmdb.custom_dashboard.titleTips')"></a-input>
          </a-form-item>
          <a-form-item
            v-if="chartType !== 'count' && chartType !== 'table'"
            :label="t('cmdb.common.type')"
            name="category"
          >
            <a-radio-group v-model:value="form.category" @change="resetForm">
              <a-radio-button v-for="key in Object.keys(categoryOptions)" :key="key" :value="Number(key)">
                {{ categoryOptions[Number(key)].label }}
              </a-radio-button>
            </a-radio-group>
          </a-form-item>
          <a-form-item v-if="chartType === 'table'" :label="t('cmdb.common.type')" name="tableCategory">
            <a-radio-group v-model:value="form.tableCategory" @change="resetForm">
              <a-radio-button :value="1">
                {{ t('cmdb.custom_dashboard.calcIndicators') }}
              </a-radio-button>
              <a-radio-button :value="2">
                {{ t('cmdb.menu.ciTable') }}
              </a-radio-button>
            </a-radio-group>
          </a-form-item>
          <a-form-item
            v-if="(chartType !== 'table' && form.category !== 2) || (chartType === 'table' && form.tableCategory === 1)"
            :label="t('cmdb.ciType.ciType')"
            name="type_ids"
          >
            <CMDBTypeSelectAntd
              v-model="form.type_ids"
              mode="multiple"
              :ci-type-group="CITypeGroup"
              :placeholder="t('cmdb.ciType.selectCIType')"
              @change="changeCIType"
            />
          </a-form-item>
          <a-form-item v-else :label="t('cmdb.ciType.ciType')" name="type_id">
            <CMDBTypeSelectAntd
              v-model="form.type_id"
              :ci-type-group="CITypeGroup"
              :placeholder="t('cmdb.ciType.selectCIType')"
              @change="changeCIType"
            />
          </a-form-item>
          <a-form-item
            v-if="(['bar', 'line', 'pie'].includes(chartType) && form.category === 1) || chartType === 'table'"
            :label="t('cmdb.custom_dashboard.dimensions')"
            name="attr_ids"
          >
            <a-select
              v-model:value="form.attr_ids"
              option-filter-prop="label"
              :placeholder="t('cmdb.custom_dashboard.selectDimensions')"
              mode="multiple"
              show-search
              @change="changeAttr"
            >
              <a-select-option
                v-for="attr in commonAttributes.filter((attr) => !attr.is_password && attr.value_type !== '6')"
                :key="attr.id"
                :value="attr.id"
                :label="attr.alias || attr.name"
              >{{ attr.alias || attr.name }}</a-select-option
              >
            </a-select>
          </a-form-item>
          <a-form-item
            v-if="['bar', 'line', 'pie'].includes(chartType) && form.category === 2"
            name="type_ids"
            :label="t('cmdb.custom_dashboard.childCIType')"
          >
            <a-select
              v-model:value="form.type_ids"
              show-search
              option-filter-prop="children"
              mode="multiple"
              :placeholder="t('cmdb.ciType.selectCIType')"
            >
              <a-select-opt-group
                v-for="(key, index) in Object.keys(level2children)"
                :key="key"
                :label="t('cmdb.custom_dashboard.level') + `${index + 1}`"
              >
                <a-select-option
                  v-for="citype in level2children[key]"
                  :key="citype.id"
                  :value="citype.id"
                  @click="clickLevel2children(citype, index + 1)"
                >
                  {{ citype.alias || citype.name }}
                </a-select-option>
              </a-select-opt-group>
            </a-select>
          </a-form-item>
          <div :class="{ 'chart-left-preview': true, 'chart-left-preview-empty': !isShowPreview }">
            <span class="chart-left-preview-operation" @click="showPreview"
              ><PlayCircleOutlined /> {{ t('cmdb.custom_dashboard.preview') }}</span
            >
            <template v-if="isShowPreview">
              <div v-if="chartType !== 'count'" class="cmdb-dashboard-grid-item-title">
                <template v-if="form.showIcon && ciType">
                  <CIIcon :icon="ciType.icon" :title="ciType.name" />
                </template>
                <span :style="{ color: '#000' }"> {{ form.name }}</span>
              </div>
              <div
                class="chart-left-preview-box"
                :style="{
                  height: chartType === 'count' ? '120px' : '',
                  marginTop: chartType === 'count' ? '80px' : '',
                  background:
                    chartType === 'count'
                      ? Array.isArray(bgColor)
                        ? `linear-gradient(to bottom, ${bgColor[0]} 0%, ${bgColor[1]} 100%)`
                        : bgColor
                      : '#fafafa',
                }"
              >
                <div v-if="chartType === 'count'" :style="{ color: fontColor }">{{ form.name }}</div>
                <Chart
                  :chart-id="item.id"
                  :data="previewData"
                  :category="form.category"
                  :options="{
                    ...item.options,
                    name: form.name,
                    fontColor: fontColor,
                    bgColor: bgColor,
                    chartType: chartType,
                    showIcon: form.showIcon,
                    barDirection: barDirection,
                    barStack: barStack,
                    chartColor: chartColor,
                    type_ids: form.type_ids,
                    attr_ids: form.attr_ids,
                    isShadow: isShadow,
                    ret: form.tableCategory === 2 ? 'cis' : '',
                  }"
                  :editable="false"
                  :ci-types="ciTypes"
                  :type-id="form.type_id || form.type_ids"
                  :is-preview="true"
                />
              </div>
            </template>
          </div>
          <a-form-item name="showIcon" :label-col="{ span: 0 }" :wrapper-col="{ span: 23 }">
            <div class="chart-left-show-icon">
              <span class="chart-left-show-icon-label">{{ t('cmdb.custom_dashboard.showIcon') }}:</span>
              <a-switch v-model:checked="form.showIcon"></a-switch>
            </div>
          </a-form-item>
        </a-form>
      </div>

      <div class="chart-right">
        <h4>{{ t('cmdb.custom_dashboard.chartType') }}</h4>
        <div class="chart-right-type">
          <div
            v-for="chartTypeItem in chartTypeList"
            :key="chartTypeItem.value"
            :class="{ 'chart-right-type-box': true, 'chart-right-type-box-selected': chartType === chartTypeItem.value }"
            @click="changeChartType(chartTypeItem)"
          >
            <component :is="chartTypeIcons[chartTypeItem.value]" />
            <span>{{ chartTypeItem.label }}</span>
          </div>
        </div>
        <h4>{{ t('cmdb.custom_dashboard.dataFilter') }}</h4>
        <FilterComp
          ref="filterCompRef"
          :is-dropdown="false"
          :can-search-preference-attr-list="attributes"
          :expression="filterExp ? `q=${filterExp}` : ''"
          @set-exp-from-filter="setExpFromFilter"
        />
        <h4>{{ t('cmdb.custom_dashboard.format') }}</h4>
        <a-form :colon="false" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
          <a-form-item v-if="chartType === 'count'" :label="t('cmdb.custom_dashboard.fontColor')">
            <ColorPicker
              v-model="fontColor"
              :color-list="[
                '#1D2129',
                '#4E5969',
                '#103C93',
                '#86909C',
                '#ffffff',
                '#C9F2FF',
                '#FFEAC0',
                '#D6FFE6',
                '#F2DEFF',
              ]"
            />
          </a-form-item>
          <a-form-item v-if="chartType === 'count'" :label="t('cmdb.custom_dashboard.backgroundColor')">
            <ColorPicker
              v-model="bgColor"
              :color-list="[
                ['#6ABFFE', '#5375EB'],
                ['#C69EFF', '#A377F9'],
                ['#85EBC9', '#4AB8D8'],
                ['#FEB58B', '#DF6463'],
                '#ffffff',
                '#FFFBF0',
                '#FFF1EC',
                '#E5FFFE',
                '#E5E7FF',
              ]"
            />
          </a-form-item>
          <a-form-item v-else-if="chartType !== 'table'" :label="t('cmdb.custom_dashboard.chartColor')">
            <ColorListPicker v-model="chartColor" />
          </a-form-item>
          <a-form-item :label="t('cmdb.custom_dashboard.chartLength') + `(%)`">
            <a-radio-group v-model:value="width" class="chart-width" style="width: 100%">
              <a-radio-button :value="3">25</a-radio-button>
              <a-radio-button :value="6">50</a-radio-button>
              <a-radio-button :value="9">75</a-radio-button>
              <a-radio-button :value="12">100</a-radio-button>
            </a-radio-group>
          </a-form-item>
          <a-form-item v-if="chartType === 'bar'" :label="t('cmdb.custom_dashboard.barType')">
            <a-radio-group v-model:value="barStack">
              <a-radio value="total">
                {{ t('cmdb.custom_dashboard.stackedBar') }}
              </a-radio>
              <a-radio value="">
                {{ t('cmdb.custom_dashboard.multipleSeriesBar') }}
              </a-radio>
            </a-radio-group>
          </a-form-item>
          <a-form-item v-if="chartType === 'bar'" :label="t('cmdb.custom_dashboard.direction')">
            <a-radio-group v-model:value="barDirection">
              <a-radio value="x"> X {{ t('cmdb.custom_dashboard.axis') }} </a-radio>
              <a-radio value="y"> Y {{ t('cmdb.custom_dashboard.axis') }} </a-radio>
            </a-radio-group>
          </a-form-item>
          <a-form-item v-if="chartType === 'line'" :label="t('cmdb.custom_dashboard.lowerShadow')">
            <a-switch v-model:checked="isShadow" />
          </a-form-item>
        </a-form>
      </div>
    </div>
  </a-modal>
</template>

<style lang="less" scoped>
.chart-wrapper {
  display: flex;
  .chart-left {
    width: 50%;
    .chart-left-preview {
      border: 1px solid #e4e7ed;
      border-radius: 2px;
      height: 280px;
      width: 92%;
      position: relative;
      padding: 12px;
      margin-top: 4px;
      display: inline-block;

      .chart-left-preview-operation {
        color: #86909c;
        position: absolute;
        top: 12px;
        right: 12px;
        cursor: pointer;
      }
      .chart-left-preview-box {
        padding: 6px 12px;
        height: 250px;
        border-radius: 8px;
      }
    }
    .chart-left-preview-empty {
      background: url('../../assets/dashboard_empty.png');
      background-size: contain;
      background-repeat: no-repeat;
      background-position-x: center;
      background-position-y: center;
    }

    &-show-icon {
      display: flex;
      align-items: center;

      &-label {
        flex-shrink: 0;
        margin-right: 8px;
      }
    }
  }
  .chart-right {
    width: 50%;
    h4 {
      font-weight: 700;
      color: #000;

      &:not(:first-child) {
        margin-top: 14px;
      }
    }
    .chart-right-type {
      display: flex;
      justify-content: space-between;
      background-color: #f0f5ff;
      padding: 6px 12px;
      .chart-right-type-box {
        cursor: pointer;
        width: 70px;
        height: 60px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        > i {
          font-size: 32px;
        }
        > span {
          font-size: 12px;
        }
      }
      .chart-right-type-box-selected {
        background-color: @primary-color_3;
      }
    }
    .chart-width {
      width: 100%;
      > label {
        width: 25%;
        text-align: center;
      }
    }
  }
}
</style>
<style lang="less">
.chart-wrapper {
  .ant-form-item {
    margin-bottom: 8px;
  }
}
</style>
