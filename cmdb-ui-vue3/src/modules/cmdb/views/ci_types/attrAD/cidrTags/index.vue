<script setup lang="ts">
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { CloseOutlined } from '@ant-design/icons-vue'
import { uuidv4 } from '@/utils/uuid'
import { cloneDeep } from '@/modules/cmdb/utils/helper'

const props = withDefaults(
  defineProps<{
    value?: any[]
  }>(),
  {
    value: () => [],
  }
)

const emit = defineEmits<{
  (e: 'change', value: any[]): void
}>()

const { t } = useI18n()

const provide_labelCol = inject<() => any>('provide_labelCol')

const showAddInput = ref(false)
const inputValue = ref('')

const list = computed(() => props.value)
const labelCol = computed(() => provide_labelCol?.())

function clickClose(id: string) {
  const next = cloneDeep(props.value)
  const index = next.findIndex((item) => item.id === id)
  if (index !== -1) {
    next.splice(index, 1)
    emit('change', next)
  }
}

function addPreValue() {
  showAddInput.value = false
  const val = inputValue.value
  inputValue.value = ''
  if (!val) {
    return
  }
  const next = cloneDeep(props.value)
  next.push({
    value: val,
    id: uuidv4(),
  })
  emit('change', next)
}
</script>

<template>
  <a-form-item
    label="CIDR"
    :label-col="labelCol"
    :wrapper-col="{ span: 6 }"
    :extra="t('cmdb.ciType.snmpFormTip7')"
  >
    <div class="cidr-tag">
      <div
        v-for="item in list"
        :key="item.id"
        class="cidr-tag-item"
      >
        <a-tooltip :title="item.value">
          <span class="cidr-tag-text">{{ item.value }}</span>
        </a-tooltip>
        <CloseOutlined
          class="cidr-tag-close"
          @click.stop="clickClose(item.id)"
        />
      </div>
      <a-input
        v-if="showAddInput"
        v-model:value="inputValue"
        class="cidr-tag-input"
        autofocus
        @blur="addPreValue"
        @press-enter="showAddInput = false"
      ></a-input>
      <a v-else class="cidr-tag-add" @click="showAddInput = true">+ {{ t('new') }}</a>
    </div>
  </a-form-item>
</template>

<style lang="less" scoped>
.cidr-tag {
  width: max-content;
  max-width: 100%;
  padding: 6px 9px;
  border-radius: 2px;
  border: 1px solid #e4e7ed;
  background: #fff;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;

  &-item {
    padding: 3px 6px;
    background-color: #f0f5ff;
    display: flex;
    align-items: center;
  }

  &-text {
    font-size: 12px;
    font-weight: 400;
    color: #1d2129;
    line-height: 18px;
    text-overflow: ellipsis;
    word-break: break-all;
    white-space: nowrap;
    max-width: 100px;
    overflow: hidden;
  }

  &-close {
    font-size: 12px;
    color: #1d2129;
    margin-left: 4px;
    cursor: pointer;
  }

  &-input {
    max-width: 120px;
    height: 26px;
    line-height: 26px;
    padding: 3px 6px;
  }

  &-add {
    border: dashed 1px #e4e7ed;
    padding: 3px 6px;
    font-size: 12px;
    font-weight: 400;
    color: #1d2129;
    line-height: 18px;
    cursor: pointer;
  }
}
</style>
