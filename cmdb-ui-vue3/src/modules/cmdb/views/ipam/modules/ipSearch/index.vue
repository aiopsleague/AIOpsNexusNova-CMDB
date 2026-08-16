<script setup lang="ts">
import { computed, nextTick, onMounted, provide, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal, notification } from 'ant-design-vue'
import { SettingOutlined } from '@ant-design/icons-vue'
import { searchCI, deleteCI as deleteCIById, updateCI } from '@/modules/cmdb/api/ci'
import { getSubscribeAttributes } from '@/modules/cmdb/api/preference'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { cloneDeep, getCITableColumns } from '@/modules/cmdb/utils/helper'
import SearchForm from '@/modules/cmdb/components/searchForm/SearchForm.vue'
import CITable from '@/modules/cmdb/components/ciTable/index.vue'
import BatchDownload from '@/modules/cmdb/components/batchDownload/batchDownload.vue'
import CIDetailDrawer from '@/modules/cmdb/views/ci/modules/ciDetailDrawer.vue'
import EditAttrsPopover from '@/modules/cmdb/views/ci/modules/editAttrsPopover.vue'
import CreateInstanceForm from '@/modules/cmdb/views/ci/modules/CreateInstanceForm.vue'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    addressCIType?: Record<string, any>
  }>(),
  {
    addressCIType: () => ({}),
  }
)

const wrapRef = ref<HTMLElement | null>(null)
const searchRef = ref<any>()
const xTableRef = ref<InstanceType<typeof CITable>>()
const batchDownloadRef = ref<InstanceType<typeof BatchDownload>>()
const detailRef = ref<InstanceType<typeof CIDetailDrawer>>()
const createRef = ref<InstanceType<typeof CreateInstanceForm>>()

const page = ref(1)
const pageSize = ref(50)
const pageSizeOptions = ref(['50', '100', '200'])
const loading = ref(false)
const loadTip = ref('')
const sortByTable = ref<string | undefined>(undefined)

const instanceList = ref<any[]>([])
const totalNumber = ref(0)
const columns = ref<any[]>([])
const preferenceAttrList = ref<any[]>([])
const attrList = ref<any[]>([])
const attributes = ref<Record<string, any>>({})
const selectedRowKeys = ref<any[]>([])

const addressCITypeId = computed(() => props.addressCIType?.id || null)

const tableHeight = computed(() => window.innerHeight - 260)

provide('handleSearch', getTableData)
provide('attrList', () => attrList.value)
provide('attributes', () => attributes.value)

function getTableRef(): any {
  return xTableRef.value?.getVxetableRef() || null
}

async function getAttributeList() {
  await getCITypeAttributesById(addressCITypeId.value as number).then((res) => {
    attrList.value = res.attributes
    attributes.value = res
  })
}

async function getPreferenceAttrList() {
  const subscribed = await getSubscribeAttributes(addressCITypeId.value as number)
  preferenceAttrList.value = subscribed.attributes
}

async function getTableData() {
  try {
    loading.value = true
    const fuzzySearch = searchRef.value?.fuzzySearch
    const expression = searchRef.value?.expression || ''
    const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
    const regSort = /(?<=sort=).+/g
    const exp = expression.match(regQ) ? expression.match(regQ)[0] : null

    let sort
    if (sortByTable.value) {
      sort = sortByTable.value
    } else {
      sort = expression.match(regSort) ? expression.match(regSort)[0] : undefined
    }

    const res = await searchCI({
      q: `_type:${addressCITypeId.value}${exp ? `,${exp}` : ''}${fuzzySearch ? `,*${fuzzySearch}*` : ''}`,
      count: pageSize.value,
      page: page.value,
      sort,
    })

    totalNumber.value = res?.numfound
    const list = res.result

    const jsonAttrList = preferenceAttrList.value.filter((attr) => attr.value_type === '6')
    list.forEach((item: any) => {
      jsonAttrList.forEach(
        (jsonAttr: any) => (item[jsonAttr.name] = item[jsonAttr.name] ? JSON.stringify(item[jsonAttr.name]) : '')
      )
    })

    getColumns(list)
    instanceList.value = list
  } finally {
    loading.value = false
  }
}

function getColumns(data: any[]) {
  const width = (wrapRef.value?.clientWidth ?? 0) - 50
  const cols = getCITableColumns(data, preferenceAttrList.value, width)
  cols.forEach((item: any) => {
    if (item.editRender) {
      item.editRender.enabled = false
    }
  })
  columns.value = cols
}

function copyExpression() {
  const expression = searchRef.value?.expression || ''
  const fuzzySearch = searchRef.value?.fuzzySearch

  const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
  const exp = expression.match(regQ) ? expression.match(regQ)[0] : null
  const text = `q=_type:${addressCITypeId.value}${exp ? `,${exp}` : ''}${fuzzySearch ? `,*${fuzzySearch}*` : ''}`
  navigator.clipboard
    .writeText(text)
    .then(() => {
      message.success(t('copySuccess'))
    })
    .catch(() => {
      message.error(t('cmdb.ci.copyFailed'))
    })
}

function handleSearch() {
  getTableRef()?.clearSort()
  sortByTable.value = undefined
  nextTick(() => {
    page.value = 1
    getTableData()
  })
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

function handleSortCol({ property, order }: { property: string; order: string }) {
  let sort
  if (order === 'asc') {
    sort = property
  } else if (order === 'desc') {
    sort = `-${property}`
  }

  sortByTable.value = sort
  nextTick(() => {
    page.value = 1
    getTableData()
  })
}

function openBatchDownload() {
  batchDownloadRef.value?.open({
    preferenceAttrList: preferenceAttrList.value,
    ciTypeName: t('cmdb.ipam.ipSearch') || '',
  })
}

function batchDownload({ checkedKeys, filename, type }: any) {
  const tableRef = getTableRef()

  const jsonAttrList: string[] = []
  checkedKeys.forEach((key: string) => {
    const attr = attrList.value.find((item) => item.name === key)
    if (attr && attr.value_type === '6') jsonAttrList.push(key)
  })

  const data = cloneDeep([
    ...(tableRef?.getCheckboxReserveRecords() || []),
    ...(tableRef?.getCheckboxRecords(true) || []),
  ])
  if (!data.length) {
    const { fullData } = tableRef?.getTableData() || {}
    if (fullData) {
      data.push(...cloneDeep(fullData))
    }
  }

  tableRef?.exportData({
    filename,
    type,
    columnFilterMethod({ column }: any) {
      return checkedKeys.includes(column.property)
    },
    data: data.map((item: any) => {
      jsonAttrList.forEach((jsonAttr) => (item[jsonAttr] = item[jsonAttr] ? JSON.stringify(item[jsonAttr]) : item[jsonAttr]))
      return { ...item }
    }),
  })

  selectedRowKeys.value = []
  tableRef?.clearCheckboxRow()
  tableRef?.clearCheckboxReserve()
}

function openDetail(id: any, activeTabKey?: string, ciDetailRelationKey?: string) {
  void ciDetailRelationKey
  detailRef.value?.create(id, activeTabKey)
}

async function refreshAfterEditAttrs() {
  await getPreferenceAttrList()
  getTableData()
}

function deleteCI(record: any) {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete'),
    onOk() {
      deleteCIById(record.ci_id || record._id).then(() => {
        message.success(t('deleteSuccess'))
        getTableData()
      })
    },
  })
}

function onSelectChange(records: any[]) {
  selectedRowKeys.value = records.map((i) => i.ci_id || i._id)
}

function batchDelete() {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete'),
    onOk() {
      batchDeleteAsync()
    },
  })
}

async function batchDeleteAsync() {
  let successNum = 0
  let errorNum = 0
  loading.value = true
  loadTip.value = t('cmdb.ci.batchDeleting')

  const floor = Math.ceil(selectedRowKeys.value.length / 6)
  for (let i = 0; i < floor; i++) {
    const itemList = selectedRowKeys.value.slice(6 * i, 6 * i + 6)
    const promises = itemList.map((x) => deleteCIById(x, false))
    await Promise.allSettled(promises)
      .then((res) => {
        res.forEach((r) => {
          if (r.status === 'fulfilled') {
            successNum += 1
          } else {
            errorNum += 1
          }
        })
      })
      .finally(() => {
        loadTip.value = t('cmdb.ci.batchDeleting2', {
          total: selectedRowKeys.value.length,
          successNum,
          errorNum,
        })
      })
  }

  loading.value = false
  loadTip.value = ''
  selectedRowKeys.value = []
  getTableRef()?.clearCheckboxRow()
  getTableRef()?.clearCheckboxReserve()
  nextTick(() => {
    page.value = 1
    getTableData()
  })
}

function batchUpdate(values: Record<string, any>) {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ci.batchUpdateConfirm'),
    onOk() {
      batchUpdateAsync(values)
    },
  })
}

async function batchUpdateAsync(values: Record<string, any>) {
  let successNum = 0
  let errorNum = 0
  loading.value = true
  loadTip.value = t('cmdb.ci.batchUpdateInProgress') + '...'

  const payload: Record<string, any> = {}
  Object.keys(values).forEach((key) => {
    if (values[key] === undefined || values[key] === null) {
      payload[key] = null
    } else {
      payload[key] = values[key]
    }
  })
  createRef.value?.handleClose()
  const key = 'updatable'
  let errorMsg = ''

  for (let i = 0; i < selectedRowKeys.value.length; i++) {
    await updateCI(selectedRowKeys.value[i], payload, false)
      .then(() => {
        successNum += 1
      })
      .catch((error) => {
        errorMsg = errorMsg + '\n' + `${selectedRowKeys.value[i]}:${error.response?.data?.message ?? ''}`
        notification.warning({
          key,
          message: t('warning'),
          description: errorMsg,
          duration: 0,
          style: { whiteSpace: 'break-spaces', overflow: 'auto', maxHeight: window.innerHeight - 80 + 'px' },
        })
        errorNum += 1
      })
      .finally(() => {
        loadTip.value = t('cmdb.ci.batchUpdateInProgress2', {
          total: selectedRowKeys.value.length,
          successNum,
          errorNum,
        })
      })
  }
  loading.value = false
  loadTip.value = ''
  selectedRowKeys.value = []
  getTableRef()?.clearCheckboxRow()
  getTableRef()?.clearCheckboxReserve()
  getTableData()
}

onMounted(async () => {
  if (addressCITypeId.value) {
    await getAttributeList()
    await getPreferenceAttrList()
    getTableData()
  }
})

defineExpose({ getTableData })
</script>

<template>
  <div ref="wrapRef">
    <a-spin :tip="loadTip" :spinning="loading">
      <div class="table-header">
        <SearchForm
          ref="searchRef"
          :preference-attr-list="preferenceAttrList"
          :type-id="addressCITypeId"
          :selected-row-keys="selectedRowKeys"
          @copy-expression="copyExpression"
          @refresh="handleSearch"
        >
          <div v-show="!!selectedRowKeys.length" class="ops-list-batch-action">
            <span @click="createRef?.handleOpen(true, 'update')">{{ t('update') }}</span>
            <a-divider type="vertical" />
            <span @click="openBatchDownload">{{ t('download') }}</span>
            <a-divider type="vertical" />
            <span @click="batchDelete">{{ t('delete') }}</span>
            <span>{{ t('cmdb.ci.selectRows', { rows: selectedRowKeys.length }) }}</span>
          </div>
        </SearchForm>

        <div class="table-header-right">
          <EditAttrsPopover
            :type-id="addressCITypeId"
            @refresh="refreshAfterEditAttrs"
          >
            <a-button
              type="primary"
              ghost
              class="ops-button-ghost"
            >
              <SettingOutlined />
              {{ t('cmdb.configTable') }}
            </a-button>
          </EditAttrsPopover>
        </div>
      </div>

      <CITable
        ref="xTableRef"
        :loading="loading"
        :attr-list="preferenceAttrList"
        :columns="columns"
        :data="instanceList"
        :height="tableHeight"
        @sort-change="handleSortCol"
        @open-detail="openDetail"
        @delete-c-i="deleteCI"
        @on-select-change="onSelectChange"
      />

      <div class="table-pagination">
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
    </a-spin>

    <BatchDownload
      ref="batchDownloadRef"
      :show-file-type-select="false"
      @batch-download="batchDownload"
    />

    <CIDetailDrawer ref="detailRef" :type-id="addressCITypeId" />

    <CreateInstanceForm
      ref="createRef"
      :type-id-from-prop="addressCITypeId"
      @submit="batchUpdate"
    />
  </div>
</template>

<style lang="less" scoped>
.table-header {
  display: flex;
  align-items: baseline;
  width: 100%;
  justify-content: space-between;

  &-right {
    display: flex;
    align-items: center;
    column-gap: 12px;
  }
}

.ops-list-batch-action {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;

  span {
    cursor: pointer;
    color: @primary-color;
  }
}

.table-pagination {
  text-align: right;
  margin-top: 4px;
}
</style>
