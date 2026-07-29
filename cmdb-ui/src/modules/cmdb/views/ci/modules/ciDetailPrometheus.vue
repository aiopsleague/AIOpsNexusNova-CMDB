<template>
  <div class="ci-detail-prometheus">
    <!-- Stats Bar -->
    <div class="prom-alert-stats">
      <div class="prom-stat-card prom-stat-total">
        <div class="stat-icon"><a-icon type="alert" /></div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('cmdb.ci.alertFiring') }}</div>
          <div class="stat-value">{{ alerts.length }}</div>
        </div>
      </div>
      <div class="prom-stat-card prom-stat-critical">
        <div class="stat-icon"><a-icon type="close-circle" /></div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('cmdb.ci.alertCritical') }}</div>
          <div class="stat-value">{{ severityCounts.critical }}</div>
        </div>
      </div>
      <div class="prom-stat-card prom-stat-warning">
        <div class="stat-icon"><a-icon type="exclamation-circle" /></div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('cmdb.ci.alertWarning') }}</div>
          <div class="stat-value">{{ severityCounts.warning }}</div>
        </div>
      </div>
      <div class="prom-stat-card prom-stat-info">
        <div class="stat-icon"><a-icon type="info-circle" /></div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('cmdb.ci.alertInfo') }}</div>
          <div class="stat-value">{{ severityCounts.info }}</div>
        </div>
      </div>
      <div class="prom-refresh-area">
        <span class="last-refresh">{{ $t('cmdb.ci.alertLastRefresh') }}: {{ lastRefreshText }}</span>
        <a-button size="small" @click="loadAlerts" :loading="loading">
          <a-icon type="reload" />{{ $t('cmdb.ci.alertRefresh') }}
        </a-button>
      </div>
    </div>

    <!-- Alert Table -->
    <a-spin :spinning="loading">
      <a-table
        v-if="alerts.length"
        :columns="columns"
        :data-source="alerts"
        :pagination="false"
        rowKey="fingerprint"
        size="small"
        :expandRowByClick="true"
        class="prom-alert-table"
      >
        <template slot="severity" slot-scope="text, record">
          <a-badge
            :status="severityStatus(record.labels.severity)"
            :text="severityStatusText(record.labels.severity)"
          />
        </template>
        <template slot="activeAt" slot-scope="text">
          {{ text | formatTime }}
        </template>
        <template slot="duration" slot-scope="text, record">
          {{ formatDuration(record.activeAt) }}
        </template>
        <template slot="expandedRowRender" slot-scope="record">
          <div class="prom-alert-detail">
            <div class="prom-alert-detail-section">
              <div class="prom-alert-detail-title">{{ $t('cmdb.ci.alertLabels') }}</div>
              <div class="prom-alert-detail-tags">
                <a-tag v-for="(val, key) in record.labels" :key="key" color="blue">
                  {{ key }}={{ val }}
                </a-tag>
              </div>
            </div>
            <div v-if="record.annotations && Object.keys(record.annotations).length" class="prom-alert-detail-section">
              <div class="prom-alert-detail-title">{{ $t('cmdb.ci.alertAnnotations') }}</div>
              <div v-if="record.annotations.summary" class="prom-alert-annotation">
                <strong>Summary:</strong> {{ record.annotations.summary }}
              </div>
              <div v-if="record.annotations.description" class="prom-alert-annotation">
                <strong>Description:</strong> {{ record.annotations.description }}
              </div>
            </div>
            <div class="prom-alert-detail-section">
              <a-row :gutter="16">
                <a-col :span="12">
                  <span class="prom-alert-detail-title">{{ $t('cmdb.ci.alertRuleName') }}:</span>
                  {{ record.rule_name || '-' }}
                </a-col>
                <a-col :span="12">
                  <span class="prom-alert-detail-title">{{ $t('cmdb.ci.alertValue') }}:</span>
                  {{ record.value || '-' }}
                </a-col>
              </a-row>
            </div>
          </div>
        </template>
      </a-table>

      <!-- Empty states -->
      <a-empty
        v-else-if="!loading"
        :image-style="{ height: '100px' }"
        :style="{ paddingTop: '10%' }"
      >
        <img slot="image" :src="require('@/assets/data_empty.png')" />
        <span slot="description">
          {{ errorMsg ? errorMsg : configured ? $t('cmdb.ci.alertNoData') : $t('cmdb.ci.alertNoConfig') }}
        </span>
      </a-empty>
    </a-spin>
  </div>
</template>

<script>
import { getCIPrometheusAlerts } from '@/modules/cmdb/api/ci'

export default {
  name: 'CiDetailPrometheus',
  props: {
    ciId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      configured: true,
      errorMsg: '',
      alerts: [],
      displayColumns: [],
      lastRefreshTime: null,
      refreshTimer: null,
    }
  },
  computed: {
    severityCounts() {
      return {
        critical: this.alerts.filter((a) => this._severity(a) === 'critical').length,
        warning: this.alerts.filter((a) => this._severity(a) === 'warning').length,
        info: this.alerts.filter((a) => this._severity(a) === 'info').length,
      }
    },
    lastRefreshText() {
      if (!this.lastRefreshTime) return '-'
      const d = new Date(this.lastRefreshTime)
      return d.toLocaleTimeString()
    },
    columns() {
      const isZh = this.$i18n.locale === 'zh'
      const cols = [
        { title: this.$t('cmdb.ci.alertSeverity'), dataIndex: 'labels.severity', key: 'severity', scopedSlots: { customRender: 'severity' }, width: 110 },
      ]
      // Dynamic columns from display_columns config
      // Values are flattened to _d_<key> top-level properties by the backend
      ;(this.displayColumns || []).forEach((col) => {
        const title = isZh ? (col.title_zh || col.key) : (col.title_en || col.key)
        cols.push({
          title,
          dataIndex: '_d_' + col.key,
          key: col.key,
          ellipsis: true,
        })
      })
      cols.push(
        { title: this.$t('cmdb.ci.alertActiveAt'), dataIndex: 'activeAt', key: 'activeAt', scopedSlots: { customRender: 'activeAt' }, width: 180 },
        { title: this.$t('cmdb.ci.alertDuration'), dataIndex: 'activeAt', key: 'duration', scopedSlots: { customRender: 'duration' }, width: 110 },
      )
      return cols
    },
  },
  mounted() {
    this.loadAlerts()
    this.startAutoRefresh()
  },
  beforeDestroy() {
    this.stopAutoRefresh()
  },
  methods: {
    _severity(alert) {
      return (alert.labels || {}).severity || 'info'
    },
    async loadAlerts() {
      this.loading = true
      this.errorMsg = ''
      try {
        const res = await getCIPrometheusAlerts(this.ciId)
        this.configured = res.configured !== false
        this.alerts = res.alerts || []
        this.displayColumns = res.display_columns || []
        this.lastRefreshTime = Date.now()
      } catch (e) {
        this.alerts = []
        this.errorMsg = e.message || 'Connection error'
      } finally {
        this.loading = false
      }
    },
    startAutoRefresh() {
      this.refreshTimer = setInterval(() => {
        this.loadAlerts()
      }, 30000)
    },
    stopAutoRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer)
        this.refreshTimer = null
      }
    },
    severityStatus(severity) {
      const s = (severity || '').toLowerCase()
      if (s === 'critical') return 'error'
      if (s === 'warning') return 'warning'
      return 'processing'
    },
    severityStatusText(severity) {
      const s = (severity || '').toLowerCase()
      if (s === 'critical') return this.$t('cmdb.ci.alertCritical')
      if (s === 'warning') return this.$t('cmdb.ci.alertWarning')
      return this.$t('cmdb.ci.alertInfo')
    },
    formatDuration(activeAt) {
      if (!activeAt) return '-'
      const start = new Date(activeAt).getTime()
      const now = Date.now()
      const diff = Math.floor((now - start) / 1000)
      if (diff < 60) return diff + 's'
      if (diff < 3600) return Math.floor(diff / 60) + 'm'
      if (diff < 86400) return Math.floor(diff / 3600) + 'h'
      return Math.floor(diff / 86400) + 'd'
    },
  },
}
</script>

<style lang="less" scoped>
.ci-detail-prometheus {
  height: 100%;
}
.prom-alert-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
}
.prom-stat-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fb 100%);
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e8eaed;
  min-width: 140px;
  .stat-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    color: #fff;
  }
  .stat-content {
    .stat-label { font-size: 13px; color: #8c8c8c; }
    .stat-value { font-size: 22px; font-weight: 600; color: #262626; line-height: 1; }
  }
  &.prom-stat-total .stat-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
  &.prom-stat-critical .stat-icon { background: linear-gradient(135deg, #f5222d 0%, #cf1322 100%); }
  &.prom-stat-warning .stat-icon { background: linear-gradient(135deg, #fa8c16 0%, #d46b08 100%); }
  &.prom-stat-info .stat-icon { background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%); }
}
.prom-refresh-area {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  .last-refresh { font-size: 12px; color: #8c8c8c; }
}
.prom-alert-table {
  background: #fff;
  border-radius: 8px;
}
.prom-alert-detail {
  padding: 8px 0;
  &-section {
    margin-bottom: 12px;
  }
  &-title {
    font-weight: 600;
    margin-bottom: 6px;
    color: #262626;
  }
  &-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
}
.prom-alert-annotation {
  font-size: 13px;
  color: #595959;
  margin-bottom: 4px;
}
</style>
