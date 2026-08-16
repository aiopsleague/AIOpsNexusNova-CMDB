<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import { ExperimentOutlined, FileTextOutlined, ReloadOutlined, SyncOutlined } from '@ant-design/icons-vue'

withDefaults(
  defineProps<{
    ciTypeId?: number
    stats?: Record<string, any>
  }>(),
  {
    ciTypeId: undefined,
    stats: () => ({ total: 0, synced: 0, failed: 0 }),
  }
)

const emit = defineEmits<{ (e: 'refresh'): void; (e: 'view-log'): void }>()

const { t } = useI18n()

const syncing = ref(false)
const refreshing = ref(false)
const testModalVisible = ref(false)
const testResult = ref<any>(null)
const syncProgress = ref<any>(null)

let pollingTimer: number | null = null

function formatTime(time: string | number | Date) {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

function handleViewLog() {
  emit('view-log')
}

async function handleSyncAll() {
  Modal.confirm({
    title: t('cmdb.ciType.onetermSync.confirmSyncAll'),
    content: t('cmdb.ciType.onetermSync.confirmSyncAllContent'),
    onOk: async () => {
      // Placeholder: trigger the full OneTerm sync.
    },
  })
}

async function handleTestSync() {
  // Placeholder: run a test sync.
}

async function handleRefresh() {
  refreshing.value = true
  try {
    emit('refresh')
  } finally {
    setTimeout(() => {
      refreshing.value = false
    }, 500)
  }
}

onBeforeUnmount(() => {
  if (pollingTimer !== null) {
    clearInterval(pollingTimer)
  }
})
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <div class="sync-status">
    <a-row :gutter="16">
      <a-col :span="6">
        <a-statistic
          :title="t('cmdb.ciType.onetermSync.totalCIs')"
          :value="stats.total"
          :value-style="stats.total > 0 ? {} : { color: '#bfbfbf' }"
        />
      </a-col>
      <a-col :span="6">
        <a-statistic
          :title="t('cmdb.ciType.onetermSync.syncedCIs')"
          :value="stats.synced"
          :value-style="stats.synced > 0 ? { color: '#52c41a' } : { color: '#bfbfbf' }"
        />
      </a-col>
      <a-col :span="6">
        <a-statistic
          :title="t('cmdb.ciType.onetermSync.notSyncedCIs')"
          :value="stats.total - stats.synced"
          :value-style="(stats.total - stats.synced) > 0 ? {} : { color: '#bfbfbf' }"
        />
      </a-col>
      <a-col :span="6">
        <a-statistic
          :title="t('cmdb.ciType.onetermSync.failedCIs')"
          :value="stats.failed"
          :value-style="stats.failed > 0 ? { color: '#f5222d' } : { color: '#bfbfbf' }"
        />
      </a-col>
    </a-row>

    <a-divider />

    <div class="sync-info">
      <div class="info-row">
        <span class="info-label">{{ t('cmdb.ciType.onetermSync.lastSyncTime') }}：</span>
        <span class="info-value">
          {{ stats.last_sync_time ? formatTime(stats.last_sync_time) : '-' }}
        </span>
      </div>
      <div class="info-row" v-if="stats.last_sync_user">
        <span class="info-label">{{ t('cmdb.ciType.onetermSync.executor') }}：</span>
        <span class="info-value">{{ stats.last_sync_user }}</span>
      </div>
      <div class="info-row" v-if="syncProgress">
        <span class="info-label">{{ t('cmdb.ciType.onetermSync.syncProgress') }}：</span>
        <div style="flex: 1; max-width: 400px;">
          <a-progress
            :percent="syncProgress.percent"
            :status="syncProgress.status"
            :format="() => `${syncProgress.processed} / ${syncProgress.total}`"
          />
        </div>
      </div>
    </div>

    <div class="action-buttons">
      <a-space>
        <a-button @click="handleViewLog">
          <FileTextOutlined />
          {{ t('cmdb.ciType.onetermSync.viewSyncLog') }}
        </a-button>
        <a-button disabled type="primary" @click="handleSyncAll" :loading="syncing">
          <SyncOutlined />
          {{ t('cmdb.ciType.onetermSync.syncAllNow') }}
        </a-button>
        <a-button disabled @click="handleTestSync">
          <ExperimentOutlined />
          {{ t('cmdb.ciType.onetermSync.testSync') }}
        </a-button>
        <a-button @click="handleRefresh" :loading="refreshing">
          <ReloadOutlined />
          {{ t('refresh') }}
        </a-button>
      </a-space>
    </div>

    <!-- Test Sync Modal -->
    <a-modal
      v-model:open="testModalVisible"
      :title="t('cmdb.ciType.onetermSync.testSyncResult')"
      :footer="null"
      width="600px"
    >
      <div v-if="testResult" class="test-result">
        <a-result
          :status="testResult.success ? 'success' : 'error'"
          :title="testResult.message"
        >
          <template #extra>
            <a-descriptions bordered size="small" :column="1" v-if="testResult.preview">
              <a-descriptions-item :label="t('cmdb.ciType.onetermSync.assetName')">
                {{ testResult.preview.name }}
              </a-descriptions-item>
              <a-descriptions-item :label="t('cmdb.ciType.onetermSync.assetIP')">
                {{ testResult.preview.ip }}
              </a-descriptions-item>
              <a-descriptions-item
                v-if="testResult.preview.asset_port"
                :label="t('cmdb.ciType.onetermSync.assetPort')"
              >
                {{ testResult.preview.asset_port }}
              </a-descriptions-item>
              <a-descriptions-item :label="t('cmdb.ciType.onetermSync.folderPath')">
                {{ testResult.preview.folder_path }}
              </a-descriptions-item>
            </a-descriptions>
          </template>
        </a-result>
      </div>
    </a-modal>
  </div>
</template>

<style lang="less" scoped>
.sync-status {
  .sync-info {
    margin: 24px 0;

    .info-row {
      display: flex;
      align-items: center;
      padding: 8px 0;

      .info-label {
        font-weight: 500;
        color: @text-color_2;
        width: 130px;
        flex-shrink: 0;
      }

      .info-value {
        color: @text-color_3;
      }
    }
  }

  .action-buttons {
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid #f0f0f0;
  }

  .test-result {
    :deep(.ant-result-title) {
      font-size: 16px;
    }
  }
}
</style>
