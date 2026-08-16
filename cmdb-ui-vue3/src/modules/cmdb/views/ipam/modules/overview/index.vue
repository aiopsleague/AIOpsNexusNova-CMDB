<script setup lang="ts">
import { ref, watch } from 'vue'
import { getIPAMStats } from '@/modules/cmdb/api/ipam'
import Stats from './stats.vue'

const props = withDefaults(
  defineProps<{
    nodeId?: string
  }>(),
  {
    nodeId: '',
  }
)

const statsData = ref<Record<string, any>>({})
const tableData = ref<any[]>([])

async function initData() {
  const res = await getIPAMStats({
    parent_id: props.nodeId === 'all' ? 0 : props.nodeId,
  })
  const subnets = res?.subnets || []
  subnets.forEach((item: any) => {
    item.hosts_count = item?.hosts_count || 0
    item.used_ratio = item?.used_count && item?.hosts_count ? Math.round((item.used_count / item.hosts_count) * 100) : 0
  })

  statsData.value = res
  tableData.value = subnets
}

watch(
  () => props.nodeId,
  (newValue, oldValue) => {
    if (newValue !== oldValue) {
      initData()
    }
  },
  { deep: true, immediate: true }
)

defineExpose({ initData })
</script>

<template>
  <div class="overview">
    <Stats :stats-data="statsData" />
    <!-- TODO: wire up SubnetTable (modules/overview/subnetTable not yet migrated) -->
  </div>
</template>

<style lang="less" scoped>
.overview {
  width: 100%;
}
</style>
