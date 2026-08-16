<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Operation from './operation/index.vue'
import Scan from './scan/index.vue'

const { t } = useI18n()

const operationRef = ref<InstanceType<typeof Operation>>()

const activeKey = ref('operation')
const tabs = [
  {
    key: 'operation',
    title: 'cmdb.ipam.operationLog',
  },
  {
    key: 'scan',
    title: 'cmdb.ipam.scanLog',
  },
]

function refreshData() {
  if (activeKey.value === 'operation' && operationRef.value) {
    operationRef.value.getTableData()
  }
}

defineExpose({ refreshData })
</script>

<template>
  <div class="history">
    <div class="history-tab">
      <div
        v-for="item in tabs"
        :key="item.key"
        :class="['history-tab-item', activeKey === item.key ? 'history-tab-item-active' : '']"
        @click="activeKey = item.key"
      >
        {{ t(item.title) }}
      </div>
    </div>

    <div class="history-main">
      <Operation v-if="activeKey === 'operation'" ref="operationRef" />
      <Scan v-if="activeKey === 'scan'" />
    </div>
  </div>
</template>

<style lang="less" scoped>
.history {
  width: 100%;

  &-tab {
    display: inline-flex;
    align-items: center;
    border: solid 1px #e4e7ed;

    &-item {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 32px;
      padding: 0 20px;
      background-color: #ffffff;
      font-size: 14px;
      font-weight: 400;
      color: #4e5969;
      cursor: pointer;

      &:hover {
        color: #2f54eb;
      }

      &-active {
        background-color: #2f54eb;
        color: #ffffff !important;
      }
    }
  }

  &-main {
    width: 100%;
    margin-top: 16px;
  }
}
</style>
