<script setup lang="ts">
import { computed, provide, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import { AppstoreOutlined, UnorderedListOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { getIPAMAddress, getIPAMHosts, postIPAMAddress, getIPAMSubnetById } from '@/modules/cmdb/api/ipam'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { ADDRESS_STATUS, STATUS_COLOR, STATUS_OPTION, STATUS_LABEL } from './constants'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { searchCI } from '@/modules/cmdb/api/ci'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import addressNullImg from '@/assets/ipam_address_null.png'

import TableIP from './tableIP.vue'
import GridIP from './gridIP.vue'
import AssignForm from './assignForm.vue'

const props = withDefaults(
  defineProps<{
    nodeData?: Record<string, any> | null
    addressCIType?: Record<string, any>
  }>(),
  {
    nodeData: null,
    addressCIType: () => ({}),
  }
)

const { t } = useI18n()

const addressRef = ref<HTMLElement | null>(null)
const tableIPRef = ref<InstanceType<typeof TableIP>>()
const assignFormRef = ref<InstanceType<typeof AssignForm>>()

const searchValue = ref('')
const ipList = ref<Record<string, any[]>>({})
const currentSelectScope = ref('')
const columns = ref<any[]>([])
const attrList = ref<any[]>([])
const attributes = ref<Record<string, any>>({})
const subnetData = ref<Record<string, any>>({})
const referenceShowAttrNameMap = ref<Record<string, string>>({})
const referenceCIIdMap = ref<Record<string, Record<string, any>>>({})
const columnWidth = ref<Record<string, number>>({})
const loading = ref(false)
const selectedIPList = ref<any[]>([])
const loadTip = ref('')

const currentStatus = ref('all')
const filterOption = [
  {
    value: 'all',
    label: 'cmdb.ipam.allStatus',
  },
  ...STATUS_OPTION,
]

const currentLayout = ref('table')
const layoutList = [
  {
    value: 'table',
    icon: UnorderedListOutlined,
  },
  {
    value: 'grid',
    icon: AppstoreOutlined,
  },
]

provide('handleSearch', getIPList)
provide('attrList', () => attrList.value)
provide('attributes', () => attributes.value)

const addressNullTip = computed(() => {
  if (props.nodeData?.isSubnet && props.nodeData?.cidr && props.nodeData?.children?.length === 0) {
    const cidrSplit = props.nodeData?.cidr?.split?.('/')
    const cidrNumber = cidrSplit[cidrSplit.length - 1]
    if (Number(cidrNumber) >= 16) {
      return ''
    } else {
      return 'cmdb.ipam.addressNullTip2'
    }
  }
  return 'cmdb.ipam.addressNullTip'
})

const addressCITypeId = computed(() => props.addressCIType?.id || null)

const filterIPList = computed(() => {
  let list = ipList.value?.[currentSelectScope.value]

  if (!list?.length) {
    return []
  }

  if (searchValue.value) {
    list = list.filter((item) => item.ip.indexOf(searchValue.value) !== -1)
  }

  if (currentStatus.value !== 'all') {
    list = list.filter((item) => item._ip_status === currentStatus.value)
  }

  return list
})

const scopeSelectOption = computed(() => {
  if (typeof ipList.value === 'object') {
    return Object.keys(ipList.value)
  }

  return []
})

const statusOption = computed(() => {
  const list = ipList.value?.[currentSelectScope.value] || []
  const statusCount: Record<string, number> = {
    [ADDRESS_STATUS.OFFLINE_ASSIGNED]: 0,
    [ADDRESS_STATUS.OFFLINE_UNASSIGNED]: 0,
    [ADDRESS_STATUS.ONLINE_ASSIGNED]: 0,
    [ADDRESS_STATUS.ONLINE_UNASSIGNED]: 0,
  }
  list.forEach((item) => {
    if (item._ip_status) {
      statusCount[item._ip_status]++
    }
  })
  return STATUS_OPTION.map((option) => ({
    ...option,
    count: statusCount[option.value],
  }))
})

watch(
  () => props.nodeData,
  (node, oldNode) => {
    if (node && node?.isSubnet && node?.cidr && node?.children?.length === 0 && node?.key !== oldNode?.key) {
      const cidrSplit = node?.cidr?.split?.('/')
      const cidrNumber = cidrSplit[cidrSplit.length - 1]

      if (Number(cidrNumber) >= 16) {
        initData()
      }
    }
  },
  { deep: true, immediate: true }
)

/** Approximate rendered width of a value (drop-in for the legacy helper's strLength). */
function strLength(fData: unknown): number {
  if (!fData) return 0
  let value = fData
  if (Array.isArray(value)) {
    value = value.join(' ')
  }
  const str = String(value)
  let intLength = 0
  for (let i = 0; i < str.length; i++) {
    if (str.charCodeAt(i) < 0 || str.charCodeAt(i) > 255) {
      intLength += 2
    } else {
      intLength += 1
    }
  }
  return Math.floor(intLength * 7)
}

async function initData() {
  loadTip.value = t('loading')
  loading.value = true
  try {
    await getColumns()
    await handleReferenceShowAttrName()
    await getIPList(true)
    calcColumnWidth()
  } catch (error) {
    console.log('initData fail', error)
  }
  loading.value = false
}

async function getColumns() {
  const getAttrRes = await getCITypeAttributesById(addressCITypeId.value as number)
  attributes.value = cloneDeep(getAttrRes)
  attrList.value = cloneDeep(getAttrRes.attributes)

  const removedNames = ['ip', 'subnet_mask', 'assign_status', 'is_used', '_updated_by', '_updated_at', 'ipam_address_id']
  const removedAttrList = getAttrRes.attributes.filter((item: any) => removedNames.includes(item.name))
  const remainingAttrList = getAttrRes.attributes.filter((item: any) => !removedNames.includes(item.name))

  const nextColumns: any[] = []
  ;['ip', 'subnet_mask'].forEach((key) => {
    const attr = removedAttrList.find((item: any) => item.name === key)
    if (attr) {
      nextColumns.push({
        field: attr.name,
        title: attr.alias || attr.name || '',
      })
    }
  })

  nextColumns.push({
    field: '_ip_status',
    title: t('status'),
  })

  remainingAttrList.forEach((attr: any) => {
    nextColumns.push({
      field: attr.name,
      title: attr.alias || attr.name || '',
      ...attr,
    })
  })
  columns.value = nextColumns
}

async function getIPList(isInit = false) {
  const hostsList = await getIPAMHosts({
    cidr: props.nodeData?.cidr,
  })

  const res = await getIPAMAddress({
    parent_id: props.nodeData?.key,
  })

  const subnetRes = await getIPAMSubnetById(props.nodeData?.key)
  subnetData.value = subnetRes

  const addressMap: Record<string, any> = {}
  if (res?.result?.length) {
    res.result.forEach((item: any) => {
      addressMap[item.ip] = item
    })
  }

  const nextIpList: Record<string, any[]> = {}
  let firstScope = ''

  hostsList.forEach((ip: string) => {
    let colData: Record<string, any> = {
      ip,
      _ip_status: ADDRESS_STATUS.OFFLINE_UNASSIGNED,
    }
    if (addressMap[ip]) {
      const data = addressMap[ip]
      const assigned = data.assign_status === 0 || data.assign_status === 2

      if (data.is_used) {
        colData._ip_status = assigned ? ADDRESS_STATUS.ONLINE_ASSIGNED : ADDRESS_STATUS.ONLINE_UNASSIGNED
      } else if (assigned) {
        colData._ip_status = ADDRESS_STATUS.OFFLINE_ASSIGNED
      }

      colData = {
        ...colData,
        ...data,
      }
    }

    const itemData = {
      ...colData,
      subnet_mask: colData?.subnet_mask ?? subnetRes?.subnet_mask ?? undefined,
      gateway: colData?.gateway ?? subnetRes?.gateway ?? undefined,
    }

    const key = ip.split(/\.(?=[^.]*$)/)?.[0]
    if (nextIpList[key]) {
      nextIpList[key].push(itemData)
    } else {
      if (!firstScope) {
        firstScope = key
      }
      nextIpList[key] = [itemData]
    }
  })
  ipList.value = nextIpList
  if (isInit) {
    currentSelectScope.value = firstScope
  }
  handleReferenceCIIdMap()
}

async function handleReferenceShowAttrName() {
  const needRequiredCITypeIds =
    columns.value?.filter((col) => col?.is_reference && col?.reference_type_id).map((col) => col.reference_type_id) || []
  if (!needRequiredCITypeIds.length) {
    referenceShowAttrNameMap.value = {}
    return
  }

  const res = await getCITypes({
    type_ids: needRequiredCITypeIds.join(','),
  })

  const map: Record<string, string> = {}
  res.ci_types.forEach((ciType: any) => {
    map[ciType.id] = ciType?.show_name || ciType?.unique_name || ''
  })

  referenceShowAttrNameMap.value = map
}

async function handleReferenceCIIdMap() {
  const referenceTypeCol = columns.value.filter((col) => col?.is_reference && col?.reference_type_id) || []
  if (!ipList.value?.[currentSelectScope.value]?.length || !referenceTypeCol?.length) {
    referenceCIIdMap.value = {}
    return
  }

  const map: Record<string, Record<string, any>> = {}
  ipList.value[currentSelectScope.value].forEach((row) => {
    referenceTypeCol.forEach((col) => {
      const ids = Array.isArray(row[col.field]) ? row[col.field] : row[col.field] ? [row[col.field]] : []
      if (ids.length) {
        if (!map?.[col.reference_type_id]) {
          map[col.reference_type_id] = {}
        }
        ids.forEach((id: any) => {
          map[col.reference_type_id][id] = {}
        })
      }
    })
  })

  if (!Object.keys(map).length) {
    referenceCIIdMap.value = {}
    return
  }

  const allRes = await Promise.all(
    Object.keys(map).map((key) => {
      return searchCI({
        q: `_type:${key},_id:(${Object.keys(map[key]).join(';')})`,
        count: 9999,
      })
    })
  )

  allRes.forEach((res: any) => {
    res.result.forEach((item: any) => {
      if (map?.[item._type]?.[item._id]) {
        map[item._type][item._id] = item
      }
    })
  })

  referenceCIIdMap.value = map
}

function calcColumnWidth() {
  const nextColumnWidth: Record<string, number> = {}
  columns.value.forEach((col) => {
    const list = ipList.value[currentSelectScope.value] || []
    nextColumnWidth[col.field] = Math.min(Math.max(100, ...list.map((item) => strLength(item[col.field]))), 350)
  })

  const wrapWidth = addressRef.value?.clientWidth ?? 0
  const totalWidth = Object.values(nextColumnWidth).reduce((acc, cur) => acc + cur, 0)

  if (totalWidth < wrapWidth) {
    columnWidth.value = {
      ip: 130,
    }
  } else {
    columnWidth.value = {
      ...nextColumnWidth,
      ip: 130,
    }
  }
}

/** Escape a value for CSV output. */
function csvEscape(value: unknown): string {
  const str = value === null || value === undefined ? '' : String(value)
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

/** Generate and download a CSV file (ExcelJS is unavailable in the Vue 3 shell). */
function downloadCSV(filename: string, cols: { field: string; title: string }[], rows: Record<string, any>[]) {
  const header = cols.map((col) => csvEscape(col.title)).join(',')
  const body = rows.map((row) => cols.map((col) => csvEscape(row[col.field])).join(',')).join('\n')
  const content = `\uFEFF${header}\n${body}`
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function handleExport() {
  let tableData: any[] = []
  if (currentLayout.value === 'table') {
    tableData = tableIPRef.value?.getCheckedTableData() || []
    selectedIPList.value = []
  } else {
    tableData = filterIPList.value
  }

  if (!tableData.length) {
    return
  }

  const exportColumns = columns.value.map((col) => ({
    field: col.field,
    title: col.title,
  }))

  const rows = tableData.map((data) => {
    const row: Record<string, any> = {}
    exportColumns.forEach(({ field }) => {
      let value = data?.[field] ?? null
      if (field === '_ip_status') {
        const text = STATUS_LABEL?.[data?.[field]]
        value = text ? t(text) : null
      }
      row[field] = value
    })
    return row
  })

  const fileName = `cmdb-${t('cmdb.ipam.addressAssign')}-${dayjs().format('YYYYMMDDHHmmss')}.csv`
  downloadCSV(fileName, exportColumns, rows)
}

function openAssign(data: any) {
  assignFormRef.value?.open({
    nodeId: props.nodeData?._id,
    ipData: cloneDeep(data),
  })
}

function handleRecycle(ip: string) {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ipam.recycleTip'),
    onOk: () => {
      postIPAMAddress({
        ips: [ip],
        parent_id: props.nodeData?._id,
        assign_status: 1,
      }).then(() => {
        message.success(t('cmdb.ipam.recycleSuccess', { ip }))
        getIPList()
      })
    },
  })
}

function handleChangeLayout(value: string) {
  if (currentLayout.value !== value) {
    if (value === 'grid') {
      selectedIPList.value = []
    }
    currentLayout.value = value
  }
}

function handleTableSelectChange(ips: any[]) {
  selectedIPList.value = ips
}

function clickBatchAssign() {
  assignFormRef.value?.open({
    nodeId: props.nodeData?._id,
    ipData: {
      subnet_mask: subnetData.value?.subnet_mask ?? undefined,
      gateway: subnetData.value?.gateway ?? undefined,
    },
    ipList: selectedIPList.value,
  })
}

async function batchAssign({ paramsList, ipList: batchIpList }: { paramsList: any[]; ipList: any[] }) {
  let successNum = 0
  let errorNum = 0

  try {
    loading.value = true

    loadTip.value = t('cmdb.ipam.batchAssignInProgress', {
      total: batchIpList.length,
      successNum,
      errorNum,
    })

    for (const params of paramsList) {
      const ipCount = params?.ips?.length ?? 0
      try {
        await postIPAMAddress(params)
        successNum += ipCount
      } catch {
        errorNum += ipCount
      }
      loadTip.value = t('cmdb.ipam.batchAssignInProgress', {
        total: batchIpList.length,
        successNum,
        errorNum,
      })
    }

    if (tableIPRef.value) {
      tableIPRef.value.clearCheckbox()
      selectedIPList.value = []
    }
    message.success(t('cmdb.ipam.batchAssignCompleted'))
    loading.value = false
    getIPList()
  } catch (error) {
    console.log('error', error)
  }
}

function clickBatchRecycle() {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ipam.recycleTip'),
    onOk: () => {
      handleBatchRecycle()
    },
  })
}

async function handleBatchRecycle() {
  let successNum = 0
  let errorNum = 0

  try {
    loading.value = true

    loadTip.value = t('cmdb.ipam.batchRecycleInProgress', {
      total: selectedIPList.value.length,
      successNum,
      errorNum,
    })

    const ipChunk: string[][] = []
    for (let i = 0; i < selectedIPList.value.length; i += 5) {
      ipChunk.push(selectedIPList.value.slice(i, i + 5))
    }

    for (const ips of ipChunk) {
      const ipCount = ips.length
      try {
        await postIPAMAddress({
          ips,
          parent_id: props.nodeData?._id,
          assign_status: 1,
        })
        successNum += ipCount
      } catch {
        errorNum += ipCount
      }
      loadTip.value = t('cmdb.ipam.batchRecycleInProgress', {
        total: selectedIPList.value.length,
        successNum,
        errorNum,
      })
    }

    if (tableIPRef.value) {
      tableIPRef.value.clearCheckbox()
      selectedIPList.value = []
    }
    message.success(t('cmdb.ipam.batchRecycleCompleted'))
    loading.value = false
    getIPList()
  } catch (error) {
    console.log('error', error)
  }
}
</script>

<template>
  <div ref="addressRef" class="address">
    <div v-if="addressNullTip" class="address-null">
      <img class="address-null-img" :src="addressNullImg" />
      <div class="address-null-tip">{{ t('noData') }}</div>
      <div class="address-null-tip2">{{ t(addressNullTip) }}</div>
    </div>

    <a-spin v-else :tip="loadTip" :spinning="loading">
      <div class="address-header">
        <div class="address-header-left">
          <a-input-search
            v-model:value="searchValue"
            :placeholder="t('placeholderSearch')"
            class="address-header-search"
          />

          <a-select v-model:value="currentStatus" class="address-header-filter">
            <a-select-option
              v-for="item in filterOption"
              :key="item.value"
              :value="item.value"
            >
              {{ t(item.label) }}
            </a-select-option>
          </a-select>

          <a-select
            v-if="scopeSelectOption.length > 1"
            v-model:value="currentSelectScope"
            class="address-header-filter"
            show-search
          >
            <a-select-option
              v-for="key in scopeSelectOption"
              :key="key"
              :value="key"
            >
              {{ key }}
            </a-select-option>
          </a-select>

          <div v-if="selectedIPList.length" class="ops-list-batch-action">
            <span @click="clickBatchAssign">{{ t('cmdb.ipam.batchAssign') }}</span>
            <a-divider type="vertical" />
            <span @click="clickBatchRecycle">{{ t('cmdb.ipam.batchRecycle') }}</span>
            <a-divider type="vertical" />
            <span @click="handleExport">{{ t('export') }}</span>
            <span>{{ t('cmdb.ci.selectRows', { rows: selectedIPList.length }) }}</span>
          </div>

          <div
            v-if="currentLayout === 'grid'"
            class="address-header-status"
          >
            <div
              v-for="item in statusOption"
              :key="item.value"
              class="address-header-status-item"
            >
              <div
                class="address-header-status-dot"
                :style="{
                  backgroundColor: `${STATUS_COLOR[item.value]}22`
                }"
              >
                <div
                  class="address-header-status-dot-content"
                  :style="{
                    backgroundColor: STATUS_COLOR[item.value]
                  }"
                ></div>
              </div>
              <div class="address-header-status-text">
                {{ t(item.label) }}: {{ item.count }}
              </div>
            </div>
          </div>
        </div>

        <div class="address-header-right">
          <div class="address-header-layout">
            <div
              v-for="item in layoutList"
              :key="item.value"
              :class="['address-header-layout-item', currentLayout === item.value ? 'address-header-layout-item-active' : '']"
              @click="handleChangeLayout(item.value)"
            >
              <component :is="item.icon" />
            </div>
          </div>
        </div>
      </div>

      <div class="address-main">
        <TableIP
          v-if="currentLayout === 'table'"
          ref="tableIPRef"
          :columns="columns"
          :all-table-data="filterIPList"
          :reference-show-attr-name-map="referenceShowAttrNameMap"
          :reference-c-i-id-map="referenceCIIdMap"
          :column-width="columnWidth"
          :address-c-i-type-id="addressCITypeId"
          @open-assign="openAssign"
          @recycle="handleRecycle"
          @select-change="handleTableSelectChange"
        />

        <GridIP
          v-if="currentLayout === 'grid'"
          :ip-list="filterIPList"
          :columns="columns"
          :reference-show-attr-name-map="referenceShowAttrNameMap"
          :reference-c-i-id-map="referenceCIIdMap"
          @open-assign="openAssign"
          @recycle="handleRecycle"
        />
      </div>
    </a-spin>

    <AssignForm
      ref="assignFormRef"
      :attr-list="attrList"
      @ok="getIPList"
      @batch-assign="batchAssign"
    />
  </div>
</template>

<style lang="less" scoped>
.address {
  width: 100%;
  height: fit-content;

  &-header {
    width: 100%;
    display: flex;
    align-items: baseline;
    justify-content: space-between;

    &-left {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      row-gap: 12px;
    }

    &-search {
      height: 32px;
      width: 246px;
      flex-shrink: 0;
      margin-right: 16px;
    }

    &-filter {
      width: 150px;
      margin-right: 16px;
      flex-shrink: 0;
    }

    &-status {
      display: flex;
      align-items: center;
      flex-shrink: 0;
      column-gap: 20px;

      &-item {
        display: flex;
        align-items: center;
      }

      &-dot {
        width: 12px;
        height: 12px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;

        &-content {
          width: 6px;
          height: 6px;
          border-radius: 6px;
        }
      }

      &-text {
        margin-left: 4px;
        font-size: 14px;
        font-weight: 400;
        color: #4e5969;
      }
    }

    &-right {
      display: flex;
      align-items: center;
      flex-shrink: 0;
      column-gap: 24px;
    }

    &-layout {
      display: flex;
      align-items: center;
      height: 32px;
      border: solid 1px #e4e7ed;

      &-item {
        height: 100%;
        width: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        cursor: pointer;

        &:not(:last-child) {
          border-right: solid 1px #e4e7ed;
        }

        &-active {
          color: #2f54eb;
          background-color: #f0f5ff;
        }

        &:hover {
          color: #2f54eb;
        }
      }
    }
  }

  &-main {
    margin-top: 22px;
  }

  &-null {
    width: 100%;
    padding-top: 130px;
    text-align: center;

    &-img {
      height: 200px;
    }

    &-tip {
      font-size: 14px;
      font-weight: 400;
      color: #86909c;
    }

    &-tip2 {
      font-size: 14px;
      font-weight: 400;
      color: #2f54eb;
    }
  }
}

.ops-list-batch-action {
  display: flex;
  align-items: center;
  gap: 4px;

  span {
    cursor: pointer;
    color: @primary-color;
  }
}
</style>
