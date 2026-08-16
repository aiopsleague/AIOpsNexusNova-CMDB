<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getIPAMSubnet } from '@/modules/cmdb/api/ipam'
import { getCIType } from '@/modules/cmdb/api/CIType'
import { SUB_NET_CITYPE_NAME, ADDRESS_CITYPE_NAME } from './constants'
import SplitPane from '@/components/SplitPane/SplitPane.vue'
import IPAMTree from './components/ipamTree.vue'
import Overview from './modules/overview/index.vue'
import Address from './modules/address/index.vue'
import IPSearch from './modules/ipSearch/index.vue'
import SubnetList from './modules/subnetList/index.vue'
import HistoryLog from './modules/history/index.vue'

const TAB_STORAGE_KEY = 'ops_ipam_tab_active'
const TREE_STORAGE_KEY = 'ops_ipam_tree_active'

const { t } = useI18n()

const windowHeight = computed(() => window.innerHeight)
const paneLengthPixel = ref(204)

const tabKey = ref(localStorage.getItem(TAB_STORAGE_KEY) || 'overview')
const treeKey = ref(localStorage.getItem(TREE_STORAGE_KEY) || 'all')

const tabs = [
  { key: 'overview', title: 'cmdb.ipam.overview' },
  { key: 'address', title: 'cmdb.ipam.addressAssign' },
  { key: 'ipSearch', title: 'cmdb.ipam.ipSearch' },
  { key: 'subnet', title: 'cmdb.ipam.subnetList' },
  { key: 'history', title: 'cmdb.ipam.history' },
]

const treeData = ref<any[]>([])
const subnetCIType = ref<Record<string, any>>({})
const addressCIType = ref<Record<string, any>>({})

const overviewRef = ref<InstanceType<typeof Overview>>()
const subnetListRef = ref<InstanceType<typeof SubnetList>>()
const historyRef = ref<InstanceType<typeof HistoryLog>>()

const nodeData = computed(() => findNodeById(treeData.value, treeKey.value))

watch(
  tabKey,
  (key) => {
    switch (key) {
      case 'subnet':
        if (!subnetCIType.value?.id) {
          getSubnetCIType()
        }
        break
      case 'address':
      case 'ipSearch':
        if (!addressCIType.value?.id) {
          getAddressCIType()
        }
        break
      default:
        break
    }
  },
  { immediate: true }
)

async function getSubnetCIType() {
  const res = await getCIType(SUB_NET_CITYPE_NAME)
  subnetCIType.value = res?.ci_types?.[0] || {}
}

async function getAddressCIType() {
  const res = await getCIType(ADDRESS_CITYPE_NAME)
  addressCIType.value = res?.ci_types?.[0] || {}
}

async function getTreeData() {
  const res = await getIPAMSubnet()
  let nextTree: any[] = []

  if (res?.result?.length) {
    nextTree = res.result.map((data: any) => {
      return handleTreeData(data, res.type2name)
    })
  }

  const allCount = nextTree.reduce((acc, cur) => acc + cur.count, 0)
  nextTree.unshift({
    key: 'all',
    title: t('all'),
    count: allCount,
    icon: 'veops-entire_network_',
    iconColor: '#2F54EB',
    showCatalogBtn: true,
    showSubnetBtn: true,
    parentId: '',
    class: 'ipam-tree-node-all',
  })

  treeData.value = nextTree
}

function handleTreeData(data: any, type2name: any, parentId = ''): any {
  const title = data?.[type2name?.[data?._type]] || ''
  const isSubnet = data?.ci_type === SUB_NET_CITYPE_NAME
  const icon = isSubnet ? 'veops-subnet' : 'veops-folder'
  const iconColor = isSubnet ? '#CACDD9' : ''
  const key = String(data._id)

  if (!data?.children?.length) {
    return {
      key,
      title,
      count: isSubnet ? 1 : 0,
      icon,
      iconColor,
      showCatalogBtn: !isSubnet,
      showSubnetBtn: true,
      isSubnet,
      parentId,
      ...data,
    }
  }

  const children = data.children.map((item: any) => {
    return handleTreeData(item, type2name, key)
  })

  return {
    key,
    title,
    icon,
    iconColor,
    showCatalogBtn: !isSubnet,
    showSubnetBtn: true,
    isSubnet,
    parentId,
    ...data,
    children,
    count: children.reduce((acc: number, item: any) => {
      return acc + item.count
    }, 0),
  }
}

function findNodeById(nodes: any[], key: string): any {
  for (const node of nodes) {
    if (node.key === key) {
      return node
    }
    if (node.children) {
      const foundNode = findNodeById(node.children, key)
      if (foundNode) {
        return foundNode
      }
    }
  }
  return null
}

function handleTabChange(key: string) {
  if (key !== tabKey.value) {
    tabKey.value = key
    localStorage.setItem(TAB_STORAGE_KEY, key)
  }
}

function updateTreeKey(key: string) {
  treeKey.value = key
  localStorage.setItem(TREE_STORAGE_KEY, key)
}

function refreshData() {
  getTreeData()
  switch (tabKey.value) {
    case 'overview':
      overviewRef.value?.initData()
      break
    case 'subnet':
      subnetListRef.value?.getTableData()
      break
    case 'history':
      historyRef.value?.refreshData()
      break
    default:
      break
  }
}

getSubnetCIType()
getTreeData()
</script>

<template>
  <div class="two-column-layout" :style="{ height: `${windowHeight - 64}px` }">
    <SplitPane
      v-model:pane-length-pixel="paneLengthPixel"
      :min="200"
      :max="500"
      app-name="cmdb-ipam"
      :trigger-length="18"
      calc-based-parent
    >
      <template #one>
        <div class="two-column-layout-sidebar">
          <IPAMTree
            v-if="subnetCIType.id"
            :tree-data="treeData"
            :tree-key="treeKey"
            :subnet-c-i-type="subnetCIType"
            @refresh-data="refreshData"
            @update-tree-key="updateTreeKey"
          />
        </div>
      </template>

      <template #two>
        <div class="two-column-layout-main">
          <a-tabs
            class="ipam-tabs"
            :active-key="tabKey"
            @change="handleTabChange"
          >
            <a-tab-pane
              v-for="item in tabs"
              :key="item.key"
              :tab="t(item.title)"
            />
          </a-tabs>

          <Overview
            v-if="tabKey === 'overview'"
            ref="overviewRef"
            :node-id="treeKey"
          />
          <template v-if="addressCIType.id">
            <Address
              v-if="tabKey === 'address'"
              :node-data="nodeData"
              :address-c-i-type="addressCIType"
            />
            <IPSearch
              v-if="tabKey === 'ipSearch'"
              :address-c-i-type="addressCIType"
            />
          </template>
          <SubnetList
            v-if="tabKey === 'subnet' && subnetCIType.id"
            ref="subnetListRef"
            :subnet-c-i-type="subnetCIType"
            @delete="getTreeData"
          />
          <HistoryLog
            v-if="tabKey === 'history'"
            ref="historyRef"
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

.ipam-tabs {
  display: inline-block;
}

.ipam {
  :deep(.ant-tabs) {
    display: inline-block;
  }
}
</style>
