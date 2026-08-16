<script setup lang="ts">
import { computed, inject, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { CopyOutlined, MinusCircleOutlined, PlusCircleOutlined, QuestionCircleOutlined } from '@ant-design/icons-vue'
import { uuidv4 } from '@/utils/uuid'
import { cloneDeep } from '@/modules/cmdb/utils/helper'

const { t } = useI18n()

const provide_labelCol = inject<() => any>('provide_labelCol')

const nodes = ref<any[]>([])

const labelCol = computed(() => provide_labelCol?.())

function initNodesFunc(list: any[]) {
  nodes.value = cloneDeep(list)
}

function addNode() {
  nodes.value.push({
    id: uuidv4(),
    ip: '',
    community: 'public',
    version: '',
  })
}

function removeNode(removeId: string, minLength: number) {
  if (nodes.value.length <= minLength) {
    message.error(t('cmdb.ciType.deleteRelationAdTip'))
    return
  }
  const idx = nodes.value.findIndex((item) => item.id === removeId)
  if (idx > -1) {
    nodes.value.splice(idx, 1)
  }
}

function copyNode(id: string) {
  const target = nodes.value.find((item) => item.id === id)
  if (target) {
    nodes.value.push({
      ...target,
      id: uuidv4(),
    })
  }
}

function getNodeValue() {
  return nodes.value.map((node) => pick(node, ['ip', 'community', 'version']))
}

function pick(obj: Record<string, any>, keys: string[]) {
  const result: Record<string, any> = {}
  keys.forEach((key) => {
    result[key] = obj[key]
  })
  return result
}

defineExpose({ initNodesFunc, getNodeValue })
</script>

<template>
  <a-form-item
    :label-col="labelCol"
    :wrapper-col="{ span: 18 }"
  >
    <template #label>
      <span style="position: relative; white-space: pre">
        {{ t('cmdb.ciType.nodeList') }}
        <a-tooltip :title="t('cmdb.ciType.snmpFormTip1')">
          <QuestionCircleOutlined />
        </a-tooltip>
      </span>
    </template>
    <div class="node-setting-wrap">
      <vxe-table
        :data="nodes"
        size="mini"
        show-header-overflow
        :row-config="{ height: 42 }"
        border
        :min-height="78"
      >
        <vxe-column width="170" :title="t('cmdb.ciType.nodeSettingIp')">
          <template #default="{ row }">
            <a-input v-model:value="row.ip"></a-input>
          </template>
        </vxe-column>
        <vxe-column width="170" :title="t('cmdb.ciType.nodeSettingCommunity')">
          <template #default="{ row }">
            <a-input v-model:value="row.community"></a-input>
          </template>
        </vxe-column>
        <vxe-column width="170" :title="t('cmdb.ciType.nodeSettingVersion')">
          <template #default="{ row }">
            <a-select
              v-model:value="row.version"
              :placeholder="t('cmdb.ciType.nodeSettingVersionTip')"
              allow-clear
              class="node-setting-select"
            >
              <a-select-option value="1">
                v1
              </a-select-option>
              <a-select-option value="2c">
                v2c
              </a-select-option>
            </a-select>
          </template>
        </vxe-column>
        <vxe-column min-width="90">
          <template #default="{ row }">
            <div class="action">
              <a @click="() => copyNode(row.id)">
                <CopyOutlined />
              </a>
              <a @click="() => removeNode(row.id, 1)">
                <MinusCircleOutlined />
              </a>
              <a @click="addNode">
                <PlusCircleOutlined />
              </a>
            </div>
          </template>
        </vxe-column>
      </vxe-table>
    </div>
  </a-form-item>
</template>

<style lang="less" scoped>
.node-setting-wrap {
  max-width: 600px;

  :deep(.ant-input-clear-icon) {
    color: rgba(0, 0, 0, 0.25);

    &:hover {
      color: rgba(0, 0, 0, 0.45);
    }
  }

  .node-setting-select {
    width: 150px;
  }
}

.action {
  height: 36px;
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
