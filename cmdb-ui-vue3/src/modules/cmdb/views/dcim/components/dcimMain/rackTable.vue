<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed } from 'vue'
import CITable from '@/modules/cmdb/components/ciTable/index.vue'

withDefaults(
  defineProps<{
    rackList?: any[]
    columns?: any[]
    preferenceAttrList?: any[]
    CITypeId?: number | string
  }>(),
  {
    rackList: () => [],
    columns: () => [],
    preferenceAttrList: () => [],
    CITypeId: 0,
  }
)

const windowHeight = computed(() => window.innerHeight)
const tableHeight = computed(() => `${windowHeight.value - 295}px`)
</script>

<template>
  <div class="rack-table">
    <CITable
      :attr-list="preferenceAttrList"
      :columns="columns"
      :data="rackList"
      :height="tableHeight"
      :sort-config="{ remote: false, trigger: 'default' }"
      :show-checkbox="false"
      :show-operation="false"
    />
  </div>
</template>

<style lang="less" scoped></style>
