<script setup lang="ts">
import { useI18n } from 'vue-i18n'

withDefaults(
  defineProps<{
    tableData?: any[]
  }>(),
  {
    tableData: () => [],
  }
)

const { t } = useI18n()
</script>

<template>
  <vxe-table
    size="mini"
    stripe
    class="ops-stripe-table"
    show-overflow
    keep-source
    max-height="100%"
    :data="tableData"
    :scroll-y="{ enabled: true }"
  >
    <vxe-column field="name" :title="t('name')">
      <template #edit="{ row }">
        <vxe-input v-model="row.name" type="text"></vxe-input>
      </template>
    </vxe-column>
    <vxe-column field="type" :title="t('type')"></vxe-column>
    <vxe-column field="desc" :title="t('desc')"></vxe-column>
  </vxe-table>
</template>

<style lang="less" scoped></style>
