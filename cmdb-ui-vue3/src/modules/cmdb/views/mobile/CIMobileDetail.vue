<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeftOutlined,
  InfoCircleOutlined,
  ArrowUpOutlined,
  DownOutlined,
  UpOutlined,
  LinkOutlined,
  RightOutlined,
  ArrowDownOutlined,
  ClockCircleOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons-vue'
import { getCIMobileDetail } from '@/modules/cmdb/api/ci'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const typeId = ref<number | null>(null)
const ciId = ref<number | null>(null)
const ci = ref<Record<string, any>>({})
const typeInfo = ref<Record<string, any>>({})
const attrAliasMap = ref<Record<string, any>>({})
const parentRelations = ref<any[]>([])
const childRelations = ref<any[]>([])
const historyList = ref<any[]>([])
const parentCollapsed = ref(false)
const childCollapsed = ref(false)
const loading = ref(true)
const hasPermission = ref(true)

const coreAttrEntries = computed(() => {
  const _ci = ci.value || {}
  const aliasMap = attrAliasMap.value || {}
  const excludeKeys = new Set([
    '_id',
    '_type',
    'ci_type',
    'ci_type_alias',
    'unique',
    'unique_alias',
    '_updated_at',
    '_updated_by',
    '__ci_type_name__',
  ])
  const entries: Array<{ name: string; alias: string; value: string; _isLongValue: boolean }> = []

  Object.keys(_ci).forEach((key) => {
    if (!excludeKeys.has(key) && !key.startsWith('__') && !key.startsWith('_')) {
      const value = _ci[key]
      if (value === null || value === undefined || value === '') {
        return
      }
      if (Array.isArray(value) || (typeof value === 'object' && !Array.isArray(value))) {
        return
      }
      const alias = aliasMap[key] || key
      const strValue = String(value)
      entries.push({
        name: key,
        alias,
        value: strValue,
        _isLongValue: strValue.length > 24,
      })
    }
  })

  return entries
})

function loadFromRoute() {
  const nextTypeId = Number(route.params.typeId)
  const nextCiId = Number(route.params.ciId)
  if (nextCiId && (nextCiId !== ciId.value || nextTypeId !== typeId.value)) {
    typeId.value = nextTypeId
    ciId.value = nextCiId
    fetchData()
  }
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getCIMobileDetail(ciId.value as number)
    ci.value = res.ci || {}
    typeInfo.value = res.type || {}
    attrAliasMap.value = res.attribute_alias_map || {}
    parentRelations.value = (res.relations && res.relations.parents) || []
    childRelations.value = (res.relations && res.relations.children) || []
    historyList.value = (res.history || []).map((h: any) => {
      const colors: Record<string, string> = { '0': 'green', '1': 'red', '2': 'blue' }
      const labels: Record<string, string> = { '0': t('new'), '1': t('delete'), '2': t('update') }
      return {
        ...h,
        _operateColor: colors[h.operate_type] || 'default',
        _operateLabel: labels[h.operate_type] || h.operate_type,
      }
    })
    hasPermission.value = true
  } catch (e) {
    const status = (e as any)?.response?.status
    if (status === 403 || status === 404) {
      hasPermission.value = false
    }
  } finally {
    loading.value = false
  }
}

function formatValue(value: any) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function getCIName(_ci: any) {
  if (!_ci) return ''
  const ipFields = ['ip', 'manage_ip', 'wan_port_ip', 'wan_ip', 'lan_ip', 'private_ip', 'public_ip', 'ips']
  for (const f of ipFields) {
    const val = _ci[f]
    if (val != null && val !== '') {
      if (Array.isArray(val)) return val[0] || ''
      return String(val)
    }
  }
  if (_ci.unique && _ci[_ci.unique] != null && String(_ci[_ci.unique]).trim() !== '') {
    return String(_ci[_ci.unique])
  }
  return _ci.name || _ci.alias || _ci.hostname || _ci.manage_ip || _ci.ip || _ci.netdev_name || _ci._id || ''
}

function goToCI(nextTypeId: number | null, nextCiId: number | null) {
  if (nextTypeId != null && nextCiId != null) {
    router.push(`/cmdb/mobile/${nextTypeId}/${nextCiId}`)
  }
}

function goBack() {
  router.go(-1)
}

watch(
  () => route.params,
  () => {
    loadFromRoute()
  }
)

onMounted(() => {
  loadFromRoute()
})
</script>

<template>
  <div class="mobile-detail-page">
    <div class="mobile-header">
      <ArrowLeftOutlined class="mobile-back-btn" @click="goBack" />
      <span class="mobile-header-title">
        {{ typeInfo.alias || typeInfo.name || t('cmdb.ci.mobileDetail') }}
      </span>
      <span class="mobile-header-right"></span>
    </div>

    <div v-if="loading" class="mobile-loading">
      <a-spin size="large" />
      <p>{{ t('loading') }}</p>
    </div>

    <div v-else-if="!hasPermission" class="mobile-empty">
      <a-empty :image-style="{ height: '80px' }">
        <template #description><span>{{ t('cmdb.ci.noPermission') }}</span></template>
      </a-empty>
    </div>

    <div v-else class="mobile-content">
      <div class="mobile-card">
        <div class="mobile-card-title">
          <InfoCircleOutlined />
          {{ t('cmdb.ci.coreInfo') }}
          <span class="mobile-card-title-ciid">#{{ ci._id }}</span>
        </div>
        <div class="mobile-card-body">
          <div
            v-for="entry in coreAttrEntries"
            :key="entry.name"
            :class="['mobile-attr-row', entry._isLongValue ? 'mobile-attr-row-stacked' : '']"
          >
            <span class="mobile-attr-label">{{ entry.alias }}</span>
            <span class="mobile-attr-value">{{ entry.value }}</span>
          </div>
          <div v-if="coreAttrEntries.length === 0" class="mobile-attr-empty">
            {{ t('noData') }}
          </div>
        </div>
      </div>

      <div v-if="parentRelations.length" class="mobile-card">
        <div class="mobile-card-title mobile-card-title-collapsible" @click="parentCollapsed = !parentCollapsed">
          <ArrowUpOutlined />
          {{ t('cmdb.ci.parentRelations') }}
          <span class="mobile-card-title-count">({{ parentRelations.length }})</span>
          <component :is="parentCollapsed ? DownOutlined : UpOutlined" class="mobile-card-title-arrow" />
        </div>
        <div v-show="!parentCollapsed" class="mobile-card-body">
          <div
            v-for="(item, idx) in parentRelations"
            :key="'p-' + idx"
            class="mobile-relation-item"
            @click="goToCI(item._type, item._id)"
          >
            <LinkOutlined class="mobile-relation-icon" />
            <div class="mobile-relation-info">
              <span class="mobile-relation-type">{{ item._type_name || '' }}</span>
              <span class="mobile-relation-name">{{ getCIName(item) }}</span>
            </div>
            <RightOutlined class="mobile-relation-arrow" />
          </div>
        </div>
      </div>

      <div v-if="childRelations.length" class="mobile-card">
        <div class="mobile-card-title mobile-card-title-collapsible" @click="childCollapsed = !childCollapsed">
          <ArrowDownOutlined />
          {{ t('cmdb.ci.childRelations') }}
          <span class="mobile-card-title-count">({{ childRelations.length }})</span>
          <component :is="childCollapsed ? DownOutlined : UpOutlined" class="mobile-card-title-arrow" />
        </div>
        <div v-show="!childCollapsed" class="mobile-card-body">
          <div
            v-for="(item, idx) in childRelations"
            :key="'c-' + idx"
            class="mobile-relation-item"
            @click="goToCI(item._type, item._id)"
          >
            <LinkOutlined class="mobile-relation-icon" />
            <div class="mobile-relation-info">
              <span class="mobile-relation-type">{{ item._type_name || '' }}</span>
              <span class="mobile-relation-name">{{ getCIName(item) }}</span>
            </div>
            <RightOutlined class="mobile-relation-arrow" />
          </div>
        </div>
      </div>

      <div v-if="historyList.length" class="mobile-card">
        <div class="mobile-card-title">
          <ClockCircleOutlined />
          {{ t('cmdb.ci.recentHistory') }}
        </div>
        <div class="mobile-card-body">
          <div v-for="(h, idx) in historyList" :key="'h-' + idx" class="mobile-history-item">
            <div class="mobile-history-meta">
              <a-tag :color="h._operateColor">{{ h._operateLabel }}</a-tag>
              <span class="mobile-history-attr">{{ h.attr_alias || h.attr_name }}</span>
            </div>
            <div v-if="h.old || h.new" class="mobile-history-values">
              <span class="mobile-history-old">{{ formatValue(h.old) || '-' }}</span>
              <ArrowRightOutlined class="mobile-history-arrow-icon" />
              <span class="mobile-history-new">{{ formatValue(h.new) || '-' }}</span>
            </div>
            <div class="mobile-history-time">
              {{ h.created_at }}
              <span class="mobile-history-user">by {{ h.username }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.mobile-detail-page {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding-bottom: 32px;
  -webkit-overflow-scrolling: touch;
}

.mobile-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 16px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
}

.mobile-back-btn {
  font-size: 18px;
  color: #333;
  flex-shrink: 0;
}

.mobile-header-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
  flex: 1;
  padding: 0 8px;
}

.mobile-header-right {
  width: 18px;
  flex-shrink: 0;
}

.mobile-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  color: #999;
}

.mobile-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 60vh;
}

.mobile-content {
  padding: 12px;
}

.mobile-card {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.mobile-card-title {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;

  .anticon {
    margin-right: 6px;
    color: @primary-color;
  }
}

.mobile-card-title-ciid {
  margin-left: auto;
  font-size: 12px;
  font-weight: 400;
  color: #bbb;
}

.mobile-card-title-collapsible {
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  user-select: none;

  &:active {
    background: #f0f0f0;
  }
}

.mobile-card-title-count {
  margin-left: 4px;
  font-size: 12px;
  font-weight: 400;
  color: #bbb;
}

.mobile-card-title-arrow {
  margin-left: auto;
  font-size: 12px;
  color: #bbb;
  transition: transform 0.2s;
}

.mobile-attr-empty {
  padding: 24px 0;
  text-align: center;
  color: #bbb;
  font-size: 13px;
}

.mobile-card-body {
  padding: 0;
}

.mobile-attr-row {
  display: flex;
  align-items: flex-start;
  padding: 10px 16px;
  border-bottom: 1px solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }

  &.mobile-attr-row-stacked {
    flex-direction: column;
    gap: 4px;
  }
}

.mobile-attr-label {
  width: 100px;
  flex-shrink: 0;
  font-size: 13px;
  color: #999;
  text-align: left;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  .mobile-attr-row-stacked & {
    width: 100%;
    text-align: left;
    margin-bottom: 2px;
    overflow: visible;
    white-space: normal;
  }
}

.mobile-attr-value {
  flex: 1;
  min-width: 0;
  padding-left: 12px;
  font-size: 13px;
  color: #333;
  word-break: break-word;
  overflow-wrap: break-word;
  line-height: 1.5;

  .mobile-attr-row-stacked & {
    padding-left: 0;
  }
}

.mobile-relation-item {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background: #f5f5f5;
  }
}

.mobile-relation-icon {
  font-size: 14px;
  color: @primary-color;
  margin-right: 10px;
  flex-shrink: 0;
}

.mobile-relation-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mobile-relation-type {
  font-size: 11px;
  color: #999;
  background: #f0f0f0;
  padding: 1px 6px;
  border-radius: 3px;
  align-self: flex-start;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-relation-name {
  font-size: 13px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.mobile-relation-arrow {
  font-size: 12px;
  color: #ccc;
  margin-left: 8px;
  flex-shrink: 0;
}

.mobile-history-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }
}

.mobile-history-meta {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  flex-wrap: wrap;
  gap: 6px;
}

.mobile-history-attr {
  font-size: 13px;
  color: #333;
  font-weight: 500;
}

.mobile-history-values {
  display: flex;
  align-items: flex-start;
  font-size: 12px;
  margin-bottom: 4px;
  gap: 4px;
}

.mobile-history-old {
  color: #ff4d4f;
  background: #fff1f0;
  padding: 2px 8px;
  border-radius: 3px;
  max-width: 45%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}

.mobile-history-arrow-icon {
  margin-top: 3px;
  font-size: 11px;
  color: #999;
  flex-shrink: 0;
}

.mobile-history-new {
  color: #52c41a;
  background: #f6ffed;
  padding: 2px 8px;
  border-radius: 3px;
  max-width: 45%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}

.mobile-history-time {
  font-size: 11px;
  color: #bbb;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-history-user {
  margin-left: 8px;
}
</style>
