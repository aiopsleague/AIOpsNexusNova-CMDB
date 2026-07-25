<template>
  <div class="ci-detail-grafana">
    <a-spin :spinning="loading" :style="{ width: '100%', height: '100%' }">
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
    }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      this.loading = true
      try {
        const res = await getCIGrafana(this.ciId)
        this.notConfigured = !res.configured
        const r = res.result
        if (r && r.connection_id && r.uid) {
          // iframe 指向后端代理，由后端注入 Service Account Token，
          // 浏览器无需 Grafana 匿名访问也拿不到 api_key
          const apiBase = String(process.env.VUE_APP_API_BASE_URL || '').replace(/\/+$/, '')
          let url = `${apiBase}/v0.1/grafana/proxy/${r.connection_id}/d/${r.uid}${r.slug ? '/' + r.slug : ''}?kiosk`
          if (r.var_name && r.var_value !== undefined && r.var_value !== null && r.var_value !== '') {
            url += `&var-${r.var_name}=${encodeURIComponent(r.var_value)}`
          }
          this.iframeUrl = url
        }
      } catch (e) {
        this.iframeUrl = ''
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style lang="less" scoped>
.ci-detail-grafana {
  height: 100%;
  .ci-detail-grafana-iframe {
    width: 100%;
    height: 100%;
    min-height: 600px;
    border: none;
  }
}
</style>
