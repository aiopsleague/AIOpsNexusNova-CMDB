<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { MinusCircleOutlined, PlusCircleOutlined, PlusCircleTwoTone } from '@ant-design/icons-vue'
import { defaultConfig } from './constants'

const { t } = useI18n()

const configData = ref<Record<string, any>[]>([])

function uuidv4(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

function pickBy(obj: Record<string, any>, predicate: (value: any, key: string) => boolean): Record<string, any> {
  const result: Record<string, any> = {}
  Object.entries(obj).forEach(([key, value]) => {
    if (predicate(value, key)) {
      result[key] = value
    }
  })
  return result
}

function setData(data: any[] = []) {
  configData.value = data.map((item) => {
    return {
      ...item,
      client_id: uuidv4(),
    }
  })
}

function getData() {
  let isError = false
  const keyArr = ['name', 'host', 'account', 'password', 'id']
  const data = configData.value.map((item) => {
    return pickBy(item, (v, k) => {
      return keyArr.includes(k) && v
    })
  })

  const errMsg: Record<string, string> = {
    name: t('name'),
    host: t('cmdb.ciType.host'),
    account: t('cmdb.ciType.account'),
  }

  let errKey = ''
  for (let i = 0; i < data.length && !errKey; i++) {
    const item = data[i]
    const curErrKey = keyArr.find((key) => !item?.[key] && errMsg?.[key])
    if (curErrKey) {
      errKey = curErrKey
    }
  }

  if (errKey) {
    isError = true
    message.error(`${t('placeholder1')} ${errMsg[errKey]}`)
  }

  return {
    isError,
    data,
  }
}

function deleteItem(index: number) {
  configData.value.splice(index, 1)
}

function addItem() {
  configData.value.push({
    name: `${t('cmdb.ad.defaultName')}${configData.value.length + 1}`,
    ...defaultConfig['vcenter'],
  })
}

defineExpose({ setData, getData })
</script>

<template>
  <div class="table-wrap">
    <div v-if="configData.length === 0" class="add-btn" @click="addItem">
      <PlusCircleTwoTone class="add-btn-icon" />
      <span class="add-btn-text">{{ t('cmdb.ad.addConfig') }}</span>
    </div>
    <template v-else>
      <vxe-table
        :data="configData"
        size="mini"
        show-overflow
        show-header-overflow
        :row-config="{ height: 42 }"
        :min-height="78"
      >
        <vxe-column width="170" :title="t('name')">
          <template #header="{ column }">
            <span class="column-header-required">*</span>
            {{ column.title }}
          </template>
          <template #default="{ row }">
            <a-input v-model:value="row.name"></a-input>
          </template>
        </vxe-column>
        <vxe-column width="200" :title="t('cmdb.ciType.host')">
          <template #header="{ column }">
            <span class="column-header-required">*</span>
            {{ column.title }}
          </template>
          <template #default="{ row }">
            <a-input v-model:value="row.host"></a-input>
          </template>
        </vxe-column>
        <vxe-column width="200" :title="t('cmdb.ciType.account')">
          <template #header="{ column }">
            <span class="column-header-required">*</span>
            {{ column.title }}
          </template>
          <template #default="{ row }">
            <a-input v-model:value="row.account"></a-input>
          </template>
        </vxe-column>
        <vxe-column width="200" :title="t('cmdb.ciType.password')">
          <template #default="{ row }">
            <a-input-password v-model:value="row.password"></a-input-password>
          </template>
        </vxe-column>
      </vxe-table>
      <div class="actions">
        <div v-for="(item, index) in configData" :key="item.client_id" class="actions-item">
          <MinusCircleOutlined class="actions-item-btn" @click="deleteItem(index)" />
          <PlusCircleOutlined class="actions-item-btn" @click="addItem" />
        </div>
      </div>
    </template>
  </div>
</template>

<style lang="less" scoped>
.table-wrap {
  display: flex;

  .add-btn {
    padding: 5px 12px;
    cursor: pointer;
    border-radius: 1px;
    border: 1px solid #B1C9FF;
    background-color: #F4F9FF;
    display: flex;
    align-items: center;
    justify-content: center;

    &-icon {
      font-size: 12px;
    }

    &-text {
      font-size: 12px;
      font-weight: 400;
      color: #2F54EB;
      margin-left: 6px;
    }
  }

  .column-header-required {
    color: #FD4C6A;
  }

  .actions {
    padding-top: 36px;
    margin-left: 16px;

    &-item {
      height: 42px;
      display: flex;
      align-items: center;
      gap: 12px;

      &-btn {
        cursor: pointer;
        color: #2f54eb;
      }
    }
  }
}
</style>
