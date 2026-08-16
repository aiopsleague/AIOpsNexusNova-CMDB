<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { AppstoreOutlined, PlusCircleOutlined, RightOutlined, TableOutlined } from '@ant-design/icons-vue'
import type { Component } from 'vue'
import { Modal, message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { deleteDevice } from '@/modules/cmdb/api/dcim'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import { U_NUMBERING_DIRECTION } from '../../../constants'
import RackHeader from './rackHeader/index.vue'
import CIIcon from '@/modules/cmdb/components/ciIcon/index.vue'
import AbnormalModal from './abnormalModal.vue'
import rackFrontPartImg from '@/assets/dcim/rack_front_part.png'

const props = withDefaults(
  defineProps<{
    viewType?: string
    countList?: number[]
    unitList?: any[]
    rackData?: Record<string, any>
  }>(),
  {
    viewType: 'front',
    countList: () => [],
    unitList: () => [],
    rackData: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'openDeviceForm', data: { unitStart?: number; CITypeId?: number; deviceId?: number; unitCount?: number; name?: string }): void
  (e: 'draggable', data: { startUnit: number; deviceId: number; oldUnitList: any[] }): void
  (e: 'migrateDevice', deviceId: number): void
  (e: 'refreshRackAllData'): void
  (e: 'openDeviceDetail', data: any): void
}>()

const { t } = useI18n()

const abnormalModalRef = ref<InstanceType<typeof AbnormalModal>>()

const unitHeight = 24

// Local render list so drag-and-drop reorders do not mutate the parent prop.
const innerUnitList = ref<any[]>([])

const oldDraggableList = ref<any[]>([])
const draggableDevice = ref<any>({})
const draggingIndex = ref<number | null>(null)

watch(
  () => props.unitList,
  (list) => {
    innerUnitList.value = list
  },
  { immediate: true, deep: true }
)

const titleData = computed<{ icon: Component; text: string }>(() => {
  return {
    icon: props.viewType === 'front' ? AppstoreOutlined : TableOutlined,
    text: props.viewType === 'front' ? 'cmdb.dcim.frontView' : 'cmdb.dcim.rearView',
  }
})

function addDevice(index: number) {
  const sliceUnitList = innerUnitList.value.slice(0, index)
  const unitCount = sliceUnitList.reduce((acc, cur) => acc + cur.unitCount, 0)

  const u_numbering_direction = props?.rackData?.u_numbering_direction
  let unitStart = props.countList.length - unitCount
  if (u_numbering_direction === U_NUMBERING_DIRECTION.TOP_TO_BOTTOM) {
    unitStart = unitCount + 1
  }

  emit('openDeviceForm', { unitStart })
}

function editDevice(data: any) {
  emit('openDeviceForm', {
    CITypeId: data?._type,
    deviceId: data?.id,
    unitStart: data?.u_start,
    unitCount: data?.u_count,
    name: data?.name,
  })
}

function handleDragStart(e: DragEvent, index: number) {
  oldDraggableList.value = cloneDeep(innerUnitList.value)
  draggableDevice.value = cloneDeep(innerUnitList.value[index]) || {}
  draggingIndex.value = index
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
  }
}

function handleDragOver(e: DragEvent) {
  e.preventDefault()
}

function handleDrop(e: DragEvent, newIndex: number) {
  e.preventDefault()
  const oldIndex = draggingIndex.value
  if (oldIndex === null || oldIndex === newIndex) {
    draggingIndex.value = null
    return
  }

  // Reorder the local list to give immediate visual feedback.
  const list = [...innerUnitList.value]
  const [moved] = list.splice(oldIndex, 1)
  list.splice(newIndex, 0, moved)
  innerUnitList.value = list

  draggingIndex.value = null
  handleDraggableEnd(newIndex)
}

function handleDraggableEnd(newIndex: number) {
  const sliceUnitList = innerUnitList.value.slice(0, newIndex)
  const unitCount = sliceUnitList.reduce((acc, cur) => acc + cur.unitCount, 0)

  const u_numbering_direction = props?.rackData?.u_numbering_direction
  // Bottom-to-top: startU = totalU - sum of units above - device units + 1.
  let startUnit = props.countList.length - unitCount - draggableDevice.value.unitCount + 1
  if (u_numbering_direction === U_NUMBERING_DIRECTION.TOP_TO_BOTTOM) {
    startUnit = unitCount + 1
  }

  if (draggableDevice.value?.id) {
    emit('draggable', {
      startUnit,
      deviceId: draggableDevice.value.id,
      oldUnitList: oldDraggableList.value,
    })
  }

  draggableDevice.value = {}
  oldDraggableList.value = []
}

function getNameList(item: any) {
  const nameList = [item]

  if (item?.abnormalList?.length) {
    nameList.push(...item.abnormalList)
  }

  return nameList
}

function clickDevice(data: any) {
  if (data.abnormal) {
    abnormalModalRef.value?.open(data)
  }
}

function removeDevice(data: any) {
  const content = t('cmdb.dcim.removeDeviceTip', {
    deviceName: `${data.CITypeName} ${data.name}`,
  })

  Modal.confirm({
    title: t('warning'),
    content,
    onOk: () => {
      if (!props.rackData._id) {
        return
      }

      deleteDevice(props.rackData._id, data.id).then(() => {
        message.success(t('deleteSuccess'))
        emit('refreshRackAllData')
      })
    },
  })
}

function migrateDevice(data: any) {
  emit('migrateDevice', data.id)
}

function openDeviceDetail(deviceData: any) {
  emit('openDeviceDetail', deviceData)
}
</script>

<template>
  <div class="rack-container">
    <div class="rack-title">
      <component :is="titleData.icon" class="rack-title-icon" />
      <span class="rack-title-text">
        {{ t(titleData.text) }}
      </span>
    </div>

    <RackHeader :view-type="viewType" />

    <div
      class="rack-container-main"
      :style="{
        flexDirection: viewType === 'front' ? 'row' : 'row-reverse',
      }"
    >
      <div class="rack-container-main-left">
        <div
          v-for="(item, index) in countList"
          :key="index"
          class="rack-container-main-left-count"
          :style="{
            backgroundColor: item % 2 === 0 ? '#3D4151' : '#5E6772',
            height: unitHeight + 'px',
            lineHeight: unitHeight + 'px',
          }"
        >
          {{ item }}
        </div>
      </div>

      <div class="rack-container-main-list">
        <div
          v-for="(item, index) in innerUnitList"
          :key="item.key"
          :class="[item.type === 'gap' || item.abnormal ? 'undraggable' : '']"
          :draggable="item.type !== 'gap' && !item.abnormal"
          @dragstart="handleDragStart($event, index)"
          @dragover="handleDragOver"
          @drop="handleDrop($event, index)"
        >
          <div
            v-if="item.type === 'device'"
            :class="['rack-container-main-list-device', item.abnormal ? '' : 'rack-container-main-list-device_normal']"
            :style="{
              height: unitHeight * item.unitCount + 'px',
            }"
            @click="clickDevice(item)"
          >
            <div class="rack-container-main-list-device-action">
              <div class="rack-container-main-list-device-action-btn" @click.stop="removeDevice(item)">
                {{ t('cmdb.dcim.remove') }}
              </div>
              <div class="rack-container-main-list-device-action-btn" @click.stop="migrateDevice(item)">
                {{ t('cmdb.dcim.migrate') }}
              </div>
            </div>

            <div v-if="item.abnormal" class="rack-container-main-list-device-abnormal">
              <span class="rack-container-main-list-device-abnormal-text">
                {{ t('cmdb.dcim.unitAbnormal') }}
              </span>
              <RightOutlined class="rack-container-main-list-device-abnormal-icon" />
            </div>

            <div class="rack-container-main-list-device-header"></div>
            <img v-for="unitIndex in item.unitCount" :key="unitIndex" :src="item.deviceImage[viewType]" />

            <div
              class="rack-container-main-list-device-sider"
              :style="{
                right: viewType === 'front' ? '-154px' : '-157px',
              }"
            >
              <div
                v-for="(nameItem, nameIndex) in getNameList(item)"
                :key="nameIndex"
                class="rack-container-main-list-device-name"
                @click.stop="openDeviceDetail(nameItem)"
              >
                <CIIcon size="14" :icon="nameItem.icon" />
                <span class="rack-container-main-list-device-name-text">{{ nameItem.name }}</span>
              </div>
            </div>
          </div>
          <div
            v-if="item.type === 'gap'"
            :class="['rack-container-main-list-gap', viewType === 'rear' ? 'rack-container-main-list-gap_rear' : '']"
            :style="{
              height: unitHeight + 'px',
            }"
            @click="addDevice(index)"
          >
            <PlusCircleOutlined class="rack-container-main-list-gap-icon" />
            <span class="rack-container-main-list-gap-text">
              {{ t('cmdb.dcim.addDevice') }}
            </span>
          </div>
        </div>
      </div>

      <div class="rack-container-main-right">
        <div class="rack-container-main-right-part-1"></div>
        <div class="rack-container-main-right-part-2"></div>

        <img
          v-if="viewType === 'front'"
          :src="rackFrontPartImg"
          class="rack-container-main-right-part-3"
        />
      </div>
    </div>

    <div class="rack-container-footer">
      <template v-if="viewType === 'front'">
        <div class="rack-container-footer-dot"></div>
        <div class="rack-container-footer-dot"></div>
      </template>
    </div>

    <AbnormalModal ref="abnormalModalRef" @ok="editDevice" />
  </div>
</template>

<style lang="less" scoped>
.rack-container {
  width: 236px;

  .rack-title {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 14px;

    &-icon {
      font-size: 14px;
    }

    &-text {
      font-size: 14px;
      font-weight: 700;
      color: #4e5969;
      margin-left: 6px;
    }
  }

  &-main {
    display: flex;
    width: 100%;

    &-left {
      min-width: 17px;
      flex-shrink: 0;
      z-index: 2;

      &-count {
        width: 100%;
        border-bottom: solid 1px rgba(116, 138, 171, 0.25);
        text-align: center;
        font-size: 12px;
        font-weight: 400;
        color: #ffffff;
      }
    }

    &-list {
      width: 100%;

      &-device {
        background-color: #2c2d31;
        border-bottom: solid 1px rgba(116, 138, 171, 0.25);
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        position: relative;

        &-header {
          width: 195px;
          height: 6px;
          clip-path: polygon(20px 0, 175px 0, 195px 100%, 0px 100%);
          background-color: #5d6271;
        }

        img {
          width: 195px;
          height: 17px;
        }

        &-action {
          display: none;
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          border: 1px solid #10d4ff;
          background: linear-gradient(90deg, rgba(0, 0, 0, 0.8) 0%, rgba(102, 102, 102, 0.8) 100%);
          align-items: center;
          justify-content: center;
          z-index: 1;

          &-btn {
            font-size: 14px;
            font-weight: 400;
            color: #ffffff;
            padding: 0 10px;
            cursor: pointer;

            &:not(:first-child) {
              border-left: solid 1px rgba(165, 169, 188, 0.44);
            }

            &:hover {
              color: #10d4ff;
            }
          }
        }

        &-abnormal {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          border: 1px solid #f00;
          background-color: rgba(128, 47, 47, 0.66);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;

          &-text {
            color: #ffffff;
            font-size: 14px;
            font-weight: 700;
          }

          &-icon {
            color: #ffffff;
            font-size: 12px;
          }
        }

        &-name {
          display: flex;
          align-items: center;
          cursor: pointer;

          &-text {
            margin-left: 3px;
            font-size: 12px;
            font-weight: 400;
            color: #1d2129;

            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          &:hover {
            .rack-container-main-list-device-name-text {
              color: #3f75ff;
            }
          }
        }

        &-sider {
          position: absolute;
          top: 0;
          width: 140px;
          height: 100%;
          display: flex;
          flex-direction: column;
          justify-content: center;
          row-gap: 6px;
          padding-left: 7px;

          &::after {
            content: '';
            position: absolute;
            top: 5%;
            left: 0;
            width: 4px;
            height: 90%;
            border: solid 1px #10d4ff;
            border-left: none;
          }
        }

        &_normal:hover {
          .rack-container-main-list-device-action {
            display: flex;
          }
        }
      }

      &-gap {
        width: 100%;
        border-bottom: solid 1px rgba(116, 138, 171, 0.25);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        background-color: #ebeff8;

        &-icon {
          font-size: 12px;
          display: none;
          color: @primary-color;
        }

        &-text {
          font-size: 12px;
          font-weight: 400;
          color: @primary-color;
          margin-left: 6px;
          display: none;
        }

        &_rear {
          background-color: #cacdd9;
          border-bottom: solid 1px #e4e7ed;
        }

        &:hover {
          background-color: @primary-color_4;

          .rack-container-main-list-gap-icon {
            display: inline-block;
          }

          .rack-container-main-list-gap-text {
            display: inline-block;
          }
        }
      }
    }

    &-right {
      flex-shrink: 0;
      display: flex;
      background-color: #86909c;
      position: relative;

      &-part-1 {
        width: 7px;
        height: 100%;
        border-right: solid 1px rgba(255, 255, 255, 0.33);
      }

      &-part-2 {
        width: 7px;
        height: 100%;
        background: linear-gradient(270deg, rgba(134, 144, 156, 0) 0%, rgba(69, 78, 89, 0.88) 100%);
        filter: blur(0.25px);
      }

      &-part-3 {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 21px;
        height: 57.6px;
        transform: translate(-50%, -50%);
      }
    }
  }

  &-footer {
    height: 12px;
    width: 100%;
    background-color: #86909c;
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0px 14px;

    &-dot {
      width: 4px;
      height: 4px;
      border-radius: 4px;
      background-color: #e8ebee;
      border: solid 1px #ffffff;
      box-shadow:
        3px 3px 7px 0px rgba(136, 150, 163, 0.58) inset,
        -3px -3px 7px 0px #fff inset;
    }
  }
}
</style>
