<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { PlusOutlined, SaveOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import {
  getUniqueConstraintList,
  addUniqueConstraint,
  updateUniqueConstraint,
  deleteUniqueConstraint,
} from '@/modules/cmdb/api/CIType'

const props = withDefaults(defineProps<{ CITypeId?: number | null }>(), { CITypeId: null })

const { t } = useI18n()

const loading = ref(false)
const visible = ref(false)
const attributes = ref<any[]>([])
const tableData = ref<any[]>([])
const xTableRef = ref<any>()

const filteredAttributes = computed(() => attributes.value.filter((attr) => attr.value_type !== '6'))

function open(attrs: any[]) {
  visible.value = true
  attributes.value = attrs
  getTableList()
}

function handleCancel() {
  visible.value = false
}

function getTableList() {
  loading.value = true
  getUniqueConstraintList(props.CITypeId as number).then((res) => {
    tableData.value = res
    loading.value = false
  })
}

async function handleAddUnique(row: number) {
  const $table = xTableRef.value
  const record = { attr_ids: [] }
  const { row: newRow } = await $table.insertAt(record, row)
  await $table.setActiveRow(newRow)
}

function saveRowEvent(row: any) {
  const $table = xTableRef.value
  $table.clearActived().then(() => {
    if (row.id) {
      updateUniqueConstraint(props.CITypeId as number, row.id, { attr_ids: row.attr_ids }).then(() => {
        getTableList()
      })
    } else {
      addUniqueConstraint(props.CITypeId as number, { attr_ids: row.attr_ids }).then(() => {
        getTableList()
      })
    }
  })
}

function editRowEvent(row: any) {
  const $table = xTableRef.value
  $table.setActiveRow(row)
}

function removeRowEvent(row: any) {
  deleteUniqueConstraint(props.CITypeId as number, row.id).then(() => {
    message.success(t('deleteSuccess'))
    getTableList()
  })
}

function getDisplayName(attrId: number) {
  const found = attributes.value.find((attr) => attr.id === attrId)
  return found.alias || found.name
}

defineExpose({ open })
</script>

<template>
  <a-modal :open="visible" :footer="null" :width="550" :mask-closable="false" @cancel="handleCancel">
    <a-button ghost type="primary" size="small" :style="{ marginBottom: '10px' }" @click="handleAddUnique(-1)">
      <template #icon><PlusOutlined /></template>{{ t('new') }}
    </a-button>
    <vxe-table
      ref="xTableRef"
      :loading="loading"
      :data="tableData"
      :edit-config="{ trigger: 'manual', mode: 'row', showIcon: false, autoClear: false, showStatus: true }"
      highlight-hover-row
      show-overflow
      size="mini"
      keep-source
      stripe
      class="ops-stripe-table"
    >
      <vxe-column field="attr_ids" :title="t('cmdb.ciType.attributes')" :edit-render="{}">
        <template #default="{ row }">
          <template v-for="(attr, index) in row.attr_ids" :key="attr">
            <span class="primary-color">{{ getDisplayName(attr) }}</span>
            <span v-if="index !== row.attr_ids.length - 1"> + </span>
          </template>
        </template>
        <template #edit="{ row }">
          <vxe-select v-model="row.attr_ids" transfer size="small" clearable multiple>
            <vxe-option
              v-for="attr in filteredAttributes"
              :key="attr.id"
              :value="attr.id"
              :label="attr.alias || attr.name"
            />
          </vxe-select>
        </template>
      </vxe-column>
      <vxe-column field="operation" :title="t('operation')" width="100">
        <template #default="{ row }">
          <template v-if="xTableRef?.isActiveByRow(row)">
            <a-space>
              <a><SaveOutlined @click="saveRowEvent(row)" /></a>
            </a-space>
          </template>
          <template v-else>
            <a-space>
              <a><EditOutlined @click="editRowEvent(row)" /></a>
              <a-popconfirm :title="t('cmdb.ciType.confirmDelete2')" @confirm="removeRowEvent(row)">
                <a :style="{ color: 'red' }"><DeleteOutlined /></a>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </vxe-column>
    </vxe-table>
  </a-modal>
</template>

<style lang="less" scoped>
.primary-color {
  color: @primary-color;
}
</style>
