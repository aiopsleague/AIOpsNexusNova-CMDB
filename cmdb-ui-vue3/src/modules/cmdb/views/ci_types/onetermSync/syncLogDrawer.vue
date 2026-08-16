<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DatabaseOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  MinusCircleOutlined,
  RedoOutlined,
} from '@ant-design/icons-vue'

const props = defineProps<{
  ciTypeId: number
}>()

const { t } = useI18n()

const visible = ref(false)
const loading = ref(false)
const detailsModalVisible = ref(false)
const currentLog = ref<any>(null)
const logData = ref<any[]>([])

const filterParams = reactive<{
  search: string
  status?: string
  timeRange: any[]
}>({
  search: '',
  status: undefined,
  timeRange: [],
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showTotal: (total: number) => `${t('cmdb.ciType.onetermSync.totalRecords')}: ${total}`,
})

const stats = reactive({
  success: 0,
  failed: 0,
  skipped: 0,
})

const columns = computed(() => [
  {
    title: t('cmdb.ciType.onetermSync.syncTime'),
    dataIndex: 'created_at',
    key: 'created_at',
    width: 180,
    sorter: true,
  },
  {
    title: t('cmdb.ciType.onetermSync.ciName'),
    dataIndex: 'ci_name',
    key: 'ci_name',
    width: 180,
  },
  {
    title: t('cmdb.ciType.onetermSync.status'),
    dataIndex: 'status',
    key: 'status',
    width: 120,
  },
  {
    title: t('cmdb.ciType.onetermSync.details'),
    dataIndex: 'details',
    key: 'details',
    ellipsis: true,
  },
  {
    title: t('operation'),
    key: 'action',
    width: 200,
  },
])

function open() {
  visible.value = true
  loadLogData()
}

function handleClose() {
  visible.value = false
  resetFilter()
}

function resetFilter() {
  filterParams.search = ''
  filterParams.status = undefined
  filterParams.timeRange = []
  pagination.current = 1
}

async function loadLogData() {
  // Placeholder: load the OneTerm sync log records.
}

function handleSearch() {
  pagination.current = 1
  loadLogData()
}

function handleTableChange(page: any) {
  pagination.current = page.current
  pagination.pageSize = page.pageSize
  loadLogData()
}

function formatTime(time: string | number | Date) {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

function getOperationColor(operation: string) {
  const colorMap: Record<string, string> = {
    create: 'green',
    update: 'blue',
    delete: 'red',
    sync: 'purple',
  }
  return colorMap[operation] || 'default'
}

function getOperationLabel(operation: string) {
  const labelMap: Record<string, string> = {
    create: t('cmdb.ciType.onetermSync.create'),
    update: t('cmdb.ciType.onetermSync.update'),
    delete: t('cmdb.ciType.onetermSync.delete'),
    sync: t('cmdb.ciType.onetermSync.sync'),
  }
  return labelMap[operation] || operation
}

function getStatusBadge(status: string) {
  const badgeMap: Record<string, string> = {
    success: 'success',
    failed: 'error',
    skipped: 'default',
  }
  return badgeMap[status] || 'default'
}

function getStatusLabel(status: string) {
  const labelMap: Record<string, string> = {
    success: t('cmdb.ciType.onetermSync.success'),
    failed: t('cmdb.ciType.onetermSync.failed'),
    skipped: t('cmdb.ciType.onetermSync.skipped'),
  }
  return labelMap[status] || status
}

function truncateText(text: string, maxLength: number) {
  if (!text) return '-'
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

function formatChanges(changes: any) {
  if (!changes) return '-'
  if (typeof changes === 'string') {
    try {
      return JSON.stringify(JSON.parse(changes), null, 2)
    } catch {
      return changes
    }
  }
  return JSON.stringify(changes, null, 2)
}

function viewCI(ciId: string | number) {
  if (!ciId || !props.ciTypeId) return
  // Navigate to the CI detail page.
  window.open(`/cmdb/cidetail/${props.ciTypeId}/${ciId}`, '_blank')
}

function viewDetails(record: any) {
  currentLog.value = record
  detailsModalVisible.value = true
}

function handleRetry() {
  // Placeholder: retry a failed sync record.
}

defineExpose({ open })
</script>

<template>
  <a-drawer
    :title="t('cmdb.ciType.onetermSync.syncLog')"
    width="900"
    :open="visible"
    :body-style="{ paddingBottom: '80px' }"
    @close="handleClose"
  >
    <div class="sync-log-drawer">
      <!-- Filter Section -->
      <div class="filter-section">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-input-search
              v-model:value="filterParams.search"
              :placeholder="t('cmdb.ciType.onetermSync.searchCIName')"
              allow-clear
              @search="handleSearch"
            />
          </a-col>
          <a-col :span="6">
            <a-select
              v-model:value="filterParams.status"
              :placeholder="t('cmdb.ciType.onetermSync.filterByStatus')"
              style="width: 100%"
              allow-clear
              @change="handleSearch"
            >
              <a-select-option value="success">
                <CheckCircleOutlined style="color: #52c41a;" />
                {{ t('cmdb.ciType.onetermSync.success') }}
              </a-select-option>
              <a-select-option value="failed">
                <CloseCircleOutlined style="color: #f5222d;" />
                {{ t('cmdb.ciType.onetermSync.failed') }}
              </a-select-option>
              <a-select-option value="skipped">
                <MinusCircleOutlined style="color: #d9d9d9;" />
                {{ t('cmdb.ciType.onetermSync.skipped') }}
              </a-select-option>
            </a-select>
          </a-col>
          <a-col :span="10">
            <a-range-picker
              v-model:value="filterParams.timeRange"
              :placeholder="[t('cmdb.ciType.onetermSync.startTime'), t('cmdb.ciType.onetermSync.endTime')]"
              style="width: 100%"
              format="YYYY-MM-DD HH:mm"
              :show-time="{ format: 'HH:mm' }"
              @change="handleSearch"
            />
          </a-col>
        </a-row>
      </div>

      <!-- Log Table -->
      <a-table
        :columns="columns"
        :data-source="logData"
        :loading="loading"
        :pagination="pagination"
        :scroll="{ x: 800, y: 'calc(100vh - 400px)' }"
        row-key="id"
        size="middle"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, text, record }">
          <template v-if="column.key === 'created_at'">
            <span>{{ formatTime(text) }}</span>
          </template>

          <template v-else-if="column.key === 'ci_name'">
            <a @click="viewCI(record.ci_id)">
              <DatabaseOutlined style="margin-right: 4px;" />
              {{ text }}
            </a>
          </template>

          <template v-else-if="column.key === 'status'">
            <a-badge
              :status="getStatusBadge(text)"
              :text="getStatusLabel(text)"
            />
          </template>

          <template v-else-if="column.key === 'details'">
            <div class="details-cell">
              <span v-if="record.status === 'success'" class="success-msg">
                {{ text || t('cmdb.ciType.onetermSync.syncSuccess') }}
              </span>
              <a-tooltip v-else-if="record.status === 'failed'" :title="text">
                <span class="error-msg">
                  <ExclamationCircleOutlined />
                  {{ truncateText(text, 30) }}
                </span>
              </a-tooltip>
              <span v-else class="skipped-msg">
                {{ text || t('cmdb.ciType.onetermSync.noChanges') }}
              </span>
            </div>
          </template>

          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button
                v-if="record.status === 'failed'"
                type="link"
                size="small"
                @click="handleRetry"
              >
                <RedoOutlined />
                {{ t('cmdb.ciType.onetermSync.retry') }}
              </a-button>
              <a-button
                type="link"
                size="small"
                @click="viewDetails(record)"
              >
                <EyeOutlined />
                {{ t('cmdb.ciType.onetermSync.viewDetails') }}
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>

      <!-- Statistics Footer -->
      <div class="stats-footer">
        <a-space size="large">
          <span>
            {{ t('cmdb.ciType.onetermSync.totalRecords') }}:
            <a-tag color="blue">{{ pagination.total }}</a-tag>
          </span>
          <span>
            {{ t('cmdb.ciType.onetermSync.successCount') }}:
            <a-tag color="green">{{ stats.success }}</a-tag>
          </span>
          <span>
            {{ t('cmdb.ciType.onetermSync.failedCount') }}:
            <a-tag color="red">{{ stats.failed }}</a-tag>
          </span>
          <span>
            {{ t('cmdb.ciType.onetermSync.skippedCount') }}:
            <a-tag color="default">{{ stats.skipped }}</a-tag>
          </span>
        </a-space>
      </div>
    </div>

    <!-- Log Details Modal -->
    <a-modal
      v-model:open="detailsModalVisible"
      :title="t('cmdb.ciType.onetermSync.logDetails')"
      :footer="null"
      width="700px"
    >
      <div v-if="currentLog" class="log-details">
        <a-descriptions bordered :column="1" size="small">
          <a-descriptions-item :label="t('cmdb.ciType.onetermSync.syncTime')">
            {{ formatTime(currentLog.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('cmdb.ciType.onetermSync.ciName')">
            <a @click="viewCI(currentLog.ci_id)">{{ currentLog.ci_name }}</a>
          </a-descriptions-item>
          <a-descriptions-item :label="t('cmdb.ciType.onetermSync.operation')">
            <a-tag :color="getOperationColor(currentLog.operation)">
              {{ getOperationLabel(currentLog.operation) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item :label="t('cmdb.ciType.onetermSync.status')">
            <a-badge
              :status="getStatusBadge(currentLog.status)"
              :text="getStatusLabel(currentLog.status)"
            />
          </a-descriptions-item>
          <a-descriptions-item
            v-if="currentLog.asset_id"
            :label="t('cmdb.ciType.onetermSync.onetermAssetId')"
          >
            {{ currentLog.asset_id }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('cmdb.ciType.onetermSync.details')">
            <pre class="details-content">{{ currentLog.details || '-' }}</pre>
          </a-descriptions-item>
          <a-descriptions-item
            v-if="currentLog.changes"
            :label="t('cmdb.ciType.onetermSync.changes')"
          >
            <pre class="changes-content">{{ formatChanges(currentLog.changes) }}</pre>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </a-drawer>
</template>

<style lang="less" scoped>
.sync-log-drawer {
  .filter-section {
    margin-bottom: 16px;
    padding: 16px;
    background: #fafafa;
    border-radius: 4px;
  }

  .details-cell {
    .success-msg {
      color: #52c41a;
    }

    .error-msg {
      color: #f5222d;
      cursor: pointer;
      width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      text-wrap: nowrap;
      display: block;

      .anticon {
        margin-right: 4px;
      }
    }

    .skipped-msg {
      color: #999;
    }
  }

  .stats-footer {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 16px 24px;
    background: #fafafa;
    border-top: 1px solid #f0f0f0;
  }

  :deep(.ant-table) {
    margin-bottom: 60px;

    .ant-table-tbody > tr > td {
      padding: 12px 16px;
    }

    .ant-table-tbody > tr:hover > td {
      background: #f5f5f5;
    }
  }
}

.log-details {
  .details-content,
  .changes-content {
    margin: 0;
    padding: 12px;
    background: #f5f5f5;
    border-radius: 4px;
    font-size: 12px;
    font-family: 'Courier New', monospace;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 300px;
    overflow-y: auto;
  }
}
</style>
