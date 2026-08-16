<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getDCIMHistoryOperate } from '@/modules/cmdb/api/dcim'
import { useUserStore } from '@/stores/user'

const props = withDefaults(
  defineProps<{
    rackId?: number
  }>(),
  {
    rackId: 0,
  }
)

const { t } = useI18n()
const userStore = useUserStore()

const page = ref(1)
const pageSize = ref(50)
const pageSizeOptions = ['50', '100', '200']
const totalNumber = ref(0)
const tableData = ref<any[]>([])
const getTableDataParams: { reverse: number } = {
  reverse: 1,
}

const deviceTypeMap: Record<number, { textColor: string; backgroundColor: string; name: string }> = {
  0: {
    textColor: '#00B42A',
    backgroundColor: '#F6FFED',
    name: 'cmdb.dcim.addDevice',
  },
  1: {
    textColor: '#FD4C6A',
    backgroundColor: '#FFECE8',
    name: 'cmdb.dcim.removeDevice',
  },
  2: {
    textColor: '#FF7D00',
    backgroundColor: '#FFECCF',
    name: 'cmdb.dcim.moveDevice',
  },
}

const windowHeight = computed(() => window.innerHeight)
const tableHeight = computed(() => `${windowHeight.value - 187}px`)
const allEmployees = computed<any[]>(() => userStore.allEmployees as any[])

onMounted(() => {
  getTableData()
})

async function getTableData() {
  const res = await getDCIMHistoryOperate({
    rack_id: props.rackId,
    count: pageSize.value,
    page: page.value,
    ...getTableDataParams,
  })

  const list = res?.result || []
  list.forEach((item: any) => {
    const ci = res?.id2ci?.[item?.ci_id] || {}
    const showKey = res?.type2show_key?.[ci?._type] || ''
    const user = allEmployees.value.find((emp: any) => item.uid === emp.acl_uid)

    item.operationUser = user?.nickname || ''
    item.deviceType = ci?.ci_type_alias || ''
    item.deviceName = ci?.[showKey] || item?.ci_id || ''
    item.deviceTypeData = deviceTypeMap?.[item?.operate_type] || {}
  })

  tableData.value = list
  totalNumber.value = res?.numfound || 0
}

function handleChangePage(newPage: number) {
  page.value = newPage
  getTableData()
}

function onShowSizeChange(_: number, newPageSize: number) {
  page.value = 1
  pageSize.value = newPageSize
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
</script>

<template>
  <div class="operation-log">
    <vxe-table
      size="small"
      show-overflow
      show-header-overflow
      highlight-hover-row
      :data="tableData"
      :height="tableHeight"
      :sort-config="{ remote: true }"
      @sort-change="handleSortChange"
    >
      <vxe-column :title="t('cmdb.dcim.operationTime')" field="created_at" sortable></vxe-column>
      <vxe-column :title="t('cmdb.dcim.operationUser')" field="operationUser"></vxe-column>
      <vxe-column :title="t('cmdb.dcim.operationType')" field="operate_type">
        <template #default="{ row }">
          <div
            class="operation-log-device-type"
            :style="{
              backgroundColor: row.deviceTypeData.backgroundColor,
              color: row.deviceTypeData.textColor,
            }"
          >
            {{ t(row.deviceTypeData.name) }}
          </div>
        </template>
      </vxe-column>
      <vxe-column :title="t('cmdb.dcim.deviceType')" field="deviceType"></vxe-column>
      <vxe-column :title="t('cmdb.dcim.deviceName')" field="deviceName"></vxe-column>
    </vxe-table>

    <div class="operation-log-pagination">
      <a-pagination
        show-size-changer
        :current="page"
        size="small"
        :total="totalNumber"
        show-quick-jumper
        :page-size="pageSize"
        :page-size-options="pageSizeOptions"
        :show-total="(total: number, range: number[]) => t('pagination.total', { range0: range[0], range1: range[1], total })"
        @change="handleChangePage"
        @show-size-change="onShowSizeChange"
      />
    </div>
  </div>
</template>

<style lang="less" scoped>
.operation-log {
  &-device-type {
    font-size: 12px;
    font-weight: 400;
    line-height: 22px;
    height: 22px;
    padding: 0 9px;
    border-radius: 1px;
    display: inline-block;
  }

  &-pagination {
    text-align: right;
    margin-top: 4px;
  }
}
</style>
