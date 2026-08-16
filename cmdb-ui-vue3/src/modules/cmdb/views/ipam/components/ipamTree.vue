<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import type { Component } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import {
  ApartmentOutlined,
  DeleteOutlined,
  EditOutlined,
  FolderAddOutlined,
  FolderOutlined,
  GlobalOutlined,
  HolderOutlined,
  MoreOutlined,
  PlusCircleOutlined,
} from '@ant-design/icons-vue'
import { deleteIPAMSubnet, deleteIPAMScope, moveIPAMSubnet } from '@/modules/cmdb/api/ipam'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import SubnetForm from './subnetForm.vue'
import CatalogForm from './catalogForm.vue'

interface TreeNode {
  key: string
  title: string
  icon?: string
  iconColor?: string
  count?: number
  isSubnet?: boolean
  parentId?: string
  showCatalogBtn?: boolean
  showSubnetBtn?: boolean
  children?: TreeNode[]
  [key: string]: any
}

const props = withDefaults(
  defineProps<{
    treeData?: TreeNode[]
    treeKey?: string | number
    subnetCIType?: Record<string, any>
  }>(),
  {
    treeData: () => [],
    treeKey: '',
    subnetCIType: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'refreshData'): void
  (e: 'updateTreeKey', key: string): void
}>()

const { t } = useI18n()

const searchValue = ref('')

const subnetFormRef = ref<InstanceType<typeof SubnetForm>>()
const catalogFormRef = ref<InstanceType<typeof CatalogForm>>()

const treeIconMap: Record<string, Component> = {
  'veops-entire_network_': GlobalOutlined,
  'veops-subnet': ApartmentOutlined,
  'veops-folder': FolderOutlined,
}

function resolveTreeIcon(icon?: string): Component {
  return treeIconMap[icon || ''] || FolderOutlined
}

const filterTreeData = computed<TreeNode[]>(() => {
  if (searchValue.value) {
    const treeData = cloneDeep(props.treeData)
    return treeData.filter((data) => handleTreeDataBySearch(data))
  }

  return props.treeData
})

function handleTreeDataBySearch(data: TreeNode): TreeNode | null {
  const isMatch = data?.title?.indexOf?.(searchValue.value) !== -1
  if (!data?.children?.length) {
    return isMatch ? data : null
  }

  data.children = data.children.filter((item) => handleTreeDataBySearch(item))
  return isMatch || data.children.length ? data : null
}

function findNodeByKey(nodes: TreeNode[], key: string): TreeNode | null {
  for (const node of nodes) {
    if (String(node.key) === String(key)) {
      return node
    }
    if (node.children) {
      const foundNode = findNodeByKey(node.children, key)
      if (foundNode) {
        return foundNode
      }
    }
  }
  return null
}

function openCatalogForm(node: TreeNode, type: string) {
  const nodeId = node?.key && node?.key !== 'all' ? node.key : null
  const name = type === 'edit' ? node?.title || '' : ''

  catalogFormRef.value?.open({
    nodeId,
    type,
    name,
  })
}

function openSubnetForm(node: TreeNode, type: string) {
  const nodeId = node?.key && node?.key !== 'all' ? node.key : null
  const parentId = node?.parentId || null

  subnetFormRef.value?.open(nodeId, type, parentId)
}

function deleteNode(node: TreeNode) {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete'),
    onOk: async () => {
      if (node.isSubnet) {
        await deleteIPAMSubnet(node.key)
      } else {
        await deleteIPAMScope(node.key)
      }

      if (node.key === props.treeKey) {
        emit('updateTreeKey', 'all')
      }
      nextTick(() => {
        refreshData()
      })
    },
  })
}

function refreshData() {
  emit('refreshData')
}

function clickTreeNode(node: TreeNode) {
  emit('updateTreeKey', node.key)
}

function allowDrop(options: any): boolean {
  if (searchValue.value || options?.dropPosition !== 0) {
    return false
  }

  const targetNode = findNodeByKey(props.treeData, options?.dropNode?.eventKey)
  return targetNode?.key === 'all' || !targetNode?.isSubnet
}

function handleDragStart(info: any) {
  const dragNode = findNodeByKey(props.treeData, info?.node?.eventKey)
  if (!dragNode?.isSubnet) {
    const event = info && info.event
    if (event && event.preventDefault) {
      event.preventDefault()
    }
    if (event && event.stopPropagation) {
      event.stopPropagation()
    }
    return false
  }
}

async function handleDrop(info: any) {
  const dragNode = findNodeByKey(props.treeData, info?.dragNode?.eventKey)
  const targetNode = findNodeByKey(props.treeData, info?.node?.eventKey)

  if (!dragNode?.isSubnet || !targetNode) {
    return
  }

  const targetParentId = targetNode.key === 'all' ? null : targetNode.key
  if (`${dragNode.parentId || ''}` === `${targetParentId || ''}`) {
    return
  }

  await moveIPAMSubnet(dragNode.key, {
    target_parent_id: targetParentId,
  })

  message.success(t('editSuccess'))
  refreshData()
}
</script>

<template>
  <div class="ipam-tree">
    <a-input
      v-model:value="searchValue"
      class="ipam-tree-search"
      :placeholder="t('placeholder1')"
    />

    <div class="ipam-tree-main">
      <a-tree
        v-if="treeData.length"
        auto-expand-parent
        :tree-data="filterTreeData"
        :selected-keys="treeKey ? [treeKey] : []"
        :default-expanded-keys="treeKey ? [treeKey] : []"
        :draggable="!searchValue"
        :allow-drop="allowDrop"
        @dragstart="handleDragStart"
        @drop="handleDrop"
      >
        <template #title="treeNodeData">
          <div
            :class="[
              'ipam-tree-node',
              treeNodeData.isSubnet && !searchValue ? 'ipam-tree-node-draggable' : ''
            ]"
            @click="clickTreeNode(treeNodeData)"
          >
            <HolderOutlined
              v-if="treeNodeData.isSubnet && !searchValue"
              class="ipam-tree-node-drag-icon"
            />
            <component
              :is="resolveTreeIcon(treeNodeData.icon)"
              class="ipam-tree-node-icon"
              :style="{ color: treeNodeData.iconColor }"
            />
            <a-tooltip :title="treeNodeData.title">
              <span
                :class="['ipam-tree-node-title', treeKey === treeNodeData.key ? 'primary-color' : '']"
              >
                {{ treeNodeData.title }}
              </span>
            </a-tooltip>
            <div class="ipam-tree-node-right">
              <span
                v-if="(treeNodeData.key === 'all' && treeNodeData.count) || (treeNodeData.key !== 'all' && treeNodeData.children && treeNodeData.children.length && treeNodeData.count)"
                class="ipam-tree-node-count"
              >
                {{ treeNodeData.count }}
              </span>

              <a-dropdown :get-popup-container="(trigger: HTMLElement) => trigger">
                <a class="ipam-tree-node-action">
                  <MoreOutlined />
                </a>
                <template #overlay>
                  <a-menu>
                    <a-menu-item
                      v-if="treeNodeData.showCatalogBtn"
                      @click="openCatalogForm(treeNodeData, 'create')"
                    >
                      <FolderAddOutlined />
                      {{ t('cmdb.ipam.addCatalog') }}
                    </a-menu-item>
                    <a-menu-item
                      v-if="treeNodeData.showSubnetBtn"
                      @click="openSubnetForm(treeNodeData, 'create')"
                    >
                      <PlusCircleOutlined />
                      {{ t('cmdb.ipam.addSubnet') }}
                    </a-menu-item>

                    <template v-if="treeNodeData.key !== 'all'">
                      <a-menu-item
                        v-if="!treeNodeData.isSubnet"
                        @click="openCatalogForm(treeNodeData, 'edit')"
                      >
                        <EditOutlined />
                        {{ t('cmdb.ipam.editName') }}
                      </a-menu-item>
                      <a-menu-item
                        v-if="treeNodeData.isSubnet"
                        @click="openSubnetForm(treeNodeData, 'edit')"
                      >
                        <EditOutlined />
                        {{ t('cmdb.ipam.editNode') }}
                      </a-menu-item>
                      <a-menu-item @click="deleteNode(treeNodeData)">
                        <DeleteOutlined />
                        {{ t('cmdb.ipam.deleteNode') }}
                      </a-menu-item>
                    </template>
                  </a-menu>
                </template>
              </a-dropdown>
            </div>
          </div>
        </template>
      </a-tree>
    </div>

    <SubnetForm
      ref="subnetFormRef"
      :subnet-c-i-type="subnetCIType"
      @ok="refreshData"
    />

    <CatalogForm
      ref="catalogFormRef"
      @ok="refreshData"
    />
  </div>
</template>

<style lang="less" scoped>
.ipam-tree {
  width: 100%;

  &-search {
    width: 100%;
    height: 26px;
    line-height: 26px;
  }

  &-main {
    width: 100%;
    height: 100%;

    :deep(.ant-tree) {
      .ant-tree-switcher {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 32px;
        line-height: 32px;
      }

      .ant-tree-node-content-wrapper {
        width: calc(100% - 18px);
        padding: 0px;
        display: inline-block;
        height: fit-content;

        .ant-tree-title {
          display: inline-block;
          width: 100%;
          padding: 0 4px 0 2px;
        }
      }

      .ipam-tree-node-all {
        .ant-tree-switcher {
          display: none;
        }

        .ant-tree-node-content-wrapper {
          width: 100%;
        }
      }

      .ant-tree-switcher-icon {
        color: #CACDD9;
      }
    }
  }

  &-node {
    display: flex;
    align-items: center;
    height: 32px;
    cursor: pointer;

    &-icon {
      font-size: 12px;
      flex-shrink: 0;
    }

    &-drag-icon {
      width: 12px;
      height: 12px;
      margin-right: 1px;
      flex-shrink: 0;
      color: #A5A9BC;
      opacity: 0;
      transition: opacity 0.2s ease;
    }

    &-title {
      margin-left: 6px;
      font-size: 14px;
      font-weight: 400;

      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      text-wrap: nowrap;
    }

    &-right {
      margin-left: auto;
      display: flex;
      align-items: center;
      flex-shrink: 0;
    }

    &-count {
      font-size: 10px;
      font-weight: 400;
      color: #A5A9BC;
    }

    &-action {
      display: none;
      margin-left: 3px;
      font-size: 12px;

      &:hover {
        color: #2F54EB;
      }

      :deep(.ant-dropdown-menu) {
        padding: 4px 0;
      }

      :deep(.ant-dropdown-menu-item) {
        padding: 5px 12px;
      }
    }

    &:hover {
      .ipam-tree-node-drag-icon {
        opacity: 1;
      }

      .ipam-tree-node-action {
        display: inline-block;
      }
    }

    &-draggable {
      cursor: grab;

      &:active {
        cursor: grabbing;
      }
    }
  }
}

.primary-color {
  color: @primary-color;
}
</style>
