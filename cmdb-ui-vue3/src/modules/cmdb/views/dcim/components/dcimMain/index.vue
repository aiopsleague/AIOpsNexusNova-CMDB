<script setup lang="ts">
import { computed, provide, ref, watch } from 'vue'
import type { Component } from 'vue'
import { useI18n } from 'vue-i18n'
import { AppstoreOutlined, PlusCircleOutlined, TableOutlined } from '@ant-design/icons-vue'
import { DCIM_TYPE } from '../../constants'
import { getDCIMRacks } from '@/modules/cmdb/api/dcim'
import { cloneDeep, getCITableColumns } from '@/modules/cmdb/utils/helper'
import dcimNullImg from '@/assets/dcim_null.png'
import DCIMStats from './dcimStats.vue'
import RackGrid from './rackGrid.vue'
import RackTable from './rackTable.vue'
import RackDetail from '../rackDetail/index.vue'

const props = withDefaults(
  defineProps<{
    roomId?: string
    attrObj?: Record<string, any>
    rackCITYpe?: Record<string, any>
    preferenceAttrList?: any[]
  }>(),
  {
    roomId: '',
    attrObj: () => ({}),
    rackCITYpe: () => ({}),
    preferenceAttrList: () => [],
  }
)

const emit = defineEmits<{
  (e: 'openForm', payload: { dcimType: string; parentId: string }): void
}>()

const { t } = useI18n()

const rackMainRef = ref<HTMLElement | null>(null)
const rackDetailRef = ref<InstanceType<typeof RackDetail>>()

const searchValue = ref('')
const currentRackType = ref('all')
const rackList = ref<any[]>([])
const columns = ref<any[]>([])

const statsData = ref<Record<string, any>>({})

const currentLayout = ref('grid')
const layoutList: { value: string; icon: Component }[] = [
  {
    value: 'grid',
    icon: AppstoreOutlined,
  },
  {
    value: 'table',
    icon: TableOutlined,
  },
]

const rackTypeSelectOption = computed(() => {
  const selectOption: { value: string; label: string }[] = [
    {
      value: 'all',
      label: t('all'),
    },
  ]

  const rackTypeAttr = props.attrObj?.attributes?.find?.((item: any) => item.name === 'rack_type')
  if (rackTypeAttr?.choice_value?.length) {
    rackTypeAttr.choice_value.map((item: any) => {
      selectOption.push({
        value: item?.[0] || '',
        label: item?.[1]?.label || item?.[0] || '',
      })
    })
  }

  selectOption.push({
    value: 'unitAbnormal',
    label: t('cmdb.dcim.unitAbnormal'),
  })

  return selectOption
})

const filterRackList = computed(() => {
  let list = cloneDeep(rackList.value)

  if (searchValue.value) {
    list = list.filter((item) => item.name.indexOf(searchValue.value) !== -1)
  }

  if (currentRackType.value !== 'all') {
    if (currentRackType.value === 'unitAbnormal') {
      list = list.filter((item) => item.u_slot_abnormal)
    } else {
      list = list.filter((item) => item.rack_type === currentRackType.value)
    }
  }

  return list
})

async function initData() {
  try {
    await getRackList()
  } catch (error) {
    console.log('initData error', error)
  }
}

async function getRackList() {
  const res = await getDCIMRacks(props.roomId)
  const list = res?.result || []

  const jsonAttrList = props.preferenceAttrList.filter((attr) => attr.value_type === '6')
  list.forEach((item: any) => {
    item.free_u_count = item.free_u_count ?? 0
    item.u_count = item.u_count ?? 0
    item.u_used_count = item.u_count - item.free_u_count
    item.u_used_ratio = item.u_used_count > 0 && item.u_count > 0 ? Math.round((item.u_used_count / item.u_count) * 100) : 0

    jsonAttrList.forEach(
      (jsonAttr: any) => (item[jsonAttr.name] = item[jsonAttr.name] ? JSON.stringify(item[jsonAttr.name]) : '')
    )
  })

  getColumns(list)

  rackList.value = list
  statsData.value = res?.counter || {}
}

/** Compute table columns for the (not-yet-wired) RackTable view. */
function getColumns(data: any[]) {
  const width = (rackMainRef.value?.clientWidth ?? 0) - 50
  const cols = getCITableColumns(data, props.preferenceAttrList, width)
  cols.forEach((item: any) => {
    if (item.editRender) {
      item.editRender.enabled = false
    }
  })
  columns.value = cols
}

function handleChangeLayout(value: string) {
  if (currentLayout.value !== value) {
    currentLayout.value = value
  }
}

function addRack() {
  emit('openForm', {
    dcimType: DCIM_TYPE.RACK,
    parentId: props.roomId,
  })
}

function openRackDetail(data: any) {
  rackDetailRef.value?.open(data._id)
}

watch(
  () => props.roomId,
  (id) => {
    if (id) {
      initData()
    } else {
      rackList.value = []
      statsData.value = {}
    }
  },
  { immediate: true, deep: true }
)

provide('getRackList', getRackList)
provide('handleSearch', getRackList)
provide('attrList', () => props.attrObj?.attributes || [])
provide('attributes', () => props.attrObj)

defineExpose({ getRackList })
</script>

<template>
  <div ref="rackMainRef" class="dcim-main">
    <div v-if="!roomId" class="dcim-main-null">
      <img class="dcim-main-null-img" :src="dcimNullImg" />
      <div class="dcim-main-null-tip">{{ t('noData') }}</div>
      <div class="dcim-main-null-tip2">{{ t('cmdb.dcim.roomNullTip') }}</div>
    </div>

    <template v-else>
      <DCIMStats :stats-data="statsData" />

      <div class="dcim-main-row">
        <div class="dcim-main-filter">
          <a-input-search v-model:value="searchValue" :placeholder="t('cmdb.dcim.rackSearchTip')" class="dcim-main-row-search" />

          <a-select
            v-model:value="currentRackType"
            class="dcim-main-row-select"
            :get-popup-container="(trigger: HTMLElement) => trigger.parentElement"
          >
            <a-select-option
              v-for="item in rackTypeSelectOption"
              :key="item.value"
              :value="item.value"
              :class="item.value === 'unitAbnormal' ? 'dcim-main-row-select-unitAbnormal' : ''"
            >
              {{ item.label }}
            </a-select-option>
          </a-select>
        </div>

        <div class="dcim-main-row-right">
          <div class="dcim-main-layout">
            <div
              v-for="item in layoutList"
              :key="item.value"
              :class="['dcim-main-layout-item', currentLayout === item.value ? 'dcim-main-layout-item-active' : '']"
              @click="handleChangeLayout(item.value)"
            >
              <component :is="item.icon" />
            </div>
          </div>

          <a-button type="primary" class="ops-button-ghost" ghost @click="addRack">
            <PlusCircleOutlined />
            {{ t('cmdb.dcim.addRack') }}
          </a-button>
        </div>
      </div>

      <div class="rack-wrap">
        <RackGrid v-if="currentLayout === 'grid'" :rack-list="filterRackList" @open-rack-detail="openRackDetail" />

        <RackTable
          v-if="currentLayout === 'table'"
          :rack-list="filterRackList"
          :columns="columns"
          :preference-attr-list="preferenceAttrList"
          :c-i-type-id="rackCITYpe.id"
        />
      </div>

      <RackDetail
        ref="rackDetailRef"
        :room-id="roomId"
        :rack-c-i-type="rackCITYpe"
        :rack-list="rackList"
        @open-form="(data: any) => emit('openForm', data)"
        @refresh-rack-list="getRackList"
      />
    </template>
  </div>
</template>

<style lang="less" scoped>
.dcim-main {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

  &-null {
    width: 100%;
    padding-top: 95px;
    text-align: center;

    &-img {
      height: 200px;
    }

    &-tip {
      font-size: 14px;
      font-weight: 400;
      color: #86909c;
    }

    &-tip2 {
      font-size: 14px;
      font-weight: 400;
      color: #2f54eb;
    }
  }

  &-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    margin-top: 20px;

    &-search {
      width: 300px;
    }

    &-select {
      width: 120px;
      margin-left: 22px;
      flex-shrink: 0;

      :deep(&-unitAbnormal) {
        border-top: dashed 1px #e8e8e8;
      }
    }

    &-right {
      display: flex;
      align-items: center;
      column-gap: 21px;
    }
  }

  &-layout {
    display: flex;
    align-items: center;
    height: 32px;
    border: solid 1px #e4e7ed;

    &-item {
      height: 100%;
      width: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      cursor: pointer;

      &:not(:last-child) {
        border-right: solid 1px #e4e7ed;
      }

      &-active {
        color: #2f54eb;
        background-color: #f0f5ff;
      }

      &:hover {
        color: #2f54eb;
      }
    }
  }

  .rack-wrap {
    margin-top: 22px;
    margin-bottom: 22px;
    height: 100%;
    overflow: hidden;
  }
}
</style>
