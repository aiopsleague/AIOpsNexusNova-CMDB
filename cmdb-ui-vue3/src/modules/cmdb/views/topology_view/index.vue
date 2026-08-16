<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  PlusOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  UserAddOutlined,
  MenuOutlined,
  SearchOutlined,
  PlayCircleOutlined,
  HolderOutlined,
} from '@ant-design/icons-vue'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import emptyImage from '@/assets/data_empty.png'
import SplitPane from '@/components/SplitPane/SplitPane.vue'
import { roleHasPermissionToGrant } from '@/modules/acl/api/permission'
import { searchResourceType } from '@/modules/acl/api/resource'
import CMDBGrant from '@/modules/cmdb/components/cmdbGrant/index.vue'
import {
  getTopoGroups,
  postTopoGroup,
  putTopoGroupByGId,
  deleteTopoGroup,
  getTopoView,
  addTopoView,
  updateTopoView,
  deleteTopoView,
  getRelationsByTypeId as getRelationsByTypeIdApi,
  previewTopoView,
  showTopoView as showTopoViewApi,
} from '@/modules/cmdb/api/topology'
import CMDBExprDrawer from '@/components/CMDBExprDrawer/index.vue'
import CMDBTypeSelectAntd from '@/modules/cmdb/components/cmdbTypeSelect/cmdbTypeSelectAntd.vue'
import { useUserStore } from '@/stores/user'

const currentTopoKey = 'ops_cmdb_topo_currentId'

const { t } = useI18n()
const userStore = useUserStore()

const cmdbDrawerRef = ref<InstanceType<typeof CMDBExprDrawer>>()
const cmdbGrantRef = ref<InstanceType<typeof CMDBGrant>>()
const formRef = ref()

const paneLengthPixel = ref(250)
const loading = ref(false)
const searchValue = ref('')

const currentId = ref<string | null>(null)
const topoGroups = ref<any[]>([])
const CITypeId = ref<number | null>(null)

const modalTitle = ref(t('cmdb.ciType.addGroup'))
const modalVisible = ref(false)
const editingGroup = ref<any>({})
const editingInput = ref('')

const resource_type = ref<Record<string, any>>({})

const drawerVisible = ref(false)
const drawerTitle = ref('')
const selectGroup = ref<any>({})

const isShowPreview = ref(false)

const checkedNodes = ref<string[]>([])
const nodes = ref<any[]>([])

const currentNodes = ref<any[]>([])
const isShowNodeTipsPanel = ref(false)

const errorMessageShow = ref(false)

const topoViewJsonData = ref<any>({})
const topoViewOption = ref<Record<string, any>>({})
const topoViewSearchValue = ref('')

const formModel = reactive<{
  id?: number
  name?: string
  central_node_type?: number
  central_node_instances?: string
  aggregation_count?: number
}>({
  id: undefined,
  name: undefined,
  central_node_type: undefined,
  central_node_instances: undefined,
  aggregation_count: undefined,
})

const rules = {
  name: [{ required: true, message: t('cmdb.topo.inputNameTips') }],
  central_node_type: [{ required: true, message: t('cmdb.topo.typeRequired') }],
  central_node_instances: [{ required: true, message: t('cmdb.topo.instancesRequired') }],
}

const permissions = computed<string[]>(() => (userStore.roles?.permissions ?? []).map((p: any) => p.name))
const windowHeight = computed(() => window.innerHeight)
const currentGId = computed(() => {
  if (currentId.value) {
    return Number(currentId.value.split('%')[0])
  }
  return null
})
const currentCId = computed(() => {
  if (currentId.value) {
    if (currentId.value.split('%')[1] !== 'null') {
      return Number(currentId.value.split('%')[1])
    }
    return null
  }
  return null
})
const computedTopoGroups = computed(() => {
  if (searchValue.value) {
    const groups = cloneDeep(topoGroups.value)
    groups.forEach((item: any) => {
      item.views = item.views.filter((_item: any) =>
        _item.name.toLowerCase().includes(searchValue.value.toLowerCase())
      )
    })
    return groups
  }
  return topoGroups.value
})

function closeNodeTips() {
  if (isShowNodeTipsPanel.value === true) {
    isShowNodeTipsPanel.value = false
  }
  if (errorMessageShow.value === true) {
    errorMessageShow.value = false
  }
}

function handleClickAddGroup() {
  editingGroup.value = {}
  editingInput.value = ''
  modalTitle.value = t('cmdb.ciType.addGroup')
  modalVisible.value = true
}

function handleClickGroup(gId: number) {
  currentId.value = null
  nextTick(() => {
    currentId.value = `${gId}%null%null`
    localStorage.setItem(currentTopoKey, currentId.value)
  })
}

function handleClickView(gId: number, viewId: number, viewName: string) {
  currentId.value = null
  nextTick(() => {
    currentId.value = `${gId}%${viewId}%${viewName}`
    localStorage.setItem(currentTopoKey, currentId.value)
    showTopoView(viewId)
  })
}

function handleEditGroup(g: any) {
  editingGroup.value = g
  editingInput.value = g.name
  modalTitle.value = t('cmdb.ciType.editGroup')
  modalVisible.value = true
}

function handleDeleteGroup(g: any) {
  if (g.views && g.views.length > 0) {
    message.error(t('cmdb.ciType.cannotDeleteGroupTips'))
    return
  }
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ciType.confirmDeleteGroup', { groupName: `${g.name}` }),
    onOk() {
      deleteTopoGroup(g.id).then(() => {
        message.success(t('deleteSuccess'))
        loadTopoViews(true)
      })
    },
  })
}

async function loadTopoViews(isResetCurrentId = false) {
  const groups = await getTopoGroups()
  let alreadyReset = false
  if (isResetCurrentId) {
    currentId.value = null
  }
  nextTick(() => {
    groups.forEach((g: any) => {
      if (isResetCurrentId && !alreadyReset && g.views && g.views.length) {
        currentId.value = `${g.id}%${g.views[0].id}%${g.views[0].name}`
        alreadyReset = true
      }
      if (!g.views) {
        g.views = []
      }
    })
    topoGroups.value = groups
    localStorage.setItem(currentTopoKey, currentId.value ?? '')
  })
}

async function handleSubmitEditGroup() {
  if (editingGroup.value && editingGroup.value.id) {
    await putTopoGroupByGId(editingGroup.value.id, {
      name: editingInput.value,
      view_ids: editingGroup.value.views.map((i: any) => i.id),
    })
    message.success(t('updateSuccess'))
  } else {
    const { id } = await postTopoGroup({ name: editingInput.value })
    currentId.value = `${id}%null%null`
    message.success(t('addSuccess'))
  }
  modalVisible.value = false
  loadTopoViews()
}

function handleCreate(g: any) {
  drawerTitle.value = t('cmdb.topo.addTopoView')
  drawerVisible.value = true
  selectGroup.value = g
}

function handleCreateViewFromEmpty() {
  drawerTitle.value = t('cmdb.topo.addTopoView')
  drawerVisible.value = true
  const _find = topoGroups.value.find((item) => item.id === currentGId.value)
  selectGroup.value = _find
}

async function handleSubmit() {
  formRef.value
    .validate()
    .then(async () => {
      const { name, central_node_type, central_node_instances, aggregation_count } = formModel
      const payload: Record<string, any> = { name, central_node_type, central_node_instances }
      if (aggregation_count) {
        payload.option = { aggregation_count }
      } else {
        payload.option = {}
      }
      if (selectGroup.value && selectGroup.value.id) {
        payload.group_id = selectGroup.value.id
      }
      payload.path = wrapPath()
      loading.value = true
      if (formModel.id) {
        await updateTopoView(formModel.id, payload).then((res: any) => {
          const { id } = res
          currentId.value = `${selectGroup.value?.id || ''}%${id}%${payload.name}`
          showTopoView(id)
        })
      } else {
        if (!payload.group_id) {
          message.error(t('cmdb.topo.groupRequired'))
          loading.value = false
          return
        }
        await addTopoView(payload).then((res: any) => {
          const { id } = res
          currentId.value = `${selectGroup.value?.id || ''}%${id}%${payload.name}`
          showTopoView(id)
        })
      }
      localStorage.setItem(currentTopoKey, currentId.value ?? '')
      setTimeout(() => {
        loadTopoViews()
      }, 2000)
      drawerVisible.value = false
    })
    .catch(() => {})
  loading.value = false
}

function wrapPath() {
  const path: Record<string, string[]> = {}
  checkedNodes.value.forEach((nodeId) => {
    const _nodes = nodes.value.filter((i) => String(i.id) === nodeId)
    _nodes.forEach((_node) => {
      const levels = _node.level || [0]
      levels.forEach((level: number) => {
        if (level in path) {
          path[level].push(nodeId)
        } else {
          path[level] = [nodeId]
        }
      })
    })
  })
  return path
}

function onClose() {
  formRef.value?.resetFields()
  drawerVisible.value = false
}

function showPreview() {
  isShowPreview.value = true
  formRef.value
    .validate()
    .then(async () => {
      const payload = {
        central_node_type: formModel.central_node_type,
        central_node_instances: formModel.central_node_instances,
        path: wrapPath(),
      }
      previewTopoView(payload).then((res) => {
        const nodes: any[] = []
        const links: any[] = []
        res.links.forEach((item: any) => {
          links.push({
            from: `${item.from}`,
            to: `${item.to}`,
            disableDefaultClickEffect: true,
          })
        })
        const type2meta = res?.type2meta
        res.nodes.forEach((item: any) => {
          const icon = type2meta?.[item?.type_id] || ''
          nodes.push({
            id: `${item.id}`,
            text: item.name,
            data: { icon },
          })
        })
        if (!nodes.length) {
          message.error(t('cmdb.topo.noData'))
          return
        }
        // TODO: migrate topology (relation-graph) preview rendering.
      })
    })
    .catch(() => {})
}

async function showTopoView(viewId: number | string) {
  if (viewId === 'null' || !viewId) {
    return
  }
  const topoViewRes = await getTopoView(viewId)
  if (topoViewRes?.option) {
    topoViewOption.value = topoViewRes.option
  }
  showTopoViewApi(viewId).then(async (res) => {
    const nodes: any[] = []
    const links: any[] = []
    currentNodes.value = res.nodes
    const seenLinks = new Set()
    res.links.forEach((item: any) => {
      const from = `${item.from}`
      const to = `${item.to}`
      if (!from || !to || from === to) {
        return
      }
      const linkKey = from < to ? `${from}->${to}` : `${to}->${from}`
      if (seenLinks.has(linkKey)) {
        return
      }
      seenLinks.add(linkKey)
      links.push({ from, to })
    })
    const type2meta = res?.type2meta
    const nodeIds = new Set()
    res.nodes.forEach((item: any) => {
      const id = `${item.id}`
      if (nodeIds.has(id)) {
        return
      }
      nodeIds.add(id)
      const icon = type2meta?.[item?.type_id] || ''
      nodes.push({ id, text: item.name, data: { icon } })
    })
    if (!nodes.length) {
      message.error(t('cmdb.topo.noData'))
      return
    }
    // TODO: migrate topology (relation-graph) rendering. The node/link payload is
    // stored for the search filter until the graph renderer is ported.
    topoViewJsonData.value = { nodes: new Map(nodes.map((n) => [n.id, n])), links }
    topoViewSearchValue.value = ''
  })
}

function handleOpenCmdb() {
  cmdbDrawerRef.value?.open()
}

function copySuccess(text: string) {
  formModel.central_node_instances = `${text}`
}

async function CITypeChange(value: number) {
  CITypeId.value = value
  formModel.central_node_instances = ''
  checkedNodes.value = [String(value)]
  getRelationsByTypeId(value)
}

function handlePerm(v: any) {
  roleHasPermissionToGrant({
    app_id: 'cmdb',
    resource_type_name: 'TopologyView',
    perm: 'grant',
    resource_name: v.name,
  }).then((res: any) => {
    if (res.result) {
      cmdbGrantRef.value?.open({ name: v.name, cmdbGrantType: 'TopologyView', CITypeId: v.id })
    } else {
      message.error(t('noPermission'))
    }
  })
}

async function handleEdit(record: any) {
  drawerTitle.value = t('cmdb.topo.editTopoView')
  drawerVisible.value = true
  await getTopoView(record.id)
  nextTick(() => {
    formModel.id = record.id
    formModel.name = record.name
    formModel.central_node_type = record.central_node_type
    formModel.central_node_instances = record.central_node_instances
    formModel.aggregation_count = record.option?.aggregation_count
  })
  const nextCheckedNodes: string[] = []
  Object.values(record.path).forEach((item: any) => {
    nextCheckedNodes.push(...item)
  })
  checkedNodes.value = Array.from(new Set(nextCheckedNodes))
  await getRelationsByTypeId(record.central_node_type)
  CITypeId.value = record.central_node_type
}

function handleDelete(record: any) {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.topo.confirmDeleteView', { viewName: `${record.name}` }),
    onOk() {
      deleteTopoView(record.id).then(() => {
        message.success(t('deleteSuccess'))
        loadTopoViews(true)
      })
    },
  })
}

async function getRelationsByTypeId(typeId: number) {
  getRelationsByTypeIdApi(typeId).then((res) => {
    nodes.value = res.nodes
    if (!res.nodes?.length) {
      message.error(t('cmdb.topo.noData'))
      return
    }
    // TODO: migrate topology (relation-graph) path-selection rendering.
  })
}

onMounted(async () => {
  searchResourceType({ page_size: 9999, app_id: 'cmdb' }).then((res: any) => {
    resource_type.value = { groups: res.groups, id2perms: res.id2perms }
  })
  const _currentId = localStorage.getItem(currentTopoKey)
  if (_currentId) {
    currentId.value = _currentId
  }
  await loadTopoViews(!_currentId)
  if (currentId.value) {
    showTopoView(currentId.value.split('%')[1])
  }
})
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <div class="topo-wrap" :style="{ height: `${windowHeight - 96}px` }" @click="closeNodeTips">
    <div v-if="!topoGroups.length" class="topo-empty">
      <a-empty :image="emptyImage" description=""></a-empty>
      <a-button type="primary" size="small" @click="handleClickAddGroup">
        <template #icon><PlusOutlined /></template>
        {{ t('cmdb.ciType.addGroup') }}
      </a-button>
    </div>
    <SplitPane
      v-else
      :min="180"
      :max="300"
      v-model:pane-length-pixel="paneLengthPixel"
      app-name="cmdb-topo-views"
      :trigger-length="18"
      calc-based-parent
    >
      <template #one>
        <a-input
          v-model:value="searchValue"
          :placeholder="t('cmdb.topo.searchPlaceholder')"
          class="cmdb-topo-left-input"
        >
          <template #prefix><SearchOutlined /></template>
        </a-input>
        <div class="topo-left">
          <div class="topo-left-title">
            <a-button
              type="primary"
              size="small"
              ghost
              @click="handleClickAddGroup"
              class="ops-button-ghost"
              v-if="permissions.includes('admin') || permissions.includes('cmdb_admin')"
            >
              <template #icon><PlusOutlined /></template>
              {{ t('cmdb.ciType.group') }}
            </a-button>
          </div>
          <!-- TODO: restore drag-and-drop group/view reordering (vuedraggable not yet ported) -->
          <div class="topo-left-content">
            <div v-for="group in computedTopoGroups" :key="group.id || group.name">
              <div
                :class="`${currentGId === group.id && !currentCId ? 'selected' : ''} topo-left-group`"
                @click="handleClickGroup(group.id)"
              >
                <div>
                  <HolderOutlined
                    v-if="group.id"
                    style="width: 17px; height: 17px; display: none; position: absolute; left: 5px; top: 13px"
                  />
                  <span class="topo-left-group-name">{{ group.name || t('other') }}</span>
                  <span>{{ group.views.length }}</span>
                </div>
                <div class="topo-left-group-action">
                  <a-tooltip :title="t('cmdb.topo.addTopoViewInGroup')">
                    <a v-if="permissions.includes('admin') || permissions.includes('cmdb_admin')">
                      <PlusOutlined @click="handleCreate(group)" />
                    </a>
                  </a-tooltip>
                  <template v-if="group.id">
                    <a-tooltip :title="t('cmdb.ciType.editGroup')">
                      <a v-if="permissions.includes('admin') || permissions.includes('cmdb_admin')">
                        <EditOutlined @click="handleEditGroup(group)" />
                      </a>
                    </a-tooltip>
                    <a-tooltip :title="t('cmdb.ciType.deleteGroup')">
                      <a
                        v-if="permissions.includes('admin') || permissions.includes('cmdb_admin')"
                        :style="{ color: 'red' }"
                      >
                        <DeleteOutlined @click="handleDeleteGroup(group)" />
                      </a>
                    </a-tooltip>
                  </template>
                </div>
              </div>
              <div>
                <div
                  v-for="topo in group.views"
                  :key="topo.id"
                  :class="`${currentCId === topo.id ? 'selected' : ''} topo-left-detail`"
                  @click="handleClickView(group.id, topo.id, topo.name)"
                >
                  <div>
                    <HolderOutlined
                      v-if="group.id"
                      style="width: 17px; height: 17px; display: none; position: absolute; left: -1px; top: 8px"
                    />
                    <span class="topo-left-detail-icon">
                      <template v-if="topo.icon">
                        <img
                          v-if="topo.icon.split('$$')[2]"
                          :src="`/api/common-setting/v1/file/${topo.icon.split('$$')[3]}`"
                        />
                        <span
                          v-else
                          :style="{ color: topo.icon.split('$$')[1], fontSize: '14px' }"
                        >
                          {{ topo.icon.split('$$')[0] ? topo.icon.split('$$')[0][0].toUpperCase() : '' }}
                        </span>
                      </template>
                      <span class="primary-color" v-else>{{ topo.name[0].toUpperCase() }}</span>
                    </span>
                  </div>
                  <span class="topo-left-detail-title">{{ topo.alias || topo.name }}</span>
                  <a-dropdown>
                    <a class="topo-left-detail-action"><MoreOutlined /></a>
                    <template #overlay>
                      <a-menu>
                        <a-menu-item @click="handlePerm(topo)">
                          <UserAddOutlined />
                          {{ t('grant') }}
                        </a-menu-item>
                        <a-menu-item @click="handleEdit(topo)">
                          <EditOutlined />
                          {{ t('cmdb.topo.edit') }}
                        </a-menu-item>
                        <a-menu-item @click="handleDelete(topo)">
                          <DeleteOutlined />
                          {{ t('cmdb.topo.delete') }}
                        </a-menu-item>
                      </a-menu>
                    </template>
                  </a-dropdown>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
      <template #two>
        <div class="topo-right">
          <div v-if="currentCId" :style="{ height: `${windowHeight - 80}px` }">
            <!-- TODO: migrate topology (relation-graph/butterfly-dag). The graph
                 canvas is stubbed; data is fetched via showTopoView() above. -->
            <div class="topo-graph-stub">
              <a-empty :image="emptyImage" :description="t('cmdb.topo.topoViewSearchPlaceholder')" />
            </div>
          </div>
          <div v-else class="topo-right-empty">
            <a-empty :image="emptyImage" description=""></a-empty>
            <a-button
              type="primary"
              size="small"
              :disabled="!permissions.includes('admin') && !permissions.includes('cmdb_admin')"
              @click="handleCreateViewFromEmpty"
            >
              <template #icon><PlusOutlined /></template>
              {{ t('cmdb.topo.addTopoView') }}
            </a-button>
          </div>
        </div>
      </template>
    </SplitPane>
    <a-modal v-model:open="modalVisible" :title="modalTitle" @ok="handleSubmitEditGroup">
      <a-form-item :label="t('name')" :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
        <a-input v-model:value="editingInput" />
      </a-form-item>
    </a-modal>
    <CMDBExprDrawer
      ref="cmdbDrawerRef"
      type="resourceView"
      :type-id="CITypeId"
      @copy-success="copySuccess"
    />
    <CMDBGrant ref="cmdbGrantRef" resource-type="TopologyView" app_id="cmdb" />
    <a-drawer
      :open="drawerVisible"
      :title="drawerTitle"
      placement="right"
      width="900px"
      :closable="false"
      :body-style="{ height: 'calc(100vh - 108px)' }"
      @close="onClose"
    >
      <a-form ref="formRef" :model="formModel" :rules="rules" :label-col="{ span: 5 }" :wrapper-col="{ span: 16 }">
        <a-form-item :label="t('cmdb.topo.viewName')" name="name">
          <a-input v-model:value="formModel.name" :placeholder="t('cmdb.topo.viewNamePlaceholder')" />
        </a-form-item>
        <a-form-item :label="t('cmdb.topo.centralNodeType')" name="central_node_type">
          <CMDBTypeSelectAntd
            v-model="formModel.central_node_type"
            :placeholder="t('cmdb.ciType.selectModel')"
            @change="CITypeChange"
          />
          <div class="ant-form-explain">{{ t('cmdb.topo.centralNodeTypeTip') }}</div>
        </a-form-item>
        <a-form-item :label="t('cmdb.topo.filterInstances')" name="central_node_instances">
          <a-input
            v-model:value="formModel.central_node_instances"
            :placeholder="t('cmdb.ciType.selectFromCMDBTips')"
          >
            <template #suffix>
              <a @click="handleOpenCmdb"><MenuOutlined /></a>
            </template>
          </a-input>
          <div class="ant-form-explain">{{ t('cmdb.topo.filterInstancesTip') }}</div>
        </a-form-item>
        <a-form-item :label="t('cmdb.topo.path')" name="path">
          <!-- TODO: migrate topology path selection (SeeksRelationGraph / relation-graph). -->
          <div class="topo-path-stub">{{ t('cmdb.topo.centralNodeTypeTip') }}</div>
        </a-form-item>
        <a-form-item :label="t('cmdb.topo.aggregationCount')" name="aggregation_count" :help="t('cmdb.topo.aggreationCountTip')">
          <a-input-number v-model:value="formModel.aggregation_count" :style="{ width: '100%' }" :min="0" />
        </a-form-item>
        <div :class="{ 'chart-left-preview': true }">
          <span class="chart-left-preview-operation" :style="{ zIndex: '800' }" @click="showPreview">
            <PlayCircleOutlined />
            {{ t('cmdb.custom_dashboard.preview') }}
          </span>
          <template v-if="isShowPreview">
            <!-- TODO: migrate topology (relation-graph) preview rendering. -->
          </template>
        </div>
        <div class="custom-drawer-bottom-action">
          <a-button @click="handleSubmit" :loading="loading" type="primary" style="margin-right: 1rem">{{
            t('confirm')
          }}</a-button>
          <a-button @click="onClose">{{ t('cancel') }}</a-button>
        </div>
      </a-form>
    </a-drawer>
  </div>
</template>

<style lang="less" scoped>
.ant-message {
  z-index: 99999999 !important;
}
.topo-wrap {
  margin: 0 0 -24px 0;
  .topo-empty {
    position: absolute;
    text-align: center;
    left: 50%;
    top: 40%;
    transform: translate(-50%, -50%);
  }

  .topo-left {
    width: 100%;
    height: calc(100% - 28px);
    overflow: auto;
    float: left;
    background-color: #f7f8fa;
    border-right: 1px solid #e8eaed;
    padding: 12px 8px;

    .topo-left-content {
      height: calc(100% - 45px);
      overflow: hidden;
      margin-top: 10px;

      &:hover {
        overflow: auto;
      }
    }
    .topo-left-title {
      padding-bottom: 4px;
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      color: @text-color_3;
    }
    .topo-left-group {
      position: relative;
      padding: 10px 12px 10px 22px;
      margin-bottom: 8px;
      color: @text-color_1;
      cursor: pointer;
      font-size: 15px;
      font-weight: 600;
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      align-items: center;
      border-radius: 6px;
      transition: all 0.2s ease;
      width: 100%;
      overflow: hidden;
      column-gap: 6px;

      > div:first-child {
        display: flex;
        align-items: center;
        gap: 4px;
        max-width: 100%;
        overflow: hidden;

        > span:last-child {
          font-size: 12px;
          font-weight: 500;
          background: #e8eaed;
          color: @text-color_3;
          padding: 2px 6px;
          border-radius: 10px;
        }
      }

      &-name {
        font-weight: 700;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        text-wrap: nowrap;
      }

      &-action {
        align-items: center;
        column-gap: 4px;
        font-size: 14px;
        display: none;
      }

      &:hover {
        background-color: @primary-color_7;
        box-shadow: 0px 2px 8px fade(@primary-color, 15%);

        > div:nth-child(2) {
          display: inline-flex;
        }
        :deep(.anticon) {
          display: inline !important;
        }
      }
    }
    .topo-left-detail {
      padding: 6px 12px 6px 26px;
      margin: 0 4px 6px 4px;
      cursor: pointer;
      position: relative;
      display: flex;
      flex-direction: row;
      justify-content: flex-start;
      align-items: center;
      height: 36px;
      border-radius: 6px;
      transition: all 0.2s ease;

      .topo-left-detail-action {
        display: none;
        margin-left: auto;
        flex-shrink: 0;
        position: relative;
        z-index: 10;
      }

      .topo-left-detail-title {
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        font-size: 14px;
        color: @text-color_1;
        transition: color 0.2s ease;
        flex: 1;
      }

      .topo-left-detail-icon {
        display: inline-flex;
        flex-shrink: 0;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-right: 8px;
        background: #fff;
        border: 1px solid #e8eaed;
        transition: transform 0.2s ease;

        img {
          max-height: 18px;
          max-width: 18px;
        }
      }

      &:hover {
        background-color: @primary-color_7;
        box-shadow: 0px 2px 8px fade(@primary-color, 15%);

        .topo-left-detail-icon {
          transform: scale(1.05);
        }

        :deep(.anticon) {
          display: inline !important;
        }

        .topo-left-detail-action {
          display: inline-flex;
        }
      }
    }
    .selected {
      background-color: @primary-color_6;
      box-shadow: 0 1px 3px fade(@primary-color, 10%);
      position: relative;
      z-index: 1;

      .topo-left-detail-title {
        font-weight: 600;
        color: @primary-color;
      }

      .topo-left-detail-icon {
        box-shadow: 0 2px 4px fade(@primary-color, 20%);
      }
    }
  }
  .topo-right {
    width: 100%;
    position: relative;
    background-color: #fff;
    height: 100%;

    .topo-right-empty {
      position: absolute;
      text-align: center;
      left: 50%;
      top: 40%;
      transform: translate(-50%, -50%);
    }
  }
}
.topo-graph-stub,
.topo-path-stub {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 250px;
  border: 1px solid #e4e7ed;
  border-radius: 2px;
  color: @text-color_3;
}
.chart-left-preview {
  border: 1px solid #e4e7ed;
  border-radius: 2px;
  height: 280px;
  width: 92%;
  position: relative;
  padding: 12px;
  .chart-left-preview-operation {
    color: #86909c;
    position: absolute;
    top: 12px;
    right: 12px;
    cursor: pointer;
  }
}
</style>

<style lang="less">
.cmdb-topo-left-input {
  margin-bottom: 12px;

  input {
    background-color: #fff;
    border-radius: 6px;
    border: 1px solid #e8eaed;
    transition: all 0.2s ease;

    &:hover {
      border-color: #c3cdd7;
    }

    &:focus {
      border-color: @primary-color;
      box-shadow: 0 0 0 2px fade(@primary-color, 10%);
    }
  }

  .ant-input-prefix {
    color: @text-color_3;
  }
}
</style>
