<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { tabList, TAB_KEY } from '../constants'

const props = withDefaults(
  defineProps<{
    value?: string
  }>(),
  {
    value: TAB_KEY.CUSTOM,
  }
)

const emit = defineEmits<{
  (e: 'change', value: string): void
}>()

const { t } = useI18n()

const activeKey = computed({
  get: () => props.value,
  set: (newValue) => emit('change', newValue),
})

function clickTab(key: string) {
  emit('change', key)
}
</script>

<template>
  <div class="cloud-tabs">
    <div
      v-for="item in tabList"
      :key="item.key"
      :class="['cloud-tabs-item', activeKey === item.key ? 'cloud-tabs-item-active' : '']"
      @click="clickTab(item.key)"
    >
      {{ t(item.text) }}
    </div>
  </div>
</template>

<style lang="less" scoped>
.cloud-tabs {
  display: flex;
  align-items: center;
  margin-bottom: 26px;

  &-item {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 400;
    color: @text-color_2;
    background-color: @primary-color_7;
    width: 105px;
    height: 32px;
    cursor: pointer;

    &-active {
      border: solid 1px @primary-color_8;
      background-color: @primary-color_4;
      color: @primary-color;
    }

    &:hover {
      color: @primary-color;
    }
  }
}
</style>
