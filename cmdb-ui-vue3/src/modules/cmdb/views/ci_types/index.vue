<script setup lang="ts">
import { computed, nextTick, provide, reactive, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  AppstoreOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  ExportOutlined,
  HolderOutlined,
  ImportOutlined,
  MoreOutlined,
  PlusOutlined,
  SearchOutlined,
  UserAddOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import SplitPane from '@/components/SplitPane/SplitPane.vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import CMDBTypeSelect from '../../components/cmdbTypeSelect/index.vue'
import CMDBGrant from '../../components/cmdbGrant/index.vue'
import CreateNewAttribute from './ceateNewAttribute.vue'
import CITypeDetail from './ciTypedetail.vue'
import IconArea from './iconArea.vue'
import AttributeStore from './attributeStore.vue'
import ModelExport from './modelExport.vue'
import emptyImage from '@/assets/data_empty.png'
import {
  createCIType,
  updateCIType,
  deleteCIType,
  getCIType,
  postCiTypeInheritance,
  deleteCiTypeInheritance,
} from '@/modules/cmdb/api/CIType'
import {
  getCITypeGroupsConfig,
  postCITypeGroup,
  putCITypeGroupByGId,
  putCITypeGroups,
  deleteCITypeGroup,
  exportCITypeGroups,
} from '@/modules/cmdb/api/ciTypeGroup'
import { searchAttributes, getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { getPreference } from '@/modules/cmdb/api/preference'
import { searchResourceType } from '@/modules/acl/api/resource'
import { roleHasPermissionToGrant } from '@/modules/acl/api/permission'
import { getAllDepAndEmployee } from '@/api/company'
import { cloneDeep } from '../../utils/helper'
import draggable from 'vuedraggable'

const { t } = useI18n()
const userStore = useUserStore()

const pageLoading = ref(false)
const CITypeGroups = ref<any[]>([])
const allAttributes = ref<any[]>([])
const currentId = ref<string | null>(null)

const modalVisible = ref(false)
const modalTitle = ref(t('cmdb.ciType.addGroup'))
const editingGroup = ref<any>({})
const editingInput = ref('')

const formRef = ref()
const formModel = reactive<Record<string, any>>({
  name: '',
  alias: '',
  parent_ids: [],
  unique_key: null,
  show_id: null,
  default_order_attr: null,
  id: null,
})

const drawerVisible = ref(false)
const drawerTitle = ref('')
const selectGroup = ref<any>({})

const newAttrAreaVisible = ref(false)
const resourceType = ref<Record<string, any>>({})
const paneLengthPixel = ref(280)
const loading = ref(false)

const filterInput = ref('')
const showIdFilterInput = ref('')

const currentTypeAttrs = ref<any[]>([])
const defaultOrderAsc = ref('1')
const allTreeDepAndEmp = ref<any[]>([])

const editCiType = ref<any>(null)
const isInherit = ref(false)
const uniqueId = ref<number | null>(null)

const searchValue = ref('')
const modelExportVisible = ref(false)
const preferenceData = ref<Record<string, any>>({})

const startId = ref<number | null>(null)
const startGroup = ref<any>(null)
const endId = ref<number | null>(null)
const addId = ref<number | null>(null)

const iconAreaRef = ref<{
  setIcon: (icon?: Record<string, any>) => void
  getIcon: () => Record<string, any> | undefined
}>()
const attributeStoreRef = ref<{ open: () => void }>()

const createNewAttributeRef = ref<{ checkCanDefineComputed: () => void }>()
const cmdbGrantRef = ref<{ open: (arg: Record<string, any>) => void }>()

const ciTypesUploadUrl = `${import.meta.env.VITE_API_BASE_URL || '/api'}/v0.1/ci_types/template/import/file`

const windowHeight = computed(() => window.innerHeight)

const permissions = computed<string[]>(() => (userStore.roles?.permissions ?? []).map((p: any) => p.name))

const currentGId = computed<number | null>(() => {
  if (currentId.value) {
    const id = currentId.value.split('%')[0]
    if (id !== 'null') return Number(id)
    return null
  }
  return null
})

const currentCId = computed<number | null>(() => {
  if (currentId.value) {
    const id = currentId.value.split('%')[1]
    if (id !== 'null') return Number(id)
    return null
  }
  return null
})

const currentCName = computed<string | null>(() => {
  if (currentId.value) {
    const name = currentId.value.split('%')[2]
    if (name !== 'null') return name
    return null
  }
  return null
})

const filterAttributes = computed(() => {
  const _attributes = allAttributes.value.filter(
    (item) => !item.is_choice && !item.is_computed && !['6', '7'].includes(item.value_type)
  )
  if (filterInput.value) {
    return _attributes.filter(
      (item) =>
        item.name.toLowerCase().includes(filterInput.value.toLowerCase()) ||
        item.alias.toLowerCase().includes(filterInput.value.toLowerCase())
    )
  }
  return _attributes
})

const orderSelectionOptions = computed(() => currentTypeAttrs.value.filter((item) => item.is_required))

const showIdSelectOptions = computed(() => {
  const _options = currentTypeAttrs.value.filter(
    (item) =>
      item.id !== uniqueId.value &&
      !['6'].includes(item.value_type) &&
      !item.is_password &&
      !item.is_list &&
      !item.is_bool &&
      !item.is_reference &&
      !item?.choice_value?.length
  )
  if (showIdFilterInput.value) {
    return _options.filter(
      (item) =>
        item.name.toLowerCase().includes(showIdFilterInput.value.toLowerCase()) ||
        item.alias.toLowerCase().includes(showIdFilterInput.value.toLowerCase())
    )
  }
  return _options
})

const computedCITypeGroups = computed(() => {
  if (searchValue.value) {
    const ciTypes = cloneDeep(CITypeGroups.value)
    ciTypes.forEach((item) => {
      item.ci_types = item.ci_types.filter((_item: any) =>
        _item.alias.toLowerCase().includes(searchValue.value.toLowerCase())
      )
    })
    return ciTypes
  }
  return CITypeGroups.value
})

const rules = computed(() => ({
  name: [
    { required: true, message: t('cmdb.ciType.inputAttributeName') },
    { message: t('cmdb.ciType.attributeNameTips'), pattern: /^(?!\d)[a-zA-Z_0-9]+$/ },
  ],
  unique_key: [{ required: true, message: t('cmdb.ciType.uniqueKeySelect') }],
}))

function getAllDepAndEmployeeData() {
  getAllDepAndEmployee({ block: 0 }).then((res) => {
    allTreeDepAndEmp.value = res
  })
}

function handleSearch(e: { target: { value: string } }) {
  searchValue.value = e.target.value
}

function getPreferenceData() {
  getPreference().then((res) => {
    preferenceData.value = res || {}
  })
}

async function loadCITypes(isResetCurrentId = false, isInit = false) {
  const groups = await getCITypeGroupsConfig({ need_other: true })
  let alreadyReset = false
  if (isResetCurrentId) {
    currentId.value = null
  }
  nextTick(() => {
    groups.forEach((g: any) => {
      if (!g.id) {
        g.id = -1
      }
      if (isResetCurrentId && !alreadyReset && g.ci_types && g.ci_types.length) {
        currentId.value = `${g.id}%${g.ci_types[0].id}%${g.ci_types[0].name}`
        alreadyReset = true
      }
      if (!g.ci_types) {
        g.ci_types = []
      }
    })

    if (isInit) {
      const isMatch = groups.some((g: any) => {
        const matchGroup = `${g?.id}%null%null` === currentId.value
        const matchCIType = g?.ci_types?.some((item: any) => {
          return (
            `${g?.id}%${item?.id}%${item?.name}` === currentId.value ||
            `null%${item?.id}%${item?.name}` === currentId.value
          )
        })
        return matchGroup || matchCIType
      })

      if (!isMatch) {
        if (groups?.[0]?.ci_types?.[0]?.id) {
          currentId.value = `${groups[0].id}%${groups[0].ci_types[0].id}%${groups[0].ci_types[0].name}`
        }
      }
    }

    CITypeGroups.value = groups
    localStorage.setItem('ops_cityps_currentId', currentId.value || '')
  })
}

function getAttributes() {
  searchAttributes({ page_size: 10000 }).then((res) => {
    allAttributes.value = res.attributes
  })
}

function start(g: any) {
  startId.value = g.id
  startGroup.value = cloneDeep(g)
}

function end(g: any) {
  endId.value = g.id
  if (startId.value === g.id && g.id !== -1 && addId.value !== -1) {
    putCITypeGroupByGId(g.id, { name: g.name, type_ids: g.ci_types.map((i: any) => i.id) })
      .then(() => {
        message.success(t('saveSuccess'))
      })
      .catch(() => {
        loadCITypes(!currentId.value)
      })
      .finally(() => {
        startId.value = null
        endId.value = null
        addId.value = null
      })
  }
  if (startId.value === g.id && g.id !== -1 && addId.value === -1) {
    const changedCiTypes = startGroup.value.ci_types
      .filter((ciType: any) => {
        const _find = g.ci_types.find((gCiType: any) => ciType.id === gCiType.id)
        if (_find) {
          return false
        }
        return true
      })
      .map((item: any) => item.id)
    deleteCITypeGroup(g.id, { name: g.name, type_ids: changedCiTypes })
      .then(() => {
        message.success(t('saveSuccess'))
      })
      .catch(() => {
        loadCITypes(!currentId.value)
      })
      .finally(() => {
        startId.value = null
        endId.value = null
        addId.value = null
      })
  }
}

function add(g: any) {
  addId.value = g.id
  if (g.id && g.id !== -1) {
    putCITypeGroupByGId(g.id, { name: g.name, type_ids: g.ci_types.map((i: any) => i.id) })
      .then(() => {
        message.success(t('saveSuccess'))
      })
      .catch(() => {
        loadCITypes(!currentId.value)
      })
      .finally(() => {
        startId.value = null
        endId.value = null
        addId.value = null
      })
  }
}

function handleChangeGroups() {
  putCITypeGroups({ group_ids: CITypeGroups.value.filter((c: any) => c.id).map((c: any) => c.id) })
    .then(() => {
      message.success(t('saveSuccess'))
    })
    .catch(() => {
      loadCITypes(!currentId.value)
    })
}

function handleClickAddGroup() {
  editingGroup.value = {}
  editingInput.value = ''
  modalTitle.value = t('cmdb.ciType.addGroup')
  modalVisible.value = true
}

async function handleSubmitEditGroup() {
  if (editingGroup.value && editingGroup.value.id && editingGroup.value.id !== -1) {
    await putCITypeGroupByGId(editingGroup.value.id, {
      name: editingInput.value,
      type_ids: editingGroup.value.ci_types.map((i: any) => i.id),
    })
    message.success(t('updateSuccess'))
  } else {
    const { id } = await postCITypeGroup({ name: editingInput.value })
    currentId.value = `${id}%null%null`
    message.success(t('addSuccess'))
  }
  modalVisible.value = false
  localStorage.setItem('ops_cityps_currentId', currentId.value || '')
  loadCITypes()
}

function handleClickGroup(gId: number) {
  currentId.value = null
  nextTick(() => {
    currentId.value = `${gId}%null%null`
    localStorage.setItem('ops_cityps_currentId', currentId.value || '')
  })
}

function handleClickCIType(gId: number, cId: number, cName: string) {
  currentId.value = null
  nextTick(() => {
    currentId.value = `${gId}%${cId}%${cName}`
    localStorage.setItem('ops_cityps_currentId', currentId.value || '')
  })
}

function handleCreate(g: any) {
  drawerTitle.value = t('cmdb.ciType.addCIType')
  drawerVisible.value = true
  selectGroup.value = g
  nextTick(() => {
    iconAreaRef.value?.setIcon()
  })
}

function handleCreateCiFromEmpty() {
  drawerTitle.value = t('cmdb.ciType.addCIType')
  drawerVisible.value = true
  const _find = CITypeGroups.value.find((item) => item.id === currentGId.value)
  selectGroup.value = _find
  nextTick(() => {
    iconAreaRef.value?.setIcon()
  })
}

function handleEditGroup(g: any) {
  editingGroup.value = g
  editingInput.value = g.name
  modalTitle.value = t('cmdb.ciType.editGroup')
  modalVisible.value = true
}

function handleDeleteGroup(g: any) {
  if (g.ci_types && g.ci_types.length > 0) {
    message.error(t('cmdb.ciType.cannotDeleteGroupTips'))
    return
  }
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ciType.confirmDeleteGroup', { groupName: `${g.name}` }),
    onOk() {
      deleteCITypeGroup(g.id).then(() => {
        message.success(t('deleteSuccess'))
        loadCITypes(true)
      })
    },
  })
}

function onClose() {
  filterInput.value = ''
  formRef.value?.resetFields()
  drawerVisible.value = false
  isInherit.value = false
}

function handleCreateNewAttrDone() {
  getAttributes()
  newAttrAreaVisible.value = false
}

function handleSubmit() {
  formRef.value
    .validate()
    .then(async () => {
      loading.value = true
      const values: Record<string, any> = { ...formModel }
      if (values.default_order_attr && defaultOrderAsc.value === '2') {
        values.default_order_attr = `-${values.default_order_attr}`
      }
      const _icon = iconAreaRef.value?.getIcon()
      const icon = _icon && _icon.name ? `${_icon.name}$${_icon.color || ''}$${_icon.id || ''}$${_icon.url || ''}` : ''
      if (values.id) {
        const { parent_ids: oldP = [] } = editCiType.value || {}
        const { parent_ids: newP = [] } = values
        const { remove, add } = compareArrays(newP, oldP)
        if (add && add.length) {
          await postCiTypeInheritance({ parent_ids: add, child_id: values.id }).catch(() => {
            loading.value = false
          })
        }
        if (remove && remove.length) {
          for (const pid of remove) {
            await deleteCiTypeInheritance({ parent_id: pid, child_id: values.id }).catch(() => {
              loading.value = false
            })
          }
        }
        delete values.parent_ids
        await doUpdateCIType(values.id, { ...values, show_id: values.show_id || null, icon })
      } else {
        await doCreateCIType({ ...values, icon })
      }
    })
    .catch(() => {
      /* validation failed */
    })
}

function compareArrays(newArr: any[], oldArr: any[]) {
  const remove: any[] = []
  const add: any[] = []
  for (const item of oldArr) {
    if (newArr.indexOf(item) === -1) {
      remove.push(item)
    }
  }
  for (const item of newArr) {
    if (oldArr.indexOf(item) === -1) {
      add.push(item)
    }
  }
  return { remove, add }
}

async function doCreateCIType(data: Record<string, any>) {
  const { type_id } = await createCIType(data).catch(() => {
    loading.value = false
  })
  message.success(t('addSuccess'))
  if (selectGroup.value && selectGroup.value.id && selectGroup.value.id !== -1) {
    const ids = selectGroup.value.ci_types.map((i: any) => i.id)
    ids.push(type_id)
    await putCITypeGroupByGId(selectGroup.value.id, { name: selectGroup.value.name, type_ids: ids })
  }
  currentId.value = `${selectGroup.value?.id || ''}%${type_id}%${data.name}`
  localStorage.setItem('ops_cityps_currentId', currentId.value || '')
  setTimeout(() => {
    loadCITypes()
    loading.value = false
    drawerVisible.value = false
    isInherit.value = false
  }, 1000)
}

async function doUpdateCIType(CITypeId: number, data: Record<string, any>) {
  await updateCIType(CITypeId, data)
    .then(() => {
      message.success(t('updateSuccess'))
      const _currentId = currentId.value
      currentId.value = null
      nextTick(() => {
        currentId.value = _currentId
        localStorage.setItem('ops_cityps_currentId', currentId.value || '')
        setTimeout(() => {
          loadCITypes()
          loading.value = false
          drawerVisible.value = false
          isInherit.value = false
        }, 1000)
      })
    })
    .finally(() => {
      loading.value = false
    })
}

function handleDelete(e: any, record: any) {
  e.domEvent.preventDefault()
  e.domEvent.stopPropagation()
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ciType.confirmDeleteCIType', { typeName: `${record.alias || record.name}` }),
    onOk() {
      deleteCIType(record.id).then(() => {
        message.success(t('deleteSuccess'))
        loadCITypes(true)
      })
    },
  })
}

async function handleDownloadCiType(e: any, ci: any) {
  e.domEvent.preventDefault()
  e.domEvent.stopPropagation()

  const hide = message.loading(t('cmdb.common.loading'), 0)
  try {
    const res = await exportCITypeGroups({ type_ids: ci.id })
    if (res) {
      const jsonStr = JSON.stringify(res)
      const blob = new Blob([jsonStr], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${ci.alias || ci.name}.json`
      a.click()
      URL.revokeObjectURL(url)
    }
  } catch {
    // ignore
  }
  hide()
}

async function handleEdit(e: any, record: any) {
  e.domEvent.preventDefault()
  e.domEvent.stopPropagation()
  drawerTitle.value = t('cmdb.ciType.editCIType')
  drawerVisible.value = true
  await getCITypeAttributesById(record.id).then((res) => {
    currentTypeAttrs.value = res.attributes
    uniqueId.value = res.unique_id
  })
  await getCIType(record.id).then((res) => {
    const ci_type = res.ci_types[0]
    editCiType.value = ci_type ?? null
    if (ci_type.parent_ids && ci_type.parent_ids.length) {
      isInherit.value = true
      nextTick(() => {
        formModel.parent_ids = ci_type.parent_ids
      })
    }
    formModel.show_id = ci_type.show_id ?? null
  })
  nextTick(() => {
    defaultOrderAsc.value = record.default_order_attr && record.default_order_attr.startsWith('-') ? '2' : '1'
    formModel.id = record.id
    formModel.alias = record.alias
    formModel.name = record.name
    formModel.unique_key = record.unique_id
    formModel.default_order_attr =
      record.default_order_attr && record.default_order_attr.startsWith('-')
        ? record.default_order_attr.slice(1)
        : record.default_order_attr
    iconAreaRef.value?.setIcon(
      record.icon
        ? {
            name: record.icon.split('$$')[0] || '',
            color: record.icon.split('$$')[1] || '',
            id: record.icon.split('$$')[2] ? Number(record.icon.split('$$')[2]) : null,
            url: record.icon.split('$$')[3] || '',
          }
        : {}
    )
  })
}

function handleCreatNewAttr() {
  newAttrAreaVisible.value = !newAttrAreaVisible.value
  if (newAttrAreaVisible.value) {
    nextTick(() => {
      createNewAttributeRef.value?.checkCanDefineComputed()
    })
  }
}

function handlePerm(e: any, ci: any) {
  e.domEvent.preventDefault()
  e.domEvent.stopPropagation()
  roleHasPermissionToGrant({
    app_id: 'cmdb',
    resource_type_name: 'CIType',
    perm: 'grant',
    resource_name: ci.name,
  }).then((res: any) => {
    if (res.result) {
      cmdbGrantRef.value?.open({ name: ci.name, cmdbGrantType: 'ci_type', CITypeId: ci.id })
    } else {
      message.error(t('noPermission'))
    }
  })
}

function changeUploadFile({ file }: any) {
  const key = 'upload'
  if (file.status === 'uploading') {
    message.loading({ content: t('cmdb.ciType.uploading'), key, duration: 0 })
  }
  if (file.status === 'done') {
    message.success({ content: t('cmdb.common.uploadSuccess'), key, duration: 2 })
    window.location.reload()
  }
  if (file.status === 'error') {
    message.error({ content: file?.response?.message || t('cmdb.ciType.uploadFailed'), key, duration: 2 })
  }
}

function handleChangeUnique(value: number) {
  uniqueId.value = value
  if (formModel.show_id === value) {
    formModel.show_id = null
  }
}

provide('resource_type', () => resourceType.value)
provide('provide_allTreeDepAndEmp', () => allTreeDepAndEmp.value)

getAllDepAndEmployeeData()
const _currentId = localStorage.getItem('ops_cityps_currentId')
if (_currentId) {
  currentId.value = _currentId
}
searchResourceType({ page_size: 9999, app_id: 'cmdb' }).then((res: any) => {
  resourceType.value = { groups: res.groups, id2perms: res.id2perms }
})

pageLoading.value = true
loadCITypes(!_currentId, true).then(() => {
  pageLoading.value = false
})

getAttributes()
getPreferenceData()
</script>

<template>
<!-- eslint-disable vue/attribute-hyphenation -->
  <div class="ci-types-wrap" :style="{ height: `${windowHeight - 96}px` }">
    <div v-if="pageLoading" class="ci-types-loading">
      <a-spin size="large" />
    </div>

    <div v-else-if="!CITypeGroups.length" class="ci-types-empty">
      <a-empty :image="emptyImage" description=""></a-empty>
      <a-button size="small" type="primary" @click="handleClickAddGroup">
        <template #icon><PlusOutlined /></template>{{ t('cmdb.ciType.addGroup') }}
      </a-button>
    </div>
    <SplitPane
      v-else
      v-model:pane-length-pixel="paneLengthPixel"
      :min="220"
      :max="500"
      app-name="cmdb-ci-types"
      :trigger-length="18"
      calc-based-parent
    >
      <template #one>
        <div class="ci-types-left">
          <div class="ci-types-left-header">
            <a-input
              :placeholder="t('cmdb.preference.searchPlaceholder')"
              class="ci-types-left-header-input"
              @press-enter="handleSearch"
            >
              <template #prefix><SearchOutlined /></template>
            </a-input>
            <a-dropdown>
              <a-button class="ci-types-left-header-more"><MoreOutlined /></a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item key="0" @click="handleClickAddGroup">
                    <PlusOutlined />
                    <span>{{ t('cmdb.ciType.addGroup2') }}</span>
                  </a-menu-item>
                  <a-menu-item key="1" @click="attributeStoreRef?.open()">
                    <AppstoreOutlined />
                    <span>{{ t('cmdb.ciType.viewAttributeLibray') }}</span>
                  </a-menu-item>
                  <a-menu-item v-if="permissions.includes('admin') || permissions.includes('cmdb_admin')" key="2">
                    <a-upload
                      name="file"
                      accept=".json"
                      :show-upload-list="false"
                      :with-credentials="true"
                      style="display: inline-block"
                      :action="ciTypesUploadUrl"
                      @change="changeUploadFile"
                    >
                      <ImportOutlined />
                      <span style="margin-left: 8px">{{ t('cmdb.common.upload') }}</span>
                    </a-upload>
                  </a-menu-item>
                  <a-menu-item
                    v-if="permissions.includes('admin') || permissions.includes('cmdb_admin')"
                    key="3"
                    @click="modelExportVisible = true"
                  >
                    <span><ExportOutlined /> {{ t('cmdb.common.export') }}</span>
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
          <draggable class="ci-types-left-content" :list="computedCITypeGroups" filter=".undraggable" @end="handleChangeGroups">
            <div v-for="g in computedCITypeGroups" :key="g.id || g.name">
              <div
                :class="
                  `${currentGId === g.id && !currentCId ? 'selected' : ''} ci-types-left-group ${
                    g.id === -1 ? 'undraggable' : ''
                  }`
                "
                @click="handleClickGroup(g.id)"
              >
                <div>
                  <HolderOutlined
                    v-if="g.id !== -1"
                    style="width: 17px; height: 17px; display: none; position: absolute; left: 5px; top: 13px"
                  />
                  <span class="ci-types-left-group-name">{{ g.name || t('cmdb.common.other') }}</span>
                  <span>{{ g.ci_types.length }}</span>
                </div>
                <div class="ci-types-left-group-action">
                  <a-tooltip :title="t('cmdb.ciType.addCITypeInGroup')">
                    <a><PlusOutlined @click="handleCreate(g)" /></a>
                  </a-tooltip>
                  <template v-if="g.id !== -1">
                    <a-tooltip :title="t('cmdb.ciType.editGroup')">
                      <a><EditOutlined @click="handleEditGroup(g)" /></a>
                    </a-tooltip>
                    <a-tooltip :title="t('cmdb.ciType.deleteGroup')">
                      <a :style="{ color: 'red' }"><DeleteOutlined @click="handleDeleteGroup(g)" /></a>
                    </a-tooltip>
                  </template>
                </div>
              </div>
              <draggable
                v-model="g.ci_types"
                group="ciType"
                :animation="100"
                filter=".undraggable"
                @start="start(g)"
                @end="end(g)"
                @add="add(g)"
              >
                <div
                  v-for="ci in g.ci_types"
                  :key="ci.id"
                  :class="`${currentCId === ci.id ? 'selected' : ''} ci-types-left-detail`"
                  @click="handleClickCIType(g.id, ci.id, ci.name)"
                >
                  <div :class="`${g.id === -1 ? 'undraggable' : ''}`">
                    <HolderOutlined
                      v-if="g.id !== -1"
                      style="width: 17px; height: 17px; display: none; position: absolute; left: 4px; top: 9px"
                    />
                    <span class="ci-types-left-detail-icon">
                      <template v-if="ci.icon">
                        <img
                          v-if="ci.icon.split('$$')[2]"
                          :src="`/api/common-setting/v1/file/${ci.icon.split('$$')[3]}`"
                        />
                        <span v-else class="primary-color" :style="{ fontSize: '14px' }">{{
                          ci.name[0].toUpperCase()
                        }}</span>
                      </template>
                      <span v-else class="primary-color">{{ ci.name[0].toUpperCase() }}</span>
                    </span>
                  </div>
                  <span class="ci-types-left-detail-title">{{ ci.alias || ci.name }}</span>
                  <a-dropdown :get-popup-container="(trigger: HTMLElement) => trigger">
                    <a class="ci-types-left-detail-action"><MoreOutlined /></a>
                    <template #overlay>
                      <a-menu>
                        <a-menu-item @click="(e: any) => handlePerm(e, ci)">
                          <UserAddOutlined />
                          {{ t('grant') }}
                        </a-menu-item>
                        <a-menu-item @click="(e: any) => handleEdit(e, ci)">
                          <EditOutlined />
                          {{ t('cmdb.ciType.editCIType') }}
                        </a-menu-item>
                        <a-menu-item
                          v-if="permissions.includes('admin') || permissions.includes('cmdb_admin')"
                          @click="(e: any) => handleDownloadCiType(e, ci)"
                        >
                          <DownloadOutlined />
                          {{ t('cmdb.ciType.downloadType') }}
                        </a-menu-item>
                        <a-menu-item @click="(e: any) => handleDelete(e, ci)">
                          <DeleteOutlined />
                          {{ t('cmdb.ciType.deleteCIType') }}
                        </a-menu-item>
                      </a-menu>
                    </template>
                  </a-dropdown>
                </div>
              </draggable>
            </div>
          </draggable>
        </div>
      </template>
      <template #two>
        <div class="ci-types-right">
          <CITypeDetail
            v-if="currentCId"
            :CITypeId="currentCId"
            :CITypeName="currentCName || ''"
            :preference-data="preferenceData"
          />
          <div v-else class="ci-types-right-empty">
            <a-empty :image="emptyImage" description=""></a-empty>
            <a-button size="small" type="primary" @click="handleCreateCiFromEmpty">
              <template #icon><PlusOutlined /></template>{{ t('cmdb.ciType.addCIType') }}
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
    <CustomDrawer
      :closable="false"
      :title="drawerTitle"
      :open="drawerVisible"
      placement="right"
      width="900px"
      :destroy-on-close="true"
      :body-style="{ height: 'calc(100vh - 108px)' }"
      @close="onClose"
    >
      <a-form ref="formRef" :model="formModel" :rules="rules" :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
        <a-form-item :label="t('cmdb.ciType.CITypeName')" name="name">
          <a-input
            v-model:value="formModel.name"
            :disabled="drawerTitle === t('cmdb.ciType.editCIType')"
            :placeholder="t('cmdb.ciType.English')"
          />
          <div v-if="drawerTitle !== t('cmdb.ciType.editCIType')" class="ant-form-explain">
            {{ t('cmdb.ciType.ciTypeNameHint') }}
          </div>
        </a-form-item>
        <a-form-item :label="t('cmdb.common.alias')" name="alias">
          <a-input v-model:value="formModel.alias" />
        </a-form-item>
        <a-form-item :label="t('cmdb.ciType.isInherit')">
          <a-radio-group v-model:value="isInherit">
            <a-radio :value="true">{{ t('yes') }}</a-radio>
            <a-radio :value="false">{{ t('no') }}</a-radio>
          </a-radio-group>
          <div class="ant-form-explain">{{ t('cmdb.ciType.isInheritHint') }}</div>
        </a-form-item>
        <a-form-item v-if="isInherit" :label="t('cmdb.ciType.inheritType')" name="parent_ids">
          <CMDBTypeSelect
            multiple
            :value="formModel.parent_ids"
            :placeholder="t('cmdb.ciType.inheritTypePlaceholder')"
            select-type="ci_type"
            :class="{ 'custom-treeselect': true }"
            :style="{ '--custom-height': '32px', lineHeight: '32px', '--custom-multiple-lineHeight': '14px' }"
            @change="(v) => (formModel.parent_ids = v)"
          />
          <div class="ant-form-explain">{{ t('cmdb.ciType.inheritTypeHint') }}</div>
        </a-form-item>
        <a-form-item :label="t('cmdb.common.icon')">
          <IconArea ref="iconAreaRef" class="ci_types-icon-area" />
          <div class="ant-form-explain">{{ t('cmdb.ciType.iconHint') }}</div>
        </a-form-item>
        <a-form-item v-if="drawerTitle === t('cmdb.ciType.editCIType')" :label="t('cmdb.ciType.defaultSort')">
          <a-select
            v-model:value="formModel.default_order_attr"
            show-search
            allow-clear
            :placeholder="t('placeholder2')"
          >
            <a-select-option v-for="item in orderSelectionOptions" :key="item.name" :value="item.name">
              {{ item.alias || item.name }}
            </a-select-option>
          </a-select>
          <a-radio-group v-model:value="defaultOrderAsc">
            <a-radio value="1">{{ t('cmdb.ciType.asec') }}</a-radio>
            <a-radio value="2">{{ t('cmdb.ciType.desc') }}</a-radio>
          </a-radio-group>
          <div class="ant-form-explain">{{ t('cmdb.ciType.defaultSortHint') }}</div>
        </a-form-item>
        <a-form-item :help="t('cmdb.ciType.uniqueKeyTips')" :label="t('cmdb.ciType.uniqueKey')" name="unique_key">
          <a-select
            v-model:value="formModel.unique_key"
            show-search
            :filter-option="false"
            :placeholder="t('placeholder2')"
            @search="(v: string) => (filterInput = v)"
            @change="handleChangeUnique"
          >
            <a-select-option v-for="item in filterAttributes" :key="item.id" :value="item.id">
              {{ item.alias || item.name }}
            </a-select-option>
          </a-select>
          <a-divider type="vertical" />
          <a @click="handleCreatNewAttr">{{ t('cmdb.ciType.notfound') }}</a>
        </a-form-item>
        <a-form-item
          v-if="drawerTitle === t('cmdb.ciType.editCIType')"
          :help="t('cmdb.ciType.showTips')"
          :label="t('cmdb.ciType.show')"
          name="show_id"
        >
          <a-select
            v-model:value="formModel.show_id"
            show-search
            allow-clear
            :filter-option="false"
            :placeholder="t('placeholder2')"
            @search="(v: string) => (showIdFilterInput = v)"
          >
            <a-select-option v-for="item in showIdSelectOptions" :key="item.id" :value="item.id">
              {{ item.alias || item.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <div v-if="newAttrAreaVisible" :style="{ padding: '15px 8px 0 8px', backgroundColor: '#fafafa' }">
          <CreateNewAttribute
            ref="createNewAttributeRef"
            @done="handleCreateNewAttrDone"
            @cancel="newAttrAreaVisible = false"
          />
        </div>
        <a-form-item>
          <a-input v-model:value="formModel.id" type="hidden" />
        </a-form-item>
        <div class="custom-drawer-bottom-action">
          <a-button :loading="loading" type="primary" style="margin-right: 1rem" @click="handleSubmit">{{
            t('confirm')
          }}</a-button>
          <a-button @click="onClose">{{ t('cancel') }}</a-button>
        </div>
      </a-form>
    </CustomDrawer>
    <CMDBGrant ref="cmdbGrantRef" resource-type="CIType" app_id="cmdb" />
    <AttributeStore ref="attributeStoreRef" />
    <ModelExport :visible="modelExportVisible" :CITypeGroups="CITypeGroups" @cancel="() => (modelExportVisible = false)" />
  </div>
</template>

<style lang="less" scoped>
.ci-types-wrap {
  margin: 0 0 -24px 0;

  .ci-types-loading {
    text-align: center;
    padding-top: 150px;
  }

  .ci-types-empty {
    position: absolute;
    text-align: center;
    left: 50%;
    top: 40%;
    transform: translate(-50%, -50%);
  }

  .ci-types-left {
    width: 100%;
    overflow: auto;
    float: left;
    background-color: #f7f8fa;
    border-right: 1px solid #e8eaed;
    padding: 12px 8px;

    &-header {
      display: flex;
      gap: 6px;
      margin-bottom: 12px;

      &-more {
        flex-shrink: 0;
        width: 32px;
        padding: 0px;
      }

      :deep(&-input) {
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
    }

    .ci-types-left-content {
      height: calc(100% - 45px);
      overflow: hidden;
      margin-top: 10px;

      &:hover {
        overflow: auto;
      }
    }

    .ci-types-left-group {
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

      &::before {
        content: '';
        position: absolute;
        left: 2px;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 32px;
        background: @primary-color;
        border-radius: 2px;
        opacity: 0;
        transition: opacity 0.2s ease;
      }

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
        svg {
          display: inline !important;
        }
      }
    }

    .ci-types-left-detail {
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

      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background: @primary-color;
        border-radius: 0 2px 2px 0;
        opacity: 0;
        transition: opacity 0.2s ease;
      }

      .ci-types-left-detail-action {
        display: none;
        margin-left: auto;
        flex-shrink: 0;
        position: relative;
        z-index: 10;
      }

      .ci-types-left-detail-title {
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        font-size: 14px;
        color: @text-color_1;
        transition: color 0.2s ease;
        flex: 1;
      }

      &:hover {
        background-color: @primary-color_7;
        box-shadow: 0px 2px 8px fade(@primary-color, 15%);

        .ci-types-left-detail-icon {
          transform: scale(1.05);
        }

        svg {
          display: inline !important;
        }
        .ci-types-left-detail-action {
          display: inline-flex;
        }
      }
    }

    .ci-types-left-detail-icon {
      display: inline-flex;
      flex-shrink: 0;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 6px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      margin-right: 8px;
      background-color: #fff;
      border: 1px solid #e8eaed;
      transition: transform 0.2s ease;

      img {
        max-height: 18px;
        max-width: 18px;
      }
    }

    .selected {
      background-color: @primary-color_6;
      box-shadow: 0 1px 3px fade(@primary-color, 10%);
      position: relative;
      z-index: 1;

      &::before {
        opacity: 1;
      }

      .ci-types-left-detail-title {
        color: @primary-color;
        font-weight: 600;
      }

      .ci-types-left-detail-icon {
        box-shadow: 0 2px 4px fade(@primary-color, 20%);
      }
    }
  }
  .ci-types-right {
    width: 100%;
    position: relative;
    background-color: #fff;
    .ci-types-right-empty {
      position: absolute;
      text-align: center;
      left: 50%;
      top: 40%;
      transform: translate(-50%, -50%);
    }
  }
  .ci-types-left,
  .ci-types-right {
    height: 100%;
  }
}
</style>

<style lang="less">
.ci_types-icon-area {
  margin-top: 5px;
  > .icon-area-item > span {
    margin-right: 0 !important;
  }
}
</style>
