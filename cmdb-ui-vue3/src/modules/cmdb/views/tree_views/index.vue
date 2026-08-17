<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, provide, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal, notification } from 'ant-design-vue'
import {
  PlusOutlined,
  InfoCircleOutlined,
  StarFilled,
  SettingOutlined,
  HolderOutlined,
} from '@ant-design/icons-vue'
import { cloneDeep, getCITableColumns } from '@/modules/cmdb/utils/helper'
import {
  getSubscribeTreeView,
  getSubscribeAttributes,
  subscribeTreeView,
  preferenceCitypeOrder,
} from '@/modules/cmdb/api/preference'
import { searchCI, updateCI, deleteCI } from '@/modules/cmdb/api/ci'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { getCITypeAttributesById, getAttrPassword } from '@/modules/cmdb/api/CITypeAttr'
import SearchForm from '@/modules/cmdb/components/searchForm/SearchForm.vue'
import SubscribeSetting from '@/modules/cmdb/components/subscribeSetting/subscribeSetting.vue'
import SplitPane from '@/components/SplitPane/SplitPane.vue'
import TreeViewsNode from './modules/treeViewsNode.vue'
import EditAttrsPopover from '@/modules/cmdb/views/ci/modules/editAttrsPopover.vue'
import CiDetailDrawer from '@/modules/cmdb/views/ci/modules/ciDetailDrawer.vue'
import CreateInstanceForm from '@/modules/cmdb/views/ci/modules/CreateInstanceForm.vue'
import CITable from '@/modules/cmdb/components/ciTable/index.vue'
import BatchDownload from '@/modules/cmdb/components/batchDownload/batchDownload.vue'
import PreferenceSearch from '@/modules/cmdb/components/preferenceSearch/preferenceSearch.vue'
import MetadataDrawer from '@/modules/cmdb/views/ci/modules/MetadataDrawer.vue'
import draggable from 'vuedraggable'
import Sortable from 'sortablejs'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const keySplit = '---'

// Child component refs.
const xTableRef = ref<InstanceType<typeof CITable>>()
const searchRef = ref<any>()
const preferenceSearchRef = ref<any>()
const subscribeSettingRef = ref<InstanceType<typeof SubscribeSetting>>()
const detailRef = ref<InstanceType<typeof CiDetailDrawer>>()
const createRef = ref<InstanceType<typeof CreateInstanceForm>>()
const batchDownloadRef = ref<InstanceType<typeof BatchDownload>>()
const metadataDrawerRef = ref<InstanceType<typeof MetadataDrawer>>()

const treeData = ref<any[]>([])
const treeNode = ref<any>(null)
const treeKeys = ref<string[]>([])
const subscribeTreeViewCiTypes = ref<any[]>([])
const subscribeTreeViewCiTypesLoading = ref(false)
const levels = ref<any[]>([])
const typeId = ref<number | null>(null)
const instanceList = ref<any[]>([])
const columns = ref<any[]>([])
const loading = ref(false)
const loadTip = ref('')
const pageSizeOptions = ref(['50', '100', '200', '100000'])
const pageSize = ref(50)
const currentPage = ref(1)
const totalNumber = ref(0)
const currentAttrList = ref<any[]>([])
const newLoad = ref(true)
const sortByTable = ref<string | undefined>(undefined)
const paneLengthPixel = ref(205)
const expandedKeys = ref<string[]>([])
const attrList = ref<any[]>([])
const attributes = ref<Record<string, any>>({})
const selectedRowKeys = ref<any[]>([])
const initialInstanceList = ref<any[]>([])
const citypes = ref<any[]>([])
const isSetDataNodes = ref<any[]>([])
const initialPasswordValue = ref<Record<string, any>>({})
const passwordValue = ref<Record<string, any>>({})
const lastEditCiId = ref<string | number | null>(null)
const isContinueCloseEdit = ref(true)
const sortable = ref<any>(null)
const tableDragClassName = ref<string[]>([])

const windowHeight = computed(() => window.innerHeight)
const tableHeight = computed(() => windowHeight.value - 240)

const selectedKeys = computed(() => {
  if (treeKeys.value.length <= 1) {
    return treeKeys.value.map((item) => `${keySplit}${item}`)
  }
  return [treeKeys.value.join(keySplit)]
})

const treeViewsLevels = computed(() => {
  const _find = subscribeTreeViewCiTypes.value.find((item) => item.type_id === Number(typeId.value))
  return _find?.levels || []
})

const treeViewId = computed(() => {
  const _find = subscribeTreeViewCiTypes.value.find((item) => item.type_id === Number(typeId.value))
  return _find?.id
})

const currentCiTypeName = computed(() => {
  const _find = citypes.value.find((item) => Number(item.id) === Number(typeId.value))
  return _find?.alias || _find?.name || ''
})

provide('handleSearch', handleLoadInstance)
provide('setPreferenceSearchCurrent', setPreferenceSearchCurrent)
provide('attrList', () => attrList.value)
provide('attributes', () => attributes.value)
provide('filterCompPreferenceSearch', () => ({ ptv_id: treeViewId.value }))

function getXTable(): any {
  return xTableRef.value?.getVxetableRef() || null
}

async function getAttributeList() {
  const res = await getCITypeAttributesById(Number(typeId.value))
  attrList.value = res.attributes
  attributes.value = res
}

async function getTreeViews() {
  subscribeTreeViewCiTypesLoading.value = true
  const res = await getSubscribeTreeView()
  subscribeTreeViewCiTypesLoading.value = false
  subscribeTreeViewCiTypes.value = res
  if (subscribeTreeViewCiTypes.value.length) {
    typeId.value = (route.params.typeId as any) || subscribeTreeViewCiTypes.value[0].type_id
    selectedRowKeys.value = []
    getXTable()?.clearCheckboxRow()
    getXTable()?.clearCheckboxReserve()
    levels.value = res.find((item: any) => item.type_id.toString() === typeId.value?.toString()).levels
    await initPage()
  }
}

async function initPage() {
  treeNode.value = null
  treeKeys.value = []
  levels.value = []
  currentPage.value = 1
  totalNumber.value = 0
  instanceList.value = []
  selectedRowKeys.value = []
  expandedKeys.value = []
  getXTable()?.clearCheckboxRow()
  getXTable()?.clearCheckboxReserve()
  await loadCurrentView()
  await getAttributeList()
  await loadAttrList()
  await handleLoadInstance()
}

async function loadCurrentView() {
  if (subscribeTreeViewCiTypes.value.length) {
    typeId.value = (route.params.typeId as any) || subscribeTreeViewCiTypes.value[0].type_id
    selectedRowKeys.value = []
    getXTable()?.clearCheckboxRow()
    getXTable()?.clearCheckboxReserve()
    levels.value = subscribeTreeViewCiTypes.value.find(
      (item: any) => item.type_id.toString() === typeId.value?.toString()
    ).levels
  }
}

async function loadAttrList() {
  const res = await getSubscribeAttributes(typeId.value as number)
  currentAttrList.value = res.attributes
}

async function handleLoadInstance(params: { sortByTable?: string } = {}) {
  loading.value = true
  let q = `_type:${typeId.value}`

  if (treeKeys.value.length > 0) {
    treeKeys.value.forEach((item, idx) => {
      q += `,${levels.value[idx].name}:${item}`
    })
  }

  const expression = searchRef.value ? searchRef.value.expression || '' : ''

  const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
  const regSort = /(?<=sort=).+/g
  const exp = expression.match(regQ) ? expression.match(regQ)[0] : null
  if (exp) {
    q = `${q},${exp}`
  }
  const fuzzySearch = searchRef.value?.fuzzySearch
  if (fuzzySearch) {
    q = `${q},*${fuzzySearch}*`
  }
  const payload: Record<string, any> = { q }

  let sort
  const { sortByTable } = params
  if (sortByTable) {
    sort = sortByTable
  } else {
    sort = expression.match(regSort) ? expression.match(regSort)[0] : undefined
  }
  payload.sort = sort

  if (levels.value.length > treeKeys.value.length) {
    payload['facet'] = `${levels.value[treeKeys.value.length].name}`
  }
  payload['page'] = currentPage.value
  payload['count'] = pageSize.value

  try {
    const res = await searchCI(payload)
    totalNumber.value = res.numfound

    if (Object.values(res.facet).length) {
      wrapTreeData(res.facet)
    }

    const jsonAttrList = currentAttrList.value.filter((attr) => attr.value_type === '6')
    instanceList.value = res['result'].map((item: any) => {
      jsonAttrList.forEach(
        (jsonAttr) => (item[jsonAttr.name] = item[jsonAttr.name] ? JSON.stringify(item[jsonAttr.name]) : '')
      )
      return { ...cloneDeep(item) }
    })
    initialInstanceList.value = cloneDeep(instanceList.value)
    const treeViewsRight = document.getElementById('tree-views-right')
    if (treeViewsRight) {
      const width = treeViewsRight.clientWidth - 50
      columns.value = getCITableColumns(res.result, currentAttrList.value, width)
      columns.value.forEach((col) => {
        if (col.is_password) {
          initialPasswordValue.value[col.field] = ''
          passwordValue.value[col.field] = ''
        }
      })
    }
  } catch (e) {
    console.log(e)
    message.error(e as any)
  } finally {
    loading.value = false
    nextTick(() => {
      if (xTableRef.value) {
        xTableRef.value.getVxetableRef().refreshColumn()
      }
    })
  }
  newLoad.value = false
}

function wrapTreeData(facet: any) {
  const _treeData = (Object.values(facet)[0] as any[]).map((item: any) => {
    let title = item[0]
    const attr = attrList.value.find((attr: any) => attr.name === item[2])
    if (attr?.choice_value?.length) {
      const choice = attr.choice_value.find((choice: any) => item[0] === choice?.[0])
      if (choice?.[1]?.label) {
        title = choice[1].label
      }
    }

    return {
      title: title,
      childLength: item[1],
      key: treeKeys.value.join(keySplit) + keySplit + item[0],
      isLeaf: levels.value.length - 1 === treeKeys.value.length,
    }
  })
  if (treeNode.value === null && newLoad.value) {
    treeData.value = _treeData
    treeNode.value = { dataRef: {} }
  } else {
    if (!isSetDataNodes.value.includes(treeNode.value.dataRef.key)) {
      treeNode.value.dataRef.children = _treeData
      treeData.value = [...treeData.value]
      isSetDataNodes.value.push(treeNode.value.dataRef.key)
    }
  }
}

function onLoadData(treeNodeParam: any) {
  return new Promise((resolve) => {
    if (treeNodeParam.dataRef.children) {
      resolve(undefined)
      return
    }
    treeKeys.value = treeNodeParam.eventKey.split(keySplit).filter((item: string) => item !== '')
    treeNode.value = treeNodeParam
    selectedRowKeys.value = []
    getXTable()?.clearCheckboxRow()
    getXTable()?.clearCheckboxReserve()
    resolve(undefined)
  })
}

function handleChangeCi(value: number) {
  if (value && Number(typeId.value) !== Number(value)) {
    treeData.value = []
    router.push({
      name: 'cmdb_tree_views_item',
      params: { typeId: Number(value) },
    })
    typeId.value = Number(value)
  } else {
    typeId.value = null
    nextTick(() => {
      typeId.value = Number(value)
      newLoad.value = true
      initPage()
    })
  }
  isSetDataNodes.value = []
}

function reloadData() {
  currentPage.value = 1
  sortByTable.value = undefined
  const xTable = getXTable()
  if (xTable) {
    xTable.clearSort().then(() => {
      handleLoadInstance()
    })
  } else {
    handleLoadInstance()
  }
}

async function reload() {
  await getTreeViews()
}

function cancelSubscribe(e: Event, ciType: any) {
  e.stopPropagation()
  e.preventDefault()
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.preference.confirmcancelSub2', { name: ciType.alias || ciType.name }),
    onOk() {
      subscribeTreeView(ciType.type_id, []).then(() => {
        message.success(t('cmdb.preference.cancelSubSuccess'))
        if (Number(route.params.typeId) === Number(ciType.type_id)) {
          router.push('/cmdb/tree_views')
          reload()
        } else {
          reload()
        }
      })
    },
  })
}

function subscribeSetting(e: Event, ciType: any) {
  e.stopPropagation()
  e.preventDefault()
  subscribeSettingRef.value?.open(ciType)
}

function columnDrop() {
  nextTick(() => {
    const xTable = getXTable()
    if (!xTable) {
      return
    }
    const header = xTable.$el?.querySelector('.body--wrapper>.vxe-table--header .vxe-header--row')
    if (!header) {
      return
    }
    sortable.value = Sortable.create(header as HTMLElement, {
      handle: '.vxe-handle',
      onChoose: () => {
        const headerRow = xTable.$el.querySelector('.body--wrapper>.vxe-table--header .vxe-header--row')
        const classNameList: string[] = []
        headerRow.childNodes.forEach((item: any) => {
          classNameList.push(item.classList[1])
        })
        tableDragClassName.value = classNameList
      },
      onEnd: (params: any) => {
        // Virtual scrolling makes newIndex/oldIndex virtual; recover the real
        // column ids from the class names captured on drag start.
        const { newIndex, oldIndex } = params
        const fromColid = tableDragClassName.value[oldIndex]
        const toColid = tableDragClassName.value[newIndex]
        const fromColumn = xTable.getColumnById(fromColid)
        const toColumn = xTable.getColumnById(toColid)
        const fromIndex = xTable.getColumnIndex(fromColumn)
        const toIndex = xTable.getColumnIndex(toColumn)
        const tableColumn = xTable.getColumns()
        const currRow = tableColumn.splice(fromIndex, 1)[0]
        tableColumn.splice(toIndex, 0, currRow)
        xTable.loadColumn(tableColumn)
      },
    })
  })
}

function handleSortCol({ property, order }: { property: string; order: string }) {
  let sortByTableLocal: string | undefined
  if (order === 'asc') {
    sortByTableLocal = property
  } else if (order === 'desc') {
    sortByTableLocal = `-${property}`
  }
  sortByTable.value = sortByTableLocal
  currentPage.value = 1
  handleLoadInstance({ sortByTable: sortByTableLocal })
}

function onNodeClick(keys: string) {
  if (keys) {
    const _tempKeys = keys.split(keySplit).filter((item) => item !== '')
    if (_tempKeys.length === levels.value.length) {
      getXTable()?.clearCheckboxRow()
      getXTable()?.clearCheckboxReserve()
      selectedRowKeys.value = []
    }
    treeKeys.value = _tempKeys
  }
  const idx = expandedKeys.value.findIndex((item) => item === keys)
  if (idx > -1) {
    expandedKeys.value.splice(idx, 1)
  } else {
    expandedKeys.value.push(keys)
  }
  handleLoadInstance()
}

async function refreshAfterEditAttrs() {
  await loadAttrList()
  await handleLoadInstance()
}

function deleteCIItem(record: any) {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete'),
    onOk() {
      deleteCI(record.ci_id || record._id).then(() => {
        message.success(t('deleteSuccess'))
        reload()
      })
    },
  })
}

function onSelectChange(records: any[]) {
  selectedRowKeys.value = records.map((i) => i.ci_id || i._id)
}

function handleEditActived() {
  const passwordCol = columns.value.filter((col) => col.is_password)
  nextTick(() => {
    const editRecord = getXTable()?.getEditRecord()
    const { row, column } = editRecord
    if (passwordCol.length && lastEditCiId.value !== row._id) {
      nextTick(async () => {
        for (let i = 0; i < passwordCol.length; i++) {
          await getAttrPassword(row._id, passwordCol[i].attr_id).then((res: any) => {
            initialPasswordValue.value[passwordCol[i].field] = res.value
            passwordValue.value[passwordCol[i].field] = res.value
          })
        }
        isContinueCloseEdit.value = false
        await getXTable()?.clearEdit()
        isContinueCloseEdit.value = true
        nextTick(() => {
          getXTable()?.setEditCell(row, column.field)
        })
      })
    }
    lastEditCiId.value = row._id
  })
}

function handleEditClose({ row, rowIndex }: { row: any; rowIndex: number }) {
  if (!isContinueCloseEdit.value) {
    return
  }
  const $table = getXTable()
  if (!$table) return
  const data: Record<string, any> = {}
  columns.value.forEach((item) => {
    if (
      !(item.field in initialPasswordValue.value) &&
      JSON.stringify(row[item.field]) !== JSON.stringify(initialInstanceList.value[rowIndex][item.field])
    ) {
      data[item.field] = row[item.field] ?? null
    }
  })
  Object.keys(initialPasswordValue.value).forEach((key) => {
    if (initialPasswordValue.value[key] !== passwordValue.value[key]) {
      data[key] = passwordValue.value[key]
      row[key] = passwordValue.value[key]
    }
  })
  lastEditCiId.value = null
  if (JSON.stringify(data) !== '{}') {
    updateCI(row._id, data)
      .then(() => {
        message.success(t('saveSuccess'))
        const arr1 = treeViewsLevels.value.map((item: any) => item.name)
        const arr2 = Object.keys(data)
        const arr3 = arr1.filter((item: string) => {
          return arr2.includes(item)
        })
        if (arr3.length) {
          reload()
          return
        }
        $table.reloadRow(row, null)
        const _initialInstanceList = cloneDeep(initialInstanceList.value)
        _initialInstanceList[rowIndex] = {
          ..._initialInstanceList[rowIndex],
          ...data,
        }
        initialInstanceList.value = _initialInstanceList
      })
      .catch((err) => {
        console.log(err)
        $table.revertData(row)
      })
  }
  columns.value.forEach((col) => {
    if (col.is_password) {
      initialPasswordValue.value[col.field] = ''
      passwordValue.value[col.field] = ''
    }
  })
}

function openBatchDownload() {
  batchDownloadRef.value?.open({
    preferenceAttrList: currentAttrList.value.filter((attr) => !attr?.is_reference),
    ciTypeName: currentCiTypeName.value,
  })
}

function batchDownload({ filename, type, checkedKeys }: any) {
  const jsonAttrList: string[] = []
  checkedKeys.forEach((key: any) => {
    const _find = currentAttrList.value.find((attr) => attr.name === key)
    if (_find && _find.value_type === '6') jsonAttrList.push(key)
  })
  const xTable = getXTable()
  const data = cloneDeep([...xTable.getCheckboxReserveRecords(), ...xTable.getCheckboxRecords(true)])
  xTable.exportData({
    filename,
    type,
    columnFilterMethod({ column }: { column: any }) {
      return checkedKeys.includes(column.property)
    },
    data: [
      ...data.map((item: any) => {
        jsonAttrList.forEach((jsonAttr) => (item[jsonAttr] = item[jsonAttr] ? JSON.stringify(item[jsonAttr]) : ''))
        return { ...item }
      }),
    ],
  })
  selectedRowKeys.value = []
  xTable.clearCheckboxRow()
  xTable.clearCheckboxReserve()
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
    const promises = itemList.map((x) => deleteCI(x, false))
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
          successNum: successNum,
          errorNum: errorNum,
        })
      })
  }
  loading.value = false
  loadTip.value = ''
  reload()
}

function sumbitFromCreateInstance() {
  reload()
}

function batchUpdateFromCreateInstance(values: Record<string, any>) {
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
  loadTip.value = t('cmdb.ci.batchUpdateInProgress')
  const payload: Record<string, any> = {}
  Object.keys(values).forEach((key) => {
    if (values[key] || values[key] === 0) {
      payload[key] = values[key]
    }
    if (values[key] === undefined || values[key] === null) {
      payload[key] = null
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
      .catch((error: any) => {
        errorMsg = errorMsg + '\n' + `${selectedRowKeys.value[i]}:${error.response?.data?.message ?? ''}`
        notification.warning({
          key,
          message: t('warning'),
          description: errorMsg,
          duration: 0,
          style: { whiteSpace: 'break-spaces' },
        })
        errorNum += 1
      })
      .finally(() => {
        loadTip.value = t('cmdb.ci.batchUpdateInProgress2', {
          total: selectedRowKeys.value.length,
          successNum: successNum,
          errorNum: errorNum,
        })
      })
  }
  loading.value = false
  loadTip.value = ''
  const arr1 = treeViewsLevels.value.map((item: any) => item.name)
  const arr2 = Object.keys(values)
  const arr3 = arr1.filter((item: string) => {
    return arr2.includes(item)
  })
  if (arr3.length) {
    reload()
    return
  }
  selectedRowKeys.value = []
  getXTable()?.clearCheckboxRow()
  getXTable()?.clearCheckboxReserve()
  handleLoadInstance()
}

function onShowSizeChange(_current: number, nextPageSize: number) {
  pageSize.value = nextPageSize
  currentPage.value = 1
  handleLoadInstance()
}

function getQAndSort() {
  const fuzzySearch = searchRef.value?.fuzzySearch || ''
  const expression = searchRef.value?.expression || ''
  preferenceSearchRef.value?.savePreference({ fuzzySearch, expression })
}

function setParamsFromPreferenceSearch(item: any) {
  const { fuzzySearch, expression } = item.option
  if (searchRef.value) {
    searchRef.value.fuzzySearch = fuzzySearch
    searchRef.value.expression = expression
  }
  currentPage.value = 1
  selectedRowKeys.value = []
  getXTable()?.clearCheckboxRow()
  getXTable()?.clearCheckboxReserve()
  nextTick(() => {
    handleLoadInstance()
  })
}

function setPreferenceSearchCurrent(id: number | null = null) {
  nextTick(() => {
    if (preferenceSearchRef.value) {
      preferenceSearchRef.value.currentPreferenceSearch = id
    }
  })
}

function copyExpression() {
  const expression = searchRef.value?.expression || ''
  const fuzzySearch = searchRef.value?.fuzzySearch

  const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g

  const exp = expression.match(regQ) ? expression.match(regQ)[0] : null
  const text = `q=_type:${typeId.value}${exp ? `,${exp}` : ''}${fuzzySearch ? `,*${fuzzySearch}*` : ''}`
  navigator.clipboard
    .writeText(text)
    .then(() => {
      message.success(t('copySuccess'))
    })
    .catch(() => {
      message.error(t('cmdb.ci.copyFailed'))
    })
}

function orderChange(_e: any, subscribeTreeViewCiTypesList: any[]) {
  preferenceCitypeOrder({
    type_ids: subscribeTreeViewCiTypesList.map((type) => type.type_id),
    is_tree: true,
  }).catch(() => {
    getTreeViews()
  })
}

function openDetail(id: any, activeTabKey?: string) {
  detailRef.value?.create(id, activeTabKey)
}

watch(
  () => route.path,
  () => {
    newLoad.value = true
    typeId.value = route.params.typeId as any
    initPage()
  }
)

onMounted(() => {
  getTreeViews()
  setTimeout(() => {
    columnDrop()
  }, 1000)
  getCITypes().then((res) => {
    citypes.value = res.ci_types
  })
})

onBeforeUnmount(() => {
  if (sortable.value) {
    sortable.value.destroy()
  }
})
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order, vue/v-on-event-hyphenation -->
  <div :style="{ marginBottom: '-24px' }">
    <div v-if="subscribeTreeViewCiTypesLoading" class="page-loading">
      <a-spin size="large" />
    </div>
    <div v-else-if="subscribeTreeViewCiTypes.length === 0">
      <a-alert banner>
        <template #message>
          <span>{{ t('cmdb.preference.tips1') }}</span>
          <router-link to="/cmdb/preference">{{ t('cmdb.preference.tips2') }}</router-link>
          <span>{{ t('cmdb.preference.tips3') }}</span>
        </template>
      </a-alert>
    </div>
    <div class="tree-views" v-else>
      <SplitPane
        :min="200"
        :max="500"
        v-model:pane-length-pixel="paneLengthPixel"
        app-name="cmdb-tree-views"
        :trigger-length="18"
        calc-based-parent
      >
        <template #one>
          <div class="tree-views-left" :style="{ height: `${windowHeight - 64}px` }">
            <draggable
              v-model="subscribeTreeViewCiTypes"
              :animation="300"
              @change="(e) => orderChange(e, subscribeTreeViewCiTypes)"
            >
              <div v-for="ciType in subscribeTreeViewCiTypes" :key="ciType.type_id">
              <div
                @click="handleChangeCi(ciType.type_id)"
                :class="{
                  'custom-header': true,
                  'custom-header-selected': Number(ciType.type_id) === Number(typeId) && !treeKeys.length,
                }"
              >
                <HolderOutlined class="move-icon" />
                <span class="tree-views-left-header-icon">
                  <template v-if="ciType.icon">
                    <img
                      v-if="ciType.icon.split('$$')[2]"
                      :src="`/api/common-setting/v1/file/${ciType.icon.split('$$')[3]}`"
                      :style="{ maxHeight: '14px', maxWidth: '14px' }"
                    />
                    <span
                      v-else
                      class="primary-color"
                      :style="{ color: ciType.icon.split('$$')[1], fontSize: '14px' }"
                    >{{ ciType.icon.split('$$')[0] ? ciType.icon.split('$$')[0][0].toUpperCase() : '' }}</span>
                  </template>
                  <span class="primary-color" v-else>{{ ciType.name[0].toUpperCase() }}</span>
                </span>
                <span class="tree-views-left-header-name">{{ ciType.alias || ciType.name }}</span>
                <div class="actions">
                  <a-tooltip :title="t('cmdb.preference.cancelSub')">
                    <div class="action" @click="(e) => cancelSubscribe(e, ciType)">
                      <StarFilled />
                    </div>
                  </a-tooltip>
                  <a-tooltip :title="t('cmdb.tree.subSettings')">
                    <div class="action" @click="(e) => subscribeSetting(e, ciType)">
                      <SettingOutlined />
                    </div>
                  </a-tooltip>
                </div>
              </div>
              <a-tree
                :selected-keys="selectedKeys"
                :tree-data="treeData"
                :load-data="onLoadData"
                :expanded-keys="expandedKeys"
                v-if="Number(ciType.type_id) === Number(typeId)"
              >
                <template #title="treeNodeData">
                  <TreeViewsNode
                    :title="treeNodeData.title"
                    :tree-key="treeNodeData.key"
                    :levels="levels"
                    :child-length="treeNodeData.childLength"
                    :is-leaf="treeNodeData.isLeaf"
                    @on-node-click="onNodeClick"
                  />
                </template>
              </a-tree>
            </div>
          </draggable>
          </div>
        </template>
        <template #two>
          <div class="tree-views-right" id="tree-views-right" :style="{ height: `${windowHeight - 64}px` }">
            <div class="cmdb-views-header">
              <span>
                <span class="cmdb-views-header-title">{{ currentCiTypeName }}</span>
                <span
                  @click="metadataDrawerRef?.open(typeId as number)"
                  class="cmdb-views-header-metadata"
                >
                  <InfoCircleOutlined />
                  {{ t('cmdb.ci.attributeDesc') }}
                </span>
              </span>
              <a-space>
                <a-button
                  type="primary"
                  class="ops-button-ghost"
                  ghost
                  @click="createRef?.handleOpen(true, 'create')"
                >
                  <template #icon><PlusOutlined /></template>
                  {{ t('create') }}
                </a-button>
                <EditAttrsPopover :type-id="Number(typeId)" class="operation-icon" @refresh="refreshAfterEditAttrs">
                  <a-button type="primary" ghost class="ops-button-ghost">
                    <template #icon><SettingOutlined /></template>{{ t('cmdb.configTable') }}
                  </a-button>
                </EditAttrsPopover>
              </a-space>
            </div>
            <SearchForm
              ref="searchRef"
              @refresh="reloadData"
              :preference-attr-list="currentAttrList"
              :type-id="Number(typeId)"
              @copy-expression="copyExpression"
            >
              <PreferenceSearch
                v-show="!selectedRowKeys.length"
                ref="preferenceSearchRef"
                @get-q-and-sort="getQAndSort"
                @set-params-from-preference-search="setParamsFromPreferenceSearch"
              />
              <div class="ops-list-batch-action">
                <template v-if="selectedRowKeys.length">
                  <span @click="createRef?.handleOpen(true, 'update')">{{ t('update') }}</span>
                  <a-divider type="vertical" />
                  <span @click="openBatchDownload">{{ t('download') }}</span>
                  <a-divider type="vertical" />
                  <span @click="batchDelete">{{ t('delete') }}</span>
                  <span>{{ t('cmdb.ci.selectRows', { rows: selectedRowKeys.length }) }}</span>
                </template>
              </div>
            </SearchForm>

            <CITable
              ref="xTableRef"
              :id="`cmdb-tree-${typeId}`"
              :loading="loading"
              :attr-list="currentAttrList"
              :columns="columns"
              :password-value="passwordValue"
              :data="instanceList"
              :height="tableHeight"
              :loading-tip="loadTip"
              @on-select-change="onSelectChange"
              @edit-closed="handleEditClose"
              @edit-actived="handleEditActived"
              @sort-change="handleSortCol"
              @open-detail="openDetail"
              @delete-c-i="deleteCIItem"
            />

            <div :style="{ textAlign: 'right', marginTop: '4px' }">
              <a-pagination
                show-size-changer
                :current="currentPage"
                size="small"
                :total="totalNumber"
                show-quick-jumper
                :page-size="pageSize"
                :page-size-options="pageSizeOptions"
                :show-total="
                  (total: number, range: number[]) =>
                    t('pagination.total', { range0: range[0], range1: range[1], total })
                "
                :style="{ alignSelf: 'flex-end' }"
                @show-size-change="onShowSizeChange"
                @change="
                  (page: number) => {
                    currentPage = page
                    handleLoadInstance({ sortByTable })
                  }
                "
              >
                <template #buildOptionText="{ value }">
                  <span v-if="value !== '100000'">{{ value }}{{ t('itemsPerPage') }}</span>
                  <span v-if="value === '100000'">{{ t('all') }}</span>
                </template>
              </a-pagination>
            </div>
          </div>
        </template>
      </SplitPane>
    </div>
    <SubscribeSetting ref="subscribeSettingRef" @reload="reload" />
    <CiDetailDrawer ref="detailRef" :type-id="Number(typeId)" :tree-views-levels="treeViewsLevels" />
    <CreateInstanceForm
      ref="createRef"
      :type-id-from-relation="Number(typeId)"
      @reload="sumbitFromCreateInstance"
      @submit="batchUpdateFromCreateInstance"
    />
    <BatchDownload ref="batchDownloadRef" @batch-download="batchDownload" />
    <MetadataDrawer ref="metadataDrawerRef" />
  </div>
</template>

<style lang="less">
.page-loading {
  text-align: center;
  padding-top: 150px;
}

.cmdb-views-header {
  border-left: 4px solid @primary-color;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  .cmdb-views-header-title {
    font-size: 16px;
    font-weight: bold;
    color: @text-color_1;
    margin-left: 10px;
  }
  .cmdb-views-header-metadata {
    cursor: pointer;
    font-size: 12px;
    color: @text-color_3;
    margin-left: 20px;
    &:hover {
      color: @primary-color;
    }
  }
}

.tree-views {
  width: 100%;
  height: calc(100% - 32px);
  .tree-views-left {
    float: left;
    position: relative;
    overflow: hidden;
    width: 100%;
    &:hover {
      overflow: auto;
    }
    .custom-header {
      width: 100%;
      display: inline-flex;
      flex-direction: row;
      flex-wrap: nowrap;
      justify-content: flex-start;
      align-items: center;
      padding: 8px 0 8px 12px;
      cursor: move;
      border-radius: 2px;
      position: relative;
      &:hover {
        background-color: @primary-color_3;
        > .actions,
        > .move-icon {
          display: inherit;
        }
      }
      .move-icon {
        width: 14px;
        height: 20px;
        cursor: move;
        position: absolute;
        display: none;
        left: 0;
      }
      .tree-views-left-header-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 2px;
        margin-right: 6px;
      }
      .tree-views-left-header-name {
        flex: 1;
        font-weight: bold;
        margin-left: 5px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: @text-color_1;
      }
      .actions {
        display: none;
        margin-left: auto;
        cursor: pointer;
      }
      .action {
        display: inline-block;
        width: 22px;
        text-align: center;
        border-radius: 5px;
        &:hover {
          background-color: #cacaca;
        }
      }
    }
    .custom-header-selected {
      background-color: @primary-color_3 !important;
    }
    .ant-tree li {
      padding: 2px 0;
    }
    .ant-tree-switcher {
      display: none;
    }
    .ant-tree-node-content-wrapper {
      width: 100%;
      padding: 4px 0;
      display: inline-block;
      height: 100%;
      .ant-tree-title {
        display: inline-block;
        width: 100%;
        padding: 0 6px;
      }
    }
    .ant-tree li .ant-tree-node-content-wrapper.ant-tree-node-selected {
      background-color: @primary-color_3;
    }
  }
  .tree-views-right {
    background-color: #fff;
    display: flex;
    flex-direction: column;
    padding: 20px;
    overflow: auto;
    width: 100%;
    border-radius: @border-radius-box;
  }
}
</style>
