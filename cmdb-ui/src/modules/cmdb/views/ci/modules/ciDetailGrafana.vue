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
      <template slot="message">
        <span class="grafana-alert-title">{{ $t('cmdb.ci.grafanaConnectionError') }}</span>
      </template>
      <template slot="description">
        <div class="grafana-alert-desc">
          <span>{{ $t('cmdb.ci.grafanaConnectionErrorDesc') }}</span>
          <span v-if="connectionStatus.error" class="grafana-alert-error-detail">{{ connectionStatus.error }}</span>
          <a-button size="small" type="link" @click="reload" :loading="loading">
            <a-icon type="reload" />{{ $t('cmdb.ci.grafanaConnectionRetry') }}
          </a-button>
        </div>
      </template>
    </a-alert>

    <a-spin :spinning="loading" class="ci-detail-grafana-spin">
      <iframe
        v-if="iframeUrl"
        :src="iframeUrl"
        class="ci-detail-grafana-iframe"
        frameborder="0"
      ></iframe>
      <a-empty
        v-else-if="!loading"
        :image-style="{ height: '100px' }"
        :style="{ paddingTop: '10%' }"
      >
        <img slot="image" :src="require('@/assets/data_empty.png')" />
        <span slot="description">
          {{ notConfigured ? $t('cmdb.ci.grafanaNotConfigured') : $t('cmdb.ci.grafanaNoDashboard') }}
        </span>
      </a-empty>
    </a-spin>
  </div>
</template>

<script>
import { getCIGrafana } from '@/modules/cmdb/api/ci'

export default {
  name: 'CiDetailGrafana',
  props: {
    ciId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      notConfigured: false,
      iframeUrl: '',
      connectionStatus: null,
    }
  },
  mounted() {
    this.load()
    this._onThemeChange = () => { this.load() }
    window.addEventListener('ops:theme-change', this._onThemeChange)
  },
  beforeDestroy() {
    if (this._onThemeChange) {
      window.removeEventListener('ops:theme-change', this._onThemeChange)
    }
  },
  methods: {
    async load() {
      this.loading = true
      try {
        const res = await getCIGrafana(this.ciId)
        this.notConfigured = !res.configured
        this.connectionStatus = res.connection_status || null
        this.$emit('connectionStatusChange', this.connectionStatus)
        const r = res.result
        if (r && r.connection_id && r.uid) {
          // iframe 指向后端代理，由后端注入 Service Account Token，
          // 浏览器无需 Grafana 匿名访问也拿不到 api_key
          const apiBase = String(process.env.VUE_APP_API_BASE_URL || '').replace(/\/+$/, '')
          let url = `${apiBase}/v0.1/grafana/proxy/${r.connection_id}/d/${r.uid}${r.slug ? '/' + r.slug : ''}?kiosk`
          ;(r.vars || []).forEach((v) => {
            if (v.name && v.value !== undefined && v.value !== null && v.value !== '') {
              const prefix = v.var_type === 'native' ? '' : 'var-'
              url += `&${prefix}${v.name}=${encodeURIComponent(v.value)}`
            }
          })
          // If no theme parameter is configured in var_mapping, pass the resolved
          // app theme ('light' | 'dark') to Grafana.
          const hasThemeVar = (r.vars || []).some((v) => v.name === 'theme')
          if (!hasThemeVar) {
            const resolved = this.$store.state.app.theme || 'light'
            url += `&theme=${resolved}`
          }
          this.iframeUrl = url
        }
      } catch (e) {
        this.iframeUrl = ''
      } finally {
        this.loading = false
      }
    },
    reload() {
      this.load()
    },
  },
}
</script>

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
    /deep/ .ant-spin-container {
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
