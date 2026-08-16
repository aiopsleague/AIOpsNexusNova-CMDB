<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons-vue'
import { uuidv4 } from '@/utils/uuid'

interface HeaderItem {
  id: string
  key: string
  value: string
}

const { t } = useI18n()

const headers = ref<HeaderItem[]>([
  {
    id: uuidv4(),
    key: '',
    value: '',
  },
])

function clearAll() {
  headers.value = [
    {
      id: uuidv4(),
      key: '',
      value: '',
    },
  ]
}

function add() {
  headers.value.push({
    id: uuidv4(),
    key: '',
    value: '',
  })
}

function deleteParam(index: number) {
  headers.value.splice(index, 1)
}

defineExpose({ headers })
</script>

<template>
  <div>
    <div class="headers-header">
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
    <div class="headers-box">
      <table>
        <tr v-for="(item, index) in headers" :key="item.id">
          <td>
            <a-input
              v-model:value="item.key"
              class="headers-input"
              :placeholder="t('cmdb.components.param', { param: `${index + 1}` })"
            />
          </td>
          <td>
            <a-input
              v-model:value="item.value"
              class="headers-input"
              :placeholder="t('cmdb.components.value', { value: `${index + 1}` })"
            />
          </td>
          <td class="headers-delete">
            <a style="color: red">
              <DeleteOutlined @click="deleteParam(index)" />
            </a>
          </td>
        </tr>
      </table>
    </div>
  </div>
</template>

<style scoped>
.headers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.headers-header :deep(.anticon) {
  cursor: pointer;
}
.headers-box table {
  width: 100%;
  border-collapse: collapse;
}
.headers-box table,
.headers-box td,
.headers-box th {
  border: 1px solid #f3f4f6;
}
.headers-input {
  border: 1px solid transparent;
}
.headers-input:focus {
  box-shadow: none;
  border-color: #2f54eb;
}
.headers-input:hover {
  border-color: #2f54eb;
}
.headers-delete {
  text-align: center;
}
</style>
