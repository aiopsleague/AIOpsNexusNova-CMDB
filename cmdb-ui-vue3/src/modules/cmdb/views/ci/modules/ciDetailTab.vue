<script setup lang="ts">
import { computed, inject, nextTick, provide, ref } from 'vue'
import {
  AlertOutlined,
  BookOutlined,
  BranchesOutlined,
  ClockCircleOutlined,
  DashboardOutlined,
  DeleteOutlined,
  EditOutlined,
  HistoryOutlined,
  LinkOutlined,
  PlusCircleOutlined,
  ShareAltOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { getCITypeGroupById, getCITypes } from '@/modules/cmdb/api/CIType'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { getCIHistory } from '@/modules/cmdb/api/history'
import { checkCITypeMonitoring, checkCIPrometheus, getCIById, searchCI } from '@/modules/cmdb/api/ci'
import { getCITypeChildren, getCITypeParent } from '@/modules/cmdb/api/CITypeRelation'
import { searchCIRelation } from '@/modules/cmdb/api/CIRelation'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import dataEmptyImg from '@/assets/data_empty.png'
import CIDetailTitle from './ciDetailComponent/ciDetailTitle.vue'
import CIDetailTableTitle from './ciDetailComponent/ciDetailTableTitle.vue'
import CIDetailAttrContent from './ciDetailAttrContent.vue'
import CIRelationTable from './ciDetailComponent/ciRelationTable.vue'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    typeId: number
    treeViewsLevels?: any[]
    attributeHistoryTableHeight?: number | null
  }>(),
  {
    treeViewsLevels: () => [],
    attributeHistoryTableHeight: null,
  }
)

const emit = defineEmits<{
  (e: 'navigateToCi', payload: { typeId: number; ciId: number }): void
}>()

const reload = inject<(() => void) | null>('reload', null)
const handleSearch = inject<(() => void) | null>('handleSearch', null)
const injectedAttrList = inject<() => any[]>('attrList', () => [])

const ci = ref<Record<string, any>>({})
const attributeGroups = ref<any[]>([])
const activeTabKey = ref('tab_1')
const ciHistory = ref<any[]>([])
const ciId = ref<number | null>(null)
const ciTypes = ref<any[]>([])
const hasPermission = ref(true)
const localAttrList = ref<any[]>([])
const localAttributes = ref<Record<string, any>>({})
const hasMonitoring = ref(false)
const hasPrometheus = ref(false)
const grafanaConHealthy = ref<boolean | null>(null)
const promConHealthy = ref<boolean | null>(null)

// relationData + relation mixin logic (inlined)
const relationData = ref<Record<string, any>>({
  parentCITypeList: [],
  childCITypeList: [],
  parentCIList: [],
  childCIList: [],
})

const xTableRef = ref<any>()

const tableHeight = computed(() => props.attributeHistoryTableHeight || window.innerHeight - 130)

const operateTypeMap = computed<Record<number, string>>(() => ({
  0: t('new'),
  1: t('delete'),
  2: t('update'),
}))

const ciHistoryStatsList = [
  { label: 'cmdb.history.totalChanges', icon: HistoryOutlined, type: 'total', value: 'total' },
  { label: 'new', icon: PlusCircleOutlined, type: 'new', value: 0 },
  { label: 'update', icon: EditOutlined, type: 'update', value: 2 },
  { label: 'delete', icon: DeleteOutlined, type: 'delete', value: 1 },
]

provide('ci_types', () => ciTypes.value)
provide('attrList', () => localAttrList.value)
provide('attributes', () => localAttributes.value)

async function create(newCiId: number, newActiveTabKey = 'tab_1', typeId: number | null = null) {
  const effectiveTypeId = typeId || props.typeId
  activeTabKey.value = newActiveTabKey
  ciId.value = newCiId

  await getCI()
  if (hasPermission.value) {
    getAttributes(effectiveTypeId)
    loadAttrList(effectiveTypeId)
    checkMonitoring(effectiveTypeId)
    checkPrometheus(effectiveTypeId)
    loadCIHistory()
    const ciTypeRes = await getCITypes()
    ciTypes.value = ciTypeRes.ci_types

    initRelationData(effectiveTypeId, ciId.value)
  }
}

function getAttributes(typeIdOverride?: number) {
  const typeId = typeIdOverride || props.typeId
  getCITypeGroupById(typeId, { need_other: 1 })
    .then((res) => {
      attributeGroups.value = (res || []).filter((group: any) => group?.attributes?.length)
      handleReferenceAttr()
    })
    .catch(() => {})
}

async function loadAttrList(typeIdOverride?: number) {
  const typeId = typeIdOverride || props.typeId
  try {
    const res = await getCITypeAttributesById(typeId)
    localAttrList.value = res.attributes || []
    localAttributes.value = res
  } catch {
    localAttrList.value = []
    localAttributes.value = {}
  }
}

async function handleReferenceAttr() {
  const map: Record<string, Record<string, unknown>> = {}
  attributeGroups.value.forEach((group) => {
    group.attributes.forEach((attr: any) => {
      if (attr?.is_reference && attr?.reference_type_id && ci.value[attr.name]) {
        const ids = Array.isArray(ci.value[attr.name])
          ? ci.value[attr.name]
          : ci.value[attr.name]
            ? [ci.value[attr.name]]
            : []
        if (ids.length) {
          if (!map?.[attr.reference_type_id]) {
            map[attr.reference_type_id] = {}
          }
          ids.forEach((id: any) => {
            map[attr.reference_type_id][id] = {}
          })
        }
      }
    })
  })

  if (!Object.keys(map).length) {
    return
  }

  const ciTypesRes = await getCITypes({
    type_ids: Object.keys(map).join(','),
  })
  const showAttrNameMap: Record<string, string> = {}
  ciTypesRes.ci_types.forEach((ciType: any) => {
    showAttrNameMap[ciType.id] = ciType?.show_name || ciType?.unique_name || ''
  })

  const allRes = await Promise.all(
    Object.keys(map).map((key) => {
      return searchCI({
        q: `_type:${key},_id:(${Object.keys(map[key]).join(';')})`,
        count: 9999,
      })
    })
  )

  const ciNameMap: Record<string, any> = {}
  allRes.forEach((res) => {
    res.result.forEach((item: any) => {
      ciNameMap[item._id] = item
    })
  })

  const newAttrGroups = cloneDeep(attributeGroups.value)

  newAttrGroups.forEach((group: any) => {
    group.attributes.forEach((attr: any) => {
      if (attr?.is_reference && attr?.reference_type_id) {
        attr.showAttrName = showAttrNameMap?.[attr?.reference_type_id] || ''

        const referenceShowAttrNameMap: Record<string, string> = {}
        const referenceCIIds = ci.value[attr.name]
        ;(Array.isArray(referenceCIIds) ? referenceCIIds : referenceCIIds ? [referenceCIIds] : []).forEach(
          (id: any) => {
            referenceShowAttrNameMap[id] = ciNameMap?.[id]?.[attr.showAttrName] ?? id
          }
        )
        attr.referenceShowAttrNameMap = referenceShowAttrNameMap
      }
    })
  })

  attributeGroups.value = newAttrGroups
}

async function getCI() {
  await getCIById(ciId.value as number)
    .then((res) => {
      if (res.result.length) {
        ci.value = res.result[0]
      } else {
        hasPermission.value = false
      }
    })
    .catch(() => {})
}

async function checkMonitoring(typeIdOverride?: number) {
  const typeId = typeIdOverride || props.typeId
  try {
    const res = await checkCITypeMonitoring(typeId)
    hasMonitoring.value = res.has_monitoring || false
  } catch {
    hasMonitoring.value = false
  }
}

async function checkPrometheus(typeIdOverride?: number) {
  const typeId = typeIdOverride || props.typeId
  try {
    const res = await checkCIPrometheus(typeId)
    hasPrometheus.value = res.has_prometheus || false
  } catch {
    hasPrometheus.value = false
  }
}

function loadCIHistory() {
  getCIHistory(ciId.value as number)
    .then((res) => {
      ciHistory.value = res
    })
    .catch((e) => {
      console.log(e)
    })
}

function changeTab(key: string) {
  activeTabKey.value = key
  if (key === 'tab_3') {
    nextTick(() => {
      const $table = xTableRef.value
      if ($table) {
        const usernameColumn = $table.getColumnByField('username')
        const attrColumn = $table.getColumnByField('attr_alias')
        if (usernameColumn) {
          const usernameList = [...new Set(ciHistory.value.map((item) => item.username))]
          $table.setFilter(
            usernameColumn,
            usernameList.map((item) => ({ value: item, label: item }))
          )
        }
        if (attrColumn) {
          $table.setFilter(
            attrColumn,
            injectedAttrList().map((attr) => ({ value: attr.alias || attr.name, label: attr.alias || attr.name }))
          )
        }
      }
    })
  }
}

function handleNavigateToCi({ typeId, ciId: newCiId }: { typeId: number; ciId: number }) {
  create(newCiId, 'tab_2', typeId)
  emit('navigateToCi', { typeId, ciId: newCiId })
}

function filterUsernameMethod({ value, row }: any) {
  return row.username === value
}

function filterOperateMethod({ value, row }: any) {
  return Number(row.operate_type) === Number(value)
}

function filterAttrMethod({ value, row }: any) {
  return row.attr_alias === value
}

function refresh(editAttrName: string) {
  getCI()
  const _find = props.treeViewsLevels.find((level) => level.name === editAttrName)
  setTimeout(() => {
    if (_find) {
      reload?.()
    } else {
      handleSearch?.()
    }
  }, 500)
}

function mergeRowMethod({ row, _rowIndex, column, visibleData }: any) {
  const fields = ['created_at', 'username']
  const cellValue1 = row['created_at']
  const cellValue2 = row['username']
  if (cellValue1 && cellValue2 && fields.includes(column.property)) {
    const prevRow = visibleData[_rowIndex - 1]
    let nextRow = visibleData[_rowIndex + 1]
    if (prevRow && prevRow['created_at'] === cellValue1 && prevRow['username'] === cellValue2) {
      return { rowspan: 0, colspan: 0 }
    } else {
      let countRowspan = 1
      while (nextRow && nextRow['created_at'] === cellValue1 && nextRow['username'] === cellValue2) {
        nextRow = visibleData[++countRowspan + _rowIndex]
      }
      if (countRowspan > 1) {
        return { rowspan: countRowspan, colspan: 1 }
      }
    }
  }
}

function updateCIByself(params: Record<string, any>, editAttrName: string) {
  ci.value = { ...cloneDeep(ci.value), ...params }
  const _find = props.treeViewsLevels.find((level) => level.name === editAttrName)
  setTimeout(() => {
    if (_find) {
      reload?.()
    } else {
      handleSearch?.()
    }
  }, 500)
}

async function shareCi() {
  const text = `${document.location.host}/cmdb/cidetail/${props.typeId}/${ciId.value}`
  try {
    await navigator.clipboard.writeText(text)
    message.success(t('copySuccess'))
  } catch {
    message.error(t('cmdb.ci.copyFailed'))
  }
}

function handleRollbackCI() {
  // TODO: wire up CIRollbackForm (rollback drawer not yet ported)
}

function handleExport() {
  xTableRef.value?.exportData({
    filename: t('cmdb.ci.history'),
    sheetName: 'Sheet1',
    type: 'xlsx',
    types: ['xlsx', 'csv', 'html', 'xml', 'txt'],
    data: ciHistory.value,
    isMerge: true,
    isColgroup: true,
  })
}

function getOperateTypeCount(operateType: number | string) {
  return ciHistory.value.filter((item) => Number(item.operate_type) === Number(operateType)).length
}

// --- relation mixin logic (inlined) ---
async function initRelationData(typeId: number, targetCiId: number | null) {
  const { parentCITypeList, childCITypeList } = await getRelationCITypeList(typeId)
  const { parentCIList, childCIList } = await getRelationCIList(targetCiId)
  relationData.value = { parentCITypeList, childCITypeList, parentCIList, childCIList }
}

async function getRelationCITypeList(typeId: number) {
  let parentCITypeList: any[] = []
  let childCITypeList: any[] = []

  if (typeId) {
    parentCITypeList = await getParentCITypeList(typeId)
    childCITypeList = await getChildCITypeList(typeId)
  }

  return { parentCITypeList, childCITypeList }
}

async function getRelationCIList(targetCiId: number | null) {
  let parentCIList: any[] = []
  let childCIList: any[] = []

  if (targetCiId) {
    parentCIList = await getParentCIList(targetCiId)
    childCIList = await getChildCIList(targetCiId)
  }

  return { parentCIList, childCIList }
}

async function refreshRelationCI(targetCiId: number | null) {
  const { parentCIList, childCIList } = await getRelationCIList(targetCiId)
  relationData.value.parentCIList = parentCIList
  relationData.value.childCIList = childCIList
}

async function getParentCITypeList(typeId: number) {
  const res = await getCITypeParent(typeId)
  return res?.parents || []
}

async function getChildCITypeList(typeId: number) {
  const res = await getCITypeChildren(typeId)
  return res.children || []
}

async function getParentCIList(targetCiId: number) {
  const res = await searchCIRelation(`root_id=${targetCiId}&level=1&reverse=1&count=10000`)
  return res?.result || []
}

async function getChildCIList(targetCiId: number) {
  const res = await searchCIRelation(`root_id=${targetCiId}&level=1&reverse=0&count=10000`)
  return res?.result || []
}

defineExpose({ create, handleNavigateToCi })
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <div :style="{ height: '100%' }">
    <a-tabs v-if="hasPermission" v-model:activeKey="activeTabKey" class="ci-detail-tab" @change="changeTab">
      <template #tabBarExtraContent>
        <span class="tab-bar-extra">
          <!-- TODO: wire up QRCodeButton (:typeId="typeId" :ciId="ciId") -->
          <a @click="shareCi">
            <ShareAltOutlined />
            {{ t('cmdb.ci.share') }}
          </a>
        </span>
      </template>
      <a-tab-pane key="tab_1">
        <template #tab><BookOutlined />{{ t('cmdb.ci.detail') }}</template>

        <div class="ci-detail-table">
          <CIDetailTitle :ci="ci" :ci_types="ciTypes" />

          <div class="ci-detail-table-attr">
            <CIDetailTableTitle :title="t('cmdb.attribute')" />

            <div class="ci-detail-table-attr-wrap">
              <div v-for="group in attributeGroups" :key="group.name" class="ci-detail-table-attr-group">
                <div class="ci-detail-table-attr-group-name">
                  {{ group.name || t('other') }}
                </div>

                <div class="ci-detail-attrs-grid">
                  <div
                    v-for="attr in group.attributes"
                    :key="attr.name"
                    :class="['ci-detail-attr-item', attr._isTableFormatDisplay ? 'ci-detail-attr-item-full' : '']"
                  >
                    <div class="ci-detail-attr-label">
                      <a-tooltip :title="attr.alias || attr.name">
                        <span class="ci-detail-attr-label-text">{{ attr.alias || attr.name }}</span>
                      </a-tooltip>
                      <span class="ci-detail-attr-label-colon">:</span>
                    </div>
                    <div class="ci-detail-attr-content">
                      <CIDetailAttrContent
                        :ci="ci"
                        :attr="attr"
                        :attribute-groups="attributeGroups"
                        @refresh="refresh"
                        @update-c-i-byself="updateCIByself"
                        @refresh-reference-attr="handleReferenceAttr"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <CIRelationTable
            :ci-id="ciId"
            :type-id="typeId"
            :ci="ci"
            :relation-data="relationData"
            @refresh-relation-c-i="refreshRelationCI(ciId)"
          />
        </div>
      </a-tab-pane>
      <a-tab-pane key="tab_2">
        <template #tab><BranchesOutlined />{{ t('cmdb.ci.topo') }}</template>
        <div :style="{ height: '100%', padding: '24px', overflow: 'auto' }">
          <!-- TODO: wire up CIDetailRelation (topology tab not yet ported) -->
        </div>
      </a-tab-pane>
      <a-tab-pane key="tab_3">
        <template #tab><ClockCircleOutlined />{{ t('cmdb.ci.changeHistory') }}</template>
        <div class="ci-history-container">
          <!-- Statistics Information Card -->
          <div class="ci-history-stats">
            <div v-for="stat in ciHistoryStatsList" :key="stat.type" class="ci-history-stat-card">
              <div :class="`stat-icon stat-icon-${stat.type}`">
                <component :is="stat.icon" />
              </div>
              <div class="stat-content">
                <div class="stat-label">{{ t(stat.label) }}</div>
                <div class="stat-value">
                  {{ stat.value === 'total' ? ciHistory.length : getOperateTypeCount(stat.value) }}
                </div>
              </div>
            </div>
          </div>

          <!-- Operation Button Group -->
          <div class="ci-history-actions">
            <a-button type="primary" class="ops-button-ghost" ghost @click="handleRollbackCI()">
              {{ t('cmdb.ci.rollback') }}
            </a-button>
            <a-button type="primary" class="ops-button-ghost" ghost @click="handleExport">
              {{ t('export') }}
            </a-button>
          </div>

          <!-- Change Log Table -->
          <vxe-table
            ref="xTableRef"
            show-overflow
            show-header-overflow
            :data="ciHistory"
            size="small"
            :height="tableHeight - 130"
            highlight-hover-row
            :span-method="mergeRowMethod"
            :scroll-y="{ enabled: false, gt: 20 }"
            :scroll-x="{ enabled: false, gt: 0 }"
            border
            resizable
            class="ops-unstripe-table ci-history-table"
          >
            <template #empty>
              <a-empty :image="dataEmptyImg" :image-style="{ height: '100px' }" :style="{ paddingTop: '10%' }">
                <template #description>{{ t('noData') }}</template>
              </a-empty>
            </template>
            <vxe-column sortable field="created_at" :title="t('created_at')" width="180"></vxe-column>
            <vxe-column
              field="username"
              :title="t('user')"
              :filters="[]"
              :filter-method="filterUsernameMethod"
              width="140"
            ></vxe-column>
            <vxe-column
              field="operate_type"
              :filters="[
                { value: 0, label: t('new') },
                { value: 1, label: t('delete') },
                { value: 2, label: t('update') },
              ]"
              :filter-method="filterOperateMethod"
              :title="t('operation')"
              width="120"
            >
              <template #default="{ row }">
                <a-tag>{{ operateTypeMap[row.operate_type] }}</a-tag>
              </template>
            </vxe-column>
            <vxe-column
              field="attr_alias"
              :title="t('cmdb.attribute')"
              :filters="[]"
              :filter-method="filterAttrMethod"
              width="180"
            >
              <template #default="{ row }">
                <a-tag color="blue" :style="{ borderRadius: '4px' }">{{ row.attr_alias }}</a-tag>
              </template>
            </vxe-column>
            <vxe-column field="old" :title="t('cmdb.history.old')" min-width="200">
              <template #default="{ row }">
                <div class="ci-history-value ci-history-value-old">
                  <span v-if="row.value_type === '6'">{{ JSON.parse(row.old) }}</span>
                  <span v-else>{{ row.old || '-' }}</span>
                </div>
              </template>
            </vxe-column>
            <vxe-column field="new" :title="t('cmdb.history.new')" min-width="200">
              <template #default="{ row }">
                <div class="ci-history-value ci-history-value-new">
                  <span v-if="row.value_type === '6'">{{ JSON.parse(row.new) }}</span>
                  <span v-else>{{ row.new || '-' }}</span>
                </div>
              </template>
            </vxe-column>
          </vxe-table>
        </div>
      </a-tab-pane>
      <a-tab-pane key="tab_4">
        <template #tab><ThunderboltOutlined />{{ t('cmdb.history.triggerHistory') }}</template>
        <div :style="{ padding: '24px', height: '100%' }">
          <!-- TODO: wire up TriggerTable (:ci_id="ci._id") -->
        </div>
      </a-tab-pane>
      <a-tab-pane key="tab_5">
        <template #tab><LinkOutlined />{{ t('cmdb.ci.relITSM') }}</template>
        <div :style="{ padding: '24px', height: '100%' }">
          <!-- TODO: wire up RelatedItsm -->
        </div>
      </a-tab-pane>
      <a-tab-pane key="tab_6" v-if="hasMonitoring">
        <template #tab>
          <DashboardOutlined />{{ t('cmdb.ci.monitoring') }}
          <a-badge v-if="grafanaConHealthy === false" status="error" class="tab-status-dot" />
        </template>
        <div :style="{ padding: '24px', height: '100%' }">
          <!-- TODO: wire up CiDetailMonitoring (:ciId="ciId") -->
        </div>
      </a-tab-pane>
      <a-tab-pane key="tab_7" v-if="hasPrometheus">
        <template #tab>
          <AlertOutlined />{{ t('cmdb.ci.prometheusAlerts') }}
          <a-badge v-if="promConHealthy === false" status="error" class="tab-status-dot" />
        </template>
        <div :style="{ padding: '24px', height: '100%' }">
          <!-- TODO: wire up CiDetailPrometheus (:ciId="ciId") -->
        </div>
      </a-tab-pane>
    </a-tabs>
    <a-empty v-else :image="dataEmptyImg" :image-style="{ height: '100px' }" :style="{ paddingTop: '20%' }">
      <template #description>{{ t('cmdb.ci.noPermission') }}</template>
    </a-empty>
  </div>
</template>

<style lang="less">
.ci-detail-tab {
  height: 100%;

  .tab-status-dot {
    margin-left: 6px;
    vertical-align: middle;

    :deep(.ant-badge-status-dot) {
      width: 8px;
      height: 8px;
    }
  }

  .ant-tabs-content {
    height: calc(100% - 45px);
    .ant-tabs-tabpane {
      height: 100%;
    }
  }
  .ant-tabs-bar {
    margin: 0;
  }
  .ant-tabs-extra-content {
    line-height: 44px;
    margin-right: 24px;
  }
  .ci-detail-table {
    height: 100%;
    overflow-x: hidden;
    overflow-y: auto;
    padding: 20px;
    background-color: #f5f7fa;

    &-attr {
      width: 100%;
      margin-top: 16px;

      &-wrap {
        padding: 20px;
        width: 100%;
        border: none;
        background: #ffffff;
        border-radius: 0 0 8px 8px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
      }

      &-group {
        &:not(:last-child) {
          margin-bottom: 24px;
          padding-bottom: 24px;
          border-bottom: 1px solid #e8eaed;
        }

        &-name {
          font-size: 14px;
          font-weight: 600;
          color: @text-color_1;
          margin-bottom: 16px;
          width: 100%;
          text-align: left;
          display: flex;
          align-items: center;
          position: relative;
          padding-left: 12px;
          line-height: 16px;

          &::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            width: 4px;
            height: 16px;
            background: @primary-color;
            border-radius: 2px;
          }
        }
      }
    }
  }

  // 属性Grid布局
  .ci-detail-attrs-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 4px 18px;
  }

  .ci-detail-attr-item {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 8px;
    padding: 8px 12px;
    transition: background-color 0.2s ease;
    border-radius: 4px;
    min-height: 28px;
    align-items: center;

    &:hover {
      background-color: #f8f9fb;
    }

    &-full {
      grid-column: ~"1 / -1";
      grid-template-columns: 120px 1fr;
      align-items: flex-start;
    }
  }

  .ci-detail-attr-label {
    font-size: 13px;
    font-weight: 500;
    color: @text-color_3;
    display: flex;
    align-items: center;
    white-space: nowrap;

    &-text {
      overflow: hidden;
      text-overflow: ellipsis;
    }

    &-colon {
      flex-shrink: 0;
      margin-left: 2px;
    }
  }

  .ci-detail-attr-content {
    overflow-wrap: break-word;
    font-size: 13px;
    color: @text-color_1;
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 28px;

    > span {
      display: flex;
      align-items: center;
      gap: 8px;
      flex: 1;
      min-width: 0;
    }

    .ant-form-item {
      margin-bottom: 0;
    }

    a[opacity] {
      flex-shrink: 0;
      display: flex;
      align-items: center;
      height: 32px;
    }

    &:hover a {
      opacity: 1 !important;
    }
  }

  .ci-detail-table {
    .ant-form-item {
      margin-bottom: 0;
    }
    .ant-form-item-control {
      line-height: 19px;
    }
  }
}

// CI变更记录页面样式
.ci-history-container {
  padding: 24px;
  height: 100%;
  background-color: #f5f7fa;
  overflow-y: auto;
}

// 统计信息卡片
.ci-history-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.ci-history-stat-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fb 100%);
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e8eaed;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }

  .stat-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;

    &.stat-icon-total {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #fff;
    }

    &.stat-icon-new {
      background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
      color: #fff;
    }

    &.stat-icon-update {
      background: linear-gradient(135deg, #fa8c16 0%, #d46b08 100%);
      color: #fff;
    }

    &.stat-icon-delete {
      background: linear-gradient(135deg, #f5222d 0%, #cf1322 100%);
      color: #fff;
    }
  }

  .stat-content {
    flex: 1;
  }

  .stat-label {
    font-size: 13px;
    color: @text-color_3;
    margin-bottom: 4px;
  }

  .stat-value {
    font-size: 22px;
    font-weight: 600;
    color: @text-color_1;
    line-height: 1;
  }
}

// 操作按钮组
.ci-history-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

// 变更记录表格
.ci-history-table {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;

  .ci-history-value {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 13px;
    min-height: 32px;
    overflow: hidden;
    text-overflow: ellipsis;
    text-wrap-mode: nowrap;

    &.ci-history-value-old {
      background-color: #f5f5f5;
      color: #8c8c8c;
      border: 1px solid #d9d9d9;
    }

    &.ci-history-value-new {
      background-color: #e6f7ff;
      color: @primary-color;
      border: 1px solid #91d5ff;
    }
  }
}
</style>
