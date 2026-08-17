<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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
import ServiceTreeModal from './serviceTreeModal.vue'

const { t } = useI18n()

const isEdit = ref(false)
const relationViews = ref<any>({})
const checkedNodes = ref<any[]>([])
const loading = ref(false)
const graphJsonData = ref<any>({})

const serviceTreeModalRef = ref<InstanceType<typeof ServiceTreeModal>>()

const windowHeight = computed(() => window.innerHeight)

async function getMainData() {
  const { relations: ciTypeRelations } = await getCITypeRelations()
  const nodes: any[] = []
  const links: any[] = []
  ciTypeRelations.forEach((item: any) => {
    links.push({
      from: `${item.parent_id}`,
      to: `${item.child_id}`,
      text: item.relation_type.name,
      disableDefaultClickEffect: true,
    })
    if (nodes.findIndex((node: any) => String(node.id) === String(item.child_id)) < 0) {
      nodes.push({
        id: `${item.child_id}`,
        name: item.child.alias || item.child.name,
        nodeShape: 1,
        borderWidth: -1,
        disableDefaultClickEffect: true,
      })
    }
    if (nodes.findIndex((node: any) => String(node.id) === String(item.parent_id)) < 0) {
      nodes.push({
        id: `${item.parent_id}`,
        name: item.parent.alias || item.parent.name,
        nodeShape: 1,
        borderWidth: -1,
        disableDefaultClickEffect: true,
      })
    }
  })
  const _from = links.map((item: any) => item.from)
  const _to = links.map((item: any) => item.to)
  const rootId = findMost([..._from, _to])
  graphJsonData.value = { rootId, nodes, links }
  // TODO: render the CI type relation graph (SeeksRelationGraph / relation-graph not yet ported).
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

async function getViewsData() {
  loading.value = true
  const data = await getRelationView()
  relationViews.value = data
  // TODO: render each service-tree view with the relation graph (SeeksRelationGraph not yet ported).
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

function handleSave() {
  // TODO: persist the CI type relation graph layout (graph rendering not yet ported).
  console.log(graphJsonData.value)
}

function cancelEdit() {
  isEdit.value = false
  checkedNodes.value = []
}

onMounted(() => {
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
      <!-- TODO: render the CI type relation graph (SeeksRelationGraph / relation-graph not yet ported). -->
      <div class="ci-type-relation-graph-stub">{{ t('cmdb.preference_relation.tips5') }}</div>
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
            <!-- TODO: render service-tree view graph (SeeksRelationGraph not yet ported). -->
            <div :style="{ height: '250px' }"></div>
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
    .ci-type-relation-graph-stub {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      min-height: 250px;
      color: @text-color_3;
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
