<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  PlusOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  UserAddOutlined,
  MenuOutlined,
  SearchOutlined,
  PlayCircleOutlined,
  HolderOutlined,
} from '@ant-design/icons-vue'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import emptyImage from '@/assets/data_empty.png'
import SplitPane from '@/components/SplitPane/SplitPane.vue'
import { roleHasPermissionToGrant } from '@/modules/acl/api/permission'
import { searchResourceType } from '@/modules/acl/api/resource'
import CMDBGrant from '@/modules/cmdb/components/cmdbGrant/index.vue'
import {
  getTopoGroups,
  postTopoGroup,
  putTopoGroupByGId,
  putTopoGroupsOrder,
  deleteTopoGroup,
  getTopoView,
  addTopoView,
  updateTopoView,
  deleteTopoView,
  getRelationsByTypeId as getRelationsByTypeIdApi,
  previewTopoView,
  showTopoView as showTopoViewApi,
} from '@/modules/cmdb/api/topology'
import CMDBExprDrawer from '@/components/CMDBExprDrawer/index.vue'
import CMDBTypeSelectAntd from '@/modules/cmdb/components/cmdbTypeSelect/cmdbTypeSelectAntd.vue'
import { useUserStore } from '@/stores/user'
import draggable from 'vuedraggable'
import RelationGraphComponent from 'relation-graph/vue3'
import type { RGOptions } from 'relation-graph/vue3'
import { getSubscribeAttributes } from '@/modules/cmdb/api/preference'
import { searchCI } from '@/modules/cmdb/api/ci'

// relation-graph ships VueElement-style type declarations that vue-tsc cannot use to
// infer scoped-slot prop types; cast the component so `node` slot props and event
// handlers are treated as loosely-typed in the template.
const RelationGraph = RelationGraphComponent as any

const currentTopoKey = 'ops_cmdb_topo_currentId'

const { t } = useI18n()
const userStore = useUserStore()

const cmdbDrawerRef = ref<InstanceType<typeof CMDBExprDrawer>>()
const cmdbGrantRef = ref<InstanceType<typeof CMDBGrant>>()
const formRef = ref()

const paneLengthPixel = ref(250)
const loading = ref(false)
const searchValue = ref('')

const currentId = ref<string | null>(null)
const topoGroups = ref<any[]>([])
const CITypeId = ref<number | null>(null)

const startId = ref<number | null>(null)
const endId = ref<number | null>(null)
const addId = ref<number | null>(null)
const addGroup = ref<any>(null)

const modalTitle = ref(t('cmdb.ciType.addGroup'))
const modalVisible = ref(false)
const editingGroup = ref<any>({})
const editingInput = ref('')

const resource_type = ref<Record<string, any>>({})

const drawerVisible = ref(false)
const drawerTitle = ref('')
const selectGroup = ref<any>({})

const isShowPreview = ref(false)

const checkedNodes = ref<string[]>([])
const nodes = ref<any[]>([])

const currentNodes = ref<any[]>([])
const isShowNodeTipsPanel = ref(false)

const errorMessageShow = ref(false)

const topoViewJsonData = ref<any>({})
const topoViewOption = ref<Record<string, any>>({})
const topoViewSearchValue = ref('')

// --- relation-graph canvas state ---
const showTopoViewRef = ref<any>()
const previewTopoViewRef = ref<any>()
const ciTypeRelationGraphRef = ref<any>()

const currentNode = ref<any>({})
const currentNodeValues = ref<Record<string, any> | null>(null)
const currentNodeAttributes = ref<any[]>([])
const nodeTipsPosition = ref<Record<string, string>>({})
const errorMessage = ref('')

const nodeStyle: Record<string, { backgroundColor: string }> = {
  '0': { backgroundColor: '#2F54EB' },
  '1': { backgroundColor: '#29AAE1' },
  '2': { backgroundColor: '#7F97FA' },
  '3': { backgroundColor: '#75C5CA' },
  '4': { backgroundColor: '#A699F6' },
  '5': { backgroundColor: '#A4B5E1' },
}

const graphOptions: RGOptions = {
  allowShowMiniToolBar: false,
  defaultFocusRootNode: false,
  defaultNodeColor: 'rgba(230, 247, 255, 1)',
  defaultNodeFontColor: 'rgba(33, 32, 32, 1)',
  layouts: [{ layoutName: 'tree' }],
}

const graphOptions2: RGOptions = {
  backgrounImageNoRepeat: true,
  moveToCenterWhenRefresh: true,
  zoomToFitWhenRefresh: true,
  useAnimationWhenExpanded: false,
  defaultNodeShape: 1,
  defaultLineShape: 4,
  defaultNodeBorderWidth: 0,
  defaultNodeWidth: 150,
  defaultNodeHeight: 30,
  defaultExpandHolderPosition: 'right',
  defaultJunctionPoint: 'border',
  layouts: [
    {
      layoutName: 'tree',
      from: 'left',
      max_per_width: 200,
      min_per_height: 40,
    },
  ],
}

const graphOptionsPreview: RGOptions = {
  ...graphOptions2,
  toolBarDirection: 'h',
  toolBarPositionH: 'left',
  toolBarPositionV: 'top',
}

const formModel = reactive<{
  id?: number
  name?: string
  central_node_type?: number
  central_node_instances?: string
  aggregation_count?: number
}>({
  id: undefined,
  name: undefined,
  central_node_type: undefined,
  central_node_instances: undefined,
  aggregation_count: undefined,
})

const rules = {
  name: [{ required: true, message: t('cmdb.topo.inputNameTips') }],
  central_node_type: [{ required: true, message: t('cmdb.topo.typeRequired') }],
  central_node_instances: [{ required: true, message: t('cmdb.topo.instancesRequired') }],
}

const permissions = computed<string[]>(() => (userStore.roles?.permissions ?? []).map((p: any) => p.name))
const windowHeight = computed(() => window.innerHeight)
const currentGId = computed(() => {
  if (currentId.value) {
    return Number(currentId.value.split('%')[0])
  }
  return null
})
const currentCId = computed(() => {
  if (currentId.value) {
    if (currentId.value.split('%')[1] !== 'null') {
      return Number(currentId.value.split('%')[1])
    }
    return null
  }
  return null
})
const computedTopoGroups = computed(() => {
  if (searchValue.value) {
    const groups = cloneDeep(topoGroups.value)
    groups.forEach((item: any) => {
      item.views = item.views.filter((_item: any) =>
        _item.name.toLowerCase().includes(searchValue.value.toLowerCase())
      )
    })
    return groups
  }
  return topoGroups.value
})

function closeNodeTips() {
  if (isShowNodeTipsPanel.value === true) {
    isShowNodeTipsPanel.value = false
  }
  if (errorMessageShow.value === true) {
    errorMessageShow.value = false
  }
}

function handleClickAddGroup() {
  editingGroup.value = {}
  editingInput.value = ''
  modalTitle.value = t('cmdb.ciType.addGroup')
  modalVisible.value = true
}

function handleClickGroup(gId: number) {
  currentId.value = null
  nextTick(() => {
    currentId.value = `${gId}%null%null`
    localStorage.setItem(currentTopoKey, currentId.value)
  })
}

function handleClickView(gId: number, viewId: number, viewName: string) {
  currentId.value = null
  nextTick(() => {
    currentId.value = `${gId}%${viewId}%${viewName}`
    localStorage.setItem(currentTopoKey, currentId.value)
    showTopoView(viewId)
  })
}

function handleEditGroup(g: any) {
  editingGroup.value = g
  editingInput.value = g.name
  modalTitle.value = t('cmdb.ciType.editGroup')
  modalVisible.value = true
}

function handleDeleteGroup(g: any) {
  if (g.views && g.views.length > 0) {
    message.error(t('cmdb.ciType.cannotDeleteGroupTips'))
    return
  }
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ciType.confirmDeleteGroup', { groupName: `${g.name}` }),
    onOk() {
      deleteTopoGroup(g.id).then(() => {
        message.success(t('deleteSuccess'))
        loadTopoViews(true)
      })
    },
  })
}

function start(g: any) {
  startId.value = g.id
}

function end(g: any) {
  endId.value = g.id
  let groupId: number | null = null
  const payload: Record<string, any> = {}
  if (startId.value === g.id && g.id && addId.value) {
    groupId = addGroup.value.id
    payload.name = addGroup.value.name
    payload.view_ids = addGroup.value.views.map((i: any) => i.id)
  }
  if (startId.value === g.id && g.id && !addId.value) {
    groupId = g.id
    payload.name = g.name
    payload.view_ids = g.views.map((i: any) => i.id)
  }
  if (groupId) {
    putTopoGroupByGId(groupId, { view_ids: payload.view_ids })
      .then(() => {
        message.success(t('saveSuccess'))
      })
      .catch(() => {
        loadTopoViews(!currentId.value)
      })
      .finally(() => {
        startId.value = null
        endId.value = null
        addId.value = null
      })
  }
}

function add(g: any) {
  addId.value = g.id
  addGroup.value = cloneDeep(g)
}

function handleChangeGroups() {
  putTopoGroupsOrder({ group_ids: topoGroups.value.filter((c: any) => c.id).map((c: any) => c.id) })
    .then(() => {
      message.success(t('saveSuccess'))
    })
    .catch(() => {
      loadTopoViews(!currentId.value)
    })
}

async function loadTopoViews(isResetCurrentId = false) {
  const groups = await getTopoGroups()
  let alreadyReset = false
  if (isResetCurrentId) {
    currentId.value = null
  }
  nextTick(() => {
    groups.forEach((g: any) => {
      if (isResetCurrentId && !alreadyReset && g.views && g.views.length) {
        currentId.value = `${g.id}%${g.views[0].id}%${g.views[0].name}`
        alreadyReset = true
      }
      if (!g.views) {
        g.views = []
      }
    })
    topoGroups.value = groups
    localStorage.setItem(currentTopoKey, currentId.value ?? '')
  })
}

async function handleSubmitEditGroup() {
  if (editingGroup.value && editingGroup.value.id) {
    await putTopoGroupByGId(editingGroup.value.id, {
      name: editingInput.value,
      view_ids: editingGroup.value.views.map((i: any) => i.id),
    })
    message.success(t('updateSuccess'))
  } else {
    const { id } = await postTopoGroup({ name: editingInput.value })
    currentId.value = `${id}%null%null`
    message.success(t('addSuccess'))
  }
  modalVisible.value = false
  loadTopoViews()
}

function handleCreate(g: any) {
  drawerTitle.value = t('cmdb.topo.addTopoView')
  drawerVisible.value = true
  selectGroup.value = g
}

function handleCreateViewFromEmpty() {
  drawerTitle.value = t('cmdb.topo.addTopoView')
  drawerVisible.value = true
  const _find = topoGroups.value.find((item) => item.id === currentGId.value)
  selectGroup.value = _find
}

async function handleSubmit() {
  formRef.value
    .validate()
    .then(async () => {
      const { name, central_node_type, central_node_instances, aggregation_count } = formModel
      const payload: Record<string, any> = { name, central_node_type, central_node_instances }
      if (aggregation_count) {
        payload.option = { aggregation_count }
      } else {
        payload.option = {}
      }
      if (selectGroup.value && selectGroup.value.id) {
        payload.group_id = selectGroup.value.id
      }
      payload.path = wrapPath()
      loading.value = true
      if (formModel.id) {
        await updateTopoView(formModel.id, payload).then((res: any) => {
          const { id } = res
          currentId.value = `${selectGroup.value?.id || ''}%${id}%${payload.name}`
          showTopoView(id)
        })
      } else {
        if (!payload.group_id) {
          message.error(t('cmdb.topo.groupRequired'))
          loading.value = false
          return
        }
        await addTopoView(payload).then((res: any) => {
          const { id } = res
          currentId.value = `${selectGroup.value?.id || ''}%${id}%${payload.name}`
          showTopoView(id)
        })
      }
      localStorage.setItem(currentTopoKey, currentId.value ?? '')
      setTimeout(() => {
        loadTopoViews()
      }, 2000)
      drawerVisible.value = false
    })
    .catch(() => {})
  loading.value = false
}

function wrapPath() {
  const path: Record<string, string[]> = {}
  checkedNodes.value.forEach((nodeId) => {
    const _nodes = nodes.value.filter((i) => String(i.id) === nodeId)
    _nodes.forEach((_node) => {
      const levels = _node.level || [0]
      levels.forEach((level: number) => {
        if (level in path) {
          path[level].push(nodeId)
        } else {
          path[level] = [nodeId]
        }
      })
    })
  })
  return path
}

function onClose() {
  formRef.value?.resetFields()
  drawerVisible.value = false
}

function showPreview() {
  isShowPreview.value = true
  formRef.value
    .validate()
    .then(async () => {
      const payload = {
        central_node_type: formModel.central_node_type,
        central_node_instances: formModel.central_node_instances,
        path: wrapPath(),
      }
      previewTopoView(payload).then((res) => {
        const nodes: any[] = []
        const links: any[] = []
        res.links.forEach((item: any) => {
          links.push({
            from: `${item.from}`,
            to: `${item.to}`,
            disableDefaultClickEffect: true,
          })
        })
        const type2meta = res?.type2meta
        res.nodes.forEach((item: any) => {
          const icon = type2meta?.[item?.type_id] || ''
          nodes.push({
            id: `${item.id}`,
            text: item.name,
            data: { icon },
          })
        })
        if (!nodes.length) {
          message.error(t('cmdb.topo.noData'))
          return
        }
        nextTick(() => {
          previewTopoViewRef.value?.setJsonData({ nodes, lines: links })
        })
      })
    })
    .catch(() => {})
}

async function showTopoView(viewId: number | string) {
  if (viewId === 'null' || !viewId) {
    return
  }
  const topoViewRes = await getTopoView(viewId)
  if (topoViewRes?.option) {
    topoViewOption.value = topoViewRes.option
  }
  showTopoViewApi(viewId).then(async (res) => {
    const nodes: any[] = []
    const links: any[] = []
    currentNodes.value = res.nodes
    const seenLinks = new Set()
    res.links.forEach((item: any) => {
      const from = `${item.from}`
      const to = `${item.to}`
      if (!from || !to || from === to) {
        return
      }
      const linkKey = from < to ? `${from}->${to}` : `${to}->${from}`
      if (seenLinks.has(linkKey)) {
        return
      }
      seenLinks.add(linkKey)
      links.push({ from, to })
    })
    const type2meta = res?.type2meta
    const nodeIds = new Set()
    res.nodes.forEach((item: any) => {
      const id = `${item.id}`
      if (nodeIds.has(id)) {
        return
      }
      nodeIds.add(id)
      const icon = type2meta?.[item?.type_id] || ''
      nodes.push({ id, text: item.name, data: { icon } })
    })
    if (!nodes.length) {
      message.error(t('cmdb.topo.noData'))
      return
    }
    topoViewJsonData.value = { nodes: new Map(nodes.map((n) => [n.id, n])), lines: links }
    topoViewSearchValue.value = ''
    nextTick(() => {
      showTopoViewRef.value?.setJsonData({ nodes, lines: links })
    })
  })
}

function handleOpenCmdb() {
  cmdbDrawerRef.value?.open()
}

function copySuccess(text: string) {
  formModel.central_node_instances = `${text}`
}

async function CITypeChange(value: number) {
  CITypeId.value = value
  formModel.central_node_instances = ''
  checkedNodes.value = [String(value)]
  getRelationsByTypeId(value)
}

function handlePerm(v: any) {
  roleHasPermissionToGrant({
    app_id: 'cmdb',
    resource_type_name: 'TopologyView',
    perm: 'grant',
    resource_name: v.name,
  }).then((res: any) => {
    if (res.result) {
      cmdbGrantRef.value?.open({ name: v.name, cmdbGrantType: 'TopologyView', CITypeId: v.id })
    } else {
      message.error(t('noPermission'))
    }
  })
}

async function handleEdit(record: any) {
  drawerTitle.value = t('cmdb.topo.editTopoView')
  drawerVisible.value = true
  await getTopoView(record.id)
  nextTick(() => {
    formModel.id = record.id
    formModel.name = record.name
    formModel.central_node_type = record.central_node_type
    formModel.central_node_instances = record.central_node_instances
    formModel.aggregation_count = record.option?.aggregation_count
  })
  const nextCheckedNodes: string[] = []
  Object.values(record.path).forEach((item: any) => {
    nextCheckedNodes.push(...item)
  })
  checkedNodes.value = Array.from(new Set(nextCheckedNodes))
  await getRelationsByTypeId(record.central_node_type)
  CITypeId.value = record.central_node_type
}

function handleDelete(record: any) {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.topo.confirmDeleteView', { viewName: `${record.name}` }),
    onOk() {
      deleteTopoView(record.id).then(() => {
        message.success(t('deleteSuccess'))
        loadTopoViews(true)
      })
    },
  })
}

async function getRelationsByTypeId(typeId: number) {
  getRelationsByTypeIdApi(typeId).then((res) => {
    const pathNodes: any[] = []
    const pathLines: any[] = []
    nodes.value = res.nodes
    ;(res.edges || []).forEach((item: any) => {
      pathLines.push({
        from: `${item.from_id}`,
        to: `${item.to_id}`,
        text: `${item.text}`,
        disableDefaultClickEffect: true,
      })
    })
    ;(res.nodes || []).forEach((item: any) => {
      pathNodes.push({
        id: `${item.id}`,
        text: item.alias || item.name,
        nodeShape: 1,
        borderWidth: -1,
        disableDefaultClickEffect: true,
      })
    })
    if (!pathNodes.length) {
      message.error(t('cmdb.topo.noData'))
      return
    }
    nextTick(() => {
      ciTypeRelationGraphRef.value?.setJsonData({ rootId: `${typeId}`, nodes: pathNodes, lines: pathLines })
    })
  })
}

function checked(e: any, node: any) {
  if (e.target.checked) {
    if (checkedNodes.value.findIndex((i) => i === node.id) === -1) {
      checkedNodes.value.push(node.id)
    }
  } else {
    const idx = checkedNodes.value.findIndex((i) => i === node.id)
    if (idx > -1) {
      checkedNodes.value.splice(idx, 1)
    }
  }
}

function nodeBorderColor(node: any): string {
  if (node?.data?.btnType === 'more') return '#A4B5E1'
  const level = Math.abs(node?.lot?.level ?? 0)
  return nodeStyle[level]?.backgroundColor ?? '#A4B5E1'
}

function handleNullNodeTips(errorMsg: string) {
  errorMessage.value = errorMsg
  errorMessageShow.value = true
  currentNodeValues.value = null
  isShowNodeTipsPanel.value = false
  currentNode.value = {}
}

async function showNodeTips(nodeObject: any, event: any) {
  event.preventDefault?.()
  event.stopPropagation?.()

  if (currentNode.value !== nodeObject) {
    currentNodeValues.value = null
    errorMessageShow.value = false
    currentNode.value = nodeObject
    const rawNode = currentNodes.value.find((item: any) => item.id === nodeObject.id)
    if (rawNode) {
      try {
        const [attributes] = await Promise.all([getSubscribeAttributes(rawNode.type_id)])
        currentNodeAttributes.value = attributes?.attributes || []
        if (!currentNodeAttributes.value.length) {
          handleNullNodeTips(t('cmdb.topo.noPreferenceAttributes'))
          return
        }
        const res = await searchCI({ q: `_id:${rawNode.id}` })
        if (!res.result?.length) {
          handleNullNodeTips(t('cmdb.topo.noInstancePerm'))
        } else {
          const values = res.result[0]
          Object.keys(values).forEach((key) => {
            const attr = currentNodeAttributes.value.find((a: any) => a.name === key)
            if (attr?.choice_value?.length) {
              if (Array.isArray(values[key])) {
                values[key] = values[key].map((value: any) => {
                  const choice = attr.choice_value.find((c: any) => value === c?.[0])
                  return choice?.[1]?.label || value
                })
              } else {
                const choice = attr.choice_value.find((c: any) => values[key] === c?.[0])
                values[key] = choice?.[1]?.label || values[key]
              }
            }
          })
          currentNodeValues.value = values
        }
      } catch (error: any) {
        handleNullNodeTips((error?.response?.data || {}).message || String(error))
      }
    }
  }

  nodeTipsPosition.value = {
    top: '20px',
    right: '20px',
    maxHeight: `${windowHeight.value / 2 - 100}px`,
  }
  isShowNodeTipsPanel.value = true
}

function handleSearchTopoView(v: string) {
  const jsonData = topoViewJsonData.value
  if (!jsonData?.nodes) return
  jsonData.nodes.forEach((node: any) => {
    if (node?.data?.btnType !== 'more') {
      node.opacity = (node?.text ?? '').indexOf(v) !== -1 ? 1 : 0.1
    }
  })
  showTopoViewRef.value?.setJsonData({ nodes: Array.from(jsonData.nodes.values()), lines: jsonData.lines })
}

onMounted(async () => {
  searchResourceType({ page_size: 9999, app_id: 'cmdb' }).then((res: any) => {
    resource_type.value = { groups: res.groups, id2perms: res.id2perms }
  })
  const _currentId = localStorage.getItem(currentTopoKey)
  if (_currentId) {
    currentId.value = _currentId
  }
  await loadTopoViews(!_currentId)
  if (currentId.value) {
    showTopoView(currentId.value.split('%')[1])
  }
})
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <div class="topo-wrap" :style="{ height: `${windowHeight - 96}px` }" @click="closeNodeTips">
    <div v-if="!topoGroups.length" class="topo-empty">
      <a-empty :image="emptyImage" description=""></a-empty>
      <a-button type="primary" size="small" @click="handleClickAddGroup">
        <template #icon><PlusOutlined /></template>
        {{ t('cmdb.ciType.addGroup') }}
      </a-button>
    </div>
    <SplitPane
      v-else
      :min="180"
      :max="300"
      v-model:pane-length-pixel="paneLengthPixel"
      app-name="cmdb-topo-views"
      :trigger-length="18"
      calc-based-parent
    >
      <template #one>
        <a-input
          v-model:value="searchValue"
          :placeholder="t('cmdb.topo.searchPlaceholder')"
          class="cmdb-topo-left-input"
        >
          <template #prefix><SearchOutlined /></template>
        </a-input>
        <div class="topo-left">
          <div class="topo-left-title">
            <a-button
              type="primary"
              size="small"
              ghost
              @click="handleClickAddGroup"
              class="ops-button-ghost"
              v-if="permissions.includes('admin') || permissions.includes('cmdb_admin')"
            >
              <template #icon><PlusOutlined /></template>
              {{ t('cmdb.ciType.group') }}
            </a-button>
          </div>
          <draggable class="topo-left-content" :list="computedTopoGroups" @end="handleChangeGroups" filter=".undraggable">
            <div v-for="group in computedTopoGroups" :key="group.id || group.name">
              <div
                :class="`${currentGId === group.id && !currentCId ? 'selected' : ''} topo-left-group ${
                  group.id === undefined ? 'undraggable' : ''
                }`"
                @click="handleClickGroup(group.id)"
              >
                <div>
                  <HolderOutlined
                    v-if="group.id"
                    style="width: 17px; height: 17px; display: none; position: absolute; left: 5px; top: 13px"
                  />
                  <span class="topo-left-group-name">{{ group.name || t('other') }}</span>
                  <span>{{ group.views.length }}</span>
                </div>
                <div class="topo-left-group-action">
                  <a-tooltip :title="t('cmdb.topo.addTopoViewInGroup')">
                    <a v-if="permissions.includes('admin') || permissions.includes('cmdb_admin')">
                      <PlusOutlined @click="handleCreate(group)" />
                    </a>
                  </a-tooltip>
                  <template v-if="group.id">
                    <a-tooltip :title="t('cmdb.ciType.editGroup')">
                      <a v-if="permissions.includes('admin') || permissions.includes('cmdb_admin')">
                        <EditOutlined @click="handleEditGroup(group)" />
                      </a>
                    </a-tooltip>
                    <a-tooltip :title="t('cmdb.ciType.deleteGroup')">
                      <a
                        v-if="permissions.includes('admin') || permissions.includes('cmdb_admin')"
                        :style="{ color: 'red' }"
                      >
                        <DeleteOutlined @click="handleDeleteGroup(group)" />
                      </a>
                    </a-tooltip>
                  </template>
                </div>
              </div>
              <draggable
                v-model="group.views"
                group="topo"
                :animation="100"
                @start="start(group)"
                @end="end(group)"
                @add="add(group)"
                filter=".undraggable"
              >
                <div
                  v-for="topo in group.views"
                  :key="topo.id"
                  :class="`${currentCId === topo.id ? 'selected' : ''} topo-left-detail`"
                  @click="handleClickView(group.id, topo.id, topo.name)"
                >
                  <div :class="`${group.id === undefined ? 'undraggable' : ''}`">
                    <HolderOutlined
                      v-if="group.id"
                      style="width: 17px; height: 17px; display: none; position: absolute; left: -1px; top: 8px"
                    />
                    <span class="topo-left-detail-icon">
                      <template v-if="topo.icon">
                        <img
                          v-if="topo.icon.split('$$')[2]"
                          :src="`/api/common-setting/v1/file/${topo.icon.split('$$')[3]}`"
                        />
                        <span
                          v-else
                          :style="{ color: topo.icon.split('$$')[1], fontSize: '14px' }"
                        >
                          {{ topo.icon.split('$$')[0] ? topo.icon.split('$$')[0][0].toUpperCase() : '' }}
                        </span>
                      </template>
                      <span class="primary-color" v-else>{{ topo.name[0].toUpperCase() }}</span>
                    </span>
                  </div>
                  <span class="topo-left-detail-title">{{ topo.alias || topo.name }}</span>
                  <a-dropdown>
                    <a class="topo-left-detail-action"><MoreOutlined /></a>
                    <template #overlay>
                      <a-menu>
                        <a-menu-item @click="handlePerm(topo)">
                          <UserAddOutlined />
                          {{ t('grant') }}
                        </a-menu-item>
                        <a-menu-item @click="handleEdit(topo)">
                          <EditOutlined />
                          {{ t('cmdb.topo.edit') }}
                        </a-menu-item>
                        <a-menu-item @click="handleDelete(topo)">
                          <DeleteOutlined />
                          {{ t('cmdb.topo.delete') }}
                        </a-menu-item>
                      </a-menu>
                    </template>
                  </a-dropdown>
                </div>
              </draggable>
            </div>
          </draggable>
        </div>
      </template>
      <template #two>
        <div class="topo-right">
          <div v-if="currentCId" :style="{ height: `${windowHeight - 80}px` }">
            <RelationGraph
              ref="showTopoViewRef"
              :options="graphOptions2"
              :on-node-click="showNodeTips"
            >
              <template #node="{ node }">
                <div class="relation-graph-node" :style="{ borderColor: nodeBorderColor(node) }">
                  <template v-if="node.data && node.data.icon">
                    <img
                      v-if="node.data.icon.split('$$')[2]"
                      :src="`/api/common-setting/v1/file/${node.data.icon.split('$$')[3]}`"
                      class="relation-graph-node-image"
                    />
                    <span
                      v-else
                      class="relation-graph-node-icon"
                      :style="{ color: node.data.icon.split('$$')[1] }"
                    >
                      {{ node.data.icon.split('$$')[0] ? node.data.icon.split('$$')[0][0].toUpperCase() : '' }}
                    </span>
                  </template>
                  <span class="relation-graph-node-text">
                    {{
                      node.data && node.data.btnType === 'more'
                        ? t('cmdb.topo.moreBtn', { count: node.text })
                        : node.text
                    }}
                  </span>
                </div>
              </template>
              <template #graph-plug>
                <a-input-search
                  v-model:value="topoViewSearchValue"
                  class="relation-graph-search"
                  :placeholder="t('cmdb.topo.topoViewSearchPlaceholder')"
                  @search="handleSearchTopoView"
                />
                <div
                  v-if="(isShowNodeTipsPanel && currentNodeValues && currentNodeAttributes.length) || errorMessageShow"
                  class="node-tips"
                  :style="nodeTipsPosition"
                >
                  <a-descriptions
                    v-if="currentNodeValues"
                    bordered
                    size="small"
                    :column="{ xxl: 1, xl: 1, lg: 1, md: 1, sm: 1, xs: 1 }"
                  >
                    <a-descriptions-item v-for="attr in currentNodeAttributes" :key="attr.name" :label="attr.alias">
                      {{ currentNodeValues[attr.name] }}
                    </a-descriptions-item>
                  </a-descriptions>
                  <span v-if="errorMessageShow" style="color: red">{{ errorMessage }}</span>
                </div>
              </template>
            </RelationGraph>
          </div>
          <div v-else class="topo-right-empty">
            <a-empty :image="emptyImage" description=""></a-empty>
            <a-button
              type="primary"
              size="small"
              :disabled="!permissions.includes('admin') && !permissions.includes('cmdb_admin')"
              @click="handleCreateViewFromEmpty"
            >
              <template #icon><PlusOutlined /></template>
              {{ t('cmdb.topo.addTopoView') }}
            </a-button>
          </div>
        </div>
      </template>
    </SplitPane>
    <a-modal v-model:open="modalVisible" :title="modalTitle" @ok="handleSubmitEditGroup">
      <a-form-item :label="t('name')" :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
        <a-input v-model:value="editingInput" />
      </a-form-item>
    </a-modal>
    <CMDBExprDrawer
      ref="cmdbDrawerRef"
      type="resourceView"
      :type-id="CITypeId"
      @copy-success="copySuccess"
    />
    <CMDBGrant ref="cmdbGrantRef" resource-type="TopologyView" app_id="cmdb" />
    <a-drawer
      :open="drawerVisible"
      :title="drawerTitle"
      placement="right"
      width="900px"
      :closable="false"
      :body-style="{ height: 'calc(100vh - 108px)' }"
      @close="onClose"
    >
      <a-form ref="formRef" :model="formModel" :rules="rules" :label-col="{ span: 5 }" :wrapper-col="{ span: 16 }">
        <a-form-item :label="t('cmdb.topo.viewName')" name="name">
          <a-input v-model:value="formModel.name" :placeholder="t('cmdb.topo.viewNamePlaceholder')" />
        </a-form-item>
        <a-form-item :label="t('cmdb.topo.centralNodeType')" name="central_node_type">
          <CMDBTypeSelectAntd
            v-model="formModel.central_node_type"
            :placeholder="t('cmdb.ciType.selectModel')"
            @change="CITypeChange"
          />
          <div class="ant-form-explain">{{ t('cmdb.topo.centralNodeTypeTip') }}</div>
        </a-form-item>
        <a-form-item :label="t('cmdb.topo.filterInstances')" name="central_node_instances">
          <a-input
            v-model:value="formModel.central_node_instances"
            :placeholder="t('cmdb.ciType.selectFromCMDBTips')"
          >
            <template #suffix>
              <a @click="handleOpenCmdb"><MenuOutlined /></a>
            </template>
          </a-input>
          <div class="ant-form-explain">{{ t('cmdb.topo.filterInstancesTip') }}</div>
        </a-form-item>
        <a-form-item :label="t('cmdb.topo.path')" name="path">
          <div :style="{ height: '250px', border: '1px solid #e4e7ed' }">
            <RelationGraph ref="ciTypeRelationGraphRef" :options="graphOptions">
              <template #node="{ node }">
                <div :style="{ lineHeight: '20px' }">
                  <a-checkbox
                    :checked="checkedNodes.includes(node.id)"
                    @change="(e: any) => checked(e, node)"
                  ></a-checkbox>
                  <span :style="{ marginLeft: '5px' }">{{ node.text }}</span>
                </div>
              </template>
            </RelationGraph>
          </div>
        </a-form-item>
        <a-form-item :label="t('cmdb.topo.aggregationCount')" name="aggregation_count" :help="t('cmdb.topo.aggreationCountTip')">
          <a-input-number v-model:value="formModel.aggregation_count" :style="{ width: '100%' }" :min="0" />
        </a-form-item>
        <div :class="{ 'chart-left-preview': true }">
          <span class="chart-left-preview-operation" :style="{ zIndex: '800' }" @click="showPreview">
            <PlayCircleOutlined />
            {{ t('cmdb.custom_dashboard.preview') }}
          </span>
          <template v-if="isShowPreview">
            <RelationGraph ref="previewTopoViewRef" :options="graphOptionsPreview">
              <template #node="{ node }">
                <div class="relation-graph-node" :style="{ borderColor: nodeBorderColor(node) }">
                  <template v-if="node.data && node.data.icon">
                    <img
                      v-if="node.data.icon.split('$$')[2]"
                      :src="`/api/common-setting/v1/file/${node.data.icon.split('$$')[3]}`"
                      class="relation-graph-node-image"
                    />
                    <span
                      v-else
                      class="relation-graph-node-icon"
                      :style="{ color: node.data.icon.split('$$')[1] }"
                    >
                      {{ node.data.icon.split('$$')[0] ? node.data.icon.split('$$')[0][0].toUpperCase() : '' }}
                    </span>
                  </template>
                  <span class="relation-graph-node-text">{{ node.text }}</span>
                </div>
              </template>
            </RelationGraph>
          </template>
        </div>
        <div class="custom-drawer-bottom-action">
          <a-button @click="handleSubmit" :loading="loading" type="primary" style="margin-right: 1rem">{{
            t('confirm')
          }}</a-button>
          <a-button @click="onClose">{{ t('cancel') }}</a-button>
        </div>
      </a-form>
    </a-drawer>
  </div>
</template>

<style lang="less" scoped>
.ant-message {
  z-index: 99999999 !important;
}
.topo-wrap {
  margin: 0 0 -24px 0;
  .topo-empty {
    position: absolute;
    text-align: center;
    left: 50%;
    top: 40%;
    transform: translate(-50%, -50%);
  }

  .topo-left {
    width: 100%;
    height: calc(100% - 28px);
    overflow: auto;
    float: left;
    background-color: #f7f8fa;
    border-right: 1px solid #e8eaed;
    padding: 12px 8px;

    .topo-left-content {
      height: calc(100% - 45px);
      overflow: hidden;
      margin-top: 10px;

      &:hover {
        overflow: auto;
      }
    }
    .topo-left-title {
      padding-bottom: 4px;
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      color: @text-color_3;
    }
    .topo-left-group {
      position: relative;
      padding: 10px 12px 10px 22px;
      margin-bottom: 8px;
      color: @text-color_1;
      cursor: pointer;
      font-size: 15px;
      font-weight: 600;
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      align-items: center;
      border-radius: 6px;
      transition: all 0.2s ease;
      width: 100%;
      overflow: hidden;
      column-gap: 6px;

      > div:first-child {
        display: flex;
        align-items: center;
        gap: 4px;
        max-width: 100%;
        overflow: hidden;

        > span:last-child {
          font-size: 12px;
          font-weight: 500;
          background: #e8eaed;
          color: @text-color_3;
          padding: 2px 6px;
          border-radius: 10px;
        }
      }

      &-name {
        font-weight: 700;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        text-wrap: nowrap;
      }

      &-action {
        align-items: center;
        column-gap: 4px;
        font-size: 14px;
        display: none;
      }

      &:hover {
        background-color: @primary-color_7;
        box-shadow: 0px 2px 8px fade(@primary-color, 15%);

        > div:nth-child(2) {
          display: inline-flex;
        }
        :deep(.anticon) {
          display: inline !important;
        }
      }
    }
    .topo-left-detail {
      padding: 6px 12px 6px 26px;
      margin: 0 4px 6px 4px;
      cursor: pointer;
      position: relative;
      display: flex;
      flex-direction: row;
      justify-content: flex-start;
      align-items: center;
      height: 36px;
      border-radius: 6px;
      transition: all 0.2s ease;

      .topo-left-detail-action {
        display: none;
        margin-left: auto;
        flex-shrink: 0;
        position: relative;
        z-index: 10;
      }

      .topo-left-detail-title {
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        font-size: 14px;
        color: @text-color_1;
        transition: color 0.2s ease;
        flex: 1;
      }

      .topo-left-detail-icon {
        display: inline-flex;
        flex-shrink: 0;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-right: 8px;
        background: #fff;
        border: 1px solid #e8eaed;
        transition: transform 0.2s ease;

        img {
          max-height: 18px;
          max-width: 18px;
        }
      }

      &:hover {
        background-color: @primary-color_7;
        box-shadow: 0px 2px 8px fade(@primary-color, 15%);

        .topo-left-detail-icon {
          transform: scale(1.05);
        }

        :deep(.anticon) {
          display: inline !important;
        }

        .topo-left-detail-action {
          display: inline-flex;
        }
      }
    }
    .selected {
      background-color: @primary-color_6;
      box-shadow: 0 1px 3px fade(@primary-color, 10%);
      position: relative;
      z-index: 1;

      .topo-left-detail-title {
        font-weight: 600;
        color: @primary-color;
      }

      .topo-left-detail-icon {
        box-shadow: 0 2px 4px fade(@primary-color, 20%);
      }
    }
  }
  .topo-right {
    width: 100%;
    position: relative;
    background-color: #fff;
    height: 100%;

    .topo-right-empty {
      position: absolute;
      text-align: center;
      left: 50%;
      top: 40%;
      transform: translate(-50%, -50%);
    }
  }
}
.relation-graph-search {
  position: absolute;
  z-index: 10;
  top: 20px;
  left: 20px;
  width: 300px;
}
.node-tips {
  z-index: 999;
  padding: 16px;
  background-color: #ffffff;
  border: 1px solid #e8eaed;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: absolute;
  overflow: auto;
  max-width: 400px;
  max-height: 500px;
}
.relation-graph-node {
  padding: 6px 3px;
  border-radius: 2px;
  border-width: 2px;
  border-style: solid;
  background-color: transparent;
  display: flex;
  justify-content: center;
  align-items: center;
  &-text {
    color: #000000;
    font-size: 12px;
    font-weight: 400;
    margin-left: 6px;
    word-break: break-all;
  }
  &-icon {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.65);
  }
  &-image {
    max-height: 20px;
    max-width: 20px;
  }
}
.chart-left-preview {
  border: 1px solid #e4e7ed;
  border-radius: 2px;
  height: 280px;
  width: 92%;
  position: relative;
  padding: 12px;
  .chart-left-preview-operation {
    color: #86909c;
    position: absolute;
    top: 12px;
    right: 12px;
    cursor: pointer;
  }
}
</style>

<style lang="less">
.cmdb-topo-left-input {
  margin-bottom: 12px;

  input {
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
</style>
