<script setup lang="ts">
import { computed, inject, provide, ref } from 'vue'
import { DeleteOutlined, EditOutlined } from '@ant-design/icons-vue'
import { Modal, message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { DCIM_TYPE } from '../../constants'
import { deleteDCIM } from '@/modules/cmdb/api/dcim'
import { getCITypeChildren } from '@/modules/cmdb/api/CITypeRelation'
import { searchCIRelation } from '@/modules/cmdb/api/CIRelation'
import RackView from './rackView/index.vue'
import RackGroupAttr from './rackGroupAttr/index.vue'
import DeviceList from './deviceList/index.vue'
import OperationLog from './operationLog/index.vue'

const props = withDefaults(
  defineProps<{
    roomId?: string
    rackCITYpe?: Record<string, any>
    rackList?: any[]
  }>(),
  {
    roomId: '',
    rackCITYpe: () => ({}),
    rackList: () => [],
  }
)

const emit = defineEmits<{
  (e: 'openForm', payload: { dcimType: string; parentId: string; nodeId?: number }): void
  (e: 'refreshRackList'): void
}>()

const { t } = useI18n()

const getTreeData = inject<() => void>('getTreeData', () => {})
const getRackList = inject<() => void>('getRackList', () => {})

const visible = ref(false)
const rackId = ref(0)
const tabActive = ref('rackView')

const CITypeRelations = ref<any[]>([])
const deviceList = ref<any[]>([])

const rackData = computed(() => {
  return props.rackList.find((item) => item._id === rackId.value) || {}
})

const countList = computed(() => {
  const { u_count = 0, u_used_ratio = 0, u_slot_abnormal = false } = rackData.value

  return [
    {
      name: 'cmdb.dcim.deviceCount',
      value: deviceList.value?.length || 0,
    },
    {
      name: 'cmdb.dcim.unitCount',
      value: u_count,
    },
    {
      name: 'cmdb.dcim.unitAbnormal',
      value: u_slot_abnormal ? t('yes') : t('no'),
    },
    {
      name: 'cmdb.dcim.utilizationRation',
      value: `${u_used_ratio}%`,
    },
  ]
})

async function open(id: number) {
  rackId.value = id
  visible.value = true

  if (!CITypeRelations.value.length) {
    const res = await getCITypeChildren(props.rackCITYpe.id)
    CITypeRelations.value = res?.children || []
  }

  await getDeviceList()
}

async function getDeviceList() {
  if (!rackId.value) {
    return
  }

  const res = await searchCIRelation(`root_id=${rackId.value}&level=1&count=10000`)
  const list = res?.result || []
  list.sort((a: any, b: any) => a.u_start - b.u_start)
  deviceList.value = list
}

function handleClose() {
  rackId.value = 0
  tabActive.value = 'rackView'
  visible.value = false
}

function clickEdit() {
  emit('openForm', {
    dcimType: DCIM_TYPE.RACK,
    parentId: props.roomId,
    nodeId: rackId.value,
  })
  handleClose()
}

function clickDelete() {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete'),
    onOk: () => {
      deleteDCIM(DCIM_TYPE.RACK, rackId.value).then(() => {
        message.success(t('deleteSuccess'))
        handleClose()
        getRackList()
        getTreeData()
      })
    },
  })
}

function refreshRackList() {
  emit('refreshRackList')
}

provide('getDeviceList', getDeviceList)

defineExpose({ open, refreshRackList })
</script>

<template>
  <CustomDrawer
    width="825px"
    :open="visible"
    :body-style="{ height: '100vh', padding: '0px' }"
    :has-title="false"
    destroy-on-close
    @close="handleClose"
  >
    <div class="rack-detail">
      <div class="rack-header">
        <div class="rack-header-left">
          <div class="rack-header-name">
            <span class="rack-header-name-label">
              {{ t('cmdb.dcim.rack') }}
            </span>
            <a-tooltip :title="rackData.name">
              <span class="rack-header-name-value">
                {{ rackData.name }}
              </span>
            </a-tooltip>
          </div>
          <EditOutlined class="rack-header-edit" @click="clickEdit" />
          <DeleteOutlined class="rack-header-delete" @click="clickDelete" />
        </div>

        <div class="rack-header-right">
          <div v-for="(item, index) in countList" :key="index" class="rack-header-count">
            <span class="rack-header-count-name">{{ t(item.name) }}:</span>
            <span class="rack-header-count-value">{{ item.value }}</span>
          </div>
        </div>
      </div>

      <a-tabs v-model:active-key="tabActive" class="rack-detail-tabs">
        <a-tab-pane key="rackView" :tab="t('cmdb.dcim.rackView')">
          <RackView
            :c-i-type-relations="CITypeRelations"
            :rack-data="rackData"
            :device-list="deviceList"
            :rack-list="rackList"
          />
        </a-tab-pane>

        <a-tab-pane key="rackDetail" :tab="t('cmdb.dcim.rackDetail')">
          <RackGroupAttr :ci="rackData" :rack-c-i-type-id="rackCITYpe.id" />
        </a-tab-pane>

        <a-tab-pane key="deviceList" :tab="t('cmdb.dcim.deviceList')">
          <DeviceList :all-device-list="deviceList" :c-i-type-relations="CITypeRelations" />
        </a-tab-pane>

        <a-tab-pane key="operationLog" :tab="t('cmdb.dcim.operationLog')">
          <OperationLog v-if="tabActive === 'operationLog'" :rack-id="rackId" />
        </a-tab-pane>
      </a-tabs>
    </div>
  </CustomDrawer>
</template>

<style lang="less" scoped>
.rack-detail {
  .rack-header {
    height: 44px;
    padding: 0px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: #f7f8fa;

    &-left {
      display: flex;
      align-items: center;
      width: 100%;
      overflow: hidden;
    }

    &-name {
      display: flex;
      align-items: center;
      font-size: 16px;
      font-weight: 900;
      color: #1d2129;
      max-width: calc(100% - 48px);

      &-label {
        flex-shrink: 0;
      }

      &-value {
        color: #2f54eb;
        margin-left: 2px;

        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    &-edit {
      margin-left: 8px;
      font-size: 12px;
    }

    &-delete {
      margin-left: 12px;
      font-size: 12px;
      color: #fd4c6a;
    }

    &-right {
      display: flex;
      align-items: center;
      column-gap: 30px;
      flex-shrink: 0;
      margin-left: 12px;
    }

    &-count {
      display: flex;
      align-items: center;

      &-name {
        font-size: 12px;
        font-weight: 400;
        color: #4e5969;
      }

      &-value {
        font-size: 14px;
        font-weight: 700;
        color: #1d2129;
        margin-left: 5px;
      }
    }
  }

  &-tabs {
    margin-left: 19px;
    margin-right: 19px;

    :deep(.ant-tabs-bar) {
      display: inline-block;
    }
  }
}
</style>
