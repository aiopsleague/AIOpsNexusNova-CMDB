<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CheckCircleFilled, CloseCircleFilled } from '@ant-design/icons-vue'

const props = withDefaults(
  defineProps<{
    tableData?: any[]
  }>(),
  {
    tableData: () => [],
  }
)

const { t } = useI18n()

const windowHeight = computed(() => window.innerHeight)
const tableHeight = computed(() => `${windowHeight.value - 337}px`)
</script>

<template>
  <div class="subnet-table">
    <div class="subnet-table-title">
      {{ t('cmdb.ipam.onlineUsageStats') }}
    </div>

    <vxe-table
      ref="xTable"
      show-overflow
      show-header-overflow
      highlight-hover-row
      :data="props.tableData"
      size="small"
      :height="tableHeight"
      :column-config="{ resizable: true }"
      class="ops-unstripe-table"
    >
      <vxe-column :title="t('cmdb.ipam.subnetName')" min-width="130" field="name"></vxe-column>
      <vxe-column title="CIDR" field="cidr" min-width="130"></vxe-column>
      <vxe-column :title="t('cmdb.ipam.addressCount')" field="hosts_count" min-width="70"></vxe-column>
      <vxe-column :title="t('cmdb.ipam.onlineRatio')" field="onlineRatio" min-width="180">
        <template #default="{ row }">
          <div class="subnet-table-ratio">
            <div class="subnet-table-ratio-value">
              {{ row.used_ratio }}%
            </div>
            <div class="subnet-table-ratio-progress">
              <div
                class="subnet-table-ratio-progress-content"
                :style="{
                  width: row.used_ratio + '%'
                }"
              ></div>
            </div>
            <div class="subnet-table-ratio-count">
              {{ row.used_count }}/{{ row.hosts_count }}
            </div>
          </div>
        </template>
      </vxe-column>

      <vxe-column :title="t('cmdb.ipam.assigned')" field="assign_count" min-width="70"></vxe-column>

      <vxe-column :title="t('cmdb.ipam.free')" field="free_count" min-width="50"></vxe-column>

      <vxe-column :title="t('cmdb.ipam.scanEnable')" field="scan_enabled" min-width="100">
        <template #default="{ row }">
          <div v-if="row.scan_enabled" class="subnet-table-scan-yes">
            <CheckCircleFilled class="subnet-table-scan-yes-icon" />
            <div class="subnet-table-scan-yes-text">{{ t('yes') }}</div>
          </div>
          <div v-else class="subnet-table-scan-no">
            <CloseCircleFilled class="subnet-table-scan-no-icon" />
            <div class="subnet-table-scan-no-text">{{ t('no') }}</div>
          </div>
        </template>
      </vxe-column>

      <vxe-column :title="t('cmdb.ipam.lastScanTime')" field="last_scan_time" min-width="100"></vxe-column>
    </vxe-table>
  </div>
</template>

<style lang="less" scoped>
.subnet-table {
  width: 100%;
  margin-top: 20px;

  &-title {
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 16px;
  }

  &-ratio {
    display: flex;
    align-items: center;

    &-value {
      font-size: 14px;
      font-weight: 400;
      color: #4e5969;
    }

    &-progress {
      width: 84px;
      height: 6px;
      border-radius: 6px;
      background-color: #ebeff8;
      margin-left: 12px;

      &-content {
        height: 6px;
        border-radius: 6px;
        background-color: #7f97fa;
      }
    }

    &-count {
      margin-left: 5px;
      font-size: 10px;
      font-weight: 400;
      color: #86909c;
    }
  }

  &-scan-yes {
    padding: 4px 7px;
    border-radius: 1px;
    background-color: #dcf3e3;
    display: inline-flex;
    align-items: center;
    justify-content: center;

    &-icon {
      font-size: 12px;
      color: #00b42a;
    }

    &-text {
      font-size: 12px;
      font-weight: 400;
      color: #30ad2d;
      margin-left: 4px;
    }
  }

  &-scan-no {
    padding: 0px 7px;
    border-radius: 1px;
    background-color: #e4e7ed;
    display: inline-flex;
    align-items: center;
    justify-content: center;

    &-icon {
      font-size: 12px;
      color: #a5a9bc;
    }

    &-text {
      font-size: 12px;
      font-weight: 400;
      color: #4e5969;
      margin-left: 4px;
    }
  }
}
</style>
