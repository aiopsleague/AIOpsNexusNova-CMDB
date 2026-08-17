<script setup lang="ts">
import { computed, inject, nextTick, onMounted, provide, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { PlusOutlined, UserAddOutlined, SearchOutlined } from '@ant-design/icons-vue'
import { cloneDeep, getCITableColumns } from '@/modules/cmdb/utils/helper'
import SearchForm from '@/modules/cmdb/components/searchForm/SearchForm.vue'
import AddTableModal from './modules/AddTableModal.vue'
import ContextMenu from './modules/ContextMenu.vue'
import { getRelationView, getSubscribeAttributes } from '@/modules/cmdb/api/preference'
import {
  searchCIRelation,
  statisticsCIRelation,
  deleteCIRelationView,
  batchDeleteCIRelation as batchDeleteCIRelationApi,
  batchUpdateCIRelationChildren,
  addCIRelationView,
  searchCIRelationFull,
} from '@/modules/cmdb/api/CIRelation'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { searchCI, updateCI, deleteCI } from '@/modules/cmdb/api/ci'
import { getCITypeIcons, grantCiType, revokeCiType } from '@/modules/cmdb/api/CIType'
import { roleHasPermissionToGrant } from '@/modules/acl/api/permission'
import { searchResourceType } from '@/modules/acl/api/resource'
import SplitPane from '@/components/SplitPane/SplitPane.vue'
import EditAttrsPopover from '@/modules/cmdb/views/ci/modules/editAttrsPopover.vue'
import CiDetailDrawer from '@/modules/cmdb/views/ci/modules/ciDetailDrawer.vue'
import CreateInstanceForm from '@/modules/cmdb/views/ci/modules/CreateInstanceForm.vue'
import BatchDownload from '@/modules/cmdb/components/batchDownload/batchDownload.vue'
import PreferenceSearch from '@/modules/cmdb/components/preferenceSearch/preferenceSearch.vue'
import CMDBGrant from '@/modules/cmdb/components/cmdbGrant/index.vue'
import GrantModal from '@/modules/cmdb/components/cmdbGrant/grantModal.vue'
import { getAttrPassword } from '@/modules/cmdb/api/CITypeAttr'
import ReadPermissionsModal from './modules/ReadPermissionsModal.vue'
import RevokeModal from '@/modules/cmdb/components/cmdbGrant/revokeModal.vue'
import CITable from '@/modules/cmdb/components/ciTable/index.vue'

const relationViewKeyStorage = 'cmdb_relation_view_menu_key'

const { t } = useI18n()
const route = useRoute()
const reload = inject<(() => void) | null>('reload', null)

// Child component refs.
const xTableRef = ref<InstanceType<typeof CITable>>()
const searchRef = ref<any>()
const preferenceSearchRef = ref<any>()
const addTableModalRef = ref<InstanceType<typeof AddTableModal>>()
const cmdbGrantRef = ref<InstanceType<typeof CMDBGrant>>()
const grantModalRef = ref<InstanceType<typeof GrantModal>>()
const detailRef = ref<InstanceType<typeof CiDetailDrawer>>()
const createRef = ref<InstanceType<typeof CreateInstanceForm>>()
const batchDownloadRef = ref<InstanceType<typeof BatchDownload>>()
const readPermissionsModalRef = ref<InstanceType<typeof ReadPermissionsModal>>()
const revokeModalRef = ref<InstanceType<typeof RevokeModal>>()

const treeData = ref<any[]>([])
const triggerSelect = ref(false)
const treeNode = ref<any>(null)
const ciTypeIcons = ref<Record<string, any>>({})
const relationViews = ref<Record<string, any>>({})
const levels = ref<any[]>([])
const showTypeIds = ref<Array<string | number>>([])
const origShowTypeIds = ref<Array<string | number>>([])
const showTypes = ref<any[]>([])
const origShowTypes = ref<any[]>([])
const leaf2showTypes = ref<Record<string, any>>({})
const node2ShowTypes = ref<Record<string, any>>({})
const level2constraint = ref<Record<string, any>>({})
const leaf = ref<any[]>([])
const viewId = ref<number | null>(null)
const viewName = ref<string | null>(null)
const currentTypeId = ref<Array<string | number>>([])
const instanceList = ref<any[]>([])
const numfound = ref(0)
const pageNo = ref(1)
const pageSize = ref(50)
const pageSizeOptions = ref(['50', '100', '200', '100000'])
const treeKeys = ref<string[]>([])
const expandedKeys = ref<string[]>([])
const columns = ref<any[]>([])
const loading = ref(false)
const preferenceAttrList = ref<any[]>([])
const selectedRowKeys = ref<any[]>([])
const paneLengthPixel = ref(210)
const attrList = ref<any[]>([])
const attributes = ref<Record<string, any>>({})
const initialInstanceList = ref<any[]>([])
const sortByTable = ref<string | undefined>(undefined)
const resource_type = ref<Record<string, any>>({})
const initialPasswordValue = ref<Record<string, any>>({})
const passwordValue = ref<Record<string, any>>({})
const lastEditCiId = ref<string | number | null>(null)
const isContinueCloseEdit = ref(true)
const contextMenuKey = ref<string | null>(null)
const showBatchLevel = ref<number | null>(null)
const batchTreeKey = ref<string[]>([])
const viewOption = ref<Record<string, any>>({})
const loadRootStatisticsParams = ref<Record<string, any>>({})
const fullSearchValue = ref('')
const isFullSearch = ref(false)
const fullTreeData = ref<any[]>([])
const filterFullTreeData = ref<any[]>([])

const windowHeight = computed(() => window.innerHeight)
const tableHeight = computed(() => windowHeight.value - 244)
const selectedKeys = computed(() => [treeKeys.value.join('@^@')])
const isLeaf = computed(() => treeKeys.value.length === levels.value.length)
const isShowBatchIcon = computed(() => !!selectedRowKeys.value.length)
const topo_flatten = computed<any[]>(() => relationViews.value?.views?.[viewName.value ?? '']?.topo_flatten ?? [])
const descendant_ids = computed(() => topo_flatten.value.slice(treeKeys.value.length).join(','))
const descendant_ids_for_statistics = computed(() => topo_flatten.value.slice(treeKeys.value.length + 1).join(','))
const root_parent_path = computed(() =>
  treeKeys.value
    .slice(0, treeKeys.value.length)
    .map((item) => item.split('%')[0])
    .join(',')
)
const is_show_leaf_node = computed(() => viewOption.value?.is_show_leaf_node ?? true)
const is_show_tree_node = computed(() => viewOption.value?.is_show_tree_node ?? false)
const leaf_tree_sort = computed(() => viewOption.value?.sort ?? 1)
const relationViewMenu = computed(() => {
  const name2id = relationViews.value?.name2id || []
  return name2id.map((item: any[]) => ({ id: item?.[1] || -1, name: item?.[0] || '' }))
})

provide('handleSearch', refreshTable)
provide('setPreferenceSearchCurrent', setPreferenceSearchCurrent)
provide('attrList', () => attrList.value)
provide('attributes', () => attributes.value)
provide('relationViewRefreshNumber', relationViewRefreshNumber)
provide('filterCompPreferenceSearch', () => ({ prv_id: viewId.value }))
provide('resource_type', () => resource_type.value)

async function getAttributeList() {
  await getCITypeAttributesById(Number(currentTypeId.value[0])).then((res) => {
    attrList.value = res.attributes
    attributes.value = res
  })
}

function getCITypesList() {
  getCITypeIcons().then((res) => {
    ciTypeIcons.value = res
  })
}

function refreshTable() {
  selectedRowKeys.value = []
  sortByTable.value = undefined
  const xTable = xTableRef.value?.getVxetableRef()
  if (xTable) {
    xTable.clearCheckboxRow()
    xTable.clearCheckboxReserve()
    xTable.clearSort()
  }
  loadData()
}

async function loadData({
  parameter,
  refreshType = undefined,
  sortByTable: sortByTableParam = undefined,
}: {
  parameter?: Record<string, any>
  refreshType?: string
  sortByTable?: string
} = {}) {
  const params = parameter || {}
  let q = ''
  // Filter conditions live in the expression produced by SearchForm in the Vue 3
  // shell (there is no separate queryParam object).
  const expression = searchRef.value?.expression || ''
  const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
  const regSort = /(?<=sort=).+/g

  const exp = expression.match(regQ) ? expression.match(regQ)![0] : null
  if (exp) {
    q = `${q},${exp}`
  }

  let sort: string | undefined
  if (sortByTableParam) {
    sort = sortByTableParam
  } else {
    sort = expression.match(regSort) ? expression.match(regSort)![0] : undefined
  }
  if (sort) {
    q = `${q}&sort=${sort}`
  }
  if ('pageNo' in params) {
    q += `&page=${params.pageNo}&count=${pageSize.value}`
  } else {
    q += `&page=1&count=${pageSize.value}`
  }

  if ('sortField' in params) {
    let order = ''
    if (params.sortOrder !== 'ascend') {
      order = '-'
    }
    q += `&sort=${order}${params.sortField}`
  }
  if (q && q[0] === ',') {
    q = q.slice(1)
  }

  if (treeKeys.value.length === 0) {
    if (!refreshType && !isFullSearch.value) {
      await loadRoot()
    }
  } else {
    q += `&root_id=${treeKeys.value[treeKeys.value.length - 1].split('%')[0]}`

    if (
      Object.keys(level2constraint.value).some(
        (le) => Number(le) < Object.keys(level2constraint.value).length && level2constraint.value[le] === '2'
      )
    ) {
      q += `&ancestor_ids=${treeKeys.value
        .slice(0, treeKeys.value.length - 1)
        .map((item) => item.split('%')[0])
        .join(',')}`
    }

    await judgeCITypes()

    const typeId = parseInt(treeKeys.value[treeKeys.value.length - 1].split('%')[1])
    let level: number[] = []
    if (!leaf.value.includes(typeId)) {
      let startIdx = 0
      levels.value.forEach((item, idx) => {
        if (item.includes(typeId)) {
          startIdx = idx
        }
      })

      leaf.value.forEach((leafId) => {
        levels.value.forEach((item, levelIdx) => {
          if (item.includes(leafId) && levelIdx - startIdx + 1 > 0) {
            level.push(levelIdx - startIdx + 1)
          }
        })
      })
    } else {
      level = [1]
    }

    q += `&level=${topo_flatten.value.includes(currentTypeId.value[0]) ? 1 : level.join(',')}`
    if (!refreshType && !isFullSearch.value) {
      loadNoRoot(treeKeys.value[treeKeys.value.length - 1], level)
    }
    const fuzzySearch = searchRef.value?.fuzzySearch || ''
    if (fuzzySearch) {
      q = `q=_type:${currentTypeId.value[0]},*${fuzzySearch}*,` + q
    } else {
      q = `q=_type:${currentTypeId.value[0]},` + q
    }
    if (Object.values(level2constraint.value).includes('2')) {
      q = q + `&has_m2m=1`
    }
    if (root_parent_path.value) {
      q = q + `&root_parent_path=${root_parent_path.value}`
    }
    q = q + `&descendant_ids=${descendant_ids.value}`
    if (currentTypeId.value[0]) {
      const res = await searchCIRelation(q)

      const _data = Object.assign([], res.result)
      _data.forEach((item: any) => (item.key = item._id))
      numfound.value = res.numfound
      pageNo.value = res.page

      const jsonAttrList = preferenceAttrList.value.filter((attr) => attr.value_type === '6')
      instanceList.value = _data.map((item: any) => {
        jsonAttrList.forEach((jsonAttr) => (item[jsonAttr.name] = item[jsonAttr.name] ? JSON.stringify(item[jsonAttr.name]) : ''))
        return { ...cloneDeep(item) }
      })
      initialInstanceList.value = cloneDeep(instanceList.value)

      calcColumns()
    }
    if (refreshType === 'refreshNumber') {
      treeKeys.value.forEach((key, index) => {
        let ancestor_ids: string | undefined
        if (
          Object.keys(level2constraint.value).some(
            (le) => Number(le) < Object.keys(level2constraint.value).length && level2constraint.value[le] === '2'
          )
        ) {
          ancestor_ids = `${treeKeys.value
            .slice(0, index)
            .map((item) => item.split('%')[0])
            .join(',')}`
        }
        statisticsCIRelation({
          ancestor_ids,
          root_ids: key.split('%')[0],
          level: treeKeys.value.length - index,
          type_ids: leaf2showTypes.value[leaf.value[0]].join(','),
          has_m2m: Number(Object.values(level2constraint.value).includes('2')),
          descendant_ids: descendant_ids_for_statistics.value,
        }).then((res) => {
          let result: any
          const getTreeItem = (data: any[], id: string) => {
            for (let i = 0; i < data.length; i++) {
              if (Number(data[i].id) === Number(id)) {
                result = data[i]
                break
              } else {
                if (data[i].children && data[i].children.length) {
                  getTreeItem(data[i].children, id)
                }
              }
            }
          }
          getTreeItem(treeData.value, key.split('%')[0])

          const reg = /(?<=\()\S+(?=\))/g
          result.title = result.title.replace(reg, `${res[key.split('%')[0]]}`)
        })
      })
    }
  }
}

function changeCIType(typeId: string | number) {
  xTableRef.value?.getVxetableRef()?.clearCheckboxRow()
  xTableRef.value?.getVxetableRef()?.clearCheckboxReserve()
  searchRef.value?.reset()
  selectedRowKeys.value = []
  currentTypeId.value = [typeId]
  loadColumns()
}

async function judgeCITypes() {
  let _showTypeIds: Array<string | number> = []
  let _showTypes: any[] = []
  if (treeKeys.value.length) {
    if (is_show_leaf_node.value) {
      const typeId = parseInt(treeKeys.value[treeKeys.value.length - 1].split('%')[1])
      _showTypeIds = cloneDeep(origShowTypeIds.value)
      _showTypes = cloneDeep(node2ShowTypes.value[typeId])
    }
    if (is_show_tree_node.value) {
      const treeKeyTypeId = Number(treeKeys.value.slice(-1)[0].split('%')[1])
      const _idx = topo_flatten.value.findIndex((item) => item === treeKeyTypeId)
      if (_idx > -1 && _idx < topo_flatten.value.length - 1) {
        const _showTreeTypeId = topo_flatten.value[_idx + 1]
        const _showTreeTypes = relationViews.value.id2type[_showTreeTypeId]
        if (leaf_tree_sort.value === 1) {
          _showTypeIds.push(_showTreeTypeId)
          _showTypes.push(_showTreeTypes)
        } else {
          _showTypeIds.unshift(_showTreeTypeId)
          _showTypes.unshift(_showTreeTypes)
        }
      }
    }
    showTypeIds.value = _showTypeIds
    showTypes.value = _showTypes
  } else {
    showTypeIds.value = cloneDeep(origShowTypeIds.value)
    showTypes.value = JSON.parse(JSON.stringify(origShowTypes.value))
  }
  if (
    !currentTypeId.value.length ||
    (currentTypeId.value.length && !showTypeIds.value.includes(currentTypeId.value[0]))
  ) {
    currentTypeId.value = [showTypeIds.value[0]]
    await loadColumns()
  }
}

async function loadRoot() {
  await searchCI({
    q: `_type:(${levels.value[0].join(';')})`,
    count: 10000,
    use_id_filter: 1,
  }).then(async (res) => {
    const facet: any[] = []
    const ciIds: any[] = []
    res.result.forEach((item: any) => {
      const showName = relationViews.value.id2type[item._type]?.show_name ?? null
      facet.push({
        showName,
        showNameValue: item[showName] ?? null,
        uniqueValue: item[item.unique],
        number: 0,
        ciId: item._id,
        typeId: item._type,
        unique: item.unique,
      })
      ciIds.push(item._id)
    })

    const leafId = leaf.value[0]
    let level = 0
    levels.value.forEach((item, idx) => {
      if (item.includes(leafId)) {
        level = idx + 1
      }
    })
    const params = {
      level,
      root_ids: ciIds.join(','),
      has_m2m: Number(Object.values(level2constraint.value).includes('2')),
    }
    loadRootStatisticsParams.value = params
    await statisticsCIRelation({
      ...params,
      type_ids: leaf2showTypes.value[leaf.value[0]].join(','),
      descendant_ids: descendant_ids_for_statistics.value,
    }).then((num: Record<string, number>) => {
      facet.forEach((item, idx) => {
        item.number += num[ciIds[idx] + '']
      })
    })
    wrapTreeData(facet)
    // Default select the first node.
    onNodeClick(treeData.value[0].key)
  })
}

async function loadNoRoot(rootIdAndTypeId: string, level: number[]) {
  const rootId = rootIdAndTypeId.split('%')[0]
  const typeId = Number(rootIdAndTypeId.split('%')[1])
  const index = topo_flatten.value.findIndex((id) => id === typeId)
  const _type = topo_flatten.value[index + 1]
  if (_type) {
    let q = `q=_type:${_type}&root_id=${rootId}&level=1&count=10000`
    if (
      Object.keys(level2constraint.value).some(
        (le) => Number(le) < Object.keys(level2constraint.value).length && level2constraint.value[le] === '2'
      )
    ) {
      q += `&ancestor_ids=${treeKeys.value
        .slice(0, treeKeys.value.length - 1)
        .map((item) => item.split('%')[0])
        .join(',')}`
    }
    if (Object.values(level2constraint.value).includes('2')) {
      q = q + `&has_m2m=1`
    }
    if (root_parent_path.value) {
      q = q + `&root_parent_path=${root_parent_path.value}`
    }
    q = q + `&descendant_ids=${descendant_ids.value}`
    searchCIRelation(q).then(async (res) => {
      const facet: any[] = []
      const ciIds: any[] = []
      res.result.forEach((item: any) => {
        const showName = relationViews.value.id2type[item._type]?.show_name ?? null
        facet.push({
          showName,
          showNameValue: item[showName] ?? null,
          uniqueValue: item[item.unique],
          number: 0,
          ciId: item._id,
          typeId: item._type,
          unique: item.unique,
        })
        ciIds.push(item._id)
      })
      let ancestor_ids: string | undefined
      if (
        Object.keys(level2constraint.value).some(
          (le) => Number(le) < Object.keys(level2constraint.value).length && level2constraint.value[le] === '2'
        )
      ) {
        ancestor_ids = `${treeKeys.value.map((item) => item.split('%')[0]).join(',')}`
      }
      const promises = level.map((_level) => {
        if (_level > 1) {
          return statisticsCIRelation({
            ancestor_ids,
            root_ids: ciIds.join(','),
            level: _level - 1,
            type_ids: leaf2showTypes.value[leaf.value[0]].join(','),
            has_m2m: Number(Object.values(level2constraint.value).includes('2')),
            descendant_ids: descendant_ids_for_statistics.value,
          }).then((num: Record<string, number>) => {
            facet.forEach((item, idx) => {
              item.number += num[ciIds[idx] + '']
            })
          })
        }
      })
      await Promise.all(promises)
      wrapTreeData(facet)
    })
  }
}

function onNodeClick(keys: string | null, callback?: () => void) {
  triggerSelect.value = true
  if (keys) {
    const _tempKeys = keys.split('@^@').filter((item) => item !== '')
    if (_tempKeys.length === levels.value.length) {
      xTableRef.value?.getVxetableRef()?.clearCheckboxRow()
      xTableRef.value?.getVxetableRef()?.clearCheckboxReserve()
      selectedRowKeys.value = []
    }
    treeKeys.value = _tempKeys
  }
  const idx = expandedKeys.value.findIndex((item) => item === keys)
  if (idx > -1) {
    expandedKeys.value.splice(idx, 1)
  } else {
    expandedKeys.value.push(keys as string)
  }

  refreshTable()
  if (callback && typeof callback === 'function') {
    callback()
  }
}

function wrapTreeData(facet: any[]) {
  if (triggerSelect.value) {
    return
  }
  const nextTreeData: any[] = []
  facet.forEach((item) => {
    const _treeKeys = cloneDeep(treeKeys.value)
    _treeKeys.push(item.ciId + '%' + item.typeId + '%' + `{"${item.unique}":"${item.uniqueValue}"}`)
    nextTreeData.push({
      title: item.showName ? item.showNameValue : item.uniqueValue,
      number: item.number,
      key: _treeKeys.join('@^@'),
      isLeaf: leaf.value.includes(item.typeId),
      id: item.ciId,
      showName: item.showName,
    })
  })
  if (treeNode.value === null) {
    treeData.value = nextTreeData
  } else {
    treeNode.value.dataRef.children = nextTreeData
    treeData.value = [...treeData.value]
  }
}

function onLoadData(treeNodeParam: any) {
  triggerSelect.value = false
  return new Promise((resolve) => {
    if (treeNodeParam.dataRef.children) {
      resolve(undefined)
      return
    }
    treeKeys.value = treeNodeParam.eventKey.split('@^@').filter((item: string) => item !== '')
    treeNode.value = treeNodeParam
    resolve(undefined)
  })
}

function getRelationViews() {
  getRelationView().then((res: any) => {
    if (JSON.stringify(res) === '{}') {
      relationViews.value = {
        id2type: {},
        name2id: [],
        views: {},
      }
    } else {
      relationViews.value = res
    }
    if ((Object.keys(relationViews.value.views) || []).length) {
      let viewIdLocal =
        parseInt(localStorage.getItem(relationViewKeyStorage) || '') || parseInt(route.params.viewId as string) || relationViews.value.name2id[0][1]
      let viewNameLocal: string | null = null

      const currentView = relationViews.value.name2id.find((item: any[]) => item?.[1] === viewIdLocal)
      if (currentView) {
        viewNameLocal = currentView[0]
      } else {
        viewIdLocal = relationViews.value.name2id[0][1]
        viewNameLocal = relationViews.value.name2id[0][0]
      }

      localStorage.setItem(relationViewKeyStorage, String(viewIdLocal))
      viewId.value = viewIdLocal
      viewName.value = viewNameLocal
      refreshData()
    }
  })
}

function refreshData() {
  levels.value = relationViews.value.views[viewName.value as string].topo
  origShowTypes.value = relationViews.value.views[viewName.value as string].show_types
  const showTypeIdsLocal: Array<string | number> = []
  origShowTypes.value.forEach((item: any) => {
    showTypeIdsLocal.push(item.id)
  })
  origShowTypeIds.value = showTypeIdsLocal
  leaf2showTypes.value = relationViews.value.views[viewName.value as string].leaf2show_types
  node2ShowTypes.value = relationViews.value.views[viewName.value as string].node2show_types
  level2constraint.value = relationViews.value.views[viewName.value as string].level2constraint
  leaf.value = relationViews.value.views[viewName.value as string].leaf
  viewOption.value = relationViews.value.views[viewName.value as string].option ?? {}

  nextTick(() => {
    refreshTable()
  })
}

async function loadColumns() {
  if (currentTypeId.value[0]) {
    getAttributeList()
    const res = await getSubscribeAttributes(currentTypeId.value[0])
    preferenceAttrList.value = res.attributes
    calcColumns()
  }
}

function calcColumns() {
  const width = document.getElementById('relation-views-right')?.clientWidth ?? 1600
  columns.value = getCITableColumns(instanceList.value, preferenceAttrList.value, width)
  columns.value.forEach((col) => {
    if (col.is_password) {
      initialPasswordValue.value[col.field] = ''
      passwordValue.value[col.field] = ''
    }
  })
  nextTick(() => {
    xTableRef.value?.getVxetableRef()?.refreshColumn()
  })
}

function calculateParamsFromTreeKey(treeKey: string, menuKey: string | number) {
  const splitTreeKey = treeKey.split('@^@')
  const _tempTree = splitTreeKey[splitTreeKey.length - 1].split('%')
  const firstCIObj = JSON.parse(_tempTree[2])
  const firstCIId = _tempTree[0]
  let ancestor_ids: string | undefined
  if (
    Object.keys(level2constraint.value).some(
      (le) => Number(le) < Object.keys(level2constraint.value).length && level2constraint.value[le] === '2'
    )
  ) {
    const ancestor = treeKey
      .split('@^@')
      .slice(0, menuKey === 'delete' ? treeKey.split('@^@').length - 2 : treeKey.split('@^@').length - 1)
    ancestor_ids = ancestor.map((item) => item.split('%')[0]).join(',')
  }
  return { splitTreeKey, firstCIObj, firstCIId, _tempTree, ancestor_ids }
}

function onContextMenuClick(treeKey: string, menuKey: string | number) {
  if (treeKey) {
    if (!['batchGrant', 'batchRevoke', 'batchDelete', 'batchCancel'].includes(String(menuKey))) {
      contextMenuKey.value = treeKey
    }

    const { splitTreeKey, firstCIObj, firstCIId, _tempTree, ancestor_ids } = calculateParamsFromTreeKey(treeKey, menuKey)
    if (menuKey === 'delete') {
      const _tempTreeParent = splitTreeKey[splitTreeKey.length - 2].split('%')
      Modal.confirm({
        title: t('warning'),
        content: t('confirmDelete2', { name: Object.values(firstCIObj)[0] as string }),
        onOk() {
          deleteCIRelationView(_tempTreeParent[0], _tempTree[0], { ancestor_ids }).then(() => {
            message.success(t('deleteSuccess'))
            setTimeout(() => {
              reload?.()
            }, 500)
          })
        },
      })
    } else if (menuKey === 'grant') {
      grantModalRef.value?.open('depart')
    } else if (menuKey === 'revoke') {
      revokeModalRef.value?.open()
    } else if (menuKey === 'view') {
      readPermissionsModalRef.value?.open(treeKey)
    } else if (menuKey === 'batch') {
      showBatchLevel.value = splitTreeKey.filter((item: string) => !!item).length - 1
      batchTreeKey.value = []
    } else if (menuKey === 'batchGrant') {
      grantModalRef.value?.open('depart')
    } else if (menuKey === 'batchRevoke') {
      revokeModalRef.value?.open()
    } else if (menuKey === 'batchDelete') {
      batchDeleteCIRelationFromTree()
    } else if (menuKey === 'batchCancel') {
      showBatchLevel.value = null
      batchTreeKey.value = []
    } else {
      const childTypeId = menuKey as number

      let typeName = ''
      if (relationViews.value?.id2type?.[childTypeId]) {
        typeName = relationViews.value.id2type[childTypeId]?.name || ''
      } else {
        const node2show_types = relationViews.value?.views?.[viewName.value as string]?.node2show_types
        const typeId = _tempTree?.[1]
        if (node2show_types?.[typeId]?.length) {
          const findType = node2show_types[typeId].find((item: any) => item.id === childTypeId)
          typeName = findType?.name || ''
        }
      }
      addTableModalRef.value?.openModal(firstCIObj, firstCIId, { id: childTypeId, name: typeName }, 'children', ancestor_ids)
    }
  }
}

function onSelectChange(records: any[]) {
  selectedRowKeys.value = records
}

function batchDeleteCIRelation() {
  const currentShowType = showTypes.value.find((item) => item.id === Number(currentTypeId.value[0]))
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.serviceTree.deleteRelationConfirm', {
      name: currentShowType?.alias || currentShowType?.name,
    }),
    onOk() {
      const _tempTree = treeKeys.value[treeKeys.value.length - 1].split('%')
      const first_ci_id = Number(_tempTree[0])
      let ancestor_ids: string | undefined
      if (
        Object.keys(level2constraint.value).some(
          (le) => Number(le) < Object.keys(level2constraint.value).length && level2constraint.value[le] === '2'
        )
      ) {
        ancestor_ids = `${treeKeys.value
          .slice(0, treeKeys.value.length - 1)
          .map((item) => item.split('%')[0])
          .join(',')}`
      }
      batchDeleteCIRelationApi(
        selectedRowKeys.value.map((item) => item._id),
        [first_ci_id],
        ancestor_ids
      ).then(() => {
        xTableRef.value?.getVxetableRef()?.clearCheckboxRow()
        xTableRef.value?.getVxetableRef()?.clearCheckboxReserve()
        selectedRowKeys.value = []
        loadData({ parameter: {}, refreshType: 'refreshNumber' })
      })
    },
  })
}

function onDragEnter() {}

function onDrop(info: any) {
  const dragKey = info.dragNode.eventKey
  const targetKey = info.node.eventKey
  const _splitDragKey = dragKey.split('@^@')
  const _splitTargetKey = targetKey.split('@^@').filter((item: string) => item !== '')
  if (_splitDragKey.length - 1 === _splitTargetKey.length) {
    const dragId = _splitDragKey[_splitDragKey.length - 1].split('%')[0]
    const targetId = _splitTargetKey[_splitTargetKey.length - 1].split('%')[0]
    batchUpdateCIRelationChildren([dragId], [targetId]).then(() => {
      reload?.()
    })
  }
}

function handlePerm(resourceName?: string) {
  const _resource_name = resourceName ?? viewName.value ?? ''

  roleHasPermissionToGrant({
    app_id: 'cmdb',
    resource_type_name: 'RelationView',
    perm: 'grant',
    resource_name: _resource_name,
  }).then((res: any) => {
    if (res.result) {
      searchResourceType({ page_size: 9999, app_id: 'cmdb' }).then((res: any) => {
        resource_type.value = { groups: res.groups, id2perms: res.id2perms }
        nextTick(() => {
          cmdbGrantRef.value?.open({ name: _resource_name, cmdbGrantType: 'relation_view' })
        })
      })
    } else {
      message.error(t('noPermission'))
    }
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
  nextTick(() => {
    if (pageNo.value === 1) {
      loadData({ parameter: {}, sortByTable: sortByTableLocal })
    } else {
      pageNo.value = 1
    }
  })
}

function refreshAfterEditAttrs() {
  loadColumns()
}

function handleEditActived() {
  const passwordCol = columns.value.filter((col) => col.is_password)
  nextTick(() => {
    const editRecord = xTableRef.value?.getVxetableRef()?.getEditRecord()
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
        await xTableRef.value?.getVxetableRef()?.clearEdit()
        isContinueCloseEdit.value = true
        nextTick(() => {
          xTableRef.value?.getVxetableRef()?.setEditCell(row, column.field)
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
  const $table = xTableRef.value?.getVxetableRef()
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
    updateCI(row.ci_id || row._id, data)
      .then(() => {
        message.success(t('saveSuccess'))
        $table.reloadRow(row, null)
        const _initialInstanceList = cloneDeep(initialInstanceList.value)
        _initialInstanceList[rowIndex] = {
          ..._initialInstanceList[rowIndex],
          ...data,
        }
        initialInstanceList.value = _initialInstanceList
        nextTick(() => {
          refreshTable()
        })
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

function deleteCIItem(record: any) {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete'),
    onOk() {
      deleteCI(record.ci_id || record._id).then(() => {
        message.success(t('deleteSuccess'))
        loadData({ parameter: {}, refreshType: 'refreshNumber' })
      })
    },
  })
}

function sumbitFromCreateInstance({ ci_id }: { ci_id: string | number }) {
  const first_ci_id = treeKeys.value[treeKeys.value.length - 1].split('%')[0]
  let ancestor_ids: string | undefined
  if (
    Object.keys(level2constraint.value).some(
      (le) => Number(le) < Object.keys(level2constraint.value).length && level2constraint.value[le] === '2'
    )
  ) {
    ancestor_ids = `${treeKeys.value
      .slice(0, treeKeys.value.length - 1)
      .map((item) => item.split('%')[0])
      .join(',')}`
  }
  addCIRelationView(first_ci_id, ci_id, { ancestor_ids }).then(() => {
    setTimeout(() => {
      loadData({ parameter: {}, refreshType: 'refreshNumber' })
    }, 500)
  })
}

function batchUpdateFromCreateInstance(values: Record<string, any>) {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ci.batchUpdateConfirm'),
    onOk() {
      loading.value = true
      const payload: Record<string, any> = {}
      Object.keys(values).forEach((key) => {
        if (values[key] || values[key] === 0) {
          payload[key] = values[key]
        }
        // Field values support being cleared.
        // Some fields do not support clearing, the backend will return them.
        if (values[key] === undefined || values[key] === null) {
          payload[key] = null
        }
      })
      const promises = selectedRowKeys.value.map((row) => {
        return updateCI(row._id, payload).then(() => 'ok')
      })
      Promise.all(promises)
        .then(() => {
          message.success(t('updateSuccess'))
          createRef.value?.handleClose()
        })
        .catch((e) => {
          console.log(e)
        })
        .finally(() => {
          loading.value = false
          setTimeout(() => {
            loadData({ parameter: {} })
          }, 800)
        })
    },
  })
}

function openBatchDownload() {
  batchDownloadRef.value?.open({
    preferenceAttrList: preferenceAttrList.value.filter((attr) => !attr?.is_reference),
    ciTypeName: viewName.value ?? '',
  })
}

function batchDownload(payload: any) {
  const { filename, type, checkedKeys } = payload
  const jsonAttrList: string[] = []
  checkedKeys.forEach((key: any) => {
    const _find = preferenceAttrList.value.find((attr) => attr.name === key)
    if (_find && _find.value_type === '6') jsonAttrList.push(key)
  })
  const xTable = xTableRef.value?.getVxetableRef()
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
      loading.value = true
      const promises = selectedRowKeys.value.map((c) => {
        return deleteCI(c._id).then(() => 'ok')
      })
      Promise.all(promises)
        .then(() => {
          message.success(t('deleteSuccess'))
        })
        .catch((e) => {
          console.log(e)
        })
        .finally(() => {
          loading.value = false
          selectedRowKeys.value = []
          xTableRef.value?.getVxetableRef()?.clearCheckboxRow()
          xTableRef.value?.getVxetableRef()?.clearCheckboxReserve()
          loadData({ parameter: {}, refreshType: 'refreshNumber' })
        })
    },
  })
}

function relationViewRefreshNumber() {
  loadData({ parameter: {}, refreshType: 'refreshNumber' })
}

function onShowSizeChange(_current: number, size: number) {
  pageSize.value = size
  pageNo.value = 1
  loadData()
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
  pageNo.value = 1
  nextTick(() => {
    loadData()
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

  const exp = expression.match(regQ) ? expression.match(regQ)![0] : null
  const text = `q=_type:${currentTypeId.value[0]}${exp ? `,${exp}` : ''}${fuzzySearch ? `,*${fuzzySearch}*` : ''}`
  navigator.clipboard
    .writeText(text)
    .then(() => {
      message.success(t('copySuccess'))
    })
    .catch(() => {
      message.error(t('cmdb.serviceTreecopyFailed'))
    })
}

async function onRelationViewGrant({ department, user }: { department: any[]; user: any[] }) {
  const result: any[] = []
  if (showBatchLevel.value !== null && batchTreeKey.value && batchTreeKey.value.length) {
    for (let i = 0; i < batchTreeKey.value.length; i++) {
      await relationViewGrant({ department, user }, batchTreeKey.value[i], (_result: any[]) => {
        result.push(..._result)
      })
    }
    showBatchLevel.value = null
    batchTreeKey.value = []
  } else {
    await relationViewGrant({ department, user }, contextMenuKey.value as string, (_result: any[]) => {
      result.push(..._result)
    })
  }
  if (result.every((r) => r.status === 'fulfilled')) {
    message.success(t('operateSuccess'))
  }
}

async function relationViewGrant(
  { department, user }: { department: any[]; user: any[] },
  nodeKey: string,
  callback: (result: any[]) => void
) {
  const needGrantNodes = nodeKey
    .split('@^@')
    .filter((item) => !!item)
    .reverse()

  const needGrantRids = [...department, ...user]
  const floor = Math.ceil(needGrantRids.length / 6)
  const result: any[] = []
  for (let i = 0; i < needGrantNodes.length; i++) {
    const grantNode = needGrantNodes[i]
    const _grantNode = grantNode.split('%')
    const ciId = _grantNode[0]
    const typeId = _grantNode[1]
    const uniqueValue = Object.entries(JSON.parse(_grantNode[2]))[0][1]
    const parent_path = needGrantNodes
      .slice(i + 1)
      .map((item) => {
        return Number(item.split('%')[0])
      })
      .reverse()
      .join(',')
    for (let j = 0; j < floor; j++) {
      const itemList = needGrantRids.slice(6 * j, 6 * j + 6)
      const promises = itemList.map((rid) =>
        grantCiType(typeId, rid, {
          id_filter: { [ciId]: { name: uniqueValue, parent_path } },
          is_recursive: Number(i > 0),
        })
      )
      const _result = await Promise.allSettled(promises)
      result.push(..._result)
    }
  }
  callback(result)
}

function clickCheckbox(treeKey: string) {
  const _idx = batchTreeKey.value.findIndex((item) => item === treeKey)
  if (_idx > -1) {
    batchTreeKey.value.splice(_idx, 1)
  } else {
    batchTreeKey.value.push(treeKey)
  }
}

function batchDeleteCIRelationFromTree() {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete'),
    async onOk() {
      for (let i = 0; i < batchTreeKey.value.length; i++) {
        const { splitTreeKey, _tempTree, ancestor_ids } = calculateParamsFromTreeKey(batchTreeKey.value[i], 'delete')
        const _tempTreeParent = splitTreeKey[splitTreeKey.length - 2].split('%')
        await deleteCIRelationView(_tempTreeParent[0], _tempTree[0], { ancestor_ids })
      }
      message.success(t('deleteSuccess'))
      showBatchLevel.value = null
      batchTreeKey.value = []
      setTimeout(() => {
        reload?.()
      }, 500)
    },
  })
}

async function handleSingleRevoke(
  { users = [], roles = [] }: { users?: any[]; roles?: any[] },
  treeKey: string,
  callback: (result: any[]) => void
) {
  const rids = [...users.map((item: string) => Number(item.split('-')[1])), ...roles]
  const treeKeyPath = treeKey.split('@^@').filter((item) => !!item)
  const _treeKey = treeKeyPath.pop()!.split('%')
  const id_filter: Record<string, any> = {}
  const typeId = _treeKey[1]
  const ciId = _treeKey[0]
  const uniqueValue = Object.entries(JSON.parse(_treeKey[2]))[0][1]

  const parent_path = treeKeyPath
    .map((item) => {
      return Number(item.split('%')[0])
    })
    .join(',')
  id_filter[ciId] = { name: uniqueValue, parent_path }
  const floor = Math.ceil(rids.length / 6)
  const result: any[] = []
  for (let j = 0; j < floor; j++) {
    const itemList = rids.slice(6 * j, 6 * j + 6)
    const promises = itemList.map((rid) => revokeCiType(typeId, rid, { id_filter, perms: ['read'], parent_path }))
    const _result = await Promise.allSettled(promises)
    result.push(..._result)
  }
  callback(result)
}

async function handleRevoke(form: any) {
  const { users = [], roles = [] } = form
  const result: any[] = []
  if (showBatchLevel.value !== null && batchTreeKey.value && batchTreeKey.value.length) {
    for (let i = 0; i < batchTreeKey.value.length; i++) {
      const treeKey = batchTreeKey.value[i]
      await handleSingleRevoke({ users, roles }, treeKey, (_result: any[]) => {
        result.push(..._result)
      })
    }
  } else {
    await handleSingleRevoke({ users, roles }, contextMenuKey.value as string, (_result: any[]) => {
      result.push(..._result)
    })
  }
  if (result.every((r) => r.status === 'fulfilled')) {
    message.success(t('operateSuccess'))
  }
  showBatchLevel.value = null
  batchTreeKey.value = []
}

function findNode(node: any[], target: string | number): any {
  for (let i = 0; i < node.length; i++) {
    if (node[i].id === target) {
      return node[i]
    }
    if (node[i].children && node[i].children.length) {
      const found = findNode(node[i].children, target)
      if (found) {
        return found
      }
    }
  }
  return null
}

function updateTreeData(ciId: number, value: string) {
  const _find = findNode(treeData.value, ciId)
  if (_find) {
    _find.title = value
  }
  refreshTable()
}

function handleSearchFull(e: Event) {
  const value = (e.target as HTMLInputElement).value
  treeKeys.value = []
  expandedKeys.value = []
  if (!value) {
    reload?.()
    return
  }
  if (isFullSearch.value) {
    calcFilterFullTreeData()
    return
  }
  searchCIRelationFull({
    ...loadRootStatisticsParams.value,
    type_ids: topo_flatten.value.join(','),
  }).then((res: any) => {
    isFullSearch.value = true
    fullTreeData.value = formatTreeData(res)
    calcFilterFullTreeData()
  })
}

function calcFilterFullTreeData() {
  const _expandedKeys: string[] = []
  const predicateCiIds: any[] = []
  const filterTree = (node: any, predicate: (node: any) => boolean): boolean => {
    if (predicate(node)) {
      predicateCiIds.push(node.id)
      return true
    }
    if (node.children) {
      node.children = node.children.filter((child: any) => {
        if (
          predicateCiIds.some(
            (id) =>
              child.key
                .split('@^@')
                .map((item: string) => Number(item.split('%')[0]))
                .indexOf(id) > -1
          )
        ) {
          return true
        }
        return filterTree(child, predicate)
      })
      if (
        node.children.length &&
        !predicateCiIds.some(
          (id) =>
            node.key
              .split('@^@')
              .map((item: string) => Number(item.split('%')[0]))
              .indexOf(id) > -1
        )
      ) {
        _expandedKeys.push(node.key)
      }
      return node.children.length > 0
    }
    return false
  }
  const predicate = (node: any) => String(node.title).toLowerCase().includes(fullSearchValue.value.toLowerCase())
  const _fullTreeData = cloneDeep(fullTreeData.value)
  filterFullTreeData.value = _fullTreeData.filter((item) => filterTree(item, predicate))
  if (filterFullTreeData.value && filterFullTreeData.value.length) {
    onNodeClick(filterFullTreeData.value[0].key, () => {
      expandedKeys.value = _expandedKeys
    })
  } else {
    treeKeys.value = []
    instanceList.value = []
  }
}

function formatTreeData(array: any[], parentKey = ''): any[] {
  array.forEach((item) => {
    const showName = relationViews.value.id2type[item.type_id]?.show_name ?? null
    const uniqueName = relationViews.value.id2type[item.type_id]?.unique_name ?? null
    const keyList = parentKey.split('@^@').filter((item) => !!item)
    keyList.push(item.id + '%' + item.type_id + '%' + `{"${uniqueName}":"${item.uniqueValue}"}`)
    const key = keyList.join('@^@')
    item.key = key
    item.showName = showName
    if (!item.isLeaf && item.children && item.children.length) {
      item.children = formatTreeData(item.children, key)
    }
  })
  return array
}

function openDetail(id: any, activeTabKey?: string, _ciDetailRelationKey?: string) {
  detailRef.value?.create(id, activeTabKey || 'tab_1')
}

function clickRelationViewMenu(id: number) {
  if (id) {
    localStorage.setItem(relationViewKeyStorage, String(id))
    reload?.()
  }
}

watch(pageNo, (newPage) => {
  loadData({ parameter: { pageNo: newPage }, sortByTable: sortByTable.value })
})

onMounted(() => {
  getRelationViews()
  getCITypesList()
})
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order, vue/v-on-event-hyphenation -->
  <div :style="{ marginBottom: '-24px', overflow: 'hidden' }">
    <div v-if="relationViews.name2id && relationViews.name2id.length" class="relation-views-wrapper">
      <SplitPane
        :min="200"
        :max="500"
        v-model:pane-length-pixel="paneLengthPixel"
        :app-name="`cmdb-relation-views-${viewId}`"
        :trigger-length="18"
        calc-based-parent
      >
        <template #one>
          <div class="relation-views-left" :style="{ height: `${windowHeight - 64}px` }">
            <div class="relation-views-left-header">
              <div class="relation-views-left-header-icon">
                <SearchOutlined />
              </div>

              <div class="relation-views-left-header-name relation-views-text-scroll">
                <span>{{ viewName }}</span>
              </div>

              <a-dropdown overlay-class-name="relation-views-left-header-dropdown">
                <div class="relation-views-left-header-down">
                  <SearchOutlined />
                </div>
                <template #overlay>
                  <a-menu :selected-keys="[String(viewId)]" class="relation-views-left-header-menu">
                    <a-menu-item
                      v-for="item in relationViewMenu"
                      :key="item.id"
                      @click="clickRelationViewMenu(item.id)"
                    >
                      <a class="relation-views-left-header-menu-item">
                        <div class="relation-views-left-header-menu-name relation-views-text-scroll">
                          <span>{{ item.name }}</span>
                        </div>
                        <UserAddOutlined class="relation-views-left-header-menu-grant" @click.stop="handlePerm(item.name)" />
                      </a>
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </div>
            <a-input
              :placeholder="t('cmdb.serviceTree.searchTips')"
              class="relation-views-left-input"
              @press-enter="handleSearchFull"
              v-model:value="fullSearchValue"
            >
              <template #prefix><SearchOutlined /></template>
            </a-input>
            <div
              class="ops-list-batch-action"
              :style="{ marginBottom: '10px' }"
              v-if="showBatchLevel !== null && batchTreeKey && batchTreeKey.length"
            >
              <span @click="() => grantModalRef?.open('depart')">{{ t('grant') }}</span>
              <span @click="() => revokeModalRef?.open()">{{ t('revoke') }}</span>
              <template v-if="showBatchLevel !== null && showBatchLevel > 0">
                <span @click="batchDeleteCIRelationFromTree">{{ t('cmdb.serviceTree.remove') }}</span>
              </template>
              <span
                @click="
                  () => {
                    showBatchLevel = null
                    batchTreeKey = []
                  }
                "
              >
                {{ t('cancel') }}
              </span>
              <span>{{ t('selectRows', { rows: batchTreeKey.length }) }}</span>
            </div>
            <a-tree
              v-if="!isFullSearch"
              :selected-keys="selectedKeys"
              :load-data="onLoadData"
              :tree-data="treeData"
              draggable
              @dragenter="onDragEnter"
              @drop="onDrop"
              :expanded-keys="expandedKeys"
            >
              <template #title="treeNodeData">
                <ContextMenu
                  :tree-node-data="treeNodeData"
                  :levels="levels"
                  :current-views="relationViews.views[viewName ?? '']"
                  :id2type="relationViews.id2type"
                  :ci-type-icons="ciTypeIcons"
                  :show-batch-level="showBatchLevel"
                  :batch-tree-key="batchTreeKey"
                  @on-context-menu-click="onContextMenuClick"
                  @on-node-click="onNodeClick"
                  @click-checkbox="clickCheckbox"
                  @update-tree-data="updateTreeData"
                />
              </template>
            </a-tree>
            <a-tree
              v-else
              :tree-data="filterFullTreeData"
              default-expand-all
              :selected-keys="selectedKeys"
              :expanded-keys="expandedKeys"
            >
              <template #title="treeNodeData">
                <ContextMenu
                  :tree-node-data="treeNodeData"
                  :levels="levels"
                  :current-views="relationViews.views[viewName ?? '']"
                  :id2type="relationViews.id2type"
                  :ci-type-icons="ciTypeIcons"
                  :show-batch-level="showBatchLevel"
                  :batch-tree-key="batchTreeKey"
                  :full-search-value="fullSearchValue"
                  @on-context-menu-click="onContextMenuClick"
                  @on-node-click="onNodeClick"
                  @click-checkbox="clickCheckbox"
                  @update-tree-data="updateTreeData"
                />
              </template>
            </a-tree>
          </div>
        </template>
        <template #two>
          <div id="relation-views-right" class="relation-views-right" :style="{ height: `${windowHeight - 64}px` }">
            <a-tabs :active-key="currentTypeId[0]" class="ops-tab" @change="changeCIType" size="small">
              <a-tab-pane v-for="item in showTypes" :key="item.id">
                <template #tab>{{ item.alias || item.name }}</template>
              </a-tab-pane>
              <template #tabBarExtraContent>
                <a-space>
                  <a-button
                    v-if="isLeaf"
                    type="primary"
                    class="ops-button-ghost"
                    ghost
                    @click="createRef?.handleOpen(true, 'create')"
                  >
                    <template #icon><PlusOutlined /></template>
                    {{ t('create') }}
                  </a-button>
                  <a-button type="primary" ghost @click="handlePerm()" class="ops-button-ghost">
                    <template #icon><UserAddOutlined /></template>
                    {{ t('grant') }}
                  </a-button>
                  <EditAttrsPopover :type-id="Number(currentTypeId[0])" class="operation-icon" @refresh="refreshAfterEditAttrs">
                    <a-button type="primary" ghost class="ops-button-ghost">
                      <template #icon><PlusOutlined /></template>
                      {{ t('cmdb.configTable') }}
                    </a-button>
                  </EditAttrsPopover>
                </a-space>
              </template>
            </a-tabs>
            <SearchForm
              ref="searchRef"
              @refresh="refreshTable"
              :preference-attr-list="preferenceAttrList"
              :is-show-expression="!(isLeaf && isShowBatchIcon)"
              :type-id="Number(currentTypeId[0])"
              @copy-expression="copyExpression"
              type="relationView"
            >
              <PreferenceSearch
                v-if="!(isLeaf && isShowBatchIcon)"
                ref="preferenceSearchRef"
                @get-q-and-sort="getQAndSort"
                @set-params-from-preference-search="setParamsFromPreferenceSearch"
              />
              <template #extraContent>
                <div class="ops-list-batch-action" v-if="isLeaf && isShowBatchIcon">
                  <template v-if="selectedRowKeys.length">
                    <span @click="createRef?.handleOpen(true, 'update')">{{ t('update') }}</span>
                    <span @click="openBatchDownload">{{ t('download') }}</span>
                    <span @click="batchDelete">{{ t('cmdb.ciType.deleteInstance') }}</span>
                    <span @click="batchDeleteCIRelation">{{ t('cmdb.history.deleteRelation') }}</span>
                    <span>{{ t('cmdb.ci.selectRows', { rows: selectedRowKeys.length }) }}</span>
                  </template>
                </div>
              </template>
            </SearchForm>

            <CITable
              ref="xTableRef"
              :id="`cmdb-relation-${viewId}-${currentTypeId}`"
              :loading="loading"
              :attr-list="preferenceAttrList"
              :columns="columns"
              :password-value="passwordValue"
              :data="instanceList"
              :height="tableHeight"
              :show-checkbox="isLeaf"
              :show-delete="isLeaf"
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
                v-model:current="pageNo"
                size="small"
                :total="numfound"
                show-quick-jumper
                :page-size="pageSize"
                :page-size-options="pageSizeOptions"
                @show-size-change="onShowSizeChange"
                :show-total="
                  (total: number, range: number[]) =>
                    t('pagination.total', { range0: range[0], range1: range[1], total })
                "
              >
                <template #buildOptionText="{ value }">
                  <span v-if="value !== '100000'">{{ value }}{{ t('cmdb.history.itemsPerPage') }}</span>
                  <span v-if="value === '100000'">{{ t('cmdb.components.all') }}</span>
                </template>
              </a-pagination>
            </div>
          </div>
        </template>
      </SplitPane>
    </div>
    <a-alert :message="t('noData')" banner v-else-if="relationViews.name2id && !relationViews.name2id.length"></a-alert>
    <AddTableModal ref="addTableModalRef" @reload="reload?.()" />
    <CMDBGrant ref="cmdbGrantRef" resource-type="RelationView" app_id="cmdb" />
    <GrantModal ref="grantModalRef" @handle-ok="onRelationViewGrant" :custom-title="t('cmdb.serviceTree.grantTitle')" />
    <CiDetailDrawer ref="detailRef" :type-id="Number(currentTypeId[0])" />
    <CreateInstanceForm ref="createRef" :type-id-from-relation="Number(currentTypeId[0])" @reload="sumbitFromCreateInstance" @submit="batchUpdateFromCreateInstance" />
    <BatchDownload ref="batchDownloadRef" @batch-download="batchDownload" />
    <ReadPermissionsModal ref="readPermissionsModalRef" />
    <RevokeModal ref="revokeModalRef" @handle-revoke="handleRevoke" />
  </div>
</template>

<style lang="less">
.relation-views-wrapper {
  width: 100%;
  .relation-views-left {
    width: 100%;
    float: left;
    position: relative;
    overflow: hidden;
    padding: 12px 8px;
    background-color: #f7f8fa;
    border-right: 1px solid #e8eaed;
    &:hover {
      overflow: auto;
    }
    .relation-views-left-header {
      display: flex;
      align-items: center;
      max-width: 100%;
      overflow: hidden;
      padding-bottom: 12px;
      border-bottom: @border-color-base;
      margin-bottom: 14px;

      &-icon {
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        border-radius: 22px;
        background-color: @primary-color;

        :deep(.anticon) {
          font-size: 12px;
          color: #ffffff;
        }
      }

      &-name {
        margin-left: 9px;

        span {
          font-size: 17px;
          font-weight: 700;
          color: @primary-color;
        }
      }

      &-down {
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        border-radius: 1px;
        background-color: @primary-color_3;
        cursor: pointer;
        margin-left: auto;

        :deep(.anticon) {
          font-size: 18px;
          color: @primary-color;
        }

        &:hover {
          background-color: @primary-color_4;
        }
      }
    }
    .ant-tree li {
      padding: 2px 0;
    }
    .ant-tree-switcher {
      display: none;
    }
    .ant-tree-node-content-wrapper {
      width: 100%;
      padding: 6px 8px;
      display: inline-block;
      height: 100%;
      border-radius: 6px;
      transition: all 0.2s ease;

      &:hover {
        background-color: @primary-color_7;
        transform: translateX(2px);
      }

      &.ant-tree-node-selected {
        background-color: @primary-color_6;

        .ant-tree-title {
          color: @primary-color;
          font-weight: 600;
        }
      }
      .ant-tree-title {
        display: inline-block;
        width: 100%;
        padding: 0 4px;
      }
    }
    .relation-views-left-input {
      margin-bottom: 12px;

      .ant-input {
        background-color: #fff;
        border-radius: 6px;
        border: 1px solid #e8eaed;
        transition: all 0.2s ease;

        &:hover {
          border-color: #c3cdd7;
        }

        &:focus {
          border-color: @primary-color;
          box-shadow: 0 0 0 2px fade(@primary-color, 10%);
        }
      }

      .ant-input-prefix {
        color: @text-color_3;
      }
    }
  }
  .relation-views-right {
    width: 100%;
    overflow: auto;
    background-color: #fff;
    padding: 20px;
    border-radius: @border-radius-box;

    .ant-tabs-tab {
      padding-top: 0px;
    }
  }
}

.relation-views-left-header-dropdown {
  background-color: #ffffff;

  .relation-views-left-header-menu {
    box-shadow: none;
    max-height: 400px;
    min-height: 150px;
    overflow-y: auto;
    overflow-x: hidden;

    &-item {
      width: 150px;
      overflow: hidden;
      display: flex !important;
      align-items: center;

      &:hover {
        .relation-views-left-header-menu-grant {
          display: inline-block;
        }
      }
    }

    &-name {
      margin-right: 8px;
    }

    &-grant {
      margin-left: 8px;
      flex-shrink: 0;
      font-size: 12px;
      display: none;
      margin-left: auto;
      color: @text-color_4;

      &:hover {
        color: @primary-color;
      }
    }
  }
}

.relation-views-text-scroll {
  max-width: 100%;
  overflow: hidden;

  & > span {
    display: block;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    text-wrap: nowrap;
  }

  &:hover {
    & > span {
      overflow: visible;
      animation: scroll-left 3s linear infinite;
    }
  }

  @keyframes scroll-left {
    0% {
      transform: translateX(0);
    }
    100% {
      transform: translateX(-100%);
    }
  }
}
</style>
