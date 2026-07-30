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
        <div
          :class="['prom-stat-card', 'prom-stat-total', { 'prom-stat-active': filterSeverity === null }]"
          @click="setFilter(null)"
        >
          <div class="stat-icon"><a-icon type="alert" /></div>
          <div class="stat-content">
            <div class="stat-label">{{ $t('cmdb.ci.alertFiring') }}</div>
            <div class="stat-value">
              <template v-if="filterSeverity !== null">{{ filteredAlerts.length }} / </template>{{ alerts.length }}
            </div>
          </div>
        </div>
        <div
          v-for="sev in severityList"
          :key="sev.key"
          :class="['prom-stat-card', `prom-stat-${sev.key}`, { 'prom-stat-active': filterSeverity === sev.key }]"
          @click="setFilter(sev.key)"
        >
          <div class="stat-icon"><a-icon :type="sev.icon" /></div>
          <div class="stat-content">
            <div class="stat-label">{{ sev.label }}</div>
            <div class="stat-value">{{ severityCounts[sev.key] }}</div>
          </div>
        </div>
        <div class="prom-refresh-area">
          <span class="last-refresh">{{ $t('cmdb.ci.alertLastRefresh') }}: {{ lastRefreshText }}</span>
          <a-button size="small" @click="loadAlerts" :loading="loading">
            <a-icon type="reload" />{{ $t('cmdb.ci.alertRefresh') }}
          </a-button>
        </div>
      </div>

      <!-- Active filter indicator -->
      <div v-if="filterSeverity !== null" class="prom-filter-bar">
        <a-icon type="filter" />
        <span>{{ $t('cmdb.ci.alertFilteredBy') }}: <strong>{{ severityLabel(filterSeverity) }}</strong></span>
        <span class="prom-filter-count">({{ filteredAlerts.length }} / {{ alerts.length }})</span>
        <a-button size="small" type="link" @click="setFilter(null)">
          <a-icon type="close-circle" />{{ $t('cmdb.ci.alertClearFilter') }}
        </a-button>
      </div>

      <!-- Alert Table (scrollable) -->
      <div class="prom-alert-table-wrapper">
        <a-spin :spinning="loading" class="prom-alert-spin">
          <a-table
            v-if="filteredAlerts.length"
            :columns="columns"
            :data-source="filteredAlerts"
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
              {{ filterSeverity !== null ? $t('cmdb.ci.alertNoMatchFilter') : emptyDescription }}
            </span>
          </a-empty>
        </a-spin>
      </div>
    </div>
  </div>
</template>

<script>
import { getCIPrometheusAlerts } from '@/modules/cmdb/api/ci'

const SEVERITY_LIST = [
  { key: 'disaster', icon: 'close-circle' },
  { key: 'emergency', icon: 'close-circle' },
  { key: 'critical', icon: 'close-circle' },
  { key: 'important', icon: 'exclamation-circle' },
  { key: 'warning', icon: 'exclamation-circle' },
  { key: 'info', icon: 'info-circle' },
]

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
      filterSeverity: null,
    }
  },
  computed: {
    severityList() {
      return SEVERITY_LIST.map((s) => ({
        ...s,
        label: this.severityStatusText(s.key),
      }))
    },
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
    filteredAlerts() {
      if (this.filterSeverity === null) return this.alerts
      return this.alerts.filter((a) => this._severity(a) === this.filterSeverity)
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
    setFilter(severity) {
      if (this.filterSeverity === severity) {
        this.filterSeverity = null
      } else {
        this.filterSeverity = severity
      }
    },
    severityLabel(severity) {
      return this.severityStatusText(severity)
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
  padding-top: 3px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  align-items: center;
  flex-shrink: 0;
}

.prom-stat-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fb 100%);
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 2px solid transparent;
  min-width: 140px;
  cursor: pointer;
  user-select: none;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  outline: none;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
    border-color: #d6d8e0;
  }

  &:active {
    transform: translateY(-1px);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
  }

  &.prom-stat-active {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.13);

    &::after {
      content: '';
      position: absolute;
      top: -2px;
      left: -2px;
      right: -2px;
      bottom: -2px;
      border-radius: 11px;
      pointer-events: none;
    }

    .stat-label {
      font-weight: 600;
    }
  }

  &.prom-stat-total.prom-stat-active {
    background: linear-gradient(135deg, #f0f2ff 0%, #e8eaff 100%);
    border-color: #667eea;
    &::after { border: 2px solid rgba(102, 126, 234, 0.4); }
  }

  &.prom-stat-disaster.prom-stat-active {
    background: linear-gradient(135deg, #fff0f0 0%, #ffe6e8 100%);
    border-color: #820014;
    &::after { border: 2px solid rgba(130, 0, 20, 0.3); }
  }

  &.prom-stat-emergency.prom-stat-active {
    background: linear-gradient(135deg, #fff1f0 0%, #ffe7e5 100%);
    border-color: #cf1322;
    &::after { border: 2px solid rgba(207, 19, 34, 0.3); }
  }

  &.prom-stat-critical.prom-stat-active {
    background: linear-gradient(135deg, #fff2f0 0%, #ffe7e5 100%);
    border-color: #f5222d;
    &::after { border: 2px solid rgba(245, 34, 45, 0.3); }
  }

  &.prom-stat-important.prom-stat-active {
    background: linear-gradient(135deg, #fff7e6 0%, #fff0d9 100%);
    border-color: #fa541c;
    &::after { border: 2px solid rgba(250, 84, 28, 0.3); }
  }

  &.prom-stat-warning.prom-stat-active {
    background: linear-gradient(135deg, #fffbe6 0%, #fff5cc 100%);
    border-color: #fa8c16;
    &::after { border: 2px solid rgba(250, 140, 22, 0.3); }
  }

  &.prom-stat-info.prom-stat-active {
    background: linear-gradient(135deg, #f0f7ff 0%, #e6f3ff 100%);
    border-color: #1890ff;
    &::after { border: 2px solid rgba(24, 144, 255, 0.3); }
  }

  .stat-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    color: #fff;
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  }

  &:hover .stat-icon {
    transform: scale(1.08);
  }

  .stat-content {
    .stat-label {
      font-size: 13px;
      color: #8c8c8c;
      transition: color 0.25s;
    }
    .stat-value {
      font-size: 22px;
      font-weight: 600;
      color: #262626;
      line-height: 1;
      transition: color 0.25s;
    }
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

// Active filter indicator bar
.prom-filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #f0f5ff 0%, #e6f0ff 100%);
  border: 1px solid #b3d4ff;
  border-radius: 8px;
  font-size: 13px;
  color: #1d39c4;
  flex-shrink: 0;

  .prom-filter-count {
    color: #8c8c8c;
    font-size: 12px;
  }

  .ant-btn-link {
    margin-left: auto;
    color: #f5222d;
    font-size: 12px;
  }
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
