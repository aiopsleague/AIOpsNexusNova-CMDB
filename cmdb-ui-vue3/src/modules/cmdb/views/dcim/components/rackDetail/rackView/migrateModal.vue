<script setup lang="ts">
import { reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { migrateDevice } from '@/modules/cmdb/api/dcim'

withDefaults(
  defineProps<{
    rackList?: any[]
  }>(),
  {
    rackList: () => [],
  }
)

const emit = defineEmits<{
  (e: 'ok'): void
}>()

const { t } = useI18n()

const visible = ref(false)
const deviceMigrateFormRef = ref<any>()

const form = reactive<{
  to_rack_id?: number | string
  to_u_start?: number | string
}>({
  to_rack_id: undefined,
  to_u_start: undefined,
})

const formRules = {
  to_rack_id: [{ required: true, message: t('placeholder2') }],
  to_u_start: [{ required: true, message: t('placeholder1') }],
}

let deviceId = ''
let rackId = ''

function open(data: any) {
  visible.value = true
  deviceId = data?.deviceId || ''
  rackId = data?.rackId || ''
}

function handleCancel() {
  deviceId = ''
  rackId = ''
  form.to_rack_id = undefined
  form.to_u_start = undefined

  deviceMigrateFormRef.value?.clearValidate()
  visible.value = false
}

function handleOk() {
  deviceMigrateFormRef.value
    .validate()
    .then(async () => {
      await migrateDevice(rackId, deviceId, { ...form })

      message.success(t('cmdb.dcim.migrationSuccess'))
      handleCancel()
      emit('ok')
    })
    .catch(() => {})
}

defineExpose({ open })
</script>

<template>
  <a-modal :title="t('cmdb.dcim.deviceMigrate')" :open="visible" :width="500" @ok="handleOk" @cancel="handleCancel">
    <a-form
      ref="deviceMigrateFormRef"
      :model="form"
      :rules="formRules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
      class="device-migrate"
    >
      <a-form-item :label="t('cmdb.dcim.rack')" name="to_rack_id">
        <a-select v-model:value="form.to_rack_id" show-search allow-clear option-filter-prop="title">
          <a-select-option v-for="rack in rackList" :key="rack._id" :value="rack._id" :title="rack.name">
            {{ rack.name }}
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="t('cmdb.dcim.unitStart')" name="to_u_start">
        <a-input-number v-model:value="form.to_u_start" :min="1" :precision="0" class="device-migrate-input" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<style lang="less" scoped>
.device-migrate {
  &-input {
    width: 100%;
  }
}
</style>
