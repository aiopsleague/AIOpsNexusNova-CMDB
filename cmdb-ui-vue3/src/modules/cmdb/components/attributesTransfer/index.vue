<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { HolderOutlined, LockOutlined, UnlockOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons-vue'
import { CI_DEFAULT_ATTR } from '@/modules/cmdb/constants'

interface TransferItem {
  key: string | number
  title: string
  name: string
  [key: string]: any
}

const props = withDefaults(
  defineProps<{
    dataSource?: TransferItem[]
    targetKeys?: Array<string | number>
    hasFooter?: boolean
    isSortable?: boolean
    isFixable?: boolean
    fixedList?: Array<string | number>
    height?: number
    showDefaultAttr?: boolean
  }>(),
  {
    dataSource: () => [],
    targetKeys: () => [],
    hasFooter: true,
    isSortable: true,
    isFixable: true,
    fixedList: () => [],
    height: 400,
    showDefaultAttr: false,
  }
)

const emit = defineEmits<{
  (e: 'setTargetKeys', keys: Array<string | number>): void
  (e: 'handleSubmit'): void
  (e: 'changeSingleItem', item: TransferItem): void
  (e: 'setFixedList', keys: Array<string | number>): void
}>()

const { t } = useI18n()

const selectedKeys = ref<Array<string | number>>([])
const searchLeft = ref('')
const searchRight = ref('')
const dragIndex = ref(-1)

const defaultAttrList: TransferItem[] = [
  { title: 'cmdb.components.updater', name: 'updater', key: CI_DEFAULT_ATTR.UPDATE_USER },
  { title: 'cmdb.components.updateTime', name: 'update time', key: CI_DEFAULT_ATTR.UPDATE_TIME },
]

function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function filterOption(inputValue: string, option: TransferItem): boolean {
  const value = inputValue.toLowerCase()
  return (
    option.title.toLowerCase().includes(value) || option.name.toLowerCase().includes(value)
  )
}

const defaultAttrKeys = new Set<string>([CI_DEFAULT_ATTR.UPDATE_USER, CI_DEFAULT_ATTR.UPDATE_TIME])

function filterDefaultAttr(list: TransferItem[]): TransferItem[] {
  return props.showDefaultAttr ? list.filter((item) => !defaultAttrKeys.has(String(item.key))) : list
}

const rightOrderedItems = computed<TransferItem[]>(() => {
  return props.targetKeys
    .map((key) => props.dataSource.find((item) => item.key === key))
    .filter((item): item is TransferItem => !!item)
})

const leftItems = computed<TransferItem[]>(() => {
  const targetSet = new Set(props.targetKeys)
  return props.dataSource.filter((item) => !targetSet.has(item.key))
})

const leftFilteredItems = computed(() => filterDefaultAttr(leftItems.value).filter((item) => filterOption(searchLeft.value, item)))
const rightFilteredItems = computed(() =>
  filterDefaultAttr(rightOrderedItems.value).filter((item) => filterOption(searchRight.value, item))
)

const rightDefaultAttrList = computed<TransferItem[]>(() => {
  if (!props.showDefaultAttr) {
    return []
  }
  return defaultAttrList.filter((item) => props.targetKeys.includes(item.key))
})

const leftDefaultAttrList = computed<TransferItem[]>(() => {
  if (!props.showDefaultAttr) {
    return []
  }
  return defaultAttrList.filter((item) => !props.targetKeys.includes(item.key))
})

function setSelectedKeys(item: TransferItem) {
  const idx = selectedKeys.value.findIndex((key) => key === item.key)
  if (idx > -1) {
    selectedKeys.value.splice(idx, 1)
  } else {
    selectedKeys.value.push(item.key)
  }
}

function changeSingleItem(item: TransferItem) {
  emit('changeSingleItem', item)
}

function moveToRight() {
  const keys = [...new Set([...props.targetKeys, ...selectedKeys.value])]
  emit('setTargetKeys', keys)
}

function moveToLeft() {
  const selectedSet = new Set(selectedKeys.value)
  const keys = props.targetKeys.filter((key) => !selectedSet.has(key))
  emit('setTargetKeys', keys)
}

function changeFixed(e: MouseEvent, item: TransferItem) {
  e.stopPropagation()
  e.preventDefault()
  const fixedList = cloneDeep(props.fixedList)
  const idx = fixedList.findIndex((key) => key === item.key)
  if (idx > -1) {
    fixedList.splice(idx, 1)
  } else {
    fixedList.push(item.key)
  }
  emit('setFixedList', fixedList)
}

function onDragStart(index: number, e: DragEvent) {
  dragIndex.value = index
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
  }
}

function onDrop(index: number) {
  if (dragIndex.value < 0 || dragIndex.value === index) {
    dragIndex.value = -1
    return
  }
  const targetKeys = cloneDeep(props.targetKeys)
  const moved = targetKeys.splice(dragIndex.value, 1)[0]
  targetKeys.splice(index, 0, moved)
  emit('setTargetKeys', targetKeys)
  dragIndex.value = -1
}

function handleSubmit() {
  emit('handleSubmit')
}
</script>

<template>
  <div class="cmdb-transfer" :style="{ height: `${height}px` }">
    <div class="cmdb-transfer-list">
      <div class="cmdb-transfer-list-header">
        <span class="cmdb-transfer-list-header-title">{{ t('cmdb.components.unselectAttributes') }}</span>
      </div>
      <div class="cmdb-transfer-list-body-search-wrapper">
        <a-input v-model:value="searchLeft" size="small" :placeholder="t('search')" allow-clear />
      </div>
      <div class="cmdb-transfer-list-content">
        <div v-for="item in leftFilteredItems" :key="item.key" class="cmdb-transfer-list-content-item-wrap">
          <div
            :class="[
              'cmdb-transfer-list-content-item',
              selectedKeys.includes(item.key) ? 'cmdb-transfer-list-content-item-selected' : '',
            ]"
            @click="setSelectedKeys(item)"
            @dblclick="changeSingleItem(item)"
          >
            <div class="cmdb-transfer-list-content-item-text">
              {{ item.title }}
              <span class="cmdb-transfer-list-content-item-name">{{ item.name }}</span>
            </div>
            <RightOutlined class="cmdb-transfer-list-icon" @click="changeSingleItem(item)" />
          </div>
        </div>
        <div v-if="leftDefaultAttrList.length" class="cmdb-transfer-default-attr">
          <a-divider><span class="cmdb-transfer-default-attr-divider">{{ t('cmdb.components.default') }}</span></a-divider>
          <div
            v-for="item in leftDefaultAttrList"
            :key="item.key"
            :class="['cmdb-transfer-default-attr-item', selectedKeys.includes(item.key) ? 'cmdb-transfer-default-attr-item-selected' : '']"
            @click="setSelectedKeys(item)"
            @dblclick="changeSingleItem(item)"
          >
            <div class="cmdb-transfer-default-attr-title">{{ t(item.title) }}</div>
            <div class="cmdb-transfer-default-attr-name">{{ item.name }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="cmdb-transfer-operation">
      <div class="cmdb-transfer-operation-btn" @click="moveToRight"><RightOutlined /></div>
      <div class="cmdb-transfer-operation-btn" @click="moveToLeft"><LeftOutlined /></div>
    </div>

    <div class="cmdb-transfer-list">
      <div class="cmdb-transfer-list-header">
        <span class="cmdb-transfer-list-header-title">{{ t('cmdb.components.selectAttributes') }}</span>
      </div>
      <div class="cmdb-transfer-list-body-search-wrapper">
        <a-input v-model:value="searchRight" size="small" :placeholder="t('search')" allow-clear />
      </div>
      <div class="cmdb-transfer-list-content">
        <div
          v-for="(item, index) in rightFilteredItems"
          :key="item.key"
          :draggable="isSortable"
          class="cmdb-transfer-list-content-item-wrap"
          @dragstart="onDragStart(index, $event)"
          @dragover.prevent
          @drop="onDrop(index)"
        >
          <div
            :class="[
              'cmdb-transfer-list-content-item',
              selectedKeys.includes(item.key) ? 'cmdb-transfer-list-content-item-selected' : '',
            ]"
            @click="setSelectedKeys(item)"
            @dblclick="changeSingleItem(item)"
          >
            <HolderOutlined v-if="isSortable" class="cmdb-transfer-move-icon" />
            <div class="cmdb-transfer-list-content-item-text">
              {{ item.title }}
              <span class="cmdb-transfer-list-content-item-name">{{ item.name }}</span>
            </div>
            <span v-if="isFixable" class="cmdb-transfer-list-lock-icon" @click="(e) => changeFixed(e, item)">
              <LockOutlined v-if="fixedList.includes(item.key)" />
              <UnlockOutlined v-else />
            </span>
            <LeftOutlined class="cmdb-transfer-list-icon" @click="changeSingleItem(item)" />
          </div>
        </div>
        <div v-if="rightDefaultAttrList.length" class="cmdb-transfer-default-attr">
          <a-divider><span class="cmdb-transfer-default-attr-divider">{{ t('cmdb.components.default') }}</span></a-divider>
          <div
            v-for="item in rightDefaultAttrList"
            :key="item.key"
            :class="['cmdb-transfer-default-attr-item', selectedKeys.includes(item.key) ? 'cmdb-transfer-default-attr-item-selected' : '']"
            @click="setSelectedKeys(item)"
            @dblclick="changeSingleItem(item)"
          >
            <div class="cmdb-transfer-default-attr-title">{{ t(item.title) }}</div>
            <div class="cmdb-transfer-default-attr-name">{{ item.name }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div v-if="hasFooter" class="cmdb-transfer-footer">
    <a-button size="small" type="primary" @click="handleSubmit">{{ t('confirm') }}</a-button>
  </div>
</template>

<style scoped>
.cmdb-transfer {
  display: flex;
  width: 100%;
}
.cmdb-transfer-list {
  width: 45%;
  height: 100%;
  background-color: #f9fbff;
  border: 1px solid #e4e7ed;
  border-radius: 2px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.cmdb-transfer-list-header {
  background-color: #f9fbff;
  border-bottom: none;
  padding: 8px 12px;
}
.cmdb-transfer-list-header-title {
  color: #2f54eb;
  font-weight: 400;
  font-size: 14px;
}
.cmdb-transfer-list-body-search-wrapper {
  padding: 0 8px 5px;
}
.cmdb-transfer-list-content {
  flex: 1;
  overflow: auto;
}
.cmdb-transfer-list-content-item-wrap {
  padding: 0 12px;
}
.cmdb-transfer-list-content-item {
  transition: all 0.3s;
  border-left: 2px solid #f9fbff;
  padding: 8px 12px 8px 25px;
  position: relative;
  cursor: pointer;
}
.cmdb-transfer-list-content-item-text {
  display: inline;
  position: relative;
}
.cmdb-transfer-list-content-item-name {
  position: absolute;
  top: 15px;
  left: 0;
  font-size: 11px;
  color: #a3a3a3;
  white-space: nowrap;
}
.cmdb-transfer-list-content-item-selected {
  background-color: #f0f5ff;
  border-color: #2f54eb;
}
.cmdb-transfer-list-icon {
  position: absolute;
  top: 6px;
  right: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #2f54eb;
}
.cmdb-transfer-move-icon {
  position: absolute;
  left: 4px;
  top: 6px;
  width: 14px;
  height: 20px;
  cursor: move;
}
.cmdb-transfer-list-lock-icon {
  position: absolute;
  top: 6px;
  right: 20px;
  cursor: pointer;
  font-size: 12px;
  color: #cacdd9;
}
.cmdb-transfer-list-lock-icon:hover {
  color: #2f54eb;
}
.cmdb-transfer-operation {
  width: 10%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 8px;
}
.cmdb-transfer-operation-btn {
  width: 20px;
  height: 20px;
  border-radius: 2px;
  background-color: #f0f5ff;
  color: #2f54eb;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}
.cmdb-transfer-operation-btn:hover {
  background-color: #2f54eb;
  color: #fff;
}
.cmdb-transfer-default-attr-divider {
  font-size: 12px;
  color: #86909c;
}
.cmdb-transfer-default-attr-item {
  padding-left: 34px;
  padding-top: 4px;
  padding-bottom: 4px;
  position: relative;
  border-left: solid 2px transparent;
  margin-bottom: 6px;
  cursor: pointer;
}
.cmdb-transfer-default-attr-item-selected {
  background-color: #f0f5ff;
  border-color: #2f54eb;
}
.cmdb-transfer-default-attr-item:hover {
  background-color: #f0f5ff;
}
.cmdb-transfer-default-attr-title {
  font-size: 14px;
  line-height: 14px;
  font-weight: 400;
}
.cmdb-transfer-default-attr-name {
  font-size: 11px;
  line-height: 12px;
  color: #a3a3a3;
}
.cmdb-transfer-footer {
  margin-top: 5px;
  height: 20px;
  text-align: right;
}
</style>
