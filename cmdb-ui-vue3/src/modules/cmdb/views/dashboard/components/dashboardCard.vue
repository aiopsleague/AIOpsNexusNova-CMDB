<script setup lang="ts">
import { computed, type Component } from 'vue'
import SummaryCounter from './summaryCounter.vue'
import SystemCounter from './systemCounter.vue'
import BusinessCounter from './businessCounter.vue'

const props = withDefaults(
  defineProps<{
    title?: string
    componentName?: string
  }>(),
  {
    title: '',
    componentName: '',
  }
)

const componentMap: Record<string, Component> = {
  SummaryCounter,
  SystemCounter,
  BusinessCounter,
}

const currentComponent = computed(() => componentMap[props.componentName] || null)
</script>

<template>
  <a-card>
    <div class="dashboard-title">{{ title }}</div>
    <component :is="currentComponent" />
  </a-card>
</template>

<style lang="less" scoped>
.dashboard-title {
  font-size: large;
  font-weight: 500;
  border-left: 4px solid #57738e;
  padding-left: 8px;
  margin-bottom: 5px;
}
</style>
