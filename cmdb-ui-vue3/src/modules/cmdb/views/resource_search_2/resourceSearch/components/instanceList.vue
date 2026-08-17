<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { DownloadOutlined, StarFilled, StarOutlined } from '@ant-design/icons-vue'
import ExcelJS from 'exceljs'
import FileSaver from 'file-saver'
import dayjs from 'dayjs'

import AttrDisplay from './attrDisplay.vue'
import CIIcon from '@/modules/cmdb/components/ciIcon/index.vue'
import resourceSearchBg2 from '@/modules/cmdb/assets/resourceSearch/resource_search_bg_2.png'

const props = withDefaults(
  defineProps<{
    list?: any[]
    tabList?: any[]
    referenceShowAttrNameMap?: Record<string, string>
    referenceCIIdMap?: Record<string, Record<string, any>>
    favorList?: any[]
    detailCIId?: string | number
    searchValue?: string
  }>(),
  {
    list: () => [],
    tabList: () => [],
    referenceShowAttrNameMap: () => ({}),
    referenceCIIdMap: () => ({}),
    favorList: () => [],
    detailCIId: -1,
    searchValue: '',
  }
)

const emit = defineEmits<{
  (e: 'showDetail', data: { id: string | number; ciTypeId: string | number }): void
  (e: 'addCollect', data: Record<string, any>): void
  (e: 'deleteCollect', id: string | number): void
}>()

const { t } = useI18n()

const currentTab = ref<string | number>('')

const filterList = computed(() => {
  if (!currentTab.value || currentTab.value === -1) {
    return props.list
  }

  return props.list.filter((item) => item.ciTypeObj.id === currentTab.value)
})

watch(
  () => props.tabList,
  (newVal) => {
    currentTab.value = newVal?.[0]?.id ?? ''
  },
  { immediate: true, deep: true }
)

function clickTab(id: string | number) {
  currentTab.value = id
}

function clickInstance(id: string | number, ciTypeId: string | number) {
  emit('showDetail', {
    id,
    ciTypeId,
  })
}

function getFavorId(ciId: string | number): string | number | null {
  const id = props.favorList.find((item) => item?.option?.CIId === ciId)?.id
  return id ?? null
}

function addCollect(data: any) {
  emit('addCollect', {
    CIId: data.ci._id,
    CITypeId: data.ciTypeObj.id,
    title: data.ci[data.ciTypeObj.showAttrName],
    icon: data.ciTypeObj.icon,
    CITypeTitle: data.ciTypeObj.name,
  })
}

function deleteCollect(ciId: string | number) {
  const favorId = getFavorId(ciId)
  if (favorId) {
    emit('deleteCollect', favorId)
  }
}

function handleExport() {
  const excel_name = `cmdb-${t('cmdb.ciType.resourceSearch')}-${dayjs().format('YYYYMMDDHHmmss')}.xlsx`
  const wb = new ExcelJS.Workbook()

  props.tabList.forEach((sheet: any) => {
    if (sheet.id === -1) {
      return
    }
    const ws = wb.addWorksheet(sheet.title)
    handleSheetData({ ws, sheet })
  })

  wb.xlsx.writeBuffer().then((buffer) => {
    const file = new Blob([buffer], { type: 'application/octet-stream' })
    FileSaver.saveAs(file, excel_name)
  })
}

function handleSheetData({ ws, sheet }: { ws: ExcelJS.Worksheet; sheet: any }) {
  const listData = props.list.filter((item: any) => item.ciTypeObj.id === sheet.id)
  if (!listData.length) {
    return
  }

  const columnMap = new Map<string, any>()
  const columns = listData[0].attributes
    .filter((attr: any) => !attr.is_password)
    .map((attr: any) => {
      columnMap.set(attr.name, attr)
      return {
        header: attr.alias || attr.name || '',
        key: attr.name,
        width: 20,
      }
    })

  ws.columns = columns

  listData.forEach((data: any) => {
    const row: Record<string, any> = {}
    columns.forEach(({ key }: { key: string }) => {
      const value = data?.ci?.[key] ?? null
      const attr = columnMap.get(key)
      if (attr.valueType === '6') {
        row[key] = value ? JSON.stringify(value) : value
      } else if (attr.is_list && Array.isArray(value)) {
        row[key] = value.join(',')
      } else {
        row[key] = value
      }
    })
    ws.addRow(row)
  })
}
</script>

<template>
  <div class="list-wrap">
    <div v-if="!filterList.length" class="list-wrap-bg">
      <img :src="resourceSearchBg2" />
    </div>

    <div v-if="tabList.length" class="list-tab">
      <div class="list-tab-left">
        <div class="list-tab-label">{{ t('cmdb.ciType.currentPage') }}: </div>
        <div
          v-for="tab in tabList"
          :key="tab.id"
          :class="['list-tab-item', tab.id === currentTab ? 'list-tab-item-active' : '']"
          @click="clickTab(tab.id)"
        >
          <span class="list-tab-item-title">{{ tab.title }}</span>
          (<span class="list-tab-item-count">{{ tab.count }}</span>)
        </div>
      </div>

      <a-button type="primary" class="ops-button-ghost list-tab-export" ghost @click="handleExport">
        <template #icon><DownloadOutlined /></template>
        {{ t('download') }}
      </a-button>
    </div>

    <div v-if="filterList.length" class="list-container">
      <div
        v-for="item in filterList"
        :key="item._id"
        :class="['list-card', detailCIId === item.ci._id ? 'list-card-selected' : '']"
        @click="clickInstance(item.ci._id, item.ciTypeObj.id)"
      >
        <div class="list-card-header">
          <div class="list-card-model">
            <CIIcon :icon="item.ciTypeObj.icon" :title="item.ciTypeObj.name" />
            <span class="list-card-model-title">{{ item.ciTypeObj.title }}</span>
          </div>
          <div class="list-card-title">{{ item.ci[item.ciTypeObj.showAttrName] }}</div>

          <StarFilled
            v-if="getFavorId(item.ci._id)"
            class="list-card-collect"
            :style="{ color: '#FAD337' }"
            @click.stop="deleteCollect(item.ci._id)"
          />

          <StarOutlined
            v-else
            class="list-card-collect"
            :style="{ color: '#A5A9BC' }"
            @click.stop="addCollect(item)"
          />
        </div>
        <div class="list-card-attr">
          <div v-for="attr in item.attributes" :key="attr.name" class="list-card-attr-item">
            <div class="list-card-attr-item-label">{{ attr.alias || attr.name || '' }}: </div>
            <div class="list-card-attr-item-value">
              <AttrDisplay
                :attr="attr"
                :ci="item.ci"
                :reference-show-attr-name-map="referenceShowAttrNameMap"
                :reference-c-i-id-map="referenceCIIdMap"
                :is-ellipsis="true"
                :search-value="searchValue"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.list-wrap {
  width: 100%;
  height: 100%;
  flex-shrink: 1 !important;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  &-bg {
    width: 100%;
    padding-top: 90px;
    display: flex;
    justify-content: center;

    img {
      width: 300px;
    }
  }

  .list-tab {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    column-gap: 14px;

    &-left {
      display: flex;
      align-items: center;
      column-gap: 14px;
      row-gap: 7px;
      overflow-x: auto;
      max-width: 100%;
    }

    &-label {
      font-size: 14px;
      font-weight: 400;
      color: #4e5969;
      flex-shrink: 0;
    }

    &-item {
      display: flex;
      align-items: center;
      font-size: 14px;
      font-weight: 400;
      color: #4e5969;
      cursor: pointer;
      flex-shrink: 0;

      &-count {
        color: #2f54eb;
      }

      &-active {
        color: #2f54eb;
      }

      &:hover {
        color: #2f54eb;
      }
    }

    &-export {
      margin-left: auto;
      flex-shrink: 0;
    }
  }

  .list-container {
    width: 100%;
    margin-top: 12px;
    height: 100%;
    overflow-y: auto;
    flex-shrink: 1;
    flex-grow: 0;

    .list-card {
      width: 100%;
      background-color: #fff;
      border-radius: 4px;
      padding: 15px;
      cursor: pointer;

      &:not(:first-child) {
        margin-top: 16px;
      }

      &-selected {
        border: 1px solid #7f97fa;
        background-color: #f9fbff;
      }

      &-header {
        display: flex;
        align-items: center;
      }

      &-model {
        border-radius: 24px;
        border: 1px solid #e4e7ed;
        background-color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 24px;
        padding: 0 13px;
        flex-shrink: 0;

        &-title {
          font-size: 12px;
          font-weight: 400;
          line-height: 24px;
          color: #1d2129;
          margin-left: 4px;
        }
      }

      &-title {
        margin-left: 11px;
        font-size: 14px;
        font-weight: 700;
        color: #1d2129;

        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        text-wrap: nowrap;
      }

      &-collect {
        font-size: 12px;
        margin-left: 9px;
        display: none;
      }

      &-attr {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        overflow: hidden;
        height: 25px;
        column-gap: 40px;
        row-gap: 20px;
        margin-top: 12px;

        &-item {
          flex-shrink: 0;
          max-width: calc((100% - 160px) / 5);
          display: flex;
          align-items: center;
          overflow: hidden;

          &-label {
            color: #86909c;
            font-size: 14px;
            font-weight: 400;
            flex-shrink: 0;
          }

          &-value {
            color: #1d2129;
            font-size: 14px;
            font-weight: 400;
            margin-left: 12px;
            overflow: hidden;
          }
        }
      }

      &:hover {
        box-shadow: ~'0px 2px 12px 0px @{primary-color}15';

        .list-card-collect {
          display: inline-block;
        }
      }
    }
  }
}
</style>
