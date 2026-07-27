<template>
  <div class="ci-detail-monitoring">
    <CiDetailGrafana v-if="toolType === 'grafana'" :ciId="ciId" />
    <!-- 未来扩展:
    <CiDetailZabbix v-else-if="toolType === 'zabbix'" :ciId="ciId" />
    -->
    <a-empty
      v-else
      :image-style="{ height: '100px' }"
      :style="{ paddingTop: '10%' }"
    >
      <img slot="image" :src="require('@/assets/data_empty.png')" />
      <span slot="description">
        {{ $t('cmdb.ci.monitoringNotConfigured') }}
      </span>
    </a-empty>
  </div>
</template>

<script>
import CiDetailGrafana from './ciDetailGrafana.vue'

export default {
  name: 'CiDetailMonitoring',
  components: { CiDetailGrafana },
  props: {
    ciId: {
      type: Number,
      required: true,
    },
    toolType: {
      type: String,
      default: 'grafana',
    },
  },
}
</script>

<style lang="less" scoped>
.ci-detail-monitoring {
  height: 100%;
}
</style>
