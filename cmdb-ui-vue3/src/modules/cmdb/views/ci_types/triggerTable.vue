<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, provide, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { getTriggerList, deleteTrigger, updateTrigger } from '@/modules/cmdb/api/CIType'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { cloneDeep } from '../../utils/helper'
import TriggerForm from './triggerForm.vue'

const props = withDefaults(defineProps<{ CITypeId?: number | null }>(), { CITypeId: null })

const { t } = useI18n()

const tableData = ref<any[]>([])
const attrList = ref<any[]>([])
const triggerForm = ref<InstanceType<typeof TriggerForm>>()

const windowHeight = computed(() => window.innerHeight)

async function getTableData() {
  const [triggerList, attrs] = await Promise.all([
    getTriggerList(props.CITypeId as number),
    getCITypeAttributesById(props.CITypeId as number),
  ])
  triggerList.forEach((trigger: any) => {
    const find = attrs.attributes.find((attr: any) => attr.id === trigger.attr_id)
    if (find) {
      trigger.attr_name = find.alias || find.name
    }
  })
  tableData.value = triggerList
  attrList.value = attrs.attributes
}

function handleAddTrigger() {
  triggerForm.value?.createFromTriggerTable(attrList.value)
}

function handleDetele(id: number) {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ciType.confirmDeleteTrigger'),
    onOk() {
      deleteTrigger(props.CITypeId as number, id).then(() => {
        message.success(t('deleteSuccess'))
        getTableData()
      })
    },
  })
}

function handleEdit(row: any) {
  triggerForm.value?.open(
    {
      id: row.attr_id,
      alias: row?.option?.name ?? '',
      trigger: { id: row.id, attr_id: row.attr_id, option: row.option },
      has_trigger: true,
    },
    attrList.value
  )
}

function changeEnable(row: any) {
  const newRow = cloneDeep(row)
  delete newRow.id
  const enable = row?.option?.enable ?? true
  newRow.option.enable = !enable
  updateTrigger(props.CITypeId as number, row.id, newRow).then(() => {
    getTableData()
  })
}

provide('refresh', getTableData)

defineExpose({ getTableData })
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order, vue/v-on-event-hyphenation -->
  <div class="ci-types-triggers">
    <div class="ci-types-triggers-add">
      <a-button type="primary" @click="handleAddTrigger" ghost class="ops-button-ghost">
        <template #icon><PlusOutlined /></template>
        {{ t('create') }}
      </a-button>
    </div>
    <vxe-table
      stripe
      :data="tableData"
      size="small"
      show-overflow
      highlight-hover-row
      keep-source
      :max-height="windowHeight - 180"
      class="ops-stripe-table"
    >
      <vxe-column field="option.name" :title="t('name')"></vxe-column>
      <vxe-column field="option.description" :title="t('desc')"></vxe-column>
      <vxe-column field="type" :title="t('type')">
        <template #default="{ row }">
          <span v-if="row.attr_id">{{ t('cmdb.ciType.triggerDate') }}</span>
          <span v-else>{{ t('cmdb.ciType.triggerDataChange') }}</span>
        </template>
      </vxe-column>
      <vxe-column field="option.enable" :title="t('cmdb.ciType.triggerEnable')">
        <template #default="{ row }">
          <a-switch :checked="row.option.enable" @click="changeEnable(row)"></a-switch>
        </template>
      </vxe-column>
      <vxe-column field="operation" :title="t('operation')" width="100px" align="center">
        <template #default="{ row }">
          <a-space>
            <a @click="handleEdit(row)"><EditOutlined /></a>
            <a style="color: red" @click="handleDetele(row.id)"><DeleteOutlined /></a>
          </a-space>
        </template>
      </vxe-column>
    </vxe-table>
    <TriggerForm ref="triggerForm" :CITypeId="CITypeId" />
  </div>
</template>

<style lang="less" scoped>
.ci-types-triggers {
  padding: 0 20px 20px;

  &-add {
    margin-bottom: 10px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
