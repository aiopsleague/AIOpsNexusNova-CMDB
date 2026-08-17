<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { PlusCircleOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'

const props = withDefaults(
  defineProps<{
    operateType: string
    showIcon?: boolean
  }>(),
  { showIcon: false }
)

const { t } = useI18n()

const typeClass = computed(() => {
  const type = props.operateType.toLowerCase()
  if (type.includes(t('new').toLowerCase())) {
    return 'type-new'
  }
  if (type.includes(t('update').toLowerCase())) {
    return 'type-update'
  }
  return 'type-delete'
})

const iconType = computed(() => {
  const type = props.operateType.toLowerCase()
  if (type.includes(t('new').toLowerCase())) {
    return PlusCircleOutlined
  }
  if (type.includes(t('update').toLowerCase())) {
    return EditOutlined
  }
  return DeleteOutlined
})
</script>

<template>
  <span :class="['operate-type-text', typeClass]">
    <component :is="iconType" v-if="showIcon" class="type-icon" />
    <span>{{ operateType }}</span>
  </span>
</template>

<style lang="less" scoped>
.operate-type-text {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  line-height: 22px;
  font-weight: 400;
  white-space: nowrap;

  .type-icon {
    font-size: 14px;
  }

  &.type-new {
    color: #52c41a;

    .type-icon {
      color: #52c41a;
    }
  }

  &.type-update {
    color: #fa8c16;

    .type-icon {
      color: #fa8c16;
    }
  }

  &.type-delete {
    color: #f5222d;

    .type-icon {
      color: #f5222d;
    }
  }
}
</style>
