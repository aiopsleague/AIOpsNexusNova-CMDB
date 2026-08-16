<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  DashboardFilled,
  InfoCircleOutlined,
  SettingFilled,
  SwapOutlined,
  ToolFilled,
} from '@ant-design/icons-vue'
import { cloneDeep } from '../../../utils/helper'
import AttributeMappingTable from './attributeMappingTable.vue'
import AdvancedConfig from './advancedConfig.vue'
import SyncStatus from './syncStatus.vue'
import SyncLogDrawer from './syncLogDrawer.vue'
import { DEFAULT_ATTR_MAPPING, type AttributeMapping } from './constants'

withDefaults(
  defineProps<{
    CITypeId: number
    CITypeName?: string
  }>(),
  { CITypeName: '' }
)

const { t } = useI18n()

interface FolderRule {
  type: string
  path?: string
}

interface SyncStats {
  total: number
  synced: number
  failed: number
}

const syncConfig = reactive<{
  enabled: boolean
  protocols: string[]
  auto_sync: boolean
  sync_strategy?: string
  attribute_mapping: AttributeMapping[]
  asset_name_template: string
  folder_rule: FolderRule
  sync_stats: SyncStats
}>({
  enabled: false,
  protocols: ['ssh'],
  auto_sync: true,
  attribute_mapping: cloneDeep(DEFAULT_ATTR_MAPPING),
  asset_name_template: '',
  folder_rule: { type: 'fixed', path: 'Default' },
  sync_stats: { total: 0, synced: 0, failed: 0 },
})

const originalConfig = ref<typeof syncConfig | null>(null)

const protocols = [
  { value: 'ssh', label: 'SSH' },
  { value: 'rdp', label: 'RDP' },
  { value: 'mysql', label: 'MySQL' },
  { value: 'redis', label: 'Redis' },
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'telnet', label: 'Telnet' },
  { value: 'vnc', label: 'VNC' },
]

const syncLogDrawer = ref<InstanceType<typeof SyncLogDrawer>>()

async function loadConfig() {
  // Placeholder: load the persisted OneTerm sync configuration.
}

function handleEnableChange(enabled: boolean) {
  if (enabled && !syncConfig.attribute_mapping.length) {
    syncConfig.attribute_mapping = cloneDeep(DEFAULT_ATTR_MAPPING)
  }
}

function handleMappingChange(mappings: AttributeMapping[]) {
  syncConfig.attribute_mapping = mappings
}

function handleAdvancedConfigChange(config: Record<string, any>) {
  // Deep merge for nested objects like folder_rule
  if (config.folder_rule) {
    syncConfig.folder_rule = { ...syncConfig.folder_rule, ...config.folder_rule }
  }
  if (config.asset_name_template !== undefined) {
    syncConfig.asset_name_template = config.asset_name_template
  }
}

async function handleSave() {
  // Validate configuration
  const requiredFields = syncConfig.attribute_mapping.filter((m) => m.required)
  const missingFields = requiredFields.filter((m) => !m.cmdb_attr)
  if (missingFields.length) {
    message.warning(t('cmdb.ciType.onetermSync.missingRequiredMapping'))
    return
  }

  // Check for duplicate mappings
  const attrCounts: Record<string, number> = {}
  syncConfig.attribute_mapping.forEach((m) => {
    if (m.cmdb_attr) {
      attrCounts[m.cmdb_attr] = (attrCounts[m.cmdb_attr] || 0) + 1
    }
  })
  const duplicates = Object.keys(attrCounts).filter((attr) => attrCounts[attr] > 1)
  if (duplicates.length) {
    message.warning(t('cmdb.ciType.onetermSync.duplicateMapping', { attr: duplicates[0] }))
    return
  }

  if (!syncConfig.asset_name_template) {
    message.warning(t('cmdb.ciType.onetermSync.assetNameTemplateRequired'))
    return
  }
  console.log('syncConfig', syncConfig)
}

function handleCancel() {
  if (originalConfig.value) {
    Object.assign(syncConfig, JSON.parse(JSON.stringify(originalConfig.value)))
  }
  message.info(t('cmdb.ciType.onetermSync.canceledChanges'))
}

async function loadSyncStats() {
  // Placeholder: load the OneTerm sync statistics.
}

function openSyncLog() {
  syncLogDrawer.value?.open()
}

onMounted(() => {
  loadConfig()
  loadSyncStats()
})
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <div class="oneterm-sync-tab">
    <!-- Basic Configuration Block -->
    <a-card class="config-card" :bordered="false">
      <template #title>
        <div class="card-title">
          <SettingFilled />
          <span>{{ t('cmdb.ciType.onetermSync.basicConfig') }}</span>
        </div>
      </template>

      <a-form
        :model="syncConfig"
        :label-col="{ span: 4 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item :label="t('cmdb.ciType.onetermSync.enableSync')">
          <a-switch v-model:checked="syncConfig.enabled" @change="handleEnableChange" />
          <div class="ant-form-explain">{{ t('cmdb.ciType.onetermSync.enableSyncHint') }}</div>
        </a-form-item>

        <a-form-item :label="t('cmdb.ciType.onetermSync.protocols')">
          <a-select
            v-model:value="syncConfig.protocols"
            mode="multiple"
            style="width: 400px"
            :placeholder="t('cmdb.ciType.onetermSync.selectProtocols')"
          >
            <a-select-option
              v-for="protocol in protocols"
              :key="protocol.value"
              :value="protocol.value"
            >
              {{ protocol.label }}
            </a-select-option>
          </a-select>
          <div class="ant-form-explain">{{ t('cmdb.ciType.onetermSync.protocolsHint') }}</div>
        </a-form-item>

        <a-form-item :label="t('cmdb.ciType.onetermSync.autoSync')">
          <a-switch v-model:checked="syncConfig.auto_sync" />
          <div class="ant-form-explain">{{ t('cmdb.ciType.onetermSync.autoSyncHint') }}</div>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- Attribute Mapping Block -->
    <a-card class="config-card" :bordered="false">
      <template #title>
        <div class="card-title">
          <SwapOutlined />
          <span>{{ t('cmdb.ciType.onetermSync.attributeMapping') }}</span>
        </div>
      </template>

      <AttributeMappingTable
        :ci-type-id="CITypeId"
        :mappings="syncConfig.attribute_mapping"
        :sync-strategy="syncConfig.sync_strategy"
        @change="handleMappingChange"
      />
    </a-card>

    <!-- Advanced Config Block -->
    <a-card class="config-card" :bordered="false">
      <template #title>
        <div class="card-title">
          <ToolFilled />
          <span>{{ t('cmdb.ciType.onetermSync.advancedConfig') }}</span>
        </div>
      </template>

      <AdvancedConfig
        :config="syncConfig"
        :ci-type-id="CITypeId"
        @change="handleAdvancedConfigChange"
      />
    </a-card>

    <!-- Sync Status Block -->
    <a-card
      class="config-card"
      :bordered="false"
    >
      <template #title>
        <div class="card-title">
          <DashboardFilled />
          <span>{{ t('cmdb.ciType.onetermSync.syncStatus') }}</span>
        </div>
      </template>

      <SyncStatus
        :ci-type-id="CITypeId"
        :stats="syncConfig.sync_stats"
        @refresh="loadSyncStats"
        @view-log="openSyncLog"
      />
    </a-card>

    <!-- Footer Actions -->
    <div class="footer-actions">
      <a-button @click="handleCancel" style="margin-right: 12px;">
        {{ t('cancel') }}
      </a-button>
      <a-button disabled type="primary" @click="handleSave">
        {{ t('save') }}
        <a-tooltip placement="topRight" :title="t('cmdb.ciType.onetermSync.unableUseTip')">
          <InfoCircleOutlined style="pointer-events: auto;" />
        </a-tooltip>
      </a-button>
    </div>

    <!-- Sync Log Drawer -->
    <SyncLogDrawer ref="syncLogDrawer" :ci-type-id="CITypeId" />
  </div>
</template>

<style lang="less" scoped>
.oneterm-sync-tab {
  padding: 0;
  max-height: calc(100vh - 130px);
  overflow-y: auto;

  .config-card {
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

    :deep(.ant-card-head-title) {
      padding: 12px 0;
    }

    .card-title {
      display: flex;
      align-items: center;
      font-size: 15px;
      font-weight: 500;
      color: @text-color_2;

      .anticon {
        margin-right: 8px;
        font-size: 16px;
        color: @primary-color;
      }
    }

    :deep(.ant-card-head) {
      border-bottom: 1px solid #f0f0f0;
      background: #fafafa;
    }

    :deep(.ant-card-body) {
      padding: 24px;
    }
  }

  .footer-actions {
    position: sticky;
    bottom: 0;
    padding: 16px 24px;
    background: #fff;
    border-top: 1px solid #f0f0f0;
    text-align: right;
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.04);
    z-index: 10;
  }
}
</style>
