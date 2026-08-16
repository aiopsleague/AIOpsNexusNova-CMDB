<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  QuestionCircleOutlined,
  MinusCircleOutlined,
  PlusCircleOutlined,
  UserAddOutlined,
  DeleteOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue'
import { uuidv4 } from '@/utils/uuid'
import dataEmptyImg from '@/assets/data_empty.png'
import { createRelation, deleteRelation, getCITypeChildren, getCITypeParent, getRelationTypes } from '@/modules/cmdb/api/CITypeRelation'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { getCITypeGroupsConfig } from '@/modules/cmdb/api/ciTypeGroup'
import CMDBGrant from '@/modules/cmdb/components/cmdbGrant/index.vue'

interface AttrLink {
  id: string
  parentAttrId?: number
  childAttrId?: number
}

const props = withDefaults(
  defineProps<{
    CITypeId?: number | null
    CITypeName?: string
    isInGrantComp?: boolean
  }>(),
  { CITypeId: null, CITypeName: '', isInGrantComp: false }
)

const { t } = useI18n()

const xTableRef = ref<any>()
const cmdbGrantRef = ref<InstanceType<typeof CMDBGrant>>()
const formRef = ref()

const visible = ref(false)
const drawerTitle = ref('')
const CITypes = ref<any[]>([])
const CITypeGroups = ref<any[]>([])
const relationTypes = ref<any[]>([])
const tableData = ref<any[]>([])
const parentTableData = ref<any[]>([])
const attributes = ref<any[]>([])
const tableAttrList = ref<AttrLink[]>([])
const modalAttrList = ref<AttrLink[]>([])
const modalChildAttributes = ref<any[]>([])
const currentEditData = ref<any>(null)
const isContinueCloseEdit = ref(false)

const formModel = reactive<{
  source_ci_type_id?: number
  ci_type_id?: number
  relation_type_id?: number
  constraint?: string
}>({
  source_ci_type_id: undefined,
  ci_type_id: undefined,
  relation_type_id: undefined,
  constraint: undefined,
})

const rules = {
  source_ci_type_id: [{ required: true, message: t('cmdb.ciType.sourceCITypeTips') }],
  ci_type_id: [{ required: true, message: t('cmdb.ciType.dstCITypeTips') }],
  relation_type_id: [{ required: true, message: t('cmdb.ciType.relationTypeTips') }],
  constraint: [{ required: true, message: t('cmdb.ciType.relationConstraintTips') }],
}

const displayCITypes = computed(() => CITypes.value.filter((c) => c.id === props.CITypeId))

const constraintMap = computed<Record<string, string>>(() => ({
  '0': t('cmdb.ciType.one2Many'),
  '1': t('cmdb.ciType.one2One'),
  '2': t('cmdb.ciType.many2Many'),
}))

async function getData() {
  if (!props.isInGrantComp) {
    await getCITypeParentData()
  }
  await getCITypeChildrenData()
}

async function getCITypeParentData() {
  await getCITypeParent(props.CITypeId as number).then((res) => {
    parentTableData.value = res.parents.map((item: any) => {
      const parentAndChildAttrList = handleAttrList(item)
      return {
        ...item,
        parentAndChildAttrList,
        source_ci_type_name: props.CITypeName,
        source_ci_type_id: props.CITypeId,
        isParent: true,
      }
    })
  })
}

async function getCITypeChildrenData() {
  await getCITypeChildren(props.CITypeId as number).then((res) => {
    const data = res.children.map((obj: any) => {
      const parentAndChildAttrList = handleAttrList(obj)
      return {
        ...obj,
        parentAndChildAttrList,
        source_ci_type_name: props.CITypeName,
        source_ci_type_id: props.CITypeId,
      }
    })
    if (parentTableData.value && parentTableData.value.length) {
      tableData.value = [...data, { isDivider: true }, ...parentTableData.value]
    } else {
      tableData.value = data
    }
  })
}

function handleAttrList(data: any): AttrLink[] {
  const length = Math.min(data?.parent_attr_ids?.length || 0, data?.child_attr_ids?.length || 0)
  const parentAndChildAttrList: AttrLink[] = []
  for (let i = 0; i < length; i++) {
    parentAndChildAttrList.push({
      id: uuidv4(),
      parentAttrId: data?.parent_attr_ids?.[i] ?? undefined,
      childAttrId: data?.child_attr_ids?.[i] ?? undefined,
    })
  }
  return parentAndChildAttrList
}

function getCITypesData() {
  getCITypes().then((res) => {
    CITypes.value = res.ci_types
  })
}

function getCITypeGroups() {
  getCITypeGroupsConfig({ need_other: true }).then((raw: any[]) => {
    CITypeGroups.value = (raw || []).filter((group) => group?.ci_types?.length)
  })
}

function getRelationTypesData() {
  getRelationTypes().then((res) => {
    relationTypes.value = res
  })
}

function handleDelete(record: any) {
  deleteRelation(record.source_ci_type_id, record.id).then(() => {
    message.success(t('deleteSuccess'))
    getData()
  })
}

function handleCreate() {
  drawerTitle.value = t('cmdb.ciType.addRelation')
  visible.value = true
  modalAttrList.value = [{ id: uuidv4(), parentAttrId: undefined, childAttrId: undefined }]
  nextTick(() => {
    formModel.source_ci_type_id = props.CITypeId as number
  })
}

function onClose() {
  formRef.value?.resetFields()
  visible.value = false
}

async function handleSubmit() {
  formRef.value
    .validate()
    .then(async () => {
      const { source_ci_type_id, ci_type_id, relation_type_id, constraint } = formModel
      const { parent_attr_ids, child_attr_ids, validate } = handleValidateAttrList(modalAttrList.value)
      if (!validate) {
        return
      }
      await createRelation(source_ci_type_id as number, ci_type_id as number, {
        relation_type_id,
        constraint,
        parent_attr_ids,
        child_attr_ids,
      })
      message.success(t('addSuccess'))
      onClose()
      getData()
    })
    .catch(() => {})
}

function handleValidateAttrList(attrList: AttrLink[]) {
  const parent_attr_ids: number[] = []
  const child_attr_ids: number[] = []
  attrList.forEach((attr) => {
    if (attr.parentAttrId) {
      parent_attr_ids.push(attr.parentAttrId)
    }
    if (attr.childAttrId) {
      child_attr_ids.push(attr.childAttrId)
    }
  })

  if (parent_attr_ids.length !== child_attr_ids.length) {
    message.warning(t('cmdb.ciType.attributeAssociationTip3'))
    return { validate: false, parent_attr_ids, child_attr_ids }
  }

  return { validate: true, parent_attr_ids, child_attr_ids }
}

function handleOpenGrant(record: any) {
  cmdbGrantRef.value?.open({
    name: `${record.source_ci_type_name} -> ${record.name}`,
    typeRelationIds: [record.source_ci_type_id, record.id],
    cmdbGrantType: 'type_relation',
  })
}

function rowClass({ row }: any) {
  if (row.isDivider) return 'relation-table-divider'
  if (row.isParent) return 'relation-table-parent'
}

function handleEditActived({ row }: any) {
  nextTick(async () => {
    if (isContinueCloseEdit.value) {
      const editRecord = xTableRef.value?.getEditRecord()
      const { row: editRow, column } = editRecord
      currentEditData.value = { row: editRow, column }
      return
    }
    const nextTableAttrList: AttrLink[] = []
    const length = Math.min(row?.parent_attr_ids?.length || 0, row?.child_attr_ids?.length || 0)
    if (length) {
      for (let i = 0; i < length; i++) {
        nextTableAttrList.push({
          id: uuidv4(),
          parentAttrId: row?.parent_attr_ids?.[i] ?? undefined,
          childAttrId: row?.child_attr_ids?.[i] ?? undefined,
        })
      }
    } else {
      nextTableAttrList.push({ id: uuidv4(), parentAttrId: undefined, childAttrId: undefined })
    }
    tableAttrList.value = nextTableAttrList
  })
}

async function handleEditClose({ row }: any) {
  if (currentEditData.value) {
    currentEditData.value = null
    return
  }

  isContinueCloseEdit.value = true

  const { source_ci_type_id: parentId, id: childrenId, constraint, relation_type } = row
  const findRelation = relationTypes.value.find((item) => item.name === relation_type)
  const relation_type_id = findRelation?.id

  const { parent_attr_ids, child_attr_ids, validate } = handleValidateAttrList(tableAttrList.value)
  if (!validate) {
    isContinueCloseEdit.value = false
    return
  }

  await createRelation(
    row.isParent ? childrenId : parentId,
    row.isParent ? parentId : childrenId,
    {
      relation_type_id,
      constraint,
      parent_attr_ids,
      child_attr_ids,
    }
  ).finally(async () => {
    await getData()
    isContinueCloseEdit.value = false

    if (currentEditData.value) {
      setTimeout(async () => {
        const fullData = xTableRef.value?.getTableData()?.fullData ?? []
        const findEdit = fullData.find((item: any) => item.id === currentEditData.value?.row?.id)
        await xTableRef.value?.setEditRow(findEdit, 'attributeAssociation')
      })
    }
  })
}

function getAttrNameById(attrs: any[], id: number) {
  const findAttr = attrs.find((attr) => attr.id === id)
  return findAttr?.alias ?? findAttr?.name ?? id
}

function changeChild(value: number) {
  modalAttrList.value.forEach((item) => {
    item.childAttrId = undefined
  })
  if (value) {
    getCITypeAttributesById(value).then((res) => {
      modalChildAttributes.value = res?.attributes ?? []
    })
  }
}

function filterAttributes(
  attrs: any[],
  relationAttrId: number | undefined,
  relationAttrs: any[],
  type: 'parent' | 'child',
  constraint?: string | number
) {
  const relationAttr = relationAttrs.find((attr) => attr.id === relationAttrId)

  let filterAttrs = attrs.filter((attr) => {
    if (attr.value_type === '2' && !attr.is_index) {
      return false
    }
    return !attr.is_password && attr.value_type !== '6' && !attr.is_bool && !attr.is_reference
  })

  if (relationAttr) {
    filterAttrs = filterAttrs.filter((attr) => attr.value_type === relationAttr?.value_type)
  }

  const constraintValue = Number(constraint ?? formModel.constraint)
  if (
    (constraintValue === 0 && type === 'child') ||
    constraintValue === 1 ||
    (constraintValue === 2 && relationAttr?.is_list)
  ) {
    return filterAttrs.filter((attr) => !attr.is_list)
  }

  return filterAttrs
}

function addTableAttr() {
  tableAttrList.value.push({ id: uuidv4(), parentAttrId: undefined, childAttrId: undefined })
}

function removeTableAttr(id: string) {
  if (tableAttrList.value.length <= 1) {
    message.error(t('cmdb.ciType.attributeAssociationTip6'))
    return
  }
  const index = tableAttrList.value.findIndex((item) => item.id === id)
  if (index !== -1) {
    tableAttrList.value.splice(index, 1)
  }
}

function addModalAttr() {
  modalAttrList.value.push({ id: uuidv4(), parentAttrId: undefined, childAttrId: undefined })
}

function removeModalAttr(id: string) {
  if (modalAttrList.value.length <= 1) {
    message.error(t('cmdb.ciType.attributeAssociationTip6'))
    return
  }
  const index = modalAttrList.value.findIndex((item) => item.id === id)
  if (index !== -1) {
    modalAttrList.value.splice(index, 1)
  }
}

function handleFormConstraintChange() {
  modalAttrList.value.forEach((item) => {
    item.parentAttrId = undefined
    item.childAttrId = undefined
  })
}

onMounted(() => {
  getCITypeAttributesById(props.CITypeId as number).then((res) => {
    attributes.value = res?.attributes ?? []
  })
  getCITypesData()
  getRelationTypesData()
  getCITypeGroups()
  getData()
})
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order, vue/v-on-event-hyphenation -->
  <div class="relation-table" :style="{ padding: '0 20px 20px' }">
    <div v-if="!isInGrantComp" class="relation-table-add">
      <a-button type="primary" @click="handleCreate" ghost class="ops-button-ghost">
        <template #icon><PlusOutlined /></template>
        {{ t('create') }}
      </a-button>
    </div>
    <vxe-table
      ref="xTableRef"
      stripe
      :data="tableData"
      size="small"
      show-overflow
      show-header-overflow
      highlight-hover-row
      keep-source
      class="ops-stripe-table"
      min-height="500"
      :row-class-name="rowClass"
      :edit-config="{ trigger: 'dblclick', mode: 'cell', showIcon: false }"
      resizable
      @edit-closed="handleEditClose"
      @edit-actived="handleEditActived"
    >
      <vxe-column field="source_ci_type_name" :title="t('cmdb.ciType.sourceCIType')"></vxe-column>
      <vxe-column field="relation_type" :title="t('cmdb.ciType.relationType')">
        <template #default="{ row }">
          <span class="primary-color" v-if="row.isParent">{{ t('cmdb.ciType.isParent') }}</span>
          {{ row.relation_type }}
        </template>
      </vxe-column>
      <vxe-column field="alias" :title="t('cmdb.ciType.dstCIType')"></vxe-column>
      <vxe-column field="constraint" :title="t('cmdb.ciType.relationConstraint')">
        <template #default="{ row }">
          <span v-if="row.isParent && constraintMap[row.constraint]">{{
            constraintMap[row.constraint].split(' ').reverse().join(' ')
          }}</span>
          <span v-else>{{ constraintMap[row.constraint] }}</span>
        </template>
      </vxe-column>
      <vxe-column :width="300" field="attributeAssociation" :edit-render="{}">
        <template #header>
          <span>
            <a-tooltip>
              <template #title>
                <div>{{ t('cmdb.ciType.attributeAssociationTip1') }}</div>
                <div>{{ t('cmdb.ciType.attributeAssociationTip7') }}</div>
                <div>{{ t('cmdb.ciType.attributeAssociationTip8') }}</div>
                <div>{{ t('cmdb.ciType.attributeAssociationTip9') }}</div>
              </template>
              <a><QuestionCircleOutlined /></a>
            </a-tooltip>
            {{ t('cmdb.ciType.attributeAssociation') }}
            <span :style="{ fontSize: '10px', fontWeight: 'normal' }" class="text-color-4">
              {{ t('cmdb.ciType.attributeAssociationTip2') }}
            </span>
          </span>
        </template>
        <template #default="{ row }">
          <template v-for="item in row.parentAndChildAttrList" :key="item.id">
            <div v-if="item.parentAttrId && item.childAttrId">
              {{ getAttrNameById(row.isParent ? row.attributes : attributes, item.parentAttrId) }}=>
              {{ getAttrNameById(row.isParent ? attributes : row.attributes, item.childAttrId) }}
            </div>
          </template>
        </template>
        <template #edit="{ row }">
          <div v-for="item in tableAttrList" :key="item.id" class="table-attribute-row">
            <a-select
              allow-clear
              size="small"
              v-model:value="item.parentAttrId"
              :get-popup-container="(trigger: any) => trigger.parentNode"
              :style="{ width: '100px' }"
              show-search
              option-filter-prop="title"
            >
              <a-select-option
                v-for="attr in filterAttributes(
                  row.isParent ? row.attributes : attributes,
                  item.childAttrId,
                  row.isParent ? attributes : row.attributes,
                  'parent',
                  row.constraint
                )"
                :key="attr.id"
                :value="attr.id"
                :title="attr.alias || attr.name"
              >
                {{ attr.alias || attr.name }}
              </a-select-option>
            </a-select>
            <span class="table-attribute-row-link">=></span>
            <a-select
              allow-clear
              size="small"
              v-model:value="item.childAttrId"
              :get-popup-container="(trigger: any) => trigger.parentNode"
              :style="{ width: '100px' }"
              show-search
              option-filter-prop="title"
            >
              <a-select-option
                v-for="attr in filterAttributes(
                  row.isParent ? attributes : row.attributes,
                  item.parentAttrId,
                  row.isParent ? row.attributes : attributes,
                  'child',
                  row.constraint
                )"
                :key="attr.id"
                :value="attr.id"
                :title="attr.alias || attr.name"
              >
                {{ attr.alias || attr.name }}
              </a-select-option>
            </a-select>
            <a class="table-attribute-row-action" @click="removeTableAttr(item.id)">
              <MinusCircleOutlined />
            </a>
            <a class="table-attribute-row-action" @click="addTableAttr">
              <PlusCircleOutlined />
            </a>
          </div>
        </template>
      </vxe-column>
      <vxe-column field="operation" :title="t('operation')" width="100">
        <template #default="{ row }">
          <a-space v-if="!row.isParent && row.source_ci_type_id">
            <a @click="handleOpenGrant(row)"><UserAddOutlined /></a>
            <a-popconfirm v-if="!isInGrantComp" :title="t('cmdb.ciType.confirmDelete2')" @confirm="handleDelete(row)">
              <a style="color: red"><DeleteOutlined /></a>
            </a-popconfirm>
          </a-space>
        </template>
      </vxe-column>
      <template #empty>
        <div>
          <img :style="{ width: '100px' }" :src="dataEmptyImg" />
          <div>{{ t('noData') }}</div>
        </div>
      </template>
    </vxe-table>
    <a-modal
      :closable="false"
      :title="drawerTitle"
      :open="visible"
      @cancel="onClose"
      @ok="handleSubmit"
      width="700px"
    >
      <a-form ref="formRef" :model="formModel" :rules="rules" :label-col="{ span: 6 }" :wrapper-col="{ span: 14 }">
        <a-form-item :label="t('cmdb.ciType.sourceCIType')" name="source_ci_type_id">
          <a-select v-model:value="formModel.source_ci_type_id" :placeholder="t('cmdb.ciType.sourceCITypeTips')">
            <a-select-option v-for="CIType in displayCITypes" :key="CIType.id" :value="CIType.id">
              {{ CIType.alias }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('cmdb.ciType.dstCIType')" name="ci_type_id">
          <a-select
            v-model:value="formModel.ci_type_id"
            :placeholder="t('cmdb.ciType.dstCITypeTips')"
            show-search
            option-filter-prop="title"
            @change="changeChild"
          >
            <a-select-opt-group v-for="group in CITypeGroups" :key="group.id" :label="group.name || t('other')">
              <a-select-option
                v-for="type in group.ci_types"
                :key="type.id"
                :value="type.id"
                :title="type.alias || type.name || t('other')"
              >
                {{ type.alias || type.name || t('other') }}
                <span v-if="type.name" class="select-option-name">({{ type.name }})</span>
              </a-select-option>
            </a-select-opt-group>
          </a-select>
        </a-form-item>

        <a-form-item :label="t('cmdb.ciType.relationType')" name="relation_type_id">
          <a-select v-model:value="formModel.relation_type_id" :placeholder="t('cmdb.ciType.relationTypeTips')">
            <a-select-option
              v-for="relationType in relationTypes"
              :key="relationType.id"
              :value="relationType.id"
            >
              {{ relationType.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('cmdb.ciType.relationConstraint')" name="constraint">
          <a-select
            v-model:value="formModel.constraint"
            :placeholder="t('cmdb.ciType.relationConstraintTips')"
            @change="handleFormConstraintChange"
          >
            <a-select-option value="0">{{ t('cmdb.ciType.one2Many') }}</a-select-option>
            <a-select-option value="1">{{ t('cmdb.ciType.one2One') }}</a-select-option>
            <a-select-option value="2">{{ t('cmdb.ciType.many2Many') }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('cmdb.ciType.attributeAssociation')">
          <template #extra>
            <div>{{ t('cmdb.ciType.attributeAssociationTip7') }}</div>
            <div>{{ t('cmdb.ciType.attributeAssociationTip8') }}</div>
            <div>{{ t('cmdb.ciType.attributeAssociationTip9') }}</div>
          </template>
          <a-row v-for="item in modalAttrList" :key="item.id">
            <a-col :span="10">
              <a-form-item>
                <a-select
                  v-model:value="item.parentAttrId"
                  :placeholder="t('cmdb.ciType.attributeAssociationTip4')"
                  option-filter-prop="title"
                  show-search
                  allow-clear
                >
                  <a-select-option
                    v-for="attr in filterAttributes(attributes, item.childAttrId, modalChildAttributes, 'parent')"
                    :key="attr.id"
                    :title="attr.alias || attr.name"
                    :value="attr.id"
                  >
                    {{ attr.alias || attr.name }}
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="2" :style="{ textAlign: 'center' }"> => </a-col>
            <a-col :span="9">
              <a-form-item>
                <a-select
                  v-model:value="item.childAttrId"
                  :placeholder="t('cmdb.ciType.attributeAssociationTip5')"
                  option-filter-prop="title"
                  show-search
                  allow-clear
                >
                  <a-select-option
                    v-for="attr in filterAttributes(modalChildAttributes, item.parentAttrId, attributes, 'child')"
                    :key="attr.id"
                    :title="attr.alias || attr.name"
                    :value="attr.id"
                  >
                    {{ attr.alias || attr.name }}
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="3">
              <a class="modal-attribute-action" @click="removeModalAttr(item.id)">
                <MinusCircleOutlined />
              </a>
              <a class="modal-attribute-action" @click="addModalAttr">
                <PlusCircleOutlined />
              </a>
            </a-col>
          </a-row>
        </a-form-item>
      </a-form>
    </a-modal>
    <CMDBGrant ref="cmdbGrantRef" resourceType="CITypeRelation" app_id="cmdb" />
  </div>
</template>

<style lang="less" scoped>
.relation-table {
  :deep(.vxe-cell) {
    max-height: max-content !important;
  }

  &-add {
    margin-bottom: 10px;
    display: flex;
    justify-content: flex-end;
  }
}
.table-attribute-row {
  display: inline-flex;
  align-items: center;
  margin-top: 5px;

  &:last-child {
    margin-bottom: 5px;
  }

  &-link {
    margin: 0 5px;
  }

  &-action {
    margin-left: 5px;
  }
}

.modal-attribute-action {
  margin-left: 5px;
}

.model-select-name {
  font-size: 12px;
  color: #a5a9bc;
}

.primary-color {
  color: @primary-color;
}

.select-option-name {
  font-size: 12px;
  color: #a5a9bc;
}

.ops-stripe-table {
  :deep(.relation-table-divider) {
    background-color: #b1b8d3 !important;

    td {
      height: 2px !important;
      line-height: 2px !important;
    }
  }

  :deep(.relation-table-parent) {
    background-color: @primary-color_5 !important;
  }
}
</style>
