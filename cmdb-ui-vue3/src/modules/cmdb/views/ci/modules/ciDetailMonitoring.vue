<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import CiDetailGrafana from './ciDetailGrafana.vue'
import dataEmptyImg from '@/assets/data_empty.png'

const { t } = useI18n()

withDefaults(
  defineProps<{
    ciId: number
    toolType?: string
  }>(),
  {
    toolType: 'grafana',
  }
)

const emit = defineEmits<{
  (e: 'connectionStatusChange', status: any): void
}>()

function onConnectionStatusChange(status: any) {
  emit('connectionStatusChange', status)
}
</script>

<template>
  <div class="ci-detail-monitoring">
    <CiDetailGrafana v-if="toolType === 'grafana'" :ci-id="ciId" @connection-status-change="onConnectionStatusChange" />
    <!-- Future extension:
    <CiDetailZabbix v-else-if="toolType === 'zabbix'" :ciId="ciId" />
    -->
    <a-empty v-else :image="dataEmptyImg" :image-style="{ height: '100px' }" :style="{ paddingTop: '10%' }">
      <template #description>
        {{ t('cmdb.ci.monitoringNotConfigured') }}
      </template>
    </a-empty>
  </div>
</template>

<style lang="less" scoped>
.ci-detail-monitoring {
  height: 100%;
}
</style>
