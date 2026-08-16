<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import {
  getRelationTypes,
  deleteRelationType,
  addRelationType,
  updateRelationType,
} from '@/modules/cmdb/api/relationType'

const { t } = useI18n()

const relationTypeTable = ref<any>()

const tableData = ref<any[]>([])

async function loadData() {
  const res = await getRelationTypes()
  tableData.value = res
}

function handleEdit(row: any) {
  const $table = relationTypeTable.value
  $table.setActiveRow(row)
}

async function handleCreate() {
  const $table = relationTypeTable.value
  const newRow = {
    name: '',
    color: '#1890ff',
    created_at: dayjs().format('YYYY-MM-DD hh:mm:ss'),
  }
  const { row } = await $table.insertAt(newRow, -1)
  $table.setActiveRow(row)
}

function handleEditClose({ row }: { row: any; rowIndex: number; column: any }) {
  const $table = relationTypeTable.value
  if (row.id) {
    if (row.name && ($table.isUpdateByRow(row, 'name') || $table.isUpdateByRow(row, 'color'))) {
      saveRelationType(row.id, { name: row.name, color: row.color })
    } else {
      $table.revertData(row)
    }
  } else {
    if (row.name) {
      createRelationType({ name: row.name, color: row.color || '#1890ff' })
    } else {
      loadData()
    }
  }
}

function saveRelationType(id: string | number, data: Record<string, unknown>) {
  updateRelationType(id, data).then(() => {
    message.success(t('updateSuccess'))
    loadData()
  })
}

function createRelationType(data: Record<string, unknown>) {
  addRelationType(data).then(() => {
    message.success(t('addSuccess'))
    loadData()
  })
}

function handleDelete(record: any) {
  deleteRelationType(record.id).then(() => {
    message.success(t('deleteSuccess'))
    loadData()
  })
}

function customCloseEdit($event: any) {
  // Enter closes the active edit row.
  if ($event?.keyCode === 13) {
    const $table = relationTypeTable.value
    $table.clearActived()
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <a-card :bordered="false">
    <div class="action-btn">
      <a-button @click="handleCreate" type="primary" style="margin-bottom: 15px">{{
        t('cmdb.relation_type.addRelationType')
      }}</a-button>
    </div>
    <vxe-table
      ref="relationTypeTable"
      :data="tableData"
      keep-source
      highlight-hover-row
      :edit-config="{ trigger: 'manual', mode: 'row' }"
      @edit-closed="handleEditClose"
      stripe
      class="ops-stripe-table"
      bordered
    >
      <vxe-column field="name" :title="t('name')" :edit-render="{ autofocus: '.vxe-input--inner' }">
        <template #edit="{ row }">
          <vxe-input v-model="row.name" type="text" @keyup="customCloseEdit"></vxe-input>
        </template>
      </vxe-column>
      <vxe-column field="color" :title="t('cmdb.relation_type.color')" width="100" align="center" :edit-render="{}">
        <template #default="{ row }">
          <div class="color-swatch" :style="{ backgroundColor: row.color || '#1890ff' }"></div>
        </template>
        <template #edit="{ row }">
          <input
            v-model="row.color"
            type="color"
            style="width: 50px; height: 28px; border: 1px solid #d9d9d9; border-radius: 2px; cursor: pointer"
          />
        </template>
      </vxe-column>
      <vxe-column field="updateTime" :title="t('updated_at')">
        <template #default="{ row }">
          {{ row.updated_at || row.created_at }}
        </template>
      </vxe-column>
      <vxe-column field="operation" :title="t('operation')" align="center">
        <template #default="{ row }">
          <a @click="handleEdit(row)"><EditOutlined /></a>
          <a-divider type="vertical" />
          <a-popconfirm
            :title="t('confirmDelete')"
            @confirm="handleDelete(row)"
            :ok-text="t('yes')"
            :cancel-text="t('no')"
          >
            <a :style="{ color: 'red' }"><DeleteOutlined /></a>
          </a-popconfirm>
        </template>
      </vxe-column>
    </vxe-table>
  </a-card>
</template>

<style lang="less" scoped>
.color-swatch {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid #d9d9d9;
  vertical-align: middle;
}
</style>
