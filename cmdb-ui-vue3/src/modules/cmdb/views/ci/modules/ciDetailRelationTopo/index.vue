<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import RelationGraphComponent from 'relation-graph/vue3'
import type { RGOptions } from 'relation-graph/vue3'
import { searchCIRelation } from '@/modules/cmdb/api/CIRelation'
import dataEmptyImg from '@/assets/data_empty.png'

// relation-graph ships VueElement-style type declarations that vue-tsc cannot use to
// infer scoped-slot prop types; cast the component so `node` slot props are treated as
// loosely-typed in the template.
const RelationGraph = RelationGraphComponent as any

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    ciId?: number | null
    typeId?: number
    ci?: Record<string, any>
    parentCITypeList?: any[]
    childCITypeList?: any[]
    parentCIList?: any[]
    childCIList?: any[]
  }>(),
  {
    ciId: null,
    typeId: 0,
    ci: () => ({}),
    parentCITypeList: () => [],
    childCITypeList: () => [],
    parentCIList: () => [],
    childCIList: () => [],
  }
)

const emit = defineEmits<{
  (e: 'nodeDblclick', payload: { typeId: number; ciId: number }): void
}>()

const graphRef = ref<any>()
const graphOptions: RGOptions = {
  defaultNodeShape: 1,
  defaultLineShape: 4,
  defaultNodeBorderWidth: 0,
  defaultNodeWidth: 140,
  defaultNodeHeight: 30,
  moveToCenterWhenRefresh: true,
  zoomToFitWhenRefresh: true,
  layouts: [{ layoutName: 'center', distance_coefficient: 1 }],
}

const existingIds = new Set<string>()
let expanding = false

const currentTypeId = computed(() => (props.ci && props.ci._type) || props.typeId || 0)

function buildTypeMap(): Map<string, { name: string; alias: string }> {
  const map = new Map<string, { name: string; alias: string }>()
  props.parentCITypeList.forEach((item: any) => map.set(String(item.id), { name: item.name, alias: item.alias }))
  props.childCITypeList.forEach((item: any) => map.set(String(item.id), { name: item.name, alias: item.alias }))
  return map
}

function labelFor(typeId: any, typeMap: Map<string, { name: string; alias: string }>, item?: any): string {
  return (
    item?.ci_type_alias ||
    item?.ci_type ||
    typeMap.get(String(typeId))?.alias ||
    typeMap.get(String(typeId))?.name ||
    `${typeId}`
  )
}

function buildGraph() {
  const typeMap = buildTypeMap()
  const nodes: any[] = []
  const lines: any[] = []
  existingIds.clear()

  const rootTypeId = currentTypeId.value
  const rootId = `Root_${rootTypeId}`
  nodes.push({
    id: rootId,
    text: labelFor(rootTypeId, typeMap, props.ci),
    data: { ci_id: props.ciId, ci_type_id: rootTypeId, isRoot: true },
  })

  const addCiNode = (item: any, isParent: boolean) => {
    if (props.ciId != null && Number(item._id) === Number(props.ciId)) {
      return
    }
    const nodeId = `ci_${item._id}`
    if (existingIds.has(nodeId)) {
      return
    }
    existingIds.add(nodeId)
    nodes.push({
      id: nodeId,
      text: labelFor(item._type, typeMap, item),
      data: { ci_id: item._id, ci_type_id: item._type, side: isParent ? 'left' : 'right' },
    })
    lines.push(isParent ? { from: nodeId, to: rootId } : { from: rootId, to: nodeId })
  }

  props.parentCIList.forEach((item: any) => addCiNode(item, true))
  props.childCIList.forEach((item: any) => addCiNode(item, false))

  return { rootId, nodes, lines }
}

function render() {
  const { rootId, nodes, lines } = buildGraph()
  graphRef.value?.setJsonData({ rootId, nodes, lines })
}

async function expandNode(node: any) {
  const ciId = node?.data?.ci_id
  if (!ciId || expanding) {
    return
  }
  expanding = true
  try {
    const [childrenRes, parentsRes] = await Promise.all([
      searchCIRelation(`root_id=${ciId}&level=1&reverse=0&count=10000`),
      searchCIRelation(`root_id=${ciId}&level=1&reverse=1&count=10000`),
    ])
    const typeMap = buildTypeMap()
    const newNodes: any[] = []
    const newLines: any[] = []
    const collect = (items: any[], isParent: boolean) => {
      ;(items || []).forEach((item: any) => {
        if (Number(item._id) === Number(ciId)) {
          return
        }
        const nodeId = `ci_${item._id}`
        if (existingIds.has(nodeId)) {
          return
        }
        existingIds.add(nodeId)
        newNodes.push({
          id: nodeId,
          text: labelFor(item._type, typeMap, item),
          data: { ci_id: item._id, ci_type_id: item._type, side: isParent ? 'left' : 'right' },
        })
        newLines.push(isParent ? { from: nodeId, to: node.id } : { from: node.id, to: nodeId })
      })
    }
    collect(childrenRes?.result, false)
    collect(parentsRes?.result, true)
    if (newNodes.length) {
      graphRef.value?.appendJsonData({ nodes: newNodes, lines: newLines })
    }
  } finally {
    expanding = false
  }
}

function onNodeClick(node: any) {
  expandNode(node)
}

function onNodeDblclick(node: any) {
  const ciId = node?.data?.ci_id
  const typeId = node?.data?.ci_type_id
  if (ciId != null && typeId != null) {
    emit('nodeDblclick', { ciId: Number(ciId), typeId: Number(typeId) })
  }
}

watch(
  () => [props.ciId, props.typeId, props.ci, props.parentCIList, props.childCIList],
  () => {
    render()
  },
  { immediate: true, deep: true }
)
</script>

<template>
  <div class="ci-detail-relation-topo" :style="{ width: '100%', height: '100%', position: 'relative' }">
    <RelationGraph
      v-if="ciId != null"
      ref="graphRef"
      :options="graphOptions"
      :on-node-click="onNodeClick"
    >
      <template #node="{ node }">
        <div class="ci-topo-node" @dblclick.stop="onNodeDblclick(node)">
          <span class="ci-topo-node-text">{{ node.text }}</span>
        </div>
      </template>
    </RelationGraph>
    <a-empty
      v-else
      :image="dataEmptyImg"
      :image-style="{ height: '100px' }"
      :style="{ paddingTop: '10%' }"
    >
      <template #description>{{ t('noData') }}</template>
    </a-empty>
  </div>
</template>

<style lang="less" scoped>
.ci-detail-relation-topo {
  width: 100%;
  height: 100%;
  position: relative;
}
.ci-topo-node {
  padding: 6px 10px;
  border-radius: 4px;
  cursor: pointer;
  background-color: #f0f5ff;
  border: 1px solid #adc6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  &-text {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.85);
    word-break: break-all;
  }
}
</style>
