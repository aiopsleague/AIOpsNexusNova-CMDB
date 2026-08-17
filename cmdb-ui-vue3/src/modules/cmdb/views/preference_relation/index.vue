<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { EditOutlined, CloseOutlined } from '@ant-design/icons-vue'
import { getCITypeRelations } from '@/modules/cmdb/api/CITypeRelation'
import {
  getRelationView,
  deleteRelationView,
  subscribeRelationView,
  putRelationView,
} from '@/modules/cmdb/api/preference'
import { getSystemConfig, saveSystemConfig } from '@/modules/cmdb/api/system_config'
import RelationGraphComponent from 'relation-graph/vue3'
import type { RGOptions } from 'relation-graph/vue3'
import ServiceTreeModal from './serviceTreeModal.vue'

// relation-graph ships VueElement-style type declarations that vue-tsc cannot use to
// infer scoped-slot prop types; cast the component so `node` slot props are treated as
// loosely-typed in the template.
const RelationGraph = RelationGraphComponent as any

const { t } = useI18n()

const isEdit = ref(false)
const relationViews = ref<any>({})
const checkedNodes = ref<any[]>([])
const loading = ref(false)
const graphJsonData = ref<any>({})

const serviceTreeModalRef = ref<InstanceType<typeof ServiceTreeModal>>()

// --- relation-graph canvas state ---
const ciTypeRelationGraphRef = ref<any>()
const relationViewGraphRefs: Record<string, any> = {}
const relationViewGraphData = ref<Record<string, { rootId: string; nodes: any[]; lines: any[] }>>({})
const config = ref<Record<string, any>>({})

const graphOptions = computed<RGOptions>(() => {
  const base: RGOptions = {
    allowShowMiniToolBar: false,
    defaultFocusRootNode: false,
    defaultNodeColor: 'rgba(230, 247, 255, 1)',
    defaultNodeFontColor: 'rgba(33, 32, 32, 1)',
  }
  if (config.value?.option) {
    return { ...base, layouts: [{ layoutName: 'fixed' }] }
  }
  return { ...base, layouts: [{ layoutName: 'center', distance_coefficient: 1 }] }
})

const relationViewOptions: RGOptions = {
  allowShowMiniToolBar: false,
  defaultFocusRootNode: false,
  defaultNodeColor: 'rgba(230, 247, 255, 1)',
  defaultNodeFontColor: 'rgba(33, 32, 32, 1)',
  disableZoom: true,
  layouts: [{ layoutName: 'tree', from: 'left' }],
}

const windowHeight = computed(() => window.innerHeight)

async function getMainData() {
  const { relations: ciTypeRelations } = await getCITypeRelations()
  const nodes: any[] = []
  const lines: any[] = []
  const savedLayout = config.value?.option
  ciTypeRelations.forEach((item: any) => {
    lines.push({
      from: `${item.parent_id}`,
      to: `${item.child_id}`,
      text: item.relation_type.name,
      disableDefaultClickEffect: true,
    })
    if (nodes.findIndex((node: any) => String(node.id) === String(item.child_id)) < 0) {
      const _find = savedLayout ? savedLayout.find((n: any) => n.id === `${item.child_id}`) : undefined
      nodes.push({
        id: `${item.child_id}`,
        text: item.child.alias || item.child.name,
        nodeShape: 1,
        borderWidth: -1,
        disableDefaultClickEffect: true,
        x: _find?.x ?? 500,
        y: _find?.y ?? 500,
      })
    }
    if (nodes.findIndex((node: any) => String(node.id) === String(item.parent_id)) < 0) {
      const _find = savedLayout ? savedLayout.find((n: any) => n.id === `${item.parent_id}`) : undefined
      nodes.push({
        id: `${item.parent_id}`,
        text: item.parent.alias || item.parent.name,
        nodeShape: 1,
        borderWidth: -1,
        disableDefaultClickEffect: true,
        x: _find?.x ?? 500,
        y: _find?.y ?? 500,
      })
    }
  })
  const _from = lines.map((item: any) => item.from)
  const _to = lines.map((item: any) => item.to)
  const rootId = findMost([..._from, _to])
  graphJsonData.value = { rootId, nodes, lines }
  nextTick(() => {
    ciTypeRelationGraphRef.value?.setJsonData({ rootId, nodes, lines })
  })
}

function findMost(arr: string[]) {
  const hash: Record<string, number> = {}
  let maxNum = 0
  let maxEle: string | null = null
  for (let i = 0; i < arr.length; i++) {
    if (hash[arr[i]] === undefined) {
      hash[arr[i]] = 1
    } else {
      hash[arr[i]]++
    }
    if (hash[arr[i]] > maxNum) {
      maxEle = arr[i]
      maxNum = hash[arr[i]]
    }
  }
  return maxEle
}

function checked(e: any, node: any) {
  const graph = ciTypeRelationGraphRef.value?.getInstance?.()
  if (e.target.checked) {
    if (!graph) return
    const currentNode = graph.getNodeById(node.id)
    if (!currentNode.targetTo.length) {
      message.warning(`${node.text} ` + t('cmdb.preference_relation.childNodesNotFound'))
      return
    }
    if (!checkedNodes.value.length) {
      checkedNodes.value.push(node.id)
    } else if (checkedNodes.value.length === 1) {
      const currentCheckedNode = graph.getNodeById(checkedNodes.value[0])
      pushNodeId(currentCheckedNode, currentCheckedNode, node)
    } else {
      const startNode = graph.getNodeById(checkedNodes.value[0])
      const endNode = graph.getNodeById(checkedNodes.value[checkedNodes.value.length - 1])
      pushNodeId(startNode, endNode, node)
    }
  } else {
    const idx = checkedNodes.value.findIndex((item) => item === node.id)
    if (idx > -1) {
      if (checkedNodes.value.slice(0, idx).length >= 2) {
        checkedNodes.value = checkedNodes.value.slice(0, idx)
        return
      }
      if (checkedNodes.value.slice(idx + 1).length >= 2) {
        checkedNodes.value = checkedNodes.value.slice(idx + 1)
        return
      }
      checkedNodes.value = []
    }
  }
}

function pushNodeId(startNode: any, endNode: any, node: any) {
  const idFrom = startNode.targetFrom.findIndex((item: any) => item.id === node.id)
  const idTo = endNode.targetTo.findIndex((item: any) => item.id === node.id)
  if (idFrom <= -1 && idTo <= -1) {
    message.warning(`${node.text} ` + t('cmdb.preference_relation.tips1'))
    return
  }
  if (idFrom > -1) {
    checkedNodes.value.unshift(node.id)
  }
  if (idTo > -1) {
    checkedNodes.value.push(node.id)
  }
}

function setRelationViewGraphRef(viewName: string) {
  return (el: any) => {
    if (el) {
      relationViewGraphRefs[viewName] = el
    } else {
      delete relationViewGraphRefs[viewName]
    }
  }
}

async function getViewsData() {
  loading.value = true
  const data = await getRelationView()
  relationViews.value = data
  const { views } = data || {}
  const nextData: Record<string, { rootId: string; nodes: any[]; lines: any[] }> = {}
  Object.keys(views || {}).forEach((item) => {
    const nodes: any[] = []
    const lines: any[] = []
    const topoFlatten = views[item].topo_flatten || []
    topoFlatten.forEach((nodeId: any, idx: number) => {
      const meta = data.id2type?.[nodeId] || {}
      nodes.push({
        id: `${nodeId}`,
        text: meta.alias || meta.name,
        nodeShape: 1,
        borderWidth: -1,
        disableDefaultClickEffect: true,
      })
      if (idx !== topoFlatten.length - 1) {
        lines.push({ from: `${nodeId}`, to: `${topoFlatten[idx + 1]}` })
      }
    })
    nextData[item] = { rootId: `${topoFlatten[0] || ''}`, nodes, lines }
  })
  relationViewGraphData.value = nextData
  nextTick(() => {
    Object.keys(nextData).forEach((view) => {
      relationViewGraphRefs[view]?.setJsonData(nextData[view])
    })
  })
  loading.value = false
}

function init() {
  getMainData()
  getViewsData()
}

function openServiceTreeModal(treeData: Record<string, any>, type: string) {
  if (type === 'add' && checkedNodes.value.length < 2) {
    message.warning(t('cmdb.preference_relation.tips3'))
    return
  }
  let _treeData = { ...treeData }
  if (type === 'edit') {
    const { name } = _treeData
    _treeData = {
      ...treeData,
      ...(relationViews.value?.views[name]?.option ?? {}),
      is_public: relationViews.value?.views[name]?.is_public ?? true,
    }
  }
  serviceTreeModalRef.value?.open(_treeData, type)
}

async function submitServiceTree(treeData: Record<string, any>, type: string, originName?: string) {
  const { name, is_public, is_show_leaf_node, is_show_tree_node, sort } = treeData
  if (type === 'add') {
    const cr_ids: Array<{ parent_id: number; child_id: number }> = []
    checkedNodes.value.forEach((item, idx) => {
      if (idx !== checkedNodes.value.length - 1) {
        cr_ids.push({ parent_id: Number(item), child_id: Number(checkedNodes.value[idx + 1]) })
      }
    })
    await subscribeRelationView({
      cr_ids,
      name,
      is_public,
      option: { is_show_leaf_node, is_show_tree_node, sort, is_public },
    })
  } else {
    const _name = name === originName ? name : originName
    const topo_flatten = relationViews.value?.views[_name]?.topo_flatten ?? []
    const name2id = relationViews.value?.name2id.find((item: any[]) => item[0] === _name)
    const cr_ids: Array<{ parent_id: number; child_id: number }> = []
    topo_flatten.forEach((item: any, idx: number) => {
      if (idx !== topo_flatten.length - 1) {
        cr_ids.push({ parent_id: Number(item), child_id: Number(topo_flatten[idx + 1]) })
      }
    })
    await putRelationView(name2id?.[1], {
      cr_ids,
      name,
      is_public,
      option: { is_show_leaf_node, is_show_tree_node, sort, is_public },
    })
  }
  resetRoute()
  getViewsData()
  isEdit.value = false
  checkedNodes.value = []
}

async function confirmDelete(viewName: string) {
  await deleteRelationView(viewName)
  getViewsData()
  resetRoute()
}

function resetRoute() {
  // TODO: regenerate dynamic service-tree menu routes (route regeneration not yet wired in the Vue 3 shell).
}

async function handleSave() {
  const graph = ciTypeRelationGraphRef.value?.getInstance?.()
  const graphNodes = graph?.getNodes?.() ?? []
  if (graphNodes && graphNodes.length) {
    await saveSystemConfig({
      name: 'ci_type_relation_layout',
      option: graphNodes.map((item: any) => ({ id: item.id, x: item.x, y: item.y })),
    })
    message.success(t('saveSuccess'))
  }
}

function cancelEdit() {
  isEdit.value = false
  checkedNodes.value = []
}

onMounted(async () => {
  await getSystemConfig({ name: 'ci_type_relation_layout' }).then((res) => {
    config.value = res || {}
  })
  init()
})
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <div class="preference-relation-wrapper">
    <div class="ci-type-relation" :style="{ height: `${windowHeight - 64}px` }">
      <div class="ci-type-relation-header">
        <a-space>
          <a-button v-if="!isEdit" type="primary" size="small" @click="isEdit = true">
            {{ t('cmdb.preference_relation.newServiceTree') }}
          </a-button>
          <template v-else>
            <a-button type="primary" size="small" @click="openServiceTreeModal({}, 'add')">
              {{ t('save') }}
            </a-button>
            <a-button type="primary" size="small" ghost @click="cancelEdit">
              {{ t('cancel') }}
            </a-button>
          </template>
          <a-button size="small" @click="handleSave">{{ t('cmdb.preference_relation.saveLayout') }}</a-button>
          <span>{{ t('cmdb.preference_relation.tips5') }}</span>
        </a-space>
      </div>
      <RelationGraph ref="ciTypeRelationGraphRef" :options="graphOptions">
        <template #node="{ node }">
          <div :style="{ lineHeight: '20px' }">
            <a-checkbox
              v-if="isEdit"
              :checked="checkedNodes.includes(node.id)"
              @change="(e: any) => checked(e, node)"
            ></a-checkbox>
            <span :style="{ marginLeft: '5px' }">{{ node.text }}</span>
          </div>
        </template>
      </RelationGraph>
    </div>
    <template v-if="relationViews.views && !loading">
      <a-row :gutter="4">
        <a-col
          :xl="12"
          :lg="12"
          :md="12"
          :sm="24"
          :xs="24"
          :key="`${view}`"
          v-for="view in Object.keys(relationViews.views)"
        >
          <div class="relation-views">
            <h3 :style="{ padding: '10px 0 0 20px' }">{{ view }}</h3>
            <a class="relation-views-edit" @click="openServiceTreeModal({ name: view }, 'edit')">
              <EditOutlined />
            </a>
            <a-popconfirm :title="t('cmdb.ciType.confirmDelete', { name: `${view}` })" @confirm="confirmDelete(view)">
              <a class="relation-views-close"><CloseOutlined /></a>
            </a-popconfirm>
            <div :style="{ height: '250px' }">
              <RelationGraph :ref="setRelationViewGraphRef(view)" :options="relationViewOptions"></RelationGraph>
            </div>
          </div>
        </a-col>
      </a-row>
    </template>
    <ServiceTreeModal ref="serviceTreeModalRef" @submit-service-tree="submitServiceTree" />
  </div>
</template>

<style lang="less" scoped>
.preference-relation-wrapper {
  overflow: hidden;
  .ci-type-relation {
    background-color: #fff;
    position: relative;
    height: 600px;
    width: 100%;
    .ci-type-relation-header {
      position: absolute;
      top: 20px;
      left: 20px;
      z-index: 10;
    }
  }
  .relation-views {
    background-color: #fff;
    margin-top: 5px;
    position: relative;
    .relation-views-edit,
    .relation-views-close {
      position: absolute;
      z-index: 10;
      right: 60px;
      top: 10px;
    }
    .relation-views-edit {
      right: 46px;
    }
    .relation-views-close {
      right: 20px;
    }
  }
}
</style>
