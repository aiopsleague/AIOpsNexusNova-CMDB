<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  QuestionCircleOutlined,
  MinusCircleOutlined,
  PlusCircleOutlined,
  UserAddOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
import { uuidv4 } from '@/utils/uuid'
import { getCITypeRelations, deleteRelation, createRelation } from '@/modules/cmdb/api/CITypeRelation'
import { getRelationTypes } from '@/modules/cmdb/api/relationType'
import CMDBGrant from '@/modules/cmdb/components/cmdbGrant/index.vue'

interface AttrLink {
  id: string
  parentAttrId?: number
  childAttrId?: number
}

const { t } = useI18n()

const xTable = ref<any>()
const cmdbGrant = ref<InstanceType<typeof CMDBGrant>>()

const tableData = ref<any[]>([])
const relationTypeList = ref<any[]>([])
const type2attributes = ref<Record<string, any[]>>({})
const tableAttrList = ref<AttrLink[]>([])

const windowHeight = computed(() => window.innerHeight)

const constraintMap = computed<Record<string, string>>(() => ({
  '0': t('cmdb.ciType.one2Many'),
  '1': t('cmdb.ciType.one2One'),
  '2': t('cmdb.ciType.many2Many'),
}))

async function refresh() {
  await getRelationTypesData()
  await getMainData()
}

async function getMainData() {
  const { relations, type2attributes: type2attrs } = await getCITypeRelations()
  tableData.value = relations.map((item: any) => {
    const parentAndChildAttrList = handleAttrList(item)
    return {
      ...item,
      parentAndChildAttrList,
    }
  })
  type2attributes.value = type2attrs
}

function handleAttrList(data: any): AttrLink[] {
  const length = Math.min(data?.parent_attr_ids?.length || 0, data.child_attr_ids?.length || 0)
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

// Fetch relation types.
async function getRelationTypesData() {
  const res = await getRelationTypes()
  relationTypeList.value = res.map((item: any) => ({ value: item.id, label: item.name }))
}

// Convert relation constraint id to label.
function handleConstraint(constraintId: string | number) {
  return constraintMap.value[String(constraintId)]
}

function handleOpenGrant(record: any) {
  cmdbGrant.value?.open({
    name: `${record.parent.name} -> ${record.child.name}`,
    typeRelationIds: [record.parent_id, record.child_id],
    cmdbGrantType: 'type_relation',
  })
}

function deleteRelationItem(row: any) {
  deleteRelation(row.parent_id, row.child_id).then(() => {
    message.success(t('deleteSuccess'))
    getRelationTypesData()
    refresh()
  })
}

function handleEditActived({ row }: { row: any }) {
  const nextTableAttrList: AttrLink[] = []
  const length = Math.min(row?.parent_attr_ids?.length || 0, row.child_attr_ids?.length || 0)
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

async function handleEditClose({ row }: { row: any }) {
  const { parent_id, child_id, constraint, relation_type_id } = row

  const { parent_attr_ids, child_attr_ids, validate } = handleValidateAttrList(tableAttrList.value)
  if (!validate) {
    return
  }

  await createRelation(parent_id, child_id, {
    relation_type_id,
    constraint,
    parent_attr_ids,
    child_attr_ids,
  }).finally(() => {
    getMainData()
  })
}

function getAttrNameById(attributes: any[], id: number) {
  const _find = attributes.find((attr) => attr.id === id)
  return _find?.alias ?? _find?.name ?? id
}

function filterAttributes(row: any, relationAttrId: number | undefined, type: 'parent' | 'child') {
  const { parent_id, child_id, constraint } = row
  const currentAttrs = type2attributes.value?.[child_id] || []

  const relationAttrs = type2attributes.value?.[parent_id] || []
  const relationAttr = relationAttrs.find((attr) => attr.id === relationAttrId)

  // Filter password/json/longText/bool/reference.
  let filterAttrs = currentAttrs.filter((attr) => {
    if (attr.value_type === '2' && !attr.is_index) {
      return false
    }

    return !attr.is_password && attr.value_type !== '6' && !attr.is_bool && !attr.is_reference
  })

  if (relationAttr) {
    filterAttrs = filterAttrs.filter((attr) => attr.value_type === relationAttr?.value_type)
  }

  const constraintValue = Number(constraint)
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

onMounted(() => {
  refresh()
})

defineExpose({ refresh })
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <div class="model-relation-table">
    <vxe-table
      ref="xTable"
      stripe
      class="ops-stripe-table"
      show-header-overflow
      show-overflow
      resizable
      :scroll-y="{ enabled: false }"
      :height="`${windowHeight - 160}px`"
      :data="tableData"
      :sort-config="{ defaultSort: { field: 'created_at', order: 'desc' } }"
      :edit-config="{ trigger: 'dblclick', mode: 'cell', showIcon: false }"
      @edit-closed="handleEditClose"
      @edit-actived="handleEditActived"
    >
      <vxe-column field="created_at" :title="t('created_at')" sortable width="170"></vxe-column>
      <vxe-column field="parent.alias" :title="t('cmdb.ciType.sourceCIType')"></vxe-column>
      <vxe-column
        field="relation_type_id"
        :title="t('cmdb.custom_dashboard.relation')"
        :filters="relationTypeList"
        :filter-multiple="false"
      >
        <template #default="{ row }">
          <a-tag color="cyan">
            {{ row.relation_type.name }}
          </a-tag>
        </template>
      </vxe-column>
      <vxe-column field="child.alias" :title="t('cmdb.ciType.dstCIType')"></vxe-column>
      <vxe-column field="constraint" :title="t('cmdb.ciType.relationConstraint')">
        <template #default="{ row }">
          {{ handleConstraint(row.constraint) }}
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
            <span :style="{ fontSize: '10px', fontWeight: 'normal' }" class="text-color-4">{{
              t('cmdb.ciType.attributeAssociationTip2')
            }}</span>
          </span>
        </template>
        <template #default="{ row }">
          <template v-for="item in row.parentAndChildAttrList" :key="item.id">
            <div v-if="item.parentAttrId && item.childAttrId">
              {{ getAttrNameById(type2attributes[row.parent_id], item.parentAttrId) }}=>
              {{ getAttrNameById(type2attributes[row.child_id], item.childAttrId) }}
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
                v-for="attr in filterAttributes(row, item.childAttrId, 'parent')"
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
                v-for="attr in filterAttributes(row, item.parentAttrId, 'child')"
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
      <vxe-column field="operation" :title="t('operation')" width="89">
        <template #default="{ row }">
          <a-space>
            <a @click="handleOpenGrant(row)"><UserAddOutlined /></a>
            <a-popconfirm :title="t('cmdb.ciType.confirmDelete2')" @confirm="deleteRelationItem(row)">
              <a :style="{ color: 'red' }"><DeleteOutlined /></a>
            </a-popconfirm>
          </a-space>
        </template>
      </vxe-column>
    </vxe-table>
    <CMDBGrant ref="cmdbGrant" resourceType="CITypeRelation" app_id="cmdb" />
  </div>
</template>

<style lang="less" scoped>
.relation-table {
  :deep(.vxe-cell) {
    max-height: max-content !important;
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

  :deep(.ant-select-selection) {
    box-shadow: none;
  }
}
</style>
