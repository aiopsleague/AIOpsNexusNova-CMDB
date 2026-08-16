<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { DeleteOutlined } from '@ant-design/icons-vue'
import { STATUS_COLOR, STATUS_LABEL, ADDRESS_STATUS } from './constants'

const props = withDefaults(
  defineProps<{
    ipList?: any[]
    columns?: any[]
    referenceShowAttrNameMap?: Record<string, string>
    referenceCIIdMap?: Record<string, Record<string, any>>
  }>(),
  {
    ipList: () => [],
    columns: () => [],
    referenceShowAttrNameMap: () => ({}),
    referenceCIIdMap: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'openAssign', data: any): void
  (e: 'recycle', ip: string): void
}>()

const { t } = useI18n()

const gridItemSize = 52
const gridGap = 8

const infoCardX = ref(0)
const infoCardY = ref(0)
const infoCardWidth = 375
const infoCardVisible = ref(false)
const infoCardData = ref<Record<string, any>>({})
const infoCardTip = ref<Record<string, string>>({})

const gridList = computed(() => {
  return props.ipList.map((item) => {
    const ipSplit = item?.ip?.split('.') || []
    const gridTitle = ipSplit?.[ipSplit.length - 1] || ''

    return {
      ...item,
      gridTitle,
    }
  })
})

const filterColumns = computed(() => {
  return props.columns.filter((col) => col.field !== '_ip_status') || []
})

const infoCardHeight = computed(() => {
  let height = 311
  if (filterColumns.value.length < 6) {
    height -= (6 - filterColumns.value.length) * 36
  }

  return height
})

function handleClick(event: MouseEvent) {
  const target = event?.target as HTMLElement
  const classStr = target?.classList?.value || ''
  if (classStr.indexOf('info-card') === -1 && classStr.indexOf('ip-grid-item') === -1) {
    infoCardVisible.value = false
  }
}

function clickGridItem(item: any, event: MouseEvent) {
  if ([ADDRESS_STATUS.OFFLINE_UNASSIGNED, ADDRESS_STATUS.ONLINE_UNASSIGNED].includes(item?._ip_status)) {
    emit('openAssign', item)
  } else {
    showInfoCard(item, event)
  }
}

function showInfoCard(item: any, event: MouseEvent) {
  let nextX = event.clientX - event.offsetX
  let nextY = event.clientY - event.offsetY + gridItemSize + gridGap

  // Keep the card inside the viewport on the right.
  if (nextX + infoCardWidth > window.innerWidth) {
    nextX = nextX + gridItemSize - infoCardWidth
  }

  // Keep the card inside the viewport on the bottom.
  if (nextY + infoCardHeight.value > window.innerHeight) {
    nextY = nextY - gridItemSize - gridGap * 2 - infoCardHeight.value
  }

  const nextTip: Record<string, string> = {}
  filterColumns.value.forEach((col) => {
    const arrayValue: any[] = Array.isArray(item[col.field]) ? item[col.field] : [item[col.field]]
    nextTip[col.field] = arrayValue
      .map((value: any) => {
        if (value === undefined || value === null) {
          return value
        }

        if (col.is_reference) {
          return getReferenceAttrValue(value, col) || value
        }
        if (col.is_link || col.is_choice) {
          return getChoiceValueLabel(col, value) || value
        }
        return value
      })
      .join(', ')
  })

  infoCardX.value = nextX
  infoCardY.value = nextY
  infoCardVisible.value = true
  infoCardData.value = item
  infoCardTip.value = nextTip
}

function clickRecycle(data: any) {
  emit('recycle', data.ip)
}

function getReferenceAttrValue(id: any, col: Record<string, any>): string {
  const ci = props.referenceCIIdMap?.[col?.reference_type_id]?.[id]
  if (!ci) {
    return id
  }

  const attrName = props.referenceShowAttrNameMap?.[col.reference_type_id]
  return ci?.[attrName] || id
}

function getChoiceValueLabel(col: Record<string, any>, colValue: any): string {
  const found = col?.choice_value?.find((item: any) => String(item[0]) === String(colValue))
  if (found) {
    return found?.[1]?.label || ''
  }
  return ''
}

onMounted(() => {
  window.addEventListener('click', handleClick)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', handleClick)
})
</script>

<template>
  <div
    class="ip-grid"
    :style="{
      gap: gridGap + 'px'
    }"
  >
    <div
      v-for="item in gridList"
      :key="item.ip"
      class="ip-grid-item"
      :style="{
        width: gridItemSize + 'px',
        height: gridItemSize + 'px',
        backgroundColor: `${STATUS_COLOR[item._ip_status]}22`,
        color: STATUS_COLOR[item._ip_status],
        borderColor: STATUS_COLOR[item._ip_status]
      }"
      @click="clickGridItem(item, $event)"
    >
      {{ item.gridTitle }}
    </div>

    <div
      v-show="infoCardVisible"
      class="info-card"
      :style="{
        top: infoCardY + 'px',
        left: infoCardX + 'px',
        width: infoCardWidth + 'px',
        height: infoCardHeight + 'px',
      }"
    >
      <div class="info-card-header">
        <div class="info-card-ip">
          {{ infoCardData.ip }}
        </div>
        <div
          class="info-card-status-dot"
          :style="{
            backgroundColor: `${STATUS_COLOR[infoCardData._ip_status]}22`
          }"
        >
          <div
            class="info-card-status-dot-content"
            :style="{
              backgroundColor: STATUS_COLOR[infoCardData._ip_status]
            }"
          ></div>
        </div>

        <div class="info-card-status-text">
          {{ t(STATUS_LABEL[infoCardData._ip_status]) }}
        </div>

        <a-button
          type="primary"
          class="ops-button-ghost info-card-recycle"
          ghost
          @click="clickRecycle(infoCardData)"
        >
          <DeleteOutlined />
          {{ t('cmdb.ipam.recycle') }}
        </a-button>
      </div>
      <div class="info-card-main">
        <div
          v-for="col in filterColumns"
          :key="col.field"
          class="info-card-main-row"
        >
          <div class="info-card-main-title">
            <a-tooltip :title="col.title">
              {{ col.title }}
            </a-tooltip>
          </div>
          <div class="info-card-main-value">
            <a-tooltip :title="infoCardTip[col.field]" placement="topLeft">
              <template v-if="col.is_reference && infoCardData[col.field]">
                <a
                  v-for="ciId in (col.is_list ? infoCardData[col.field] : [infoCardData[col.field]])"
                  :key="ciId"
                  :href="`/cmdb/cidetail/${col.reference_type_id}/${ciId}`"
                  target="_blank"
                >
                  {{ getReferenceAttrValue(ciId, col) }}
                </a>
              </template>
              <template v-else-if="col.is_link && infoCardData[col.field]">
                <a
                  v-for="(linkItem, linkIndex) in (col.is_list ? infoCardData[col.field] : [infoCardData[col.field]])"
                  :key="linkIndex"
                  :href="
                    linkItem.startsWith('http') || linkItem.startsWith('https')
                      ? `${linkItem}`
                      : `http://${linkItem}`
                  "
                  target="_blank"
                >
                  {{ getChoiceValueLabel(col, linkItem) || linkItem }}
                </a>
              </template>
              <template v-else-if="col.is_choice && infoCardData[col.field]">
                <span
                  v-for="value in (col.is_list ? infoCardData[col.field] : [infoCardData[col.field]])"
                  :key="value"
                  class="column-default-choice"
                >
                  {{ getChoiceValueLabel(col, value) || value }}
                </span>
              </template>
              <template v-else>
                {{ infoCardData[col.field] !== undefined ? Array.isArray(infoCardData[col.field]) ? infoCardData[col.field].join(', ') : infoCardData[col.field] : '' }}
              </template>
            </a-tooltip>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.ip-grid {
  display: flex;
  flex-wrap: wrap;

  max-height: calc(100vh - 230px);
  overflow-y: auto;
  overflow-x: hidden;

  &-item {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 400;
    cursor: pointer;

    &:hover {
      border-style: solid;
      border-width: 1px;
    }
  }

  .info-card {
    position: fixed;
    top: 0;
    left: 0;
    transition: top 0.2s, left 0.2s;
    padding: 23px 18px;

    border-radius: 2px;
    background-color: #ffffff;
    box-shadow: -2px 4px 12px 0px rgba(168, 191, 211, 0.25);

    &-header {
      display: flex;
      align-items: center;
    }

    &-ip {
      font-size: 18px;
      font-weight: 700;
      color: #2f54eb;
    }

    &-status-dot {
      width: 12px;
      height: 12px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-left: 14px;

      &-content {
        width: 6px;
        height: 6px;
        border-radius: 6px;
      }
    }

    &-status-text {
      font-size: 12px;
      font-weight: 400;
      color: #4e5969;
      margin-left: 4px;
    }

    &-recycle {
      margin-left: auto;
    }

    &-main {
      margin-top: 15px;
      width: 100%;
      border: solid 1px #f0f1f5;
      border-bottom-style: none;
      max-height: calc(100% - 47px);
      overflow-y: auto;
      overflow-x: hidden;

      &-row {
        height: 36px;
        line-height: 36px;
        display: flex;
        align-items: center;
      }

      &-title {
        border-right: solid 1px #f0f1f5;
        background-color: #f7f8fa;
        padding-left: 17px;
        padding-right: 10px;
        width: 32%;
        height: 100%;
        flex-shrink: 0;

        font-size: 14px;
        font-weight: 400;
        color: #4e5969;
        overflow: hidden;
        text-overflow: ellipsis;
        text-wrap: nowrap;
        border-bottom: solid 1px #e4e7ed;
      }

      &-value {
        width: 68%;
        flex-shrink: 0;
        padding-left: 18px;
        padding-right: 10px;
        height: 100%;

        font-size: 14px;
        font-weight: 400;
        color: #4e5969;
        overflow: hidden;
        text-overflow: ellipsis;
        text-wrap: nowrap;
        border-bottom: solid 1px #f0f1f5;
      }
    }
  }
}
</style>
