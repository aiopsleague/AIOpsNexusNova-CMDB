<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ProfileOutlined, ShareAltOutlined, ApartmentOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import CiTable from './modules/ciTable.vue'
import RelationTable from './modules/relation.vue'
import TypeTable from './modules/typeTable.vue'
import TriggerTable from './modules/triggerTable.vue'

const { t } = useI18n()

const activeKey = ref('1')
</script>

<template>
  <div class="operation-history">
    <a-card :bordered="false" :body-style="{ padding: '16px 24px' }">
      <a-tabs v-model:active-key="activeKey" :animated="false">
        <a-tab-pane key="1">
          <template #tab>
            <ProfileOutlined />
            {{ t('cmdb.history.ciChange') }}
          </template>
          <ci-table v-if="activeKey === '1'"></ci-table>
        </a-tab-pane>
        <a-tab-pane key="2">
          <template #tab>
            <ShareAltOutlined />
            {{ t('cmdb.history.relationChange') }}
          </template>
          <relation-table v-if="activeKey === '2'"></relation-table>
        </a-tab-pane>
        <a-tab-pane key="3">
          <template #tab>
            <ApartmentOutlined />
            {{ t('cmdb.history.ciTypeChange') }}
          </template>
          <type-table v-if="activeKey === '3'"></type-table>
        </a-tab-pane>
        <a-tab-pane key="4">
          <template #tab>
            <ThunderboltOutlined />
            {{ t('cmdb.history.triggerHistory') }}
          </template>
          <trigger-table v-if="activeKey === '4'"></trigger-table>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<style lang="less" scoped>
.operation-history {
  :deep(.ant-card-body) {
    padding: 16px 24px;
  }

  :deep(.ant-tabs) {
    .ant-tabs-bar {
      margin-bottom: 0;
      border-bottom: 1px solid #e8e8e8;
    }

    .ant-tabs-nav {
      .ant-tabs-tab {
        padding: 12px 0;
        margin-right: 32px;
        font-size: 14px;
        line-height: 22px;

        .anticon {
          margin-right: 8px;
          font-size: 14px;
        }

        &:hover {
          color: @primary-color;
        }
      }

      .ant-tabs-tab-active {
        font-weight: 500;
        color: @primary-color;
      }
    }

    .ant-tabs-content {
      padding-top: 16px;
    }
  }
}
</style>
