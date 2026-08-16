<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { inject, nextTick, provide, ref, watch } from 'vue'
import { putDevice } from '@/modules/cmdb/api/dcim'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import { DEVICE_CITYPE_NAME, U_NUMBERING_DIRECTION } from '../../../constants'
import RackUnitView from './rackUnitView.vue'
import DeviceForm from './deviceForm/index.vue'
import MigrateModal from './migrateModal.vue'
import CIDetailDrawer from '@/modules/cmdb/views/ci/modules/ciDetailDrawer.vue'

import serverFrontImg from '@/assets/dcim/device/server_front.png'
import serverRearImg from '@/assets/dcim/device/server_rear.png'
import routerFrontImg from '@/assets/dcim/device/router_front.png'
import routerRearImg from '@/assets/dcim/device/router_rear.png'
import firewallFrontImg from '@/assets/dcim/device/firewall_front.png'
import firewallRearImg from '@/assets/dcim/device/firewall_rear.png'
import raidFrontImg from '@/assets/dcim/device/raid_front.png'
import raidRearImg from '@/assets/dcim/device/raid_rear.png'
import switchFrontImg from '@/assets/dcim/device/switch_front.png'
import switchRearImg from '@/assets/dcim/device/switch_rear.png'

const props = withDefaults(
  defineProps<{
    CITypeRelations?: any[]
    rackData?: Record<string, any>
    deviceList?: any[]
    rackList?: any[]
  }>(),
  {
    CITypeRelations: () => [],
    rackData: () => ({}),
    deviceList: () => [],
    rackList: () => [],
  }
)

const deviceFormRef = ref<InstanceType<typeof DeviceForm>>()
const migrateModalRef = ref<InstanceType<typeof MigrateModal>>()
const CIdetailRef = ref<InstanceType<typeof CIDetailDrawer>>()

const getRackList = inject<() => void>('getRackList', () => {})
const getDeviceList = inject<() => void>('getDeviceList', () => {})

const unitList = ref<any[]>([])
const countList = ref<number[]>([])

const deviceAttrList = ref<any[]>([])
const deviceCITypeId = ref(0)

let keyCounter = 0
function genKey(): string {
  return `unit-${Date.now()}-${keyCounter++}`
}

watch(
  () => props.deviceList,
  (deviceList) => {
    initData(deviceList)
  },
  { immediate: true, deep: true }
)

function initData(deviceList: any[]) {
  const CITypeMap = props.CITypeRelations.reduce((map: Record<string, any>, cur: any) => {
    map[cur.id] = cur
    return map
  }, {})

  const _deviceList = cloneDeep(deviceList)

  // Build the device map and detect U-position conflicts.
  const deviceMap: Record<string, any> = {}
  _deviceList.forEach((device: any, index: number) => {
    const CITYpe = CITypeMap?.[device?._type] || {}

    device.deviceImage = getDeviceViewImage(CITYpe?.name)
    device.name = device?.[CITYpe?.show_key] || device._id || ''
    device.icon = CITYpe?.icon || ''
    device.CITypeName = CITYpe?.alias || CITYpe?.name || ''
    device.id = device._id

    if (index > 0) {
      const abnormalDevice = _deviceList.slice(0, index).find((item: any) => {
        const unitCount = item.abnormal ? item.abnormalUnitcount : item.u_count
        return item.u_start <= device.u_start && device.u_start <= item.u_start + unitCount - 1
      })

      if (abnormalDevice) {
        abnormalDevice.abnormal = true
        const endCount = Math.max(abnormalDevice.u_start + abnormalDevice.u_count, device.u_start + device.u_count)
        abnormalDevice.abnormalUnitcount = endCount - abnormalDevice.u_start

        if (abnormalDevice?.abnormalList?.length) {
          abnormalDevice.abnormalList.push(device)
        } else {
          abnormalDevice.abnormalList = [device]
        }
      } else {
        deviceMap[device.u_start] = device
      }
    } else {
      deviceMap[device.u_start] = device
    }
  })

  let unitIndex = 1
  const nextUnitList: any[] = []

  while (unitIndex <= (props.rackData.u_count || 0)) {
    if (deviceMap[unitIndex]) {
      const device = deviceMap[unitIndex]
      const unitCount = device?.abnormal ? device.abnormalUnitcount : device.u_count

      nextUnitList.push({
        ...device,
        unitCount,
        type: 'device',
        key: genKey(),
        abnormal: device?.abnormal ?? false,
        abnormalList: device.abnormalList,
      })

      unitIndex += unitCount
      device.assign = true
    } else {
      nextUnitList.push({
        type: 'gap',
        unitCount: 1,
        key: genKey(),
      })
      unitIndex += 1
    }
  }

  // Adjust the unit list and number list based on the numbering direction.
  const u_numbering_direction = props?.rackData?.u_numbering_direction || U_NUMBERING_DIRECTION.BOTTOM_TO_TOP
  if (u_numbering_direction === U_NUMBERING_DIRECTION.TOP_TO_BOTTOM) {
    unitList.value = nextUnitList
    countList.value = Array.from({ length: props.rackData.u_count || 0 }, (_, i) => i + 1)
  } else {
    unitList.value = nextUnitList.reverse()
    countList.value = Array.from({ length: props.rackData.u_count || 0 }, (_, i) => (props.rackData.u_count || 0) - i)
  }
}

function getDeviceViewImage(name: string): { front: string; rear: string } {
  const image: { front: string; rear: string } = {
    front: serverFrontImg,
    rear: serverRearImg,
  }

  switch (name) {
    case DEVICE_CITYPE_NAME.ROUTER:
      image.front = routerFrontImg
      image.rear = routerRearImg
      break
    case DEVICE_CITYPE_NAME.FIRE_WALL:
      image.front = firewallFrontImg
      image.rear = firewallRearImg
      break
    case DEVICE_CITYPE_NAME.SERVER:
      image.front = serverFrontImg
      image.rear = serverRearImg
      break
    case DEVICE_CITYPE_NAME.RAID:
      image.front = raidFrontImg
      image.rear = raidRearImg
      break
    case DEVICE_CITYPE_NAME.SWITCH:
    case DEVICE_CITYPE_NAME.FC_SWITCH:
    case DEVICE_CITYPE_NAME.F5:
      image.front = switchFrontImg
      image.rear = switchRearImg
      break
    default:
      break
  }

  return image
}

function openDeviceForm(deviceData: any) {
  deviceFormRef.value?.open(deviceData)
}

function handleDraggable({ startUnit, deviceId, oldUnitList }: { startUnit: number; deviceId: number; oldUnitList: any[] }) {
  putDevice(props.rackData._id, deviceId, { to_u_start: startUnit })
    .then(() => {
      getDeviceList()
    })
    .catch((error) => {
      console.log('putDevice fail', error)
      unitList.value = oldUnitList
    })
}

function migrateDevice(deviceId: number) {
  migrateModalRef.value?.open({
    deviceId,
    rackId: props.rackData._id,
  })
}

function refreshRackAllData() {
  getRackList()
  getDeviceList()
}

async function openDeviceDetail(data: any) {
  const deviceCIType = props.CITypeRelations.find((item) => item.id === data._type)
  deviceAttrList.value = deviceCIType?.attributes || []
  deviceCITypeId.value = data?._type

  nextTick(() => {
    CIdetailRef.value?.create(data._id)
  })
}

provide('handleSearch', refreshRackAllData)
provide('attrList', () => deviceAttrList.value)
provide('attributes', () => ({ attributes: deviceAttrList.value }))
</script>

<template>
  <div v-if="unitList.length" class="rack-view">
    <div class="rack-view-col">
      <RackUnitView
        view-type="front"
        :count-list="countList"
        :unit-list="unitList"
        :rack-data="rackData"
        @migrate-device="migrateDevice"
        @open-device-form="openDeviceForm"
        @draggable="handleDraggable"
        @refresh-rack-all-data="refreshRackAllData"
        @open-device-detail="openDeviceDetail"
      />
    </div>

    <div class="rack-view-col">
      <RackUnitView
        view-type="rear"
        :count-list="countList"
        :unit-list="unitList"
        :rack-data="rackData"
        @migrate-device="migrateDevice"
        @open-device-form="openDeviceForm"
        @draggable="handleDraggable"
        @refresh-rack-all-data="refreshRackAllData"
        @open-device-detail="openDeviceDetail"
      />
    </div>

    <DeviceForm ref="deviceFormRef" :c-i-type-relations="CITypeRelations" :rack-id="rackData._id" @ok="refreshRackAllData" />

    <MigrateModal ref="migrateModalRef" :rack-list="rackList" @ok="refreshRackAllData" />

    <CIDetailDrawer ref="CIdetailRef" :type-id="deviceCITypeId" />
  </div>
</template>

<style lang="less" scoped>
.rack-view {
  display: flex;
  overflow-y: auto;
  overflow-x: hidden;
  max-height: calc(100vh - 160px);

  &-col {
    width: 50%;
  }
}
</style>
