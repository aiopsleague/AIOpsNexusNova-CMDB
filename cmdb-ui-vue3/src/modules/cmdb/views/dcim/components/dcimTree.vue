<script setup lang="ts">
import { computed, inject, nextTick, provide, ref } from 'vue'
import type { Component } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import {
  AppstoreOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  EditOutlined,
  GlobalOutlined,
  HomeOutlined,
  MoreOutlined,
  PlusCircleOutlined,
  SyncOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons-vue'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import { DCIM_TYPE, DCIM_TYPE_NAME_MAP } from '../constants'
import { deleteDCIM, calcUnitFreeCount } from '@/modules/cmdb/api/dcim'
import CIDetailDrawer from '@/modules/cmdb/views/ci/modules/ciDetailDrawer.vue'

interface TreeNode {
  key: string
  title: string
  icon?: string
  count?: number
  addType?: string
  parentId?: string
  dcimType?: string
  _id?: string | number
  _type?: number
  children?: TreeNode[]
  [key: string]: any
}

const props = withDefaults(
  defineProps<{
    treeData?: TreeNode[]
    treeKey?: string | number
  }>(),
  {
    treeData: () => [],
    treeKey: '',
  }
)

const emit = defineEmits<{
  (e: 'openForm', payload: { dcimType: string; nodeId?: string | number; parentId?: string }): void
  (e: 'updateTreeKey', key: string): void
  (e: 'getAttrList', id: string, type: string, cb: (allAttrList: Record<string, any>) => void): void
}>()

const { t } = useI18n()

const getTreeData = inject<() => void>('getTreeData', () => {})

const searchValue = ref('')
const viewDetailCITypeId = ref<number>(0)
const viewDetailAttrObj = ref<Record<string, any>>({})
const calculatedFreeUnitCount = ref(false)

const cIdetailRef = ref<any>()

const addActionTitle: Record<string, string> = {
  [DCIM_TYPE.REGION]: 'cmdb.dcim.addRegion',
  [DCIM_TYPE.IDC]: 'cmdb.dcim.addIDC',
  [DCIM_TYPE.SERVER_ROOM]: 'cmdb.dcim.addServerRoom',
}

const rootAction = [DCIM_TYPE.REGION, DCIM_TYPE.IDC]

const treeIconMap: Record<string, Component> = {
  'veops-region': GlobalOutlined,
  'veops-IDC': DatabaseOutlined,
  'a-veops-room1': HomeOutlined,
}

function resolveTreeIcon(icon?: string): Component {
  return treeIconMap[icon || ''] || AppstoreOutlined
}

const filterTreeData = computed<TreeNode[]>(() => {
  if (searchValue.value) {
    const treeData = cloneDeep(props.treeData)

    const matchedTreeData = treeData.filter((data) => handleTreeDataBySearch(data))

    // Keep sibling parents whose descendants still match the search term.
    const newTreeData: TreeNode[] = []
    treeData.forEach((item) => {
      const filterNodeData = matchedTreeData.find((data) => data.key === item.key)
      if (filterNodeData) {
        newTreeData.push(filterNodeData)
      } else if (matchedTreeData.some((data) => data.parentId === item.key)) {
        newTreeData.push(item)
      }
    })

    return newTreeData
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

function openForm({ dcimType, nodeId = undefined, parentId = '' }: { dcimType: string; nodeId?: string | number; parentId?: string }) {
  emit('openForm', {
    dcimType,
    nodeId,
    parentId,
  })
}

function deleteNode(node: TreeNode) {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete'),
    onOk: async () => {
      await deleteDCIM(node.dcimType as string, node._id as string | number)

      if (node.key === props.treeKey) {
        emit('updateTreeKey', '')
      }

      nextTick(() => {
        refreshTreeData()
      })
    },
  })
}

function refreshTreeData() {
  getTreeData()
}

function clickTreeNode(node: TreeNode) {
  if (node.dcimType === DCIM_TYPE.SERVER_ROOM) {
    emit('updateTreeKey', node.key)
  }
}

function openDetail(node: TreeNode) {
  emit('getAttrList', DCIM_TYPE_NAME_MAP[node.dcimType as string], node.dcimType as string, (allAttrList) => {
    viewDetailCITypeId.value = node._type as number
    viewDetailAttrObj.value = allAttrList[node.dcimType as string]

    nextTick(() => {
      cIdetailRef.value?.create(node._id)
    })
  })
}

function handleCalcUnitFreeCount() {
  if (calculatedFreeUnitCount.value) {
    message.info(t('cmdb.dcim.calcUnitFreeCountTip'))
  } else {
    Modal.confirm({
      title: t('tip'),
      content: t('cmdb.dcim.calcUnitFreeCountTip2'),
      onOk: () => {
        calcUnitFreeCount().then(() => {
          calculatedFreeUnitCount.value = true
          message.success(t('cmdb.dcim.calcUnitFreeCountTip1'))
        })
      },
    })
  }
}

provide('handleSearch', refreshTreeData)
provide('attrList', () => viewDetailAttrObj.value?.attributes || [])
provide('attributes', () => viewDetailAttrObj.value)
</script>

<template>
  <div class="dcim-tree">
    <div class="dcim-tree-header">
      <a-input v-model:value="searchValue" class="dcim-tree-header-search" :placeholder="t('placeholder1')" />
      <a-dropdown>
        <a-button class="dcim-tree-header-more">
          <MoreOutlined />
        </a-button>
        <template #overlay>
          <a-menu>
            <a-menu-item v-for="type in rootAction" :key="type" @click="openForm({ dcimType: type })">
              <PlusCircleOutlined class="dcim-tree-header-menu-icon" />
              {{ t(addActionTitle[type]) }}
            </a-menu-item>

            <a-menu-item class="dcim-tree-header-calc" @click="handleCalcUnitFreeCount">
              <SyncOutlined class="dcim-tree-header-menu-icon" />
              {{ t('cmdb.dcim.calcUnitFreeCount') }}
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </div>

    <div class="dcim-tree-main">
      <a-tree
        v-if="treeData.length"
        auto-expand-parent
        :tree-data="filterTreeData"
        :selected-keys="treeKey ? [treeKey] : []"
        :default-expanded-keys="treeKey ? [treeKey] : []"
      >
        <template #title="treeNodeData">
          <div class="dcim-tree-node" @click="clickTreeNode(treeNodeData)">
            <component
              :is="resolveTreeIcon(treeNodeData.icon)"
              :class="['dcim-tree-node-icon', treeNodeData.dcimType === DCIM_TYPE.REGION ? 'primary-color' : '']"
            />
            <a-tooltip :title="treeNodeData.title">
              <span :class="['dcim-tree-node-title', treeKey === treeNodeData.key ? 'primary-color' : '']">
                {{ treeNodeData.title }}
              </span>
            </a-tooltip>

            <div class="dcim-tree-node-right">
              <span v-if="treeNodeData.count" class="dcim-tree-node-count">
                {{ treeNodeData.count }}
              </span>

              <a-dropdown>
                <a class="dcim-tree-node-action">
                  <MoreOutlined />
                </a>

                <template #overlay>
                  <a-menu>
                    <a-menu-item
                      v-if="treeNodeData.addType"
                      @click="
                        openForm({
                          dcimType: treeNodeData.addType,
                          parentId: treeNodeData._id,
                        })
                      "
                    >
                      <PlusCircleOutlined />
                      {{ t(addActionTitle[treeNodeData.addType]) }}
                    </a-menu-item>
                    <a-menu-item @click="openDetail(treeNodeData)">
                      <UnorderedListOutlined />
                      {{ t('cmdb.dcim.viewDetail') }}
                    </a-menu-item>
                    <a-menu-item
                      @click="
                        openForm({
                          dcimType: treeNodeData.dcimType,
                          parentId: treeNodeData.parentId,
                          nodeId: treeNodeData._id,
                        })
                      "
                    >
                      <EditOutlined />
                      {{ t('cmdb.dcim.editNode') }}
                    </a-menu-item>
                    <a-menu-item @click="deleteNode(treeNodeData)">
                      <DeleteOutlined />
                      {{ t('cmdb.dcim.deleteNode') }}
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </div>
          </div>
        </template>
      </a-tree>
    </div>

    <CIDetailDrawer ref="cIdetailRef" :type-id="viewDetailCITypeId" />
  </div>
</template>

<style lang="less" scoped>
.dcim-tree {
  &-header {
    display: flex;
    align-items: center;
    column-gap: 14px;

    &-search {
      width: 100%;
    }

    &-more {
      flex-shrink: 0;
      width: 32px;
      padding: 0px;
    }

    &-calc {
      border-top: dashed 1px #e8e8e8;
    }

    &-menu-icon {
      margin-right: 6px;
    }
  }

  &-main {
    width: 100%;
    height: 100%;

    :deep(.ant-tree) {
      .ant-tree-node-content-wrapper {
        width: calc(100% - 24px);
        padding: 0px;
        display: inline-block;
        height: fit-content;

        .ant-tree-title {
          display: inline-block;
          width: 100%;
          padding: 0 6px;
        }
      }

      .ipam-tree-node_hide_expand {
        .ant-tree-switcher {
          display: none;
        }

        .ant-tree-node-content-wrapper {
          width: 100%;
        }
      }

      .ant-tree-switcher-icon {
        color: #cacdd9;
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
      color: #a5a9bc;
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
      color: #a5a9bc;
    }

    &-action {
      display: none;
      margin-left: 3px;
      font-size: 12px;

      &:hover {
        color: #2f54eb;
      }

      :deep(.ant-dropdown-menu) {
        padding: 4px 0;
      }

      :deep(.ant-dropdown-menu-item) {
        padding: 5px 12px;
      }
    }

    &:hover {
      .dcim-tree-node-action {
        display: inline-block;
      }
    }
  }
}

.primary-color {
  color: @primary-color;
}
</style>
