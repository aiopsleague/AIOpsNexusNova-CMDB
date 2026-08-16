<script setup lang="ts">
import { computed } from 'vue'
import CiDetailRelationTopo from './ciDetailRelationTopo/index.vue'

const props = withDefaults(
  defineProps<{
    ciId?: number | null
    typeId?: number
    ci?: Record<string, any>
    relationData?: Record<string, any>
  }>(),
  {
    ciId: null,
    typeId: 0,
    ci: () => ({}),
    relationData: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'navigateToCi', payload: { typeId: number; ciId: number }): void
}>()

// Prefer the actual type id from the current CI data, falling back to the prop
// (compat: on first load the ci may not be ready yet).
const currentTypeId = computed(() => (props.ci && props.ci._type) || props.typeId)

// Double-click a topology node: bubble the navigation intent up to the parent
// (ciDetailTab) which decides how to navigate (drawer refresh vs. page route).
function handleNodeDblclick({ typeId, ciId }: { typeId: number; ciId: number }) {
  if (!typeId || !ciId) {
    return
  }
  if (typeId === currentTypeId.value && ciId === props.ciId) {
    return // current CI itself, no navigation needed
  }
  emit('navigateToCi', { typeId, ciId })
}
</script>

<template>
  <div class="ci-detail-relation">
    <CiDetailRelationTopo
      :parent-c-i-type-list="relationData.parentCITypeList"
      :child-c-i-type-list="relationData.childCITypeList"
      @node-dblclick="handleNodeDblclick"
    />
  </div>
</template>

<style lang="less" scoped>
.ci-detail-relation {
  height: 100%;
}
</style>
