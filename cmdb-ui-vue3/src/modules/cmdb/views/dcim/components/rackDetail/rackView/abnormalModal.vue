<script setup lang="ts">
import { ref } from 'vue'
import { InfoCircleFilled } from '@ant-design/icons-vue'
import { useI18n } from 'vue-i18n'

const emit = defineEmits<{
  (e: 'ok', device: any): void
}>()

const { t } = useI18n()

const visible = ref(false)
const abnormalList = ref<any[]>([])
const currentSelect = ref<number | undefined>(undefined)

function open(data: any) {
  visible.value = true

  const list = [data]
  if (data?.abnormalList?.length) {
    list.push(...data.abnormalList)
  }
  abnormalList.value = list

  currentSelect.value = list?.[0]?.id ?? undefined
}

function handleCancel() {
  currentSelect.value = undefined
  abnormalList.value = []
  visible.value = false
}

function handleOk() {
  if (!currentSelect.value) {
    return
  }

  const device = abnormalList.value.find((item) => item.id === currentSelect.value)
  emit('ok', device)

  handleCancel()
}

defineExpose({ open })
</script>

<template>
  <a-modal :open="visible" :ok-text="t('cmdb.dcim.toChange')" :width="350" @ok="handleOk" @cancel="handleCancel">
    <div class="abnormal-modal-title">
      <InfoCircleFilled class="abnormal-modal-title-icon" />
      <span class="abnormal-modal-title-text">
        {{ t('cmdb.dcim.unitAbnormal') }}
      </span>
    </div>

    <div class="abnormal-modal-content">
      <div class="abnormal-modal-content-row">
        <span v-for="(item, index) in abnormalList" :key="item.id">
          {{ item.CITypeName }}
          <span class="abnormal-modal-content-name">
            {{ item.name }}
          </span>
          <span v-if="index !== abnormalList.length - 1">
            {{ t('cmdb.dcim.abnormalModalTip1') }}
          </span>
        </span>
        <span>{{ t('cmdb.dcim.abnormalModalTip2') }}</span>
      </div>
      <div class="abnormal-modal-content-row">
        {{ t('cmdb.dcim.abnormalModalTip3') }}
      </div>
    </div>

    <a-radio-group v-model:value="currentSelect">
      <a-radio v-for="item in abnormalList" :key="item.id" :value="item.id">
        {{ item.name }}
      </a-radio>
    </a-radio-group>
  </a-modal>
</template>

<style lang="less" scoped>
.abnormal-modal-title {
  display: flex;
  align-items: center;

  &-icon {
    font-size: 18px;
    color: #ff7d00;
  }

  &-text {
    margin-left: 8px;
    font-size: 16px;
    font-weight: 700;
    color: #1d2129;
  }
}

.abnormal-modal-content {
  font-size: 14px;
  font-weight: 400;
  line-height: 22px;
  margin: 9px 0px;
  color: #1d2129;

  &-name {
    color: #2f54eb;
  }
}
</style>
