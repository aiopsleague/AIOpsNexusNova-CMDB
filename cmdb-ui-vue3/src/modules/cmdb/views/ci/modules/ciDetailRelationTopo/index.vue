<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import dataEmptyImg from '@/assets/data_empty.png'

const { t } = useI18n()

// TODO: migrate topology (butterfly-dag / relation-graph) — needs Vue3 lib evaluation.
// The original Vue 2 implementation used `butterfly-dag` (TreeCanvas + TreeNode) plus
// jQuery for the node DOM and a shared hover detail card. That graph library has no
// clean, maintained Vue 3 path, so the topology is stubbed here while preserving the
// public props/emits interface so `ciDetailRelation.vue` can wire it back up later.

withDefaults(
  defineProps<{
    parentCITypeList?: any[]
    childCITypeList?: any[]
  }>(),
  {
    parentCITypeList: () => [],
    childCITypeList: () => [],
  }
)

defineEmits<{
  (e: 'nodeDblclick', payload: { typeId: number; ciId: number }): void
}>()

const topoData = ref<Record<string, any>>({})

// Preserved for interface parity with the Vue 2 component (called by ciDetailRelation).
function setTopoData(data: Record<string, any>) {
  topoData.value = data
}

defineExpose({ setTopoData })
</script>

<template>
  <div class="ci-detail-relation-topo" :style="{ width: '100%', height: '100%', position: 'relative' }">
    <a-empty :image="dataEmptyImg" :image-style="{ height: '100px' }" :style="{ paddingTop: '10%' }">
      <template #description>{{ t('noData') }}</template>
    </a-empty>
  </div>
</template>

<style lang="less" scoped>
.ci-detail-relation-topo {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>
