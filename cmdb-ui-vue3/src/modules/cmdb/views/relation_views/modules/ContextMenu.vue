<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  CaretRightOutlined,
  CaretDownOutlined,
  AppstoreOutlined,
  PlusCircleOutlined,
  UserAddOutlined,
  UserDeleteOutlined,
  EyeOutlined,
  CloseCircleOutlined,
  EllipsisOutlined,
  DeleteOutlined,
  EditOutlined,
  CopyOutlined,
} from '@ant-design/icons-vue'
import { updateCI } from '@/modules/cmdb/api/ci'

const props = withDefaults(
  defineProps<{
    treeNodeData: Record<string, any>
    levels: any[]
    currentViews: Record<string, any>
    id2type: Record<string, any>
    ciTypeIcons: Record<string, any>
    showBatchLevel?: number | null
    batchTreeKey?: any[]
    fullSearchValue?: string
  }>(),
  {
    levels: () => [],
    currentViews: () => ({}),
    id2type: () => ({}),
    ciTypeIcons: () => ({}),
    showBatchLevel: null,
    batchTreeKey: () => [],
    fullSearchValue: '',
  }
)

const emit = defineEmits<{
  (e: 'onContextMenuClick', treeKey: string, menuKey: string | number): void
  (e: 'onNodeClick', treeKey: string): void
  (e: 'clickCheckbox', treeKey: string): void
  (e: 'updateTreeData', ciId: number, value: string): void
}>()

const { t } = useI18n()

const switchIcon = ref('caret-right')
const isEditNodeName = ref(false)
const editNodeName = ref('')
const input = ref<{ focus: () => void }>()

const title = computed(() => props.treeNodeData.title)
const number = computed(() => props.treeNodeData.number)
const treeKey = computed(() => props.treeNodeData.key)
const isLeaf = computed(() => props.treeNodeData.isLeaf)
const showName = computed(() => props.treeNodeData.showName)

const splitTreeKey = computed(() => treeKey.value.split('@^@'))
const _tempTree = computed(() => splitTreeKey.value[splitTreeKey.value.length - 1].split('%'))

// Index of the current node type in levels.
const _typeIdIdx = computed(() =>
  props.levels.findIndex((level) => level[0] === Number(_tempTree.value[1]))
)

const showDelete = computed(() => _typeIdIdx.value !== 0)

const menuList = computed(() => {
  let _menuList: Array<{ id: number; alias: string }> = []
  if (_typeIdIdx.value > -1 && _typeIdIdx.value < props.levels.length - 1) {
    // Not a leaf node.
    const id = Number(props.levels[_typeIdIdx.value + 1])
    _menuList = [{ id, alias: props.id2type[id].alias || props.id2type[id].name }]
  } else {
    // Leaf node.
    _menuList =
      props.currentViews?.node2show_types?.[_tempTree.value?.[1]]?.map?.((item: any) => {
        return { id: item.id, alias: item.alias || item.name }
      }) || []
  }
  return _menuList
})

const icon = computed(() => {
  const _split = treeKey.value.split('@^@')
  const currentNodeTypeId = _split[_split.length - 1].split('%')[1]
  return props.ciTypeIcons[Number(currentNodeTypeId)] ?? null
})

const iconParts = computed(() => (icon.value || '').split('$$'))
const iconColor = computed(() => iconParts.value[1] || '')
const iconImgSrc = computed(() =>
  iconParts.value[2] && iconParts.value[3] ? `/api/common-setting/v1/file/${iconParts.value[3]}` : ''
)

const showCheckbox = computed(
  () => props.showBatchLevel === treeKey.value.split('@^@').filter((item: any) => !!item).length - 1
)

/** Split the title into highlight segments based on the full-search value. */
function highlightParts() {
  const text = String(title.value ?? '')
  const search = props.fullSearchValue
  if (!search) {
    return [{ text, highlighted: false }]
  }
  const lower = text.toLowerCase()
  const lowerSearch = search.toLowerCase()
  const parts: Array<{ text: string; highlighted: boolean }> = []
  let cursor = 0
  let idx = lower.indexOf(lowerSearch)
  while (idx !== -1) {
    if (idx > cursor) {
      parts.push({ text: text.slice(cursor, idx), highlighted: false })
    }
    parts.push({ text: text.slice(idx, idx + search.length), highlighted: true })
    cursor = idx + search.length
    idx = lower.indexOf(lowerSearch, cursor)
  }
  if (cursor < text.length) {
    parts.push({ text: text.slice(cursor), highlighted: false })
  }
  return parts.length ? parts : [{ text, highlighted: false }]
}

function onMenuClick({ key }: { key: string | number }) {
  onContextMenuClick(key)
}

function onContextMenuClick(menuKey: string | number) {
  if (menuKey === 'editNodeName') {
    isEditNodeName.value = true
    editNodeName.value = title.value
    nextTick(() => {
      input.value?.focus()
    })
    return
  }
  emit('onContextMenuClick', treeKey.value, menuKey)
}

function clickNode() {
  emit('onNodeClick', treeKey.value)
  switchIcon.value = switchIcon.value === 'caret-right' ? 'caret-down' : 'caret-right'
}

function clickCheckbox() {
  emit('clickCheckbox', treeKey.value)
}

function changeNodeName(e: Event) {
  const value = (e.target as HTMLInputElement).value
  if (value !== title.value) {
    const ci = treeKey.value.split('@^@').slice(-1)[0].split('%')
    const unique = Object.keys(JSON.parse(ci[2]))[0]
    const ciId = Number(ci[0])
    let editAttrName = unique
    if (showName.value) {
      editAttrName = showName.value
    }
    updateCI(ciId, { [editAttrName]: value }).then(() => {
      message.success(t('updateSuccess'))
      emit('updateTreeData', ciId, value)
    })
  }
  isEditNodeName.value = false
  editNodeName.value = ''
}
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation -->
  <div
    :class="{
      'relation-views-node': true,
      'relation-views-node-checkbox': showCheckbox,
    }"
    @click="clickNode"
  >
    <span class="relation-views-node-switch">
      <template v-if="!isLeaf">
        <CaretRightOutlined v-if="switchIcon === 'caret-right'" />
        <CaretDownOutlined v-else />
      </template>
    </span>
    <span class="relation-views-node-content">
      <a-checkbox
        v-if="showCheckbox"
        class="relation-views-node-checkbox"
        @click.stop="clickCheckbox"
      />
      <template v-if="icon">
        <img
          v-if="iconImgSrc"
          :src="iconImgSrc"
          :style="{ maxHeight: '14px', maxWidth: '14px' }"
        />
        <AppstoreOutlined
          v-else-if="iconParts[0]"
          :style="{ color: iconColor, fontSize: '14px' }"
        />
        <span v-else class="relation-views-node-icon">{{ icon ? icon[0].toUpperCase() : 'i' }}</span>
      </template>
      <span
        v-if="!isEditNodeName"
        class="relation-views-node-title"
        :title="title"
      >
        <template v-for="(part, idx) in highlightParts()" :key="idx">
          <span v-if="part.highlighted" class="relation-views-node-title-highlight">{{ part.text }}</span>
          <template v-else>{{ part.text }}</template>
        </template>
      </span>
      <a-input
        v-else
        ref="input"
        v-model:value="editNodeName"
        size="small"
        :style="{ marginLeft: '5px' }"
        @blur="changeNodeName"
        @press-enter="() => input?.focus()"
      />
      <span class="relation-views-node-number">{{ number }}</span>
      <a-dropdown overlay-class-name="relation-views-node-dropdown" :overlay-style="{ width: '200px' }">
        <a-menu @click="onMenuClick">
          <template v-if="showBatchLevel === null">
            <a-divider orientation="left">{{ t('cmdb.relation') }}</a-divider>
            <a-menu-item v-for="item in menuList" :key="item.id">
              <PlusCircleOutlined />{{ t('add') }} {{ item.alias }}
            </a-menu-item>
            <a-menu-item v-if="showDelete" key="delete">
              <DeleteOutlined />{{ t('cmdb.serviceTree.deleteNode', { name: title }) }}
            </a-menu-item>
            <a-divider orientation="left">{{ t('cmdb.components.perm') }}</a-divider>
            <a-menu-item key="grant"><UserAddOutlined />{{ t('grant') }}</a-menu-item>
            <a-menu-item key="revoke"><UserDeleteOutlined />{{ t('revoke') }}</a-menu-item>
            <a-menu-item key="view"><EyeOutlined />{{ t('cmdb.serviceTree.view') }}</a-menu-item>
            <a-menu-divider />
            <a-menu-item key="editNodeName"><EditOutlined />{{ t('cmdb.serviceTree.editNodeName') }}</a-menu-item>
            <a-menu-item key="batch"><CopyOutlined />{{ t('cmdb.serviceTree.batch') }}</a-menu-item>
          </template>
          <template v-else>
            <a-menu-item key="batchGrant" :disabled="!batchTreeKey || !batchTreeKey.length">
              <UserAddOutlined />{{ t('grant') }}
            </a-menu-item>
            <a-menu-item key="batchRevoke" :disabled="!batchTreeKey || !batchTreeKey.length">
              <UserDeleteOutlined />{{ t('revoke') }}
            </a-menu-item>
            <a-menu-divider />
            <template v-if="showBatchLevel !== null && showBatchLevel > 0">
              <a-menu-item key="batchDelete" :disabled="!batchTreeKey || !batchTreeKey.length">
                <DeleteOutlined />{{ t('cmdb.serviceTree.remove') }}
              </a-menu-item>
              <a-menu-divider />
            </template>
            <a-menu-item key="batchCancel"><CloseCircleOutlined />{{ t('cancel') }}</a-menu-item>
          </template>
        </a-menu>
        <EllipsisOutlined class="relation-views-node-operation" />
      </a-dropdown>
    </span>
  </div>
</template>

<style lang="less" scoped>
.relation-views-node {
  width: 100%;
  display: inline-flex;
  justify-content: space-between;
  align-items: center;
  .relation-views-node-switch {
    display: inline-block;
    width: 15px;
    color: @text-color_5;
    :deep(.anticon) {
      opacity: 0;
      font-size: 10px;
    }
  }
  .relation-views-node-content {
    display: flex;
    overflow: hidden;
    align-items: center;
    width: 100%;
    .relation-views-node-icon {
      display: inline-block;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background-color: #d3d3d3;
      color: #fff;
      text-align: center;
      line-height: 16px;
      font-size: 12px;
    }
    .relation-views-node-title {
      padding-left: 5px;
      text-overflow: ellipsis;
      white-space: nowrap;
      overflow: hidden;
      flex: 1;
      color: @text-color_1;
    }
    .relation-views-node-number {
      color: @text-color_4;
      font-size: 12px;
      margin: 0 5px;
    }
    .relation-views-node-operation {
      opacity: 0;
      width: 15px;
    }
  }
}
.relation-views-node-checkbox {
  > span {
    .relation-views-node-checkbox {
      margin-right: 10px;
    }
    .relation-views-node-title {
      width: calc(100% - 42px);
    }
  }
}

.relation-views-left .ant-tree:hover {
  .relation-views-node .relation-views-node-switch :deep(.anticon) {
    opacity: 1;
  }
}
</style>

<style lang="less">
.relation-views-node-title-highlight {
  color: @func-color_1;
}
.relation-views-left {
  ul:has(.relation-views-node-checkbox) > li > ul {
    margin-left: 26px;
  }
  ul:has(.relation-views-node-checkbox) {
    margin-left: 0 !important;
  }
  .ant-tree-node-content-wrapper:hover {
    .relation-views-node-operation {
      opacity: 1;
    }
  }
  .ant-tree li .ant-tree-node-content-wrapper.ant-tree-node-selected,
  .ant-tree li .ant-tree-node-content-wrapper:hover {
    background-color: @primary-color_3;
  }
}

.relation-views-node-dropdown {
  .ant-divider {
    margin: 0;
    .ant-divider-inner-text {
      font-size: 12px;
      color: @text-color_3;
    }
  }
  .ant-dropdown-menu-item {
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>
