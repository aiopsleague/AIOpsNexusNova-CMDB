<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, nextTick, provide, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  DeleteOutlined,
  EditOutlined,
  MoreOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue'
import {
  deleteCITypeGroupById,
  getCITypeGroupById,
  createCITypeGroupById,
  updateCITypeGroupById,
  getTriggerList,
  getCIType,
} from '@/modules/cmdb/api/CIType'
import {
  getCITypeAttributesById,
  updateCITypeAttributesById,
  transferCITypeAttrIndex,
  transferCITypeGroupIndex,
} from '@/modules/cmdb/api/CITypeAttr'
import AttributeCard from './attributeCard.vue'
import AttributeEditForm from './attributeEditForm.vue'
import NewCiTypeAttrModal from './newCiTypeAttrModal.vue'
import UniqueConstraint from './uniqueConstraint.vue'
import { getPropertyIcon, getPropertyType, valueTypeMap } from '../../utils/helper'
import draggable from 'vuedraggable'

interface Group {
  id: number
  name: string
  order: number
  attributes: any[]
  inherited?: boolean
  editable?: boolean
  originName?: string
  originCount?: number
  originOrder?: number
  [key: string]: any
}

const props = withDefaults(
  defineProps<{
    CITypeId?: number | null
    CITypeName?: string
  }>(),
  { CITypeId: null, CITypeName: '' }
)

const { t } = useI18n()

const attributeEditFormRef = ref<{ handleEdit: (property: any, attributes: any[]) => void }>()
const newCiTypeAttrModalRef = ref<{ handleEdit: (group: Group | null) => void }>()
const uniqueConstraintRef = ref<{ open: (attrs: any[]) => void }>()

const CITypeGroups = ref<Group[]>([])
const attributes = ref<any[]>([])
const otherGroupAttributes = ref<any[]>([])
const addGroupModal = ref(false)
const newGroupName = ref('')
const attrTypeFilter = ref<string[]>([])
const unique = ref('')
const showId = ref<number | null>(null)
const groupMaxCount = ref<Record<string, number>>({})
const addRemoveGroupFlag = ref<Record<string, any>>({})

const linkedIds = computed(() => attributes.value.map((i) => i.id))

const windowHeight = computed(() => window.innerHeight)

const valueTypeOptions = computed(() => {
  const map = valueTypeMap()
  const keys = ['0', '1', '2', '9', '3', '4', '5', '6', '7', '8', '10', '11', '12']
  return keys.map((key) => ({ key, value: map[key] }))
})

function init() {
  getCIType(props.CITypeId as number).then((res) => {
    if (res?.ci_types && res.ci_types.length) {
      showId.value = res.ci_types[0]?.show_id ?? null
    }
  })
  getCITypeGroupData()
}

function handleEditProperty(property: any) {
  attributeEditFormRef.value?.handleEdit(property, attributes.value)
}

function handleOk() {
  init()
}

function setOtherGroupAttributes() {
  const orderMap = attributes.value.reduce((map: Record<number, number>, obj: any) => {
    map[obj.id] = obj.order
    return map
  }, {})

  const inGroupAttrKeys = CITypeGroups.value
    .filter((x) => x.attributes && x.attributes.length > 0)
    .map((x) => x.attributes)
    .flat()
    .map((x) => x.id)

  CITypeGroups.value.forEach((group) => {
    group.attributes.forEach((attribute) => {
      attribute.order = orderMap[attribute.id]
      attribute.originOrder = attribute.order
      attribute.originGroupName = group.name
    })
    group.originCount = group.attributes.length
    group.editable = false
    group.originOrder = group.order
    group.originName = group.name
  })

  otherGroupAttributes.value = attributes.value
    .filter((x) => !inGroupAttrKeys.includes(x.id))
    .sort((a, b) => a.order - b.order)
  attributes.value = attributes.value.sort((a, b) => a.order - b.order)
  CITypeGroups.value = CITypeGroups.value.sort((a, b) => a.order - b.order)
  otherGroupAttributes.value.forEach((attribute) => {
    attribute.originOrder = attribute.order
  })
}

function getCITypeGroupData() {
  const promises = [
    getCITypeAttributesById(props.CITypeId as number),
    getCITypeGroupById(props.CITypeId as number),
    getTriggerList(props.CITypeId as number),
  ]
  Promise.all(promises).then((values) => {
    attributes.value = values[0].attributes
    unique.value = values[0].unique
    const temp: Record<number, any> = {}
    attributes.value.forEach((attr) => {
      temp[attr.id] = attr
    })
    CITypeGroups.value = values[1]
    CITypeGroups.value.forEach((g) => {
      groupMaxCount.value[g.name] = g.attributes.filter((a) => a.inherited).length
      g.attributes.forEach((a) => {
        a.is_required = (temp[a.id] && temp[a.id].is_required) || false
        a.default_show = (temp[a.id] && temp[a.id].default_show) || false
        const idx = values[2].findIndex((item: any) => item.attr_id === a.id)
        a.has_trigger = idx > -1
        if (idx > -1) {
          a.trigger = values[2][idx]
        }
      })
    })
    setOtherGroupAttributes()
  })
}

function handleEditGroupName(index: number, group: Group) {
  group.editable = true
  CITypeGroups.value[index] = group
}

function handleSaveGroupName(index: number, group: Group) {
  if (group.name === group.originName) {
    handleCancelGroupName(index, group)
  } else if (CITypeGroups.value.map((x) => x.originName).includes(group.name)) {
    message.error(t('cmdb.ciType.groupExisted'))
  } else {
    updateCITypeGroupById(group.id, {
      name: group.name,
      attributes: group.attributes.map((x) => x.id),
      order: group.order,
    }).then(() => {
      group.editable = false
      CITypeGroups.value[index] = group
      message.success(t('updateSuccess'))
    })
  }
}

function handleCancelGroupName(index: number, group: Group) {
  group.editable = false
  group.name = group.originName || ''
  CITypeGroups.value[index] = group
}

function handleAddGroup() {
  addGroupModal.value = true
}

function handleCreateGroup() {
  const groupOrders = CITypeGroups.value.map((x) => x.order)
  const maxGroupOrder = Math.max(groupOrders.length, groupOrders.length ? Math.max(...groupOrders) : 0)

  createCITypeGroupById(props.CITypeId as number, { name: newGroupName.value, order: maxGroupOrder + 1 }).then(() => {
    addGroupModal.value = false
    newGroupName.value = ''
    getCITypeGroupData()
  })
}

function handleCancelCreateGroup() {
  addGroupModal.value = false
  newGroupName.value = ''
}

function handleMoveGroup(beforeIndex: number, afterIndex: number) {
  const fromGroupId = CITypeGroups.value[beforeIndex].name
  const toGroupId = CITypeGroups.value[afterIndex].name
  transferCITypeGroupIndex(props.CITypeId as number, { from: fromGroupId, to: toGroupId }).then(() => {
    message.success(t('operateSuccess'))
    const beforeGroup = CITypeGroups.value[beforeIndex]
    CITypeGroups.value[beforeIndex] = CITypeGroups.value[afterIndex]
    CITypeGroups.value[afterIndex] = beforeGroup
  })
}

function handleAddGroupAttr(index: number | undefined) {
  let group: Group | null = null
  if (index === 0 || index) {
    group = CITypeGroups.value[index]
  }
  newCiTypeAttrModalRef.value?.handleEdit(group)
}

function handleDeleteGroup(group: Group) {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ciType.confirmDeleteGroup', { groupName: `${group.name}` }),
    onOk() {
      deleteCITypeGroupById(group.id).then(() => {
        CITypeGroups.value = CITypeGroups.value.filter((g) => g.id !== group.id)
        updatePropertyIndex()
      })
    },
  })
}

function handleChange(e: any, group: any) {
  if (Object.prototype.hasOwnProperty.call(e, 'moved') && e.moved.oldIndex !== e.moved.newIndex) {
    if (group === -1 || group === null) {
      refreshPage(t('cmdb.ciType.attributeSortedTips'))
    } else if (e.moved.newIndex < groupMaxCount.value[group]) {
      refreshPage(t('cmdb.ciType.attributeSortedTips2'))
    } else {
      transferCITypeAttrIndex(props.CITypeId as number, {
        from: { attr_id: e.moved.element.id, group_name: group },
        to: { order: e.moved.newIndex, group_name: group },
      })
        .then(() => message.success(t('updateSuccess')))
        .catch(() => init())
    }
  }
  if (Object.prototype.hasOwnProperty.call(e, 'added')) {
    addRemoveGroupFlag.value = { to: { group_name: group, order: e.added.newIndex }, inited: true }
  }
  if (Object.prototype.hasOwnProperty.call(e, 'removed')) {
    nextTick(() => {
      if (addRemoveGroupFlag.value.to.order < groupMaxCount.value[addRemoveGroupFlag.value.to.group_name]) {
        refreshPage(t('cmdb.ciType.attributeSortedTips2'))
      } else {
        transferCITypeAttrIndex(props.CITypeId as number, {
          from: { attr_id: e.removed.element.id, group_name: group },
          to: { group_name: addRemoveGroupFlag.value.to.group_name, order: addRemoveGroupFlag.value.to.order },
        })
          .then(() => message.success(t('saveSuccess')))
          .catch(() => init())
          .finally(() => {
            addRemoveGroupFlag.value = {}
          })
      }
    })
  }
}

function refreshPage(errorMessage: string) {
  message.error(errorMessage)
  init()
}

function updatePropertyIndex() {
  const attributesPayload: any[] = []
  let attributeOrder = 0
  let groupOrder = 0
  const promises: Promise<any>[] = []

  CITypeGroups.value.forEach((group) => {
    const groupName = group.name
    let groupAttributes: number[] = []
    let groupUpdate = false
    group.order = groupOrder

    group.attributes.forEach((attribute) => {
      groupAttributes.push(attribute.id)
      if (attribute.originGroupName !== group.name || attribute.originOrder !== attributeOrder) {
        attributesPayload.push({ attr_id: attribute.id, order: attributeOrder })
        groupUpdate = true
      }
      attributeOrder++
    })

    groupAttributes = Array.from(new Set(groupAttributes))
    if (group.originCount !== groupAttributes.length || groupUpdate || group.originOrder !== group.order) {
      promises.push(
        updateCITypeGroupById(group.id, { name: groupName, attributes: groupAttributes, order: groupOrder })
      )
    }
    groupOrder++
  })

  otherGroupAttributes.value.forEach((attribute) => {
    if (attribute.originOrder !== attributeOrder) {
      attributesPayload.push({ attr_id: attribute.id, order: attributeOrder })
    }
    attributeOrder++
  })

  if (attributesPayload.length > 0) {
    promises.unshift(updateCITypeAttributesById(props.CITypeId as number, { attributes: attributesPayload }))
  }

  Promise.all(promises).then(() => {
    message.success(t('updateSuccess'))
    getCITypeGroupData()
  })
}

function handleOpenUniqueConstraint() {
  uniqueConstraintRef.value?.open(attributes.value)
}

function handleFilterType(type: string) {
  const _idx = attrTypeFilter.value.findIndex((item) => item === type)
  if (_idx > -1) {
    attrTypeFilter.value.splice(_idx, 1)
  } else {
    attrTypeFilter.value.push(type)
  }
}

function filterValueType(array: any[]) {
  if (!attrTypeFilter.value.length) {
    return array
  }
  return array.filter((attr) => {
    const valueType = getPropertyType(attr)
    return attrTypeFilter.value.includes(valueType)
  })
}

provide('refresh', getCITypeGroupData)
provide('unique', () => unique.value)
provide('show_id', () => showId.value)
provide('providerGroupsData', () => ({
  CITypeGroups: CITypeGroups.value,
  otherGroupAttributes: otherGroupAttributes.value,
}))

init()

defineExpose({ getCITypeGroupData })
</script>

<template>
<!-- eslint-disable vue/attribute-hyphenation -->
  <div>
    <a-modal
      v-model:open="addGroupModal"
      :title="t('cmdb.ciType.addGroup')"
      @cancel="handleCancelCreateGroup"
      @ok="handleCreateGroup"
    >
      <a-form-item :label="t('name')" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-input v-model:value="newGroupName" type="text" />
      </a-form-item>
    </a-modal>
    <div class="ci-types-attributes" :style="{ height: `${windowHeight - 130}px` }">
      <a-space style="margin-bottom: 10px">
        <a-button size="small" @click="handleAddGroup"><template #icon><PlusOutlined /></template>{{ t('cmdb.ciType.group') }}</a-button>
        <a-button size="small" @click="handleOpenUniqueConstraint">{{ t('cmdb.ciType.uniqueConstraint') }}</a-button>
        <div class="ci-types-attributes-flex">
          <a-tooltip
            v-for="item in valueTypeOptions"
            :key="item.key"
            :title="t('cmdb.ciType.filterTips', { name: item.value })"
          >
            <span
              :class="{
                'ci-types-attributes-filter': true,
                'ci-types-attributes-filter-selected': attrTypeFilter.includes(item.key),
              }"
              @click="handleFilterType(item.key)"
            >
              <span class="value-type-icon"><component :is="getPropertyIcon({ value_type: item.key })" /></span>
              {{ item.value }}
            </span>
          </a-tooltip>
        </div>
      </a-space>
      <div v-for="(group, index) in CITypeGroups" :key="group.id">
        <div>
          <div
            v-if="!group.editable"
            :style="{ height: '32px', lineHeight: '32px', display: 'inline-block', fontSize: '14px' }"
          >
            <span style="font-weight: 700">{{ group.name }}</span>
            <span style="color: #c3cdd7; margin: 0 5px">({{ group.attributes.length }})</span>
          </div>
          <template v-else>
            <span>
              <a-input v-model:value="group.name" type="text" style="width: 200px; margin-right: 10px" />
              <a style="margin-right: 0.5rem" @click="handleSaveGroupName(index, group)">{{ t('cmdb.common.save') }}</a>
              <a @click="handleCancelGroupName(index, group)">{{ t('cancel') }}</a>
            </span>
          </template>
          <a-space style="float: right">
            <a-tooltip v-if="index">
              <template #title>{{ t('cmdb.ciType.up') }}</template>
              <a v-if="index"><ArrowUpOutlined @click="handleMoveGroup(index, index - 1)" /></a>
            </a-tooltip>
            <a-tooltip v-if="index !== CITypeGroups.length - 1">
              <template #title>{{ t('cmdb.ciType.down') }}</template>
              <a v-if="index !== CITypeGroups.length - 1"
                ><ArrowDownOutlined @click="handleMoveGroup(index, index + 1)"
              /></a>
            </a-tooltip>
            <a-dropdown>
              <a><MoreOutlined /></a>
              <template #overlay>
                <a-menu>
                  <a-menu-item @click="handleAddGroupAttr(index)">
                    <PlusOutlined />
                    {{ t('cmdb.ciType.addAttribute') }}
                  </a-menu-item>
                  <a-menu-item :disabled="group.inherited" @click="handleEditGroupName(index, group)">
                    <EditOutlined />
                    {{ t('cmdb.ciType.editGroupName') }}
                  </a-menu-item>
                  <a-menu-item :disabled="group.inherited" @click="handleDeleteGroup(group)">
                    <DeleteOutlined />
                    {{ t('cmdb.ciType.deleteGroup') }}
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </div>
        <div class="ci-types-attributes-wrapper">
          <draggable
            v-model="group.attributes"
            group="properties"
            :filter="'.filter-empty'"
            :animation="300"
            tag="div"
            class="ci-types-attributes-list"
            handle=".handle"
            @change="(e) => handleChange(e, group.name)"
          >
            <AttributeCard
              v-for="item in filterValueType(group.attributes)"
              :key="item.id"
              :property="item"
              :CITypeId="CITypeId"
              :attributes="attributes"
              @edit="handleEditProperty(item)"
              @ok="handleOk"
            />
            <AttributeCard is-add @add="handleAddGroupAttr(index)" />
            <i></i> <i></i> <i></i> <i></i> <i></i>
          </draggable>
        </div>
      </div>
      <div>
        <div :style="{ height: '32px', lineHeight: '32px', display: 'inline-block', fontSize: '14px' }">
          <span style="font-weight: 700">{{ t('cmdb.common.other') }}</span>
          <span style="color: #c3cdd7; margin-left: 5px">({{ otherGroupAttributes.length }})</span>
          <span style="color: #c3cdd7; margin-left: 5px; font-size: 10px">{{ t('cmdb.ciType.otherGroupTips') }}</span>
        </div>
        <div style="float: right">
          <a-tooltip>
            <template #title>{{ t('cmdb.ciType.addAttribute') }}</template>
            <a @click="handleAddGroupAttr(undefined)"><PlusOutlined /></a>
          </a-tooltip>
        </div>
      </div>

      <div class="ci-types-attributes-wrapper">
        <draggable
          v-model="otherGroupAttributes"
          group="properties"
          :animation="300"
          tag="div"
          class="ci-types-attributes-list"
          style="min-height: 2rem"
          handle=".handle"
          @change="(e) => handleChange(e, null)"
        >
          <AttributeCard
            v-for="item in filterValueType(otherGroupAttributes)"
            :key="item.id"
            :property="item"
            :CITypeId="CITypeId"
            :attributes="attributes"
            @edit="handleEditProperty(item)"
            @ok="handleOk"
          />
          <AttributeCard is-add @add="handleAddGroupAttr(undefined)" />
          <i></i> <i></i> <i></i> <i></i> <i></i>
        </draggable>
      </div>
    </div>
    <AttributeEditForm ref="attributeEditFormRef" :CITypeId="CITypeId" :CITypeName="CITypeName" @ok="handleOk" />
    <NewCiTypeAttrModal ref="newCiTypeAttrModalRef" :CITypeId="CITypeId" :linked-ids="linkedIds" @ok="handleOk" />
    <UniqueConstraint ref="uniqueConstraintRef" :CITypeId="CITypeId" />
  </div>
</template>

<style lang="less" scoped>
.value-type-icon {
  color: @primary-color;
}
.fold {
  width: calc(100% - 216px);
  display: inline-block;
}

.ci-types-attributes {
  padding: 0 20px;
  overflow-y: auto;

  &-flex {
    display: flex;
    flex-wrap: wrap;
  }

  .ci-types-attributes-filter {
    color: @text-color_4;
    cursor: pointer;
    padding: 3px 8px;
    white-space: nowrap;
    margin-right: 5px;
  }
  .ci-types-attributes-filter:hover,
  .ci-types-attributes-filter-selected {
    background-color: @primary-color_5;
  }

  .ci-types-attributes-list {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-start;
    min-height: 20px;
    column-gap: 10px;
    > i {
      width: 182px;
    }
  }
}

@media screen and (max-width: 900px) {
  .fold {
    width: 100%;
  }
}
</style>
