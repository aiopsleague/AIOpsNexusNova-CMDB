<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { useI18n } from 'vue-i18n'
import { getCIGrafana } from '@/modules/cmdb/api/ci'
import { useAppStore } from '@/stores/app'
import dataEmptyImg from '@/assets/data_empty.png'

const { t } = useI18n()

const props = defineProps<{
  ciId: number
}>()

const emit = defineEmits<{
  (e: 'connectionStatusChange', status: any): void
}>()

const loading = ref(false)
const notConfigured = ref(false)
const iframeUrl = ref('')
const connectionStatus = ref<any>(null)

const appStore = useAppStore()

let onThemeChange: (() => void) | null = null

async function load() {
  loading.value = true
  try {
    const res = await getCIGrafana(props.ciId)
    notConfigured.value = !res.configured
    connectionStatus.value = res.connection_status || null
    emit('connectionStatusChange', connectionStatus.value)
    const r = res.result
    if (r && r.connection_id && r.uid) {
      // The iframe points to the backend proxy, which injects the Service Account Token;
      // the browser neither needs Grafana anonymous access nor holds an api_key.
      const apiBase = String(import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')
      let url = `${apiBase}/v0.1/grafana/proxy/${r.connection_id}/d/${r.uid}${r.slug ? '/' + r.slug : ''}?kiosk`
      ;(r.vars || []).forEach((v: any) => {
        if (v.name && v.value !== undefined && v.value !== null && v.value !== '') {
          const prefix = v.var_type === 'native' ? '' : 'var-'
          url += `&${prefix}${v.name}=${encodeURIComponent(v.value)}`
        }
      })
      // If no theme parameter is configured in var_mapping, pass the resolved
      // app theme ('light' | 'dark') to Grafana.
      const hasThemeVar = (r.vars || []).some((v: any) => v.name === 'theme')
      if (!hasThemeVar) {
        url += `&theme=${appStore.resolvedTheme}`
      }
      iframeUrl.value = url
    }
  } catch {
    iframeUrl.value = ''
  } finally {
    loading.value = false
  }
}

function reload() {
  load()
}

onMounted(() => {
  load()
  onThemeChange = () => {
    load()
  }
  window.addEventListener('ops:theme-change', onThemeChange)
})

onBeforeUnmount(() => {
  if (onThemeChange) {
    window.removeEventListener('ops:theme-change', onThemeChange)
  }
})
</script>

<template>
  <div class="ci-detail-grafana">
    <!-- Connection error warning banner -->
    <a-alert
      v-if="connectionStatus && !connectionStatus.ok"
      type="warning"
      banner
      closable
      class="grafana-connection-alert"
    >
      <template #message>
        <span class="grafana-alert-title">{{ t('cmdb.ci.grafanaConnectionError') }}</span>
      </template>
      <template #description>
        <div class="grafana-alert-desc">
          <span>{{ t('cmdb.ci.grafanaConnectionErrorDesc') }}</span>
          <span v-if="connectionStatus.error" class="grafana-alert-error-detail">{{ connectionStatus.error }}</span>
          <a-button size="small" type="link" :loading="loading" @click="reload">
            <ReloadOutlined />{{ t('cmdb.ci.grafanaConnectionRetry') }}
          </a-button>
        </div>
      </template>
    </a-alert>

    <a-spin :spinning="loading" class="ci-detail-grafana-spin">
      <iframe v-if="iframeUrl" :src="iframeUrl" class="ci-detail-grafana-iframe" frameborder="0"></iframe>
      <a-empty v-else-if="!loading" :image="dataEmptyImg" :image-style="{ height: '100px' }" :style="{ paddingTop: '10%' }">
        <template #description>
          {{ notConfigured ? t('cmdb.ci.grafanaNotConfigured') : t('cmdb.ci.grafanaNoDashboard') }}
        </template>
      </a-empty>
    </a-spin>
  </div>
</template>

<style lang="less" scoped>
.ci-detail-grafana {
  height: 100%;
  display: flex;
  flex-direction: column;

  .grafana-connection-alert {
    flex-shrink: 0;
    margin-bottom: 12px;
  }

  .grafana-alert-title {
    font-weight: 600;
    font-size: 14px;
  }

  .grafana-alert-desc {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }

  .grafana-alert-error-detail {
    display: block;
    font-size: 12px;
    color: #8c8c8c;
    font-family: monospace;
    word-break: break-all;
  }

  .ci-detail-grafana-spin {
    flex: 1;
    width: 100%;
    :deep(.ant-spin-container) {
      height: 100%;
    }
  }
  .ci-detail-grafana-iframe {
    display: block;
    width: 100%;
    height: 100%;
    border: none;
  }
}
</style>
