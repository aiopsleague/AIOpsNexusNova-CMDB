<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { CheckCircleFilled, CloseCircleFilled } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { getIPAMHistoryScan } from '@/modules/cmdb/api/ipam'

const { t } = useI18n()

const searchValue = ref('')

const page = ref(1)
const pageSize = ref(50)
const pageSizeOptions = ['50', '100', '200']
const tableData = ref<any[]>([])
const totalNumber = ref(0)
const getTableDataParams: Record<string, any> = {}

const windowHeight = computed(() => window.innerHeight)
const tableHeight = computed(() => `${windowHeight.value - 308}px`)

async function getTableData() {
  const res = await getIPAMHistoryScan({
    page: page.value,
    page_size: pageSize.value,
    reverse: 1,
    ...getTableDataParams,
  })

  const list = res?.result || []

  list.forEach((item: any) => {
    if (item.start_at && item.end_at) {
      const startAt = dayjs(item.start_at)
      const endAt = dayjs(item.end_at)
      item.scanning_time = `${endAt.diff(startAt, 'seconds')}s`
    }
  })

  tableData.value = list
  totalNumber.value = res?.numfound || 0
}

function handleChangePage(nextPage: number) {
  page.value = nextPage
  getTableData()
}

function onShowSizeChange(_current: number, nextPageSize: number) {
  page.value = 1
  pageSize.value = nextPageSize
  getTableData()
}

function handleSearch(v: string) {
  if (v) {
    getTableDataParams.cidr = `*${v}*`
  } else if (getTableDataParams.cidr) {
    delete getTableDataParams.cidr
  }
  page.value = 1
  getTableData()
}

onMounted(() => {
  getTableData()
})

defineExpose({ getTableData })
</script>

<template>
  <div class="scan">
    <a-input-search
      v-model:value="searchValue"
      class="scan-search"
      @search="handleSearch"
    />

    <vxe-table
      ref="xTable"
      size="small"
      show-overflow
      show-header-overflow
      highlight-hover-row
      :data="tableData"
      :height="tableHeight"
      :column-config="{ resizable: true }"
      class="ops-unstripe-table scan-table"
    >
      <vxe-column title="CIDR" field="cidr"></vxe-column>
      <vxe-column :title="t('cmdb.ipam.ipNumber')" field="ip_num"></vxe-column>
      <vxe-column :title="t('cmdb.ipam.startTime')" field="start_at"></vxe-column>
      <vxe-column :title="t('cmdb.ipam.endTime')" field="end_at"></vxe-column>
      <vxe-column :title="t('cmdb.ipam.scanningTime')" field="scanning_time"></vxe-column>
      <vxe-column :title="t('cmdb.ipam.isSuccess')" field="status">
        <template #default="{ row }">
          <div v-if="row.status === 0" class="scan-table-success">
            <CheckCircleFilled class="scan-table-success-icon" />
            <div class="scan-table-success-text">{{ t('success') }}</div>
          </div>
          <div v-else class="scan-table-fail">
            <CloseCircleFilled class="scan-table-fail-icon" />
            <div class="scan-table-fail-text">{{ t('fail') }}</div>
          </div>
        </template>
      </vxe-column>
      <vxe-column :title="t('cmdb.ipam.viewResult')" field="operation" :show-overflow="false">
        <template #default="{ row }">
          <a-popover placement="left">
            <span class="scan-table-operation">
              {{ row.status === 0 ? row.ips ? row.ips.join(', ') : '' : row.stdout }}
            </span>
            <template #content>
              <div v-if="row.status === 0" class="scan-table-ip">
                <div
                  v-for="(ip, index) in row.ips"
                  :key="index"
                  class="scan-table-ip-item"
                >
                  {{ ip }}
                </div>
              </div>
              <div v-else class="scan-table-error-log">
                {{ row.stdout }}
              </div>
            </template>
          </a-popover>
        </template>
      </vxe-column>
    </vxe-table>

    <div class="scan-pagination">
      <a-pagination
        show-size-changer
        :current="page"
        size="small"
        :total="totalNumber"
        show-quick-jumper
        :page-size="pageSize"
        :page-size-options="pageSizeOptions"
        :show-total="
          (total: number, range: number[]) =>
            t('pagination.total', {
              range0: range[0],
              range1: range[1],
              total,
            })
        "
        @change="handleChangePage"
        @show-size-change="onShowSizeChange"
      />
    </div>
  </div>
</template>

<style lang="less" scoped>
.scan {
  width: 100%;

  &-search {
    width: 244px;
    margin-bottom: 22px;
  }

  &-table {
    &-success {
      padding: 4px 7px;
      border-radius: 1px;
      background-color: #dcf3e3;
      display: inline-flex;
      align-items: center;
      justify-content: center;

      &-icon {
        font-size: 12px;
        color: #00b42a;
      }

      &-text {
        font-size: 12px;
        font-weight: 400;
        color: #30ad2d;
        margin-left: 4px;
      }
    }

    &-fail {
      padding: 0px 7px;
      border-radius: 1px;
      background-color: #ffece8;
      display: inline-flex;
      align-items: center;
      justify-content: center;

      &-icon {
        font-size: 12px;
        color: #fd4c6a;
      }

      &-text {
        font-size: 12px;
        font-weight: 400;
        color: #fd4c6a;
        margin-left: 4px;
      }
    }

    &-operation {
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      text-wrap: nowrap;
    }

    &-ip {
      width: 100%;
      max-height: 216px;
      overflow-y: auto;
      overflow-x: hidden;
      border: solid 1px #f0f1f5;

      &-item {
        height: 36px;
        line-height: 36px;
        padding: 0 12px;
        font-size: 14px;
        font-weight: 400;
        color: #1d2129;

        &:not(:last-child) {
          border-bottom: solid 1px #f0f1f5;
        }
      }
    }

    &-error-log {
      max-width: 200px;
      max-height: 200px;
      overflow-y: auto;
      overflow-x: hidden;
    }
  }

  &-pagination {
    text-align: right;
    margin-top: 4px;
  }
}
</style>
