<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, inject, provide, ref, watch } from 'vue'
import { getSubscribeAttributes } from '@/modules/cmdb/api/preference'
import { getCITableColumns } from '@/modules/cmdb/utils/helper'
import CIIcon from '@/modules/cmdb/components/ciIcon/index.vue'
import CITable from '@/modules/cmdb/components/ciTable/index.vue'
import CIDetailDrawer from '@/modules/cmdb/views/ci/modules/ciDetailDrawer.vue'

const props = withDefaults(
  defineProps<{
    allDeviceList?: any[]
    CITypeRelations?: any[]
  }>(),
  {
    allDeviceList: () => [],
    CITypeRelations: () => [],
  }
)

const deviceListRef = ref<HTMLElement | null>(null)
const CIdetailRef = ref<InstanceType<typeof CIDetailDrawer>>()

const getDeviceList = inject<() => void>('getDeviceList', () => {})
const getRackList = inject<() => void>('getRackList', () => {})

const tabActive = ref<number | null>(null)
const tabs = ref<any[]>([])

const preferenceAttrList = ref<any[]>([])
const deviceList = ref<any[]>([])
const columns = ref<any[]>([])
const deviceCIType = ref<Record<string, any>>({})

const windowHeight = computed(() => window.innerHeight)
const tableHeight = computed(() => `${windowHeight.value - 210}px`)

function uniqBy<T>(list: T[], key: string): T[] {
  const seen = new Set<any>()
  return list.filter((item) => {
    const k = (item as any)[key]
    if (seen.has(k)) {
      return false
    }
    seen.add(k)
    return true
  })
}

watch(
  () => props.allDeviceList,
  () => {
    initData()
  },
  { immediate: true, deep: true }
)

function initData() {
  const nextTabs: any[] = []
  props.allDeviceList.forEach((item) => {
    const CIType = props.CITypeRelations.find((type) => type.id === item._type)

    nextTabs.push({
      icon: CIType?.icon,
      name: item.ci_type,
      alias: item.ci_type_alias,
      id: item._type,
    })
  })

  clickTab(nextTabs?.[0]?.id ?? null)
  tabs.value = uniqBy(nextTabs, 'id')
}

function clickTab(id: number | null) {
  if (id !== tabActive.value) {
    tabActive.value = id

    if (tabActive.value) {
      initTableData()
    } else {
      columns.value = []
      deviceList.value = []
    }
  }
}

async function initTableData() {
  const subscribed = await getSubscribeAttributes(tabActive.value as number)
  preferenceAttrList.value = subscribed.attributes

  const list = props.allDeviceList.filter((item) => item._type === tabActive.value)

  const foundCIType = props.CITypeRelations.find((item) => item.id === tabActive.value)
  deviceCIType.value = foundCIType || {}

  getColumns(list)
  deviceList.value = list
}

function getColumns(data: any[]) {
  const width = (deviceListRef.value?.clientWidth ?? 0) - 50
  const cols = getCITableColumns(data, preferenceAttrList.value, width)
  cols.forEach((item: any) => {
    if (item.editRender) {
      item.editRender.enabled = false
    }
  })
  columns.value = cols
}

function refreshData() {
  getDeviceList()
  getRackList()
}

function openDetail(id: any, activeTabKey?: string, _ciDetailRelationKey?: string) {
  CIdetailRef.value?.create(id, activeTabKey)
}

provide('handleSearch', refreshData)
provide('attrList', () => deviceCIType.value?.attributes || [])
provide('attributes', () => {
  return {
    attributes: deviceCIType.value?.attributes || [],
    unique_id: deviceCIType.value?.unique_id || 0,
    unique: deviceCIType.value?.show_key || '',
  }
})
</script>

<template>
  <div ref="deviceListRef" class="device-list">
    <div class="device-list-tabs">
      <div
        v-for="item in tabs"
        :key="item.id"
        :class="['device-list-tabs-item', item.id === tabActive ? 'device-list-tabs-item_active' : '']"
        @click="clickTab(item.id)"
      >
        <CIIcon :icon="item.icon" />
        <span class="device-list-tabs-item-name">{{ item.alias || item.name }}</span>
      </div>
    </div>

    <CITable
      :attr-list="preferenceAttrList"
      :columns="columns"
      :data="deviceList"
      :height="tableHeight"
      :show-checkbox="false"
      :show-delete="false"
      :sort-config="{ remote: false, trigger: 'default' }"
      @open-detail="openDetail"
    />

    <CIDetailDrawer v-if="tabActive" ref="CIdetailRef" :type-id="tabActive" />
  </div>
</template>

<style lang="less" scoped>
.device-list {
  width: 100%;

  &-tabs {
    display: flex;
    flex-wrap: wrap;
    column-gap: 9px;
    row-gap: 5px;
    margin-bottom: 18px;

    &-item {
      flex-shrink: 0;
      display: flex;
      align-items: center;
      cursor: pointer;
      padding: 4px 12px;
      background-color: #f7f8fa;
      border-radius: 1px;
      border: solid 1px transparent;
      max-width: 100%;

      &-name {
        margin-left: 4px;
        font-size: 12px;
        font-weight: 400;
        color: #1d2129;

        text-overflow: ellipsis;
        overflow: hidden;
        white-space: nowrap;
      }

      &_active {
        border-color: #b1c9ff;
        background-color: #f9fbff;
      }

      &:hover {
        .device-list-tabs-item-name {
          color: #3f75ff;
        }
      }
    }
  }
}
</style>
