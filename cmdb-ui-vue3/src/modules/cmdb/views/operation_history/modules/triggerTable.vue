<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Pager from '@/components/Pager/index.vue'
import { getCiTriggers, getCiTriggersByCiId } from '@/modules/cmdb/api/history'
import { useOperationHistory } from '../composables/useOperationHistory'
import { PAGINATION_CONFIG } from '../constants'
import dataEmptyImg from '@/assets/data_empty.png'

const props = withDefaults(
  defineProps<{
    ciId?: number | null
  }>(),
  { ciId: null }
)

const { t } = useI18n()
const { handleError } = useOperationHistory()

const loading = ref(false)
const tableData = ref<any[]>([])
const tablePage = ref({
  currentPage: 1,
  pageSize: PAGINATION_CONFIG.DEFAULT_PAGE_SIZE,
  totalResult: 0,
})
const PAGE_SIZE_OPTIONS = PAGINATION_CONFIG.PAGE_SIZE_OPTIONS

const windowHeight = computed(() => window.innerHeight)

const operateTypeMap = computed<Record<string, string>>(() => ({
  '0': t('cmdb.ciType.addInstance'),
  '1': t('cmdb.ciType.deleteInstance'),
  '2': t('cmdb.ciType.changeInstance'),
}))

onMounted(() => {
  updateTableData()
})

async function updateTableData(currentPage = 1, pageSize = tablePage.value.pageSize) {
  try {
    loading.value = true
    const params = { page: currentPage, page_size: pageSize }

    if (props.ciId) {
      const res = await getCiTriggersByCiId(props.ciId, params)
      tableData.value = res.items.map((item: any) => ({
        ...item,
        trigger: res.id2trigger[item.trigger_id],
      }))
    } else {
      const res = await getCiTriggers(params)
      tableData.value = res?.result || []
      tablePage.value = {
        currentPage: res.page,
        pageSize: res.page_size,
        totalResult: res.numfound,
      }
    }
  } catch (error) {
    handleError(error, 'fetch trigger history')
  } finally {
    loading.value = false
  }
}

function onChange(pageNum: number) {
  updateTableData(pageNum, tablePage.value.pageSize)
}

function onShowSizeChange(size: number) {
  updateTableData(1, size)
}

function getTriggerType(row: any) {
  if (!row.trigger) return ''
  return row.trigger.attr_id ? t('cmdb.ciType.triggerDate') : t('cmdb.ciType.triggerDataChange')
}

function getEventType(row: any) {
  return operateTypeMap.value[row.operate_type] || ''
}

function getActionType(row: any) {
  if (row.webhook) return 'Webhook'
  if (row.notify) return t('cmdb.ciType.notify')
  return ''
}
</script>

<template>
  <div class="operation-history-table">
    <vxe-table
      show-overflow
      show-header-overflow
      stripe
      size="small"
      class="ops-stripe-table"
      :loading="loading"
      :data="tableData"
      :height="ciId ? 'auto' : undefined"
      :max-height="ciId ? undefined : `${windowHeight - 290}px`"
    >
      <template #empty>
        <a-empty :image-style="{ height: '100px' }" :style="{ paddingTop: '10%' }">
          <template #image>
            <img :src="dataEmptyImg" />
          </template>
          <template #description>
            <span>{{ t('noData') }}</span>
          </template>
        </a-empty>
      </template>
      <vxe-column field="trigger_name" min-width="150" :title="t('cmdb.history.triggerName')"></vxe-column>
      <vxe-column field="type" min-width="120" :title="t('type')">
        <template #default="{ row }">
          {{ getTriggerType(row) }}
        </template>
      </vxe-column>
      <vxe-column min-width="120" :title="t('cmdb.history.event')">
        <template #default="{ row }">
          {{ getEventType(row) }}
        </template>
      </vxe-column>
      <vxe-column min-width="100" :title="t('cmdb.history.action')">
        <template #default="{ row }">
          {{ getActionType(row) }}
        </template>
      </vxe-column>
      <vxe-column min-width="80" :title="t('cmdb.history.status')">
        <template #default="{ row }">
          <a-tag :color="row.is_ok ? 'green' : 'red'">
            {{ row.is_ok ? t('cmdb.history.done') : t('cmdb.history.undone') }}
          </a-tag>
        </template>
      </vxe-column>
      <vxe-column min-width="160" :title="t('cmdb.history.triggerTime')">
        <template #default="{ row }">
          {{ row.updated_at || row.created_at }}
        </template>
      </vxe-column>
    </vxe-table>
    <pager
      v-if="!ciId"
      :current-page="tablePage.currentPage"
      :page-size="tablePage.pageSize"
      :page-sizes="PAGE_SIZE_OPTIONS"
      :total="tablePage.totalResult"
      :is-loading="loading"
      @change="onChange"
      @show-size-change="onShowSizeChange"
    ></pager>
  </div>
</template>

<style lang="less" scoped>
@import '../styles/table.less';
</style>
