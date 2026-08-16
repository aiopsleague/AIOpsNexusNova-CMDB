<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { OPERATE_TYPE_TEXT, OPERATE_TYPE_COLOR, OPERATE_TYPE } from './constants'
import { getIPAMHistoryOperate } from '@/modules/cmdb/api/ipam'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const userStore = useUserStore()

const searchValue = ref('')

const page = ref(1)
const pageSize = ref(50)
const pageSizeOptions = ['50', '100', '200']
const tableData = ref<any[]>([])
const totalNumber = ref(0)
const getTableDataParams: Record<string, any> = {
  reverse: 1,
}
const userFilters = ref<any[]>([])

const allEmployees = computed<any[]>(() => userStore.allEmployees as any[])

const windowHeight = computed(() => window.innerHeight)
const tableHeight = computed(() => `${windowHeight.value - 308}px`)

const operateTypeFilters = computed(() => {
  return Object.values(OPERATE_TYPE).map((key) => {
    return {
      value: key,
      label: t(OPERATE_TYPE_TEXT[key]),
    }
  })
})

/** Deduplicate a list by a given key (drop-in for lodash.uniqBy). */
function uniqBy(list: any[], key: string): any[] {
  const seen = new Set()
  return list.filter((item) => {
    const value = item[key]
    if (seen.has(value)) {
      return false
    }
    seen.add(value)
    return true
  })
}

async function getTableData() {
  const res = await getIPAMHistoryOperate({
    page: page.value,
    page_size: pageSize.value,
    ...getTableDataParams,
  })

  const list = res?.result || []
  const nextUserFilters: any[] = []
  const defaultUserChecked = getTableDataParams.uid ? getTableDataParams.uid.split(',') : []

  list.forEach((item: any) => {
    const nickname = allEmployees.value?.find?.((user: any) => user?.acl_uid === item?.uid)?.nickname
    item.nickname = nickname
    nextUserFilters.push({
      label: nickname,
      value: item.uid,
      checked: defaultUserChecked.includes(String(item.uid)),
    })
  })

  totalNumber.value = res?.numfound || 0
  tableData.value = list
  userFilters.value = uniqBy(nextUserFilters, 'value')
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

function handleChangePage(nextPage: number) {
  page.value = nextPage
  getTableData()
}

function onShowSizeChange(_current: number, nextPageSize: number) {
  page.value = 1
  pageSize.value = nextPageSize
  getTableData()
}

function handlefilterChange({ field, values }: { field: string; values: any[] }) {
  page.value = 1
  const value = values.join(',')
  if (!value && getTableDataParams[field]) {
    delete getTableDataParams[field]
  } else {
    getTableDataParams[field] = values.join(',')
  }
  getTableData()
}

function handleSortChange(data: any) {
  if (data?.order === 'asc') {
    getTableDataParams.reverse = 0
  } else {
    getTableDataParams.reverse = 1
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
  <div class="operate">
    <a-input-search
      v-model:value="searchValue"
      class="operate-search"
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
      class="ops-unstripe-table operate-table"
      :filter-config="{ remote: true }"
      :sort-config="{ remote: true, trigger: 'cell' }"
      :column-config="{ resizable: true }"
      @filter-change="handlefilterChange"
      @sort-change="handleSortChange"
    >
      <vxe-column :title="t('cmdb.ipam.operateTime')" sortable field="created_at" width="150"></vxe-column>
      <vxe-column :title="t('cmdb.ipam.operateUser')" field="uid" :filters="userFilters" width="130">
        <template #default="{ row }">
          {{ row.nickname }}
        </template>
      </vxe-column>
      <vxe-column :title="t('cmdb.ipam.operateType')" field="operate_type" :filters="operateTypeFilters" width="150">
        <template #default="{ row }">
          <div
            v-if="row.operate_type"
            class="operate-table-type"
            :style="{
              backgroundColor: OPERATE_TYPE_COLOR[row.operate_type].backgroundColor,
              color: OPERATE_TYPE_COLOR[row.operate_type].color
            }"
          >
            {{ t(OPERATE_TYPE_TEXT[row.operate_type]) }}
          </div>
        </template>
      </vxe-column>
      <vxe-column title="CIDR" field="cidr" width="150"></vxe-column>
      <vxe-column :title="t('cmdb.ipam.description')" field="description"></vxe-column>
    </vxe-table>

    <div class="operate-pagination">
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
.operate {
  width: 100%;

  &-search {
    width: 244px;
    margin-bottom: 22px;
  }

  &-table {
    &-type {
      display: inline-block;
      font-size: 12px;
      font-weight: 400;
      padding: 0 9px;
      height: 22px;
      line-height: 22px;
      border-radius: 1px;
    }
  }

  &-pagination {
    text-align: right;
    margin-top: 4px;
  }
}
</style>
