<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined, MinusCircleOutlined, PlusCircleOutlined } from '@ant-design/icons-vue'
import { searchResourceType } from '@/modules/acl/api/resource'
import { getCITypeGroupsConfig } from '@/modules/cmdb/api/ciTypeGroup'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { createRelation, getRelationTypes } from '@/modules/cmdb/api/CITypeRelation'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { uuidv4 } from '@/utils/uuid'
import ModelRelationTable from './modules/modelRelationTable.vue'
import CMDBTypeSelectAntd from '@/modules/cmdb/components/cmdbTypeSelect/cmdbTypeSelectAntd.vue'

interface AttrLink {
  id: string
  parentAttrId?: number
  childAttrId?: number
}

const { t } = useI18n()

const tableRef = ref<InstanceType<typeof ModelRelationTable>>()
const formRef = ref()

const resource_type = ref<Record<string, any>>({})
const CITypeGroups = ref<any[]>([])
const currentId = ref<string | null>(null)

const visible = ref(false)
const drawerTitle = ref('')
const CITypes = ref<any[]>([])
const relationTypes = ref<any[]>([])

const sourceCITypeId = ref<number | undefined>(undefined)
const targetCITypeId = ref<number | undefined>(undefined)

const modalParentAttributes = ref<any[]>([])
const modalChildAttributes = ref<any[]>([])
const modalAttrList = ref<AttrLink[]>([])

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

async function loadCITypes(isResetCurrentId = false) {
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
    CITypeGroups.value = groups
    localStorage.setItem('ops_cityps_currentId', currentId.value ?? '')
  })
}

function getCITypesData() {
  getCITypes().then((res) => {
    CITypes.value = res.ci_types
  })
}

function getRelationTypesData() {
  getRelationTypes().then((res) => {
    relationTypes.value = res
  })
}

function handleCreate() {
  drawerTitle.value = t('cmdb.ciType.addRelation')
  visible.value = true
  modalAttrList.value = [{ id: uuidv4(), parentAttrId: undefined, childAttrId: undefined }]
  nextTick(() => {
    formModel.source_ci_type_id = sourceCITypeId.value
  })
}

function onClose() {
  formRef.value?.resetFields()
  visible.value = false
  sourceCITypeId.value = undefined
  targetCITypeId.value = undefined
}

function handleSubmit() {
  formRef.value
    .validate()
    .then(() => {
      const { source_ci_type_id, ci_type_id, relation_type_id, constraint } = formModel

      const { parent_attr_ids, child_attr_ids, validate } = handleValidateAttrList(modalAttrList.value)
      if (!validate) {
        return
      }

      createRelation(source_ci_type_id as number, ci_type_id as number, {
        relation_type_id,
        constraint,
        parent_attr_ids,
        child_attr_ids,
      }).then(() => {
        message.success(t('addSuccess'))
        onClose()
        handleOk()
      })
    })
    .catch(() => {})

  sourceCITypeId.value = undefined
  targetCITypeId.value = undefined
}

/**
 * Validate the attribute association list.
 */
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

function handleOk() {
  tableRef.value?.refresh()
}

function handleSourceTypeChange(value: number) {
  sourceCITypeId.value = value
  modalAttrList.value.forEach((item) => {
    item.parentAttrId = undefined
  })
  getCITypeAttributesById(value).then((res) => {
    modalParentAttributes.value = res?.attributes ?? []
  })
}

function handleTargetTypeChange(value: number) {
  targetCITypeId.value = value
  modalAttrList.value.forEach((item) => {
    item.childAttrId = undefined
  })
  getCITypeAttributesById(value).then((res) => {
    modalChildAttributes.value = res?.attributes ?? []
  })
}

function filterAttributes(
  attributes: any[],
  relationAttrId: number | undefined,
  relationAttrs: any[],
  type: 'parent' | 'child'
) {
  const relationAttr = relationAttrs.find((attr) => attr.id === relationAttrId)

  // Filter password/json/longText/bool/reference.
  let filterAttrs = attributes.filter((attr) => {
    if (attr.value_type === '2' && !attr.is_index) {
      return false
    }

    return !attr.is_password && attr.value_type !== '6' && !attr.is_bool && !attr.is_reference
  })

  if (relationAttr) {
    filterAttrs = filterAttrs.filter((attr) => attr.value_type === relationAttr?.value_type)
  }

  const constraintValue = Number(formModel.constraint)
  if (
    (constraintValue === 0 && type === 'child') ||
    constraintValue === 1 ||
    (constraintValue === 2 && relationAttr?.is_list)
  ) {
    return filterAttrs.filter((attr) => !attr.is_list)
  }

  return filterAttrs
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

function handleConstraintChange() {
  modalAttrList.value.forEach((item) => {
    item.parentAttrId = undefined
    item.childAttrId = undefined
  })
}

onMounted(() => {
  getCITypesData()
  getRelationTypesData()

  const _currentId = localStorage.getItem('ops_cityps_currentId')
  if (_currentId) {
    currentId.value = _currentId
  }
  searchResourceType({ page_size: 9999, app_id: 'cmdb' }).then((res: any) => {
    resource_type.value = { groups: res.groups, id2perms: res.id2perms }
  })
  loadCITypes(!_currentId)
})
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <div class="model-relation">
    <a-button @click="handleCreate" type="primary" style="margin-bottom: 15px">
      <template #icon><PlusOutlined /></template>
      {{ t('cmdb.ciType.addRelation') }}
    </a-button>
    <ModelRelationTable ref="tableRef"></ModelRelationTable>
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
          <CMDBTypeSelectAntd
            v-model="formModel.source_ci_type_id"
            :ci-type-group="CITypeGroups"
            @change="handleSourceTypeChange"
          />
        </a-form-item>
        <a-form-item :label="t('cmdb.ciType.dstCIType')" name="ci_type_id">
          <CMDBTypeSelectAntd
            v-model="formModel.ci_type_id"
            :ci-type-group="CITypeGroups"
            @change="handleTargetTypeChange"
          />
        </a-form-item>

        <a-form-item :label="t('cmdb.ciType.relationType')" name="relation_type_id">
          <a-select v-model:value="formModel.relation_type_id">
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
          <a-select v-model:value="formModel.constraint" @change="handleConstraintChange">
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
                  :placeholder="t('cmdb.ciType.attributeAssociationTip4')"
                  option-filter-prop="title"
                  show-search
                  allow-clear
                  v-model:value="item.parentAttrId"
                >
                  <a-select-option
                    v-for="attr in filterAttributes(modalParentAttributes, item.childAttrId, modalChildAttributes, 'parent')"
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
                  :placeholder="t('cmdb.ciType.attributeAssociationTip5')"
                  option-filter-prop="title"
                  show-search
                  allow-clear
                  v-model:value="item.childAttrId"
                >
                  <a-select-option
                    v-for="attr in filterAttributes(modalChildAttributes, item.parentAttrId, modalParentAttributes, 'child')"
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
  </div>
</template>

<style lang="less" scoped>
.model-relation {
  background-color: #fff;
  border-radius: @border-radius-box;
  padding: 24px;
  height: calc(100vh - 64px);
  margin-bottom: -24px;
}

.modal-attribute-action {
  margin-left: 5px;
}

.model-select-name {
  font-size: 12px;
  color: #a5a9bc;
}
</style>
