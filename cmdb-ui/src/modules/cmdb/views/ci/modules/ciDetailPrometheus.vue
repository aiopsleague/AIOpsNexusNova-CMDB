<template>
  <div class="ci-detail-prometheus">
    <!-- Connection error warning banner: always show when there are unhealthy connections -->
    <a-alert
      v-if="unhealthyConnections.length > 0"
      type="warning"
      banner
      closable
      class="prom-connection-alert"
    >
      <template slot="message">
        <span class="prom-alert-title">{{ $t('cmdb.ci.prometheusConnectionError') }}</span>
      </template>
      <template slot="description">
        <div class="prom-alert-desc">
          <span>{{ $t('cmdb.ci.prometheusConnectionErrorDesc') }}</span>
          <span class="prom-alert-count">
            <a-badge status="success" :text="`${healthyCount} ${$t('cmdb.ci.prometheusConnectionHealthy')}`" />
            <a-badge status="error" :text="`${unhealthyConnections.length} ${$t('cmdb.ci.prometheusConnectionUnhealthy')}`" />
          </span>
          <a-button size="small" type="link" @click="loadAlerts" :loading="loading">
            <a-icon type="reload" />{{ $t('cmdb.ci.prometheusConnectionRetry') }}
          </a-button>
        </div>
      </template>
    </a-alert>

    <!-- All connections broken & no alerts: show clean empty state (matching Grafana pattern) -->
    <a-empty
      v-if="allConnectionsUnhealthy && !loading && alerts.length === 0"
      :image-style="{ height: '100px' }"
      :style="{ paddingTop: '10%' }"
    >
      <img slot="image" :src="require('@/assets/data_empty.png')" />
      <span slot="description">
        {{ $t('cmdb.ci.alertConnectionFailed') }}
      </span>
    </a-empty>

    <!-- Normal data display (stats + table) -->
    <div v-else class="prom-normal-content">
      <!-- Stats Bar -->
      <div class="prom-alert-stats">
        <div class="prom-stat-card prom-stat-total">
          <div class="stat-icon"><a-icon type="alert" /></div>
          <div class="stat-content">
            <div class="stat-label">{{ $t('cmdb.ci.alertFiring') }}</div>
            <div class="stat-value">{{ alerts.length }}</div>
          </div>
        </div>
        <div class="prom-stat-card prom-stat-disaster">
          <div class="stat-icon"><a-icon type="close-circle" /></div>
          <div class="stat-content">
            <div class="stat-label">{{ $t('cmdb.ci.alertDisaster') }}</div>
            <div class="stat-value">{{ severityCounts.disaster }}</div>
          </div>
        </div>
        <div class="prom-stat-card prom-stat-emergency">
          <div class="stat-icon"><a-icon type="close-circle" /></div>
          <div class="stat-content">
            <div class="stat-label">{{ $t('cmdb.ci.alertEmergency') }}</div>
            <div class="stat-value">{{ severityCounts.emergency }}</div>
          </div>
        </div>
        <div class="prom-stat-card prom-stat-critical">
          <div class="stat-icon"><a-icon type="close-circle" /></div>
          <div class="stat-content">
            <div class="stat-label">{{ $t('cmdb.ci.alertCritical') }}</div>
            <div class="stat-value">{{ severityCounts.critical }}</div>
          </div>
        </div>
        <div class="prom-stat-card prom-stat-important">
          <div class="stat-icon"><a-icon type="exclamation-circle" /></div>
          <div class="stat-content">
            <div class="stat-label">{{ $t('cmdb.ci.alertImportant') }}</div>
            <div class="stat-value">{{ severityCounts.important }}</div>
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

      <!-- Alert Table (scrollable) -->
      <div class="prom-alert-table-wrapper">
        <a-spin :spinning="loading" class="prom-alert-spin">
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
              {{ emptyDescription }}
            </span>
          </a-empty>
        </a-spin>
      </div>
    </div>
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
      connectionStatuses: [],
      lastRefreshTime: null,
      refreshTimer: null,
    }
  },
  computed: {
    unhealthyConnections() {
      console.log('connectionStatuses:', this.connectionStatuses)
      return this.connectionStatuses.filter((s) => !s.ok)
    },
    healthyCount() {
      return this.connectionStatuses.filter((s) => s.ok).length
    },
    allConnectionsUnhealthy() {
      // True only when there are connections AND all of them are unhealthy
      return this.connectionStatuses.length > 0 && this.unhealthyConnections.length === this.connectionStatuses.length
    },
    emptyDescription() {
      if (this.errorMsg) return this.errorMsg
      if (!this.configured) return this.$t('cmdb.ci.alertNoConfig')
      if (this.unhealthyConnections.length > 0) return this.$t('cmdb.ci.alertConnectionFailed')
      return this.$t('cmdb.ci.alertNoData')
    },
    severityCounts() {
      const counts = { disaster: 0, emergency: 0, critical: 0, important: 0, warning: 0, info: 0 }
      this.alerts.forEach((a) => {
        const s = this._severity(a)
        if (counts.hasOwnProperty(s)) counts[s]++
        else counts.info++
      })
      return counts
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
      // Backend flattens values to _d_<safe_key> where dots are replaced with "__"
      ;(this.displayColumns || []).forEach((col) => {
        const safeKey = '_d_' + col.key.replace(/\./g, '__')
        const title = isZh ? (col.title_zh || col.key) : (col.title_en || col.key)
        cols.push({
          title,
          dataIndex: safeKey,
          key: col.key,
          ellipsis: true,
        })
      })
      cols.push(
        { title: this.$t('cmdb.ci.alertActiveAt'), dataIndex: 'activeAt', key: 'activeAt', scopedSlots: { customRender: 'activeAt' }, width: 180 },
        { title: this.$t('cmdb.ci.alertDuration'), dataIndex: 'activeAt', key: 'duration', scopedSlots: { customRender: 'duration' }, width: 130 },
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
        this.connectionStatuses = res.connection_status || []
        this.lastRefreshTime = Date.now()
      } catch (e) {
        this.alerts = []
        this.connectionStatuses = []
        this.errorMsg = e.message || 'Connection error'
      } finally {
        this.loading = false
        this.$emit('connectionStatusChange', this.connectionStatuses)
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
      if (s === 'disaster' || s === 'emergency') return 'error'
      if (s === 'critical' || s === 'important') return 'error'
      if (s === 'warning') return 'warning'
      return 'processing'
    },
    severityStatusText(severity) {
      const s = (severity || '').toLowerCase()
      if (s === 'disaster') return this.$t('cmdb.ci.alertDisaster')
      if (s === 'emergency') return this.$t('cmdb.ci.alertEmergency')
      if (s === 'critical') return this.$t('cmdb.ci.alertCritical')
      if (s === 'important') return this.$t('cmdb.ci.alertImportant')
      if (s === 'warning') return this.$t('cmdb.ci.alertWarning')
      return this.$t('cmdb.ci.alertInfo')
    },
    formatDuration(activeAt) {
      if (!activeAt) return '-'
      const start = new Date(activeAt).getTime()
      const now = Date.now()
      let diff = Math.floor((now - start) / 1000)
      if (diff < 0) diff = 0

      const days = Math.floor(diff / 86400)
      diff -= days * 86400
      const hours = Math.floor(diff / 3600)
      diff -= hours * 3600
      const minutes = Math.floor(diff / 60)
      const seconds = diff - minutes * 60

      const isZh = this.$i18n.locale === 'zh'
      const parts = []
      if (days > 0) parts.push(days + (isZh ? this.$t('cmdb.ci.alertDurationDay') : ' ' + this.$t('cmdb.ci.alertDurationDay') + ' '))
      if (hours > 0) parts.push(hours + (isZh ? this.$t('cmdb.ci.alertDurationHour') : ' ' + this.$t('cmdb.ci.alertDurationHour') + ' '))
      if (minutes > 0) parts.push(minutes + (isZh ? this.$t('cmdb.ci.alertDurationMinute') : ' ' + this.$t('cmdb.ci.alertDurationMinute') + ' '))
      if (seconds > 0 || parts.length === 0) parts.push(seconds + (isZh ? this.$t('cmdb.ci.alertDurationSecond') : ' ' + this.$t('cmdb.ci.alertDurationSecond')))

      if (isZh) {
        return parts.join('')
      } else {
        return parts.join('').trim()
      }
    },
  },
}
</script>

<style lang="less" scoped>
.ci-detail-prometheus {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.prom-connection-alert {
  flex-shrink: 0;
  margin-bottom: 12px;
}

.prom-alert-title {
  font-weight: 600;
  font-size: 14px;
}

.prom-alert-desc {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.prom-alert-count {
  display: flex;
  gap: 12px;
}

.prom-normal-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.prom-alert-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
  flex-shrink: 0;
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
  &.prom-stat-disaster .stat-icon { background: linear-gradient(135deg, #820014 0%, #5c0011 100%); }
  &.prom-stat-emergency .stat-icon { background: linear-gradient(135deg, #cf1322 0%, #a8071a 100%); }
  &.prom-stat-critical .stat-icon { background: linear-gradient(135deg, #f5222d 0%, #cf1322 100%); }
  &.prom-stat-important .stat-icon { background: linear-gradient(135deg, #fa541c 0%, #d4380d 100%); }
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

.prom-alert-table-wrapper {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

.prom-alert-spin {
  height: 100%;
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
