<script setup lang="ts">
import { nextTick, ref } from 'vue'
import CiDetailTab from './ciDetailTab.vue'

withDefaults(
  defineProps<{
    typeId?: number | null
    treeViewsLevels?: any[]
  }>(),
  {
    typeId: null,
    treeViewsLevels: () => [],
  }
)

const visible = ref(false)
const ciDetailTabRef = ref<any>()

function create(ciId: number, activeTabKey = 'tab_1') {
  visible.value = true
  nextTick(() => {
    ciDetailTabRef.value?.create(ciId, activeTabKey)
  })
}

defineExpose({ create })
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <CustomDrawer
    v-model:open="visible"
    width="90%"
    placement="left"
    :has-title="false"
    :has-footer="false"
    :body-style="{ padding: 0, height: '100vh' }"
    destroy-on-close
  >
    <CiDetailTab ref="ciDetailTabRef" :type-id="typeId ?? 0" :tree-views-levels="treeViewsLevels" />
  </CustomDrawer>
</template>
