<script setup lang="ts">
import { onBeforeUnmount, onMounted, provide, ref } from 'vue'
import { dashboardList } from './constants'
import { getStatistics } from '../../api/statistics'
import DashboardCard from './components/dashboardCard.vue'

const statistics = ref<Record<string, any>>({})
let interval: ReturnType<typeof setInterval> | null = null

// Expose the statistics object to the counter components via a getter.
provide('statistics', () => statistics.value)

function getData() {
  getStatistics().then((res) => {
    statistics.value = res
  })
}

onMounted(() => {
  getData()
  interval = setInterval(() => {
    getData()
  }, 30000)
})

onBeforeUnmount(() => {
  if (interval) {
    clearInterval(interval)
    interval = null
  }
})
</script>

<template>
  <div>
    <a-row :gutter="[12, 12]">
      <a-col v-for="item in dashboardList" :key="item.title" :span="item.span">
        <DashboardCard :title="item.title" :component-name="item.component" />
      </a-col>
    </a-row>
  </div>
</template>

<style></style>
