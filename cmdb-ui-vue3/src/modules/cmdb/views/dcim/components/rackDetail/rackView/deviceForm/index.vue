<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { postDevice } from '@/modules/cmdb/api/dcim'
import DeviceSelect from './deviceSelect.vue'

const props = withDefaults(
  defineProps<{
    CITypeRelations?: any[]
    rackId?: number | string
  }>(),
  {
    CITypeRelations: () => [],
    rackId: 0,
  }
)

const emit = defineEmits<{
  (e: 'ok'): void
}>()

const { t } = useI18n()

const visible = ref(false)
const deviceFormRef = ref<any>()

const form = reactive<{
  CITypeId?: number
  deviceId?: number
  unitStart?: number
  unitCount?: number
}>({
  CITypeId: undefined,
  deviceId: undefined,
  unitStart: undefined,
  unitCount: undefined,
})

const deviceName = ref('')
const showUnitCount = ref(true)

const formRules = {
  CITypeId: [{ required: true, message: t('placeholder2') }],
  deviceId: [{ required: true, message: t('placeholder2') }],
  unitStart: [{ required: true, message: t('placeholder1') }],
  unitCount: [{ required: true, message: t('placeholder1') }],
}

const currentCITYpe = computed(() => {
  return props.CITypeRelations.find((CIType) => CIType?.id === form.CITypeId) || {}
})

function open(deviceData: any) {
  visible.value = true

  if (deviceData) {
    form.CITypeId = deviceData?.CITypeId ?? undefined
    form.deviceId = deviceData?.deviceId ?? undefined
    form.unitStart = deviceData?.unitStart ?? undefined
    form.unitCount = deviceData?.unitCount ?? undefined

    if (form.unitCount) {
      showUnitCount.value = false
    }
    deviceName.value = deviceData?.name || ''
  }
}

function handleCancel() {
  form.CITypeId = undefined
  form.deviceId = undefined
  form.unitStart = undefined
  form.unitCount = undefined
  deviceName.value = ''
  showUnitCount.value = true
  deviceFormRef.value?.clearValidate()

  visible.value = false
}

function handleOk() {
  deviceFormRef.value
    .validate()
    .then(async () => {
      await postDevice(props.rackId, form.deviceId as number, {
        u_start: form.unitStart,
        u_count: form.unitCount,
      })

      handleCancel()
      message.success(t('addSuccess'))
      emit('ok')
    })
    .catch(() => {})
}

function handleDeviceChange({ name, value, unitCount }: { name: string; value: number; unitCount?: number }) {
  form.deviceId = value
  deviceName.value = name

  form.unitCount = unitCount || undefined
  showUnitCount.value = !unitCount
}

function handleCITypeChange() {
  form.deviceId = undefined
  deviceName.value = ''
  showUnitCount.value = true
  form.unitCount = undefined
}

defineExpose({ open })
</script>

<template>
  <a-modal :open="visible" :width="500" :title="t('cmdb.dcim.addDevice')" @ok="handleOk" @cancel="handleCancel">
    <a-form
      ref="deviceFormRef"
      :model="form"
      :rules="formRules"
      :label-col="{ span: 5 }"
      :wrapper-col="{ span: 19 }"
      class="device-form"
    >
      <a-form-item :label="t('cmdb.dcim.ciType')" name="CITypeId">
        <a-select
          v-model:value="form.CITypeId"
          show-search
          allow-clear
          option-filter-prop="title"
          @change="handleCITypeChange"
        >
          <a-select-option
            v-for="item in CITypeRelations"
            :key="item.id"
            :value="item.id"
            :title="item.alias || item.name"
          >
            {{ item.alias || item.name }}
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="t('cmdb.dcim.device')" name="deviceId">
        <a-popover trigger="click" placement="bottom">
          <template #content>
            <DeviceSelect
              :c-i-type-id="form.CITypeId"
              :current-c-i-type="currentCITYpe"
              :current-select="form.deviceId"
              @change="handleDeviceChange"
            />
          </template>
          <div class="device-form-select">
            {{ deviceName }}
          </div>
        </a-popover>
      </a-form-item>

      <a-form-item :label="t('cmdb.dcim.unitStart')" name="unitStart">
        <a-input-number v-model:value="form.unitStart" :min="1" :precision="0" class="device-form-input" />
      </a-form-item>

      <a-form-item v-if="showUnitCount" :label="t('cmdb.dcim.unitCount')" name="unitCount">
        <a-input-number v-model:value="form.unitCount" :min="1" :precision="0" class="device-form-input" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<style lang="less" scoped>
.device-form {
  &-select {
    border: 1px solid #e4e7ed;
    border-radius: 2px;
    line-height: 32px;
    min-height: 32px;
    padding: 0 12px;
    cursor: pointer;

    &:hover {
      border-color: #597ef7;
    }
  }

  &-input {
    width: 100%;
  }
}
</style>
