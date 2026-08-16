<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { MinusCircleOutlined, PlusCircleOutlined, PlusOutlined } from '@ant-design/icons-vue'
import dayjs, { type Dayjs } from 'dayjs'
import DefineLabel from './defineLabel.vue'
import { ENUM_VALUE_TYPE } from '../constants'

const props = withDefaults(
  defineProps<{
    value?: any[]
    disabled?: boolean
    // Enum value control type
    enumValueType?: string
  }>(),
  { value: () => [], disabled: false, enumValueType: ENUM_VALUE_TYPE.INPUT }
)

const emit = defineEmits<{
  (e: 'change', v: any[]): void
  (e: 'update:value', v: any[]): void
}>()

const { t } = useI18n()

function genId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

const defineList = computed(() =>
  props.value.map((item) => ({
    value: item?.[0] ?? '',
    ...(item?.[1] ?? {}),
    id: genId(),
  }))
)

function emitValue(list: any[]) {
  emit('change', list)
  emit('update:value', list)
}

function addData(index?: number) {
  const list = cloneDeep(props.value)
  list.splice((index ?? -1) + 1, 0, ['', { style: {}, icon: {}, label: '' }])
  emitValue(list)
}

function deleteData(index: number) {
  if (props.value.length <= 1) {
    message.error(t('cmdb.ad.deleteTip'))
    return
  }
  const list = cloneDeep(props.value)
  list.splice(index, 1)
  emitValue(list)
}

function changeValue(rowIndex: number, value: any) {
  const list = cloneDeep(props.value)
  list[rowIndex][0] = value
  emitValue(list)
}

function changeDate(rowIndex: number, date: Dayjs | null) {
  if (!date) {
    return
  }
  const format = props.enumValueType === ENUM_VALUE_TYPE.DATE ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss'
  const value = date.format(format)
  const list = cloneDeep(props.value)
  list[rowIndex][0] = value
  emitValue(list)
}

function changeStyle(rowIndex: number, key: string, value: any) {
  const list = cloneDeep(props.value)
  list[rowIndex][1] = { ...list[rowIndex][1], [key]: value }
  emitValue(list)
}

function handleClear(rowIndex: number) {
  const list = cloneDeep(props.value)
  list[rowIndex][1] = { style: {}, icon: {}, label: '' }
  emitValue(list)
}
</script>

<template>
  <div class="define-wrap">
    <a-button
      v-if="!defineList.length"
      type="primary"
      ghost
      :disabled="disabled"
      size="small"
      class="add-btn"
      @click="addData()"
    >
      <template #icon><PlusOutlined /></template>
      {{ t('add') }}
    </a-button>

    <vxe-table
      v-else
      :data="defineList"
      size="mini"
      show-header-overflow
      :row-config="{ height: 46 }"
      :min-height="75"
      border
      class="define-wrap-table"
    >
      <vxe-column field="value" width="230" :title="t('cmdb.ciType.enumValue')">
        <template #header="{ column }">
          <span class="table-header-required">*</span>
          {{ column.title }}
        </template>
        <template #default="{ row, rowIndex }">
          <a-input
            v-if="enumValueType === ENUM_VALUE_TYPE.INPUT"
            :value="row.value"
            :placeholder="t('cmdb.ciType.valueInputTip')"
            @change="(e: any) => changeValue(rowIndex, e.target.value)"
          />
          <a-input-number
            v-else-if="enumValueType === ENUM_VALUE_TYPE.NUMBER"
            :value="row.value"
            @change="(v: any) => changeValue(rowIndex, v)"
          />
          <a-date-picker
            v-else
            style="width: 100%"
            :value="row.value ? dayjs(row.value) : null"
            :format="enumValueType === ENUM_VALUE_TYPE.DATE ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss'"
            :show-time="enumValueType === ENUM_VALUE_TYPE.DATE ? false : { format: 'HH:mm:ss' }"
            @change="(date: any) => changeDate(rowIndex, date)"
          />
        </template>
      </vxe-column>
      <vxe-column width="230" :title="t('cmdb.ciType.label')">
        <template #default="{ row, rowIndex }">
          <DefineLabel
            :label-data="row"
            @change="(key: string, value: any) => changeStyle(rowIndex, key, value)"
            @delete-data="handleClear(rowIndex)"
          />
        </template>
      </vxe-column>
    </vxe-table>
    <div class="define-wrap-action">
      <div v-for="(item, index) in defineList" :key="item.id" class="define-wrap-action-item">
        <PlusCircleOutlined class="define-wrap-action-item-icon" @click="addData(index)" />
        <MinusCircleOutlined class="define-wrap-action-item-icon" @click="deleteData(index)" />
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.define-wrap {
  display: flex;

  .add-btn {
    font-size: 12px;
    padding: 1px 7px;
  }

  &-table {
    flex-shrink: 0;

    .table-header-required {
      color: #fd4c6a;
    }

    :deep(.ant-input-number) {
      width: 100%;
    }
  }

  &-action {
    flex-shrink: 0;
    margin-left: 11px;
    padding-top: 36px;

    &-item {
      display: flex;
      align-items: center;
      height: 46px;
      gap: 12px;

      &-icon {
        cursor: pointer;
        color: #2f54eb;
      }
    }
  }
}
</style>
