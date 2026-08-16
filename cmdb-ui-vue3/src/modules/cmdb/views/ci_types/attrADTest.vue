<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import { getAdtSyncHistories } from '@/modules/cmdb/api/discovery'

const props = withDefaults(defineProps<{ adtId?: number }>(), { adtId: 0 })

const { t } = useI18n()

const checkModalVisible = ref(false)
const checkTableData = ref<any[]>([])
const testModalVisible = ref(false)
const testResultText = ref('')

async function showCheckModal() {
  await queryCheckTableData()
  checkModalVisible.value = true
}

async function queryCheckTableData() {
  const res = await getAdtSyncHistories(props.adtId)
  if (res?.result?.length) {
    const newTableData = res.result
    newTableData.forEach((item: any) => {
      const syncTime = dayjs(item.sync_at).valueOf()
      const nowTime = new Date().getTime()
      item.status = nowTime - syncTime <= 10 * 60 * 1000
    })
    checkTableData.value = newTableData
  } else {
    checkTableData.value = []
  }
}
</script>

<template>
  <div>
    <div class="attr-ad-header attr-ad-header-margin">{{ t('cmdb.ciType.configCheckTitle') }}</div>
    <div class="attr-ad-content">
      <div class="ad-test-title-info">{{ t('cmdb.ciType.checkTestTip') }}</div>
      <a-button type="primary" class="ops-button-ghost ad-test-btn" ghost @click="showCheckModal">
        {{ t('cmdb.ciType.checkTestBtn') }}
      </a-button>
      <div class="ad-test-btn-info">{{ t('cmdb.ciType.checkTestTip2') }}</div>
    </div>

    <a-modal v-model:open="checkModalVisible" :footer="null" :width="900">
      <div class="check-modal-title">{{ t('cmdb.ciType.checkModalTitle') }}</div>
      <div class="check-modal-info">{{ t('cmdb.ciType.checkModalTip') }}</div>
      <div class="check-modal-info">{{ t('cmdb.ciType.checkModalTip1') }}</div>
      <div class="check-modal-info">{{ t('cmdb.ciType.checkModalTip2') }}</div>
      <vxe-table
        size="mini"
        :data="checkTableData"
        :scroll-y="{ enabled: true }"
        height="400"
        class="check-modal-table"
      >
        <vxe-column field="oneagent_name" :title="t('cmdb.ciType.checkModalColumn1')"></vxe-column>
        <vxe-column field="oneagent_id" :title="t('cmdb.ciType.checkModalColumn2')"></vxe-column>
        <vxe-column field="status" :min-width="70" :title="t('cmdb.ciType.checkModalColumn3')">
          <template #default="{ row }">
            <div
              :class="['check-modal-status', row.status ? 'check-modal-status-online' : 'check-modal-status-offline']"
            >
              {{ t(`cmdb.ciType.${row.status ? 'checkModalColumnStatus1' : 'checkModalColumnStatus2'}`) }}
            </div>
          </template>
        </vxe-column>
        <vxe-column field="sync_at" :title="t('cmdb.ciType.checkModalColumn4')"></vxe-column>
      </vxe-table>
    </a-modal>

    <a-modal v-model:open="testModalVisible" :footer="null" :width="596">
      <div class="check-modal-title">{{ t('cmdb.ciType.testModalTitle') }}</div>
      <p class="test-modal-text">{{ testResultText }}</p>
    </a-modal>
  </div>
</template>

<style lang="less" scoped>
.attr-ad-content {
  margin-left: 17px;
  margin-bottom: 20px;

  .ad-test-title-info {
    color: @text-color_3;
    font-size: 12px;
    font-weight: 400;
  }

  .ad-test-btn {
    margin-top: 30px;
  }

  .ad-test-btn-info {
    margin-top: 4px;
    color: @text-color_3;
    font-size: 12px;
    font-weight: 400;
  }
}

.check-modal-table {
  margin-top: 14px;
}

.check-modal-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 5px;
}

.check-modal-info {
  color: @text-color_3;
  font-size: 12px;
  font-weight: 400;
}

.check-modal-status {
  display: inline-block;
  padding: 2px 11px;
  font-size: 12px;
  font-weight: 400;

  &-online {
    background-color: #e5f6df;
    color: #30ad2d;
  }

  &-offline {
    background-color: #ffdada;
    color: #f14e4e;
  }
}

.test-modal-text {
  margin-top: 14px;
  padding: 12px;
  width: 100%;
  height: 312px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  border: solid 1px @border-color-base;
}
</style>
