<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons-vue'
import { uuidv4 } from '@/utils/uuid'
import emptyImg from '@/assets/data_empty.png'

interface ParameterItem {
  id: string
  key: string
  value: string
}

const { t } = useI18n()

const parameters = ref<ParameterItem[]>([])

function clearAll() {
  parameters.value = []
}

function add() {
  parameters.value.push({
    id: uuidv4(),
    key: '',
    value: '',
  })
}

function deleteParam(index: number) {
  parameters.value.splice(index, 1)
}

defineExpose({ parameters })
</script>

<template>
  <div>
    <div class="parameters-header">
      <span>{{ t('cmdb.components.requestParam') }}</span>
      <a-space>
        <a-tooltip :title="t('cmdb.components.clear')">
          <DeleteOutlined @click="clearAll" />
        </a-tooltip>
        <a-tooltip :title="t('new')">
          <PlusOutlined @click="add" />
        </a-tooltip>
      </a-space>
    </div>
    <div v-if="parameters && parameters.length" class="parameters-box">
      <table>
        <tr v-for="(item, index) in parameters" :key="item.id">
          <td>
            <a-input
              v-model:value="item.key"
              class="parameters-input"
              :placeholder="t('cmdb.components.param', { param: `${index + 1}` })"
            />
          </td>
          <td>
            <a-input
              v-model:value="item.value"
              class="parameters-input"
              :placeholder="t('cmdb.components.value', { value: `${index + 1}` })"
            />
          </td>
          <td class="parameters-delete">
            <a style="color: red">
              <DeleteOutlined @click="deleteParam(index)" />
            </a>
          </td>
        </tr>
      </table>
    </div>
    <a-empty v-else :image-style="{ height: '60px' }">
      <template #image><img :src="emptyImg" /></template>
      <template #description>{{ t('cmdb.components.noParamRequest') }}</template>
      <a-button type="primary" size="small" @click="add">
        <template #icon><PlusOutlined /></template>
        {{ t('add') }}
      </a-button>
    </a-empty>
  </div>
</template>

<style scoped>
.parameters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.parameters-header :deep(.anticon) {
  cursor: pointer;
}
.parameters-box table {
  width: 100%;
  border-collapse: collapse;
}
.parameters-box table,
.parameters-box td,
.parameters-box th {
  border: 1px solid #f3f4f6;
}
.parameters-input {
  border: 1px solid transparent;
}
.parameters-input:focus {
  box-shadow: none;
  border-color: #2f54eb;
}
.parameters-input:hover {
  border-color: #2f54eb;
}
.parameters-delete {
  text-align: center;
}
</style>
