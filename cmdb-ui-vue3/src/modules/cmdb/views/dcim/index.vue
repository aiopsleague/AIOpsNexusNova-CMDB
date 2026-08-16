<script setup lang="ts">
import { computed, nextTick, provide, ref } from 'vue'
import { getDCIMTreeView } from '@/modules/cmdb/api/dcim'
import { DCIM_CITYPE_NAME, DCIM_TYPE, DCIM_TYPE_NAME_MAP } from './constants'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { getCIType } from '@/modules/cmdb/api/CIType'
import { getSubscribeAttributes } from '@/modules/cmdb/api/preference'
import SplitPane from '@/components/SplitPane/SplitPane.vue'
import DCIMTree from './components/dcimTree.vue'
import DCIMForm from './components/dcimForm.vue'
import DCIMMain from './components/dcimMain/index.vue'

const TREE_STORAGE_KEY = 'ops_dcim_tree_active'

const windowHeight = computed(() => window.innerHeight)
const paneLengthPixel = ref(204)

const treeKey = ref(localStorage.getItem(TREE_STORAGE_KEY) || '')
const treeData = ref<any[]>([])
const allAttrList = ref<Record<string, any>>({
  [DCIM_TYPE.REGION]: {},
  [DCIM_TYPE.IDC]: {},
  [DCIM_TYPE.SERVER_ROOM]: {},
  [DCIM_TYPE.RACK]: {},
})

const initLoading = ref(true)
const rackCITYpe = ref<Record<string, any>>({})
const rackPreferenceAttrList = ref<any[]>([])

const dcimFormRef = ref<InstanceType<typeof DCIMForm>>()
const dcimMainRef = ref<InstanceType<typeof DCIMMain>>()

async function getTreeData() {
  const res = await getDCIMTreeView()
  let nextTree: any[] = []

  if (res?.result?.length) {
    nextTree = res.result.map((data: any) => handleTreeData(data, res.type2name))
  }

  const currentNode = findNodeById(nextTree, treeKey.value)
  if (!currentNode) {
    updateTreeKey('')
  }

  const flatTreeData: any[] = []
  nextTree.forEach((item) => {
    flatTreeData.push({
      ...item,
      class: 'ipam-tree-node_hide_expand',
      children: [],
    })
    if (item.children.length) {
      flatTreeData.push(...item.children)
    }
  })

  treeData.value = flatTreeData
}

function handleTreeData(data: any, type2name: any, parentId = ''): any {
  const title = data?.[type2name?.[data?._type]] || ''
  const dcimType = DCIM_TYPE_NAME_MAP[data.ci_type]
  let icon = ''
  let iconColor = '#A5A9BC'
  let addType = ''

  const key = String(data._id)

  switch (data.ci_type) {
    case DCIM_CITYPE_NAME.REGION:
      icon = 'veops-region'
      iconColor = '#2F54EB'
      addType = DCIM_TYPE.IDC
      break
    case DCIM_CITYPE_NAME.IDC:
      icon = 'veops-IDC'
      addType = DCIM_TYPE.SERVER_ROOM
      break
    case DCIM_CITYPE_NAME.SERVER_ROOM:
      icon = 'a-veops-room1'
      break
    default:
      break
  }

  if (!data?.children?.length) {
    return {
      ...data,
      key,
      title,
      icon,
      iconColor,
      parentId,
      addType,
      dcimType,
      count: data?.rack_count || 0,
    }
  }

  const children = data.children.map((item: any) => handleTreeData(item, type2name, key))

  return {
    ...data,
    key,
    title,
    icon,
    iconColor,
    addType,
    parentId,
    children,
    dcimType,
    count: children.reduce((acc: number, item: any) => acc + item.count, 0),
  }
}

function findNodeById(nodes: any[], id: string): any {
  for (const node of nodes) {
    if (node.key === id) {
      return node
    }
    if (node.children) {
      const foundNode = findNodeById(node.children, id)
      if (foundNode) {
        return foundNode
      }
    }
  }
  return null
}

async function getRackData() {
  await getAttrList(DCIM_CITYPE_NAME.RACK, DCIM_TYPE.RACK)

  const CITypeRes = await getCIType(DCIM_CITYPE_NAME.RACK)
  rackCITYpe.value = CITypeRes?.ci_types?.[0] || {}

  if (rackCITYpe.value.id) {
    const subscribed = await getSubscribeAttributes(rackCITYpe.value.id)
    rackPreferenceAttrList.value = subscribed.attributes
  }
}

async function getAttrList(id: string, type: string, cb?: (allAttrList: Record<string, any>) => void) {
  if (Object.keys(allAttrList.value?.[type] || {}).length === 0) {
    const res = await getCITypeAttributesById(id)
    allAttrList.value[type] = res || {}
  }

  if (cb) {
    cb(allAttrList.value)
  }
}

async function openForm(data: any) {
  await getAttrList(DCIM_TYPE_NAME_MAP[data.dcimType], data.dcimType)

  nextTick(() => {
    dcimFormRef.value?.open(data)
  })
}

function updateTreeKey(key: string) {
  treeKey.value = key
  localStorage.setItem(TREE_STORAGE_KEY, key)
}

function handleDCIMFormOk({ dcimType, editType }: { dcimType: string; editType: string }) {
  switch (dcimType) {
    case DCIM_TYPE.REGION:
    case DCIM_TYPE.IDC:
    case DCIM_TYPE.SERVER_ROOM:
      getTreeData()
      break
    case DCIM_TYPE.RACK:
      getRackList()
      if (editType === 'create') {
        getTreeData()
      }
      break
    default:
      break
  }
}

function getRackList() {
  dcimMainRef.value?.getRackList()
}

async function initData() {
  initLoading.value = true

  try {
    await getTreeData()
    await getRackData()
  } catch (error) {
    console.log('initData fail', error)
  }

  initLoading.value = false
}

provide('getTreeData', getTreeData)

initData()
</script>

<template>
  <div class="two-column-layout" :style="{ height: `${windowHeight - 64}px` }">
    <SplitPane v-model:pane-length-pixel="paneLengthPixel" :min="200" :max="500" app-name="cmdb-dcim" :trigger-length="18" calc-based-parent>
      <template #one>
        <div class="two-column-layout-sidebar">
          <DCIMTree
            :tree-data="treeData"
            :tree-key="treeKey"
            @get-attr-list="getAttrList"
            @update-tree-key="updateTreeKey"
            @open-form="openForm"
          />

          <DCIMForm ref="dcimFormRef" :all-attr-list="allAttrList" @ok="handleDCIMFormOk" />
        </div>
      </template>

      <template #two>
        <div class="two-column-layout-main">
          <DCIMMain
            v-if="!initLoading && rackCITYpe.id"
            ref="dcimMainRef"
            :room-id="treeKey"
            :attr-obj="allAttrList[DCIM_TYPE.RACK]"
            :rack-c-i-type="rackCITYpe"
            :preference-attr-list="rackPreferenceAttrList"
            @open-form="openForm"
          />
        </div>
      </template>
    </SplitPane>
  </div>
</template>

<style lang="less" scoped>
.two-column-layout {
  margin-bottom: -24px;
  width: 100%;

  .two-column-layout-sidebar {
    height: 100%;
    overflow: hidden;
    background-color: #f7f8fa;
    border-right: 1px solid #e8eaed;
    padding: 12px 8px;

    &:hover {
      overflow: auto;
    }
  }

  .two-column-layout-main {
    height: 100%;
    padding: 12px;
    background-color: #fff;
    overflow-y: auto;
    border-radius: @border-radius-box;
  }
}
</style>
