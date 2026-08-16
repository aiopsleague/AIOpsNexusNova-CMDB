<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { TableOutlined, ApartmentOutlined, CloseOutlined } from '@ant-design/icons-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import {
  subscribeCIType,
  getSubscribeAttributes,
  getSubscribeTreeView,
  subscribeTreeView,
} from '@/modules/cmdb/api/preference'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import AttributesTransfer from '../attributesTransfer/index.vue'
import { CI_DEFAULT_ATTR } from '@/modules/cmdb/constants'

/**
 * Drawer for subscribing a CI type's visible attributes (instance table) or its
 * tree-view levels. `open(ciType, activeKey)` is exposed so the parent can
 * launch it directly.
 */
const emit = defineEmits<{ (e: 'reload'): void }>()

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const visible = ref(false)
const activeKey = ref('1')
const ciType = ref<Record<string, any>>({})
const instanceSubscribed = ref(false)
const treeSubscribed = ref(false)
const attrList = ref<any[]>([])
const selectedAttrList = ref<Array<string | number>>([])
const treeViews = ref<string[]>([])
const fixedList = ref<Array<string | number>>([])

const windowHeight = computed(() => window.innerHeight)

const treeViewAttrList = computed(() =>
  attrList.value.filter(
    (item) => ![CI_DEFAULT_ATTR.UPDATE_USER, CI_DEFAULT_ATTR.UPDATE_TIME].includes(item.name)
  )
)

function open(nextCiType: Record<string, any> = {}, nextActiveKey = '1') {
  ciType.value = nextCiType
  activeKey.value = nextActiveKey
  const updatedByKey = CI_DEFAULT_ATTR.UPDATE_USER
  const updatedAtKey = CI_DEFAULT_ATTR.UPDATE_TIME

  getCITypeAttributesById(nextCiType.type_id).then((res) => {
    const attributes = res.attributes.filter(
      (item: any) => ![updatedByKey, updatedAtKey].includes(item.name)
    )

    ;[updatedByKey, updatedAtKey].forEach((key) => {
      attributes.push({ alias: key, name: key, id: key })
    })

    getSubscribeAttributes(nextCiType.type_id).then((_res) => {
      instanceSubscribed.value = _res.is_subscribed
      const selected = _res.attributes.map((item: any) => item.id.toString())

      const list = attributes.map((item: any) => ({
        key: item.id.toString(),
        title: item.alias || item.name,
        name: item.name,
      }))

      attrList.value = list
      selectedAttrList.value = selected
      fixedList.value = _res.attributes
        .filter((item: any) => item.is_fixed)
        .map((item: any) => item.id.toString())
      visible.value = true
    })
  })
  getTreeView(nextCiType.type_id)
}

function getTreeView(typeId: string | number) {
  treeViews.value = []
  getSubscribeTreeView().then((res: any[]) => {
    let hasMatch = false
    res.forEach((item) => {
      if (item.type_id === typeId) {
        hasMatch = true
        const levels: string[] = []
        if (item.levels && item.levels.length >= 1) {
          item.levels.forEach((level: any) => {
            levels.push(level.name)
          })
        }
        treeSubscribed.value = levels.length > 0
        treeViews.value = levels
      }
    })
    if (!hasMatch) {
      treeSubscribed.value = false
    }
  })
}

function onClose() {
  if (!treeSubscribed.value) {
    if (Number(route.params.typeId) === Number(ciType.value.type_id)) {
      router.push('/cmdb/tree_views')
      emit('reload')
    } else {
      emit('reload')
    }
  } else {
    emit('reload')
  }
  visible.value = false
  activeKey.value = '1'
}

function subTreeSubmit() {
  subscribeTreeView(ciType.value.type_id, treeViews.value).then(() => {
    message.success(t('cmdb.components.subSuccess'))
    treeSubscribed.value = treeViews.value.length > 0
  })
}

function subInstanceSubmit() {
  const customAttr: Array<string | number> = []
  const defaultAttr: Array<string | number> = []
  selectedAttrList.value.forEach((attr) => {
    if ([CI_DEFAULT_ATTR.UPDATE_USER, CI_DEFAULT_ATTR.UPDATE_TIME].includes(attr as string)) {
      defaultAttr.push(attr)
    } else {
      customAttr.push(attr)
    }
  })
  const selected = [...customAttr, ...defaultAttr]

  subscribeCIType(
    ciType.value.type_id,
    selected.map((item) => [item, !!fixedList.value.includes(item)])
  ).then(() => {
    message.success(t('cmdb.components.subSuccess'))
    instanceSubscribed.value = selectedAttrList.value.length > 0
  })
}

function setTargetKeys(targetKeys: Array<string | number>) {
  selectedAttrList.value = targetKeys
}

function changeSingleItem(item: { key: string | number }) {
  const idx = selectedAttrList.value.findIndex((key) => key === item.key)
  if (idx > -1) {
    selectedAttrList.value.splice(idx, 1)
  } else {
    selectedAttrList.value.push(item.key)
  }
}

function setFixedList(nextFixedList: Array<string | number>) {
  fixedList.value = nextFixedList
}

function changeTreeViews(attr: { name: string }) {
  const idx = treeViews.value.findIndex((item) => item === attr.name)
  if (idx > -1) {
    treeViews.value.splice(idx, 1)
  } else {
    treeViews.value.push(attr.name)
  }
}

function closeTreeViews(_item: string, idx: number) {
  treeViews.value.splice(idx, 1)
}

function getDisplayAttr(item: string) {
  const found = attrList.value.find((attr) => attr.name === item)
  return found?.title ?? item
}

defineExpose({ open })
</script>

<template>
  <CustomDrawer
    :width="600"
    :open="visible"
    :has-title="false"
    :has-footer="false"
    :mask-closable="false"
    :body-style="{ padding: 0 }"
    wrap-class-name="cmdb-subscribe-drawer"
    @close="onClose"
  >
    <a-tabs v-model:active-key="activeKey">
      <a-tab-pane key="1">
        <template #tab><TableOutlined />{{ t('cmdb.menu.ciTable') }}</template>
        <div class="cmdb-subscribe-drawer-container" :style="{ height: `${windowHeight - 60}px` }">
          <div class="cmdb-subscribe-drawer-container-title">
            <span>{{ t('cmdb.components.subCIType') }}: {{ ciType.alias || ciType.name }}</span>
            <span :style="{ fontWeight: 500, color: instanceSubscribed ? 'green' : 'red' }">
              （{{ instanceSubscribed ? t('cmdb.components.already') : t('cmdb.components.not')
              }}{{ t('cmdb.components.sub') }}）
            </span>
          </div>
          <AttributesTransfer
            :data-source="attrList"
            :target-keys="selectedAttrList"
            :has-footer="false"
            :fixed-list="fixedList"
            :height="windowHeight - 170"
            :show-default-attr="true"
            @set-target-keys="setTargetKeys"
            @change-single-item="changeSingleItem"
            @set-fixed-list="setFixedList"
          />
          <div class="custom-drawer-bottom-action">
            <a-button type="primary" @click="subInstanceSubmit">{{ t('cmdb.preference.sub') }}</a-button>
          </div>
        </div>
      </a-tab-pane>
      <a-tab-pane key="2" force-render>
        <template #tab><ApartmentOutlined />{{ t('cmdb.menu.ciTree') }}</template>
        <div class="cmdb-subscribe-drawer-container" :style="{ height: `${windowHeight - 60}px` }">
          <div class="cmdb-subscribe-drawer-container-title">
            <span>{{ t('cmdb.components.subCIType') }}: {{ ciType.alias || ciType.name }}</span>
            <span :style="{ fontWeight: 500, color: treeSubscribed ? 'green' : 'red' }">
              （{{ treeSubscribed ? t('cmdb.components.already') : t('cmdb.components.not')
              }}{{ t('cmdb.components.sub') }}）
            </span>
          </div>
          <div
            class="cmdb-subscribe-drawer-tree-header"
            :style="{ maxHeight: `${(windowHeight - 170) / 3 - 20}px` }"
          >
            <span v-if="!treeViews.length">{{ t('cmdb.components.selectBelow') }}</span>
            <div
              v-for="(item, index) in treeViews"
              :key="item"
              class="cmdb-subscribe-drawer-tree-header-selected"
              :style="{ marginLeft: `${18 * index}px` }"
            >
              <span>
                {{ getDisplayAttr(item) }}
                <CloseOutlined
                  class="cmdb-subscribe-drawer-tree-header-selected-close"
                  @click="closeTreeViews(item, index)"
                />
              </span>
            </div>
          </div>
          <div
            class="cmdb-subscribe-drawer-tree-main"
            :style="{ maxHeight: `${((windowHeight - 170) * 2) / 3}px` }"
          >
            <div v-for="attr in treeViewAttrList" :key="attr.name" @click="changeTreeViews(attr)">
              <a-checkbox :checked="treeViews.includes(attr.name)" />
              {{ attr.title }}
            </div>
          </div>
          <div class="custom-drawer-bottom-action">
            <a-button type="primary" @click="subTreeSubmit">{{ t('cmdb.preference.sub') }}</a-button>
          </div>
        </div>
      </a-tab-pane>
    </a-tabs>
  </CustomDrawer>
</template>

<style lang="less" scoped>
.cmdb-subscribe-drawer {
  .cmdb-subscribe-drawer-container {
    padding: 0 24px;
    .cmdb-subscribe-drawer-container-title {
      margin-bottom: 12px;
    }
    .cmdb-subscribe-drawer-tree-header {
      border-radius: 4px;
      background-color: @primary-color_5;
      color: rgba(0, 0, 0, 0.4);
      padding: 8px 12px;
      margin-bottom: 12px;
      overflow: auto;
      .cmdb-subscribe-drawer-tree-header-selected {
        color: #a5a9bc;
        margin-bottom: 10px;
        > span {
          display: inline-block;
          background-color: #fff;
          border-left: 2px solid @primary-color;
          padding: 3px 12px;
          position: relative;
          white-space: nowrap;
          .cmdb-subscribe-drawer-tree-header-selected-close {
            cursor: pointer;
            font-size: 12px;
            &:hover {
              color: @primary-color;
            }
          }
        }
      }
      .cmdb-subscribe-drawer-tree-header-selected:not(:first-child) {
        > span::after {
          content: '';
          position: absolute;
          background-color: rgba(47, 84, 235, 0.5);
          height: 1px;
          width: 18px;
          left: -18px;
          top: 14px;
        }
      }
      .cmdb-subscribe-drawer-tree-header-selected:not(:last-child) {
        > span::before {
          content: '';
          position: absolute;
          width: 1px;
          height: 25px;
          left: -1px;
          top: 27px;
          background-color: rgba(47, 84, 235, 0.5);
        }
      }
    }
    .cmdb-subscribe-drawer-tree-main {
      background-color: #fff;
      box-shadow: -1px 5px 10px #dee3f9;
      padding: 10px 18px;
      overflow: auto;
      > div {
        height: 30px;
      }
    }
  }
}
</style>

<style lang="less">
.cmdb-subscribe-drawer {
  .ant-tabs-bar {
    background-color: @primary-color_5;
    border-bottom: none;
  }
}
</style>
