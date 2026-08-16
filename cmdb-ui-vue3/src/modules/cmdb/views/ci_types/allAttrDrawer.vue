<script setup lang="ts">
import { computed, inject, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { cloneDeep, getPropertyType, valueTypeMap } from '../../utils/helper'

interface AttrRow {
  id: number
  name: string
  alias: string
  value_type: string
  groupId: number
  groupName: string
  code: string
  typeText: string
  [key: string]: any
}

const { t } = useI18n()

type GroupsProvider = () => { CITypeGroups: any[]; otherGroupAttributes: any[] }

const providerGroupsData = inject<GroupsProvider>(
  'providerGroupsData',
  (): { CITypeGroups: any[]; otherGroupAttributes: any[] } => ({ CITypeGroups: [], otherGroupAttributes: [] })
)

const windowHeight = computed(() => window.innerHeight)

const visible = ref(false)
const tableData = ref<AttrRow[]>([])

async function open() {
  visible.value = true
  const rows: AttrRow[] = []
  const typeMap = valueTypeMap()
  const providerGroups = cloneDeep(providerGroupsData() || {})
  const groupsData = providerGroups?.CITypeGroups || []
  const otherAttrData = providerGroups?.otherGroupAttributes || []

  groupsData.forEach((group) => {
    if (group?.attributes?.length) {
      const attrArr = group.attributes.map((attr: any) => {
        if (attr.is_password) attr.value_type = '7'
        if (attr.is_link) attr.value_type = '8'
        attr.groupId = group.id
        attr.groupName = group.name
        attr.code = ['0', '1', '6'].includes(attr.value_type)
          ? `{{ ${attr.name} }}`
          : `'''{{ ${attr.name} }}'''`
        attr.typeText = typeMap?.[attr.value_type] ?? ''
        return attr as AttrRow
      })
      rows.push(...attrArr)
    }
  })

  otherAttrData.forEach((attr: any) => {
    attr.value_type = getPropertyType(attr)
    attr.groupId = -1
    attr.groupName = t('cmdb.common.other')
    attr.code = `{{ ${attr.name} }}`
    attr.typeText = typeMap?.[attr.value_type] ?? ''
  })
  rows.push(...otherAttrData)

  tableData.value = rows
}

function mergeRowMethod({ row, _rowIndex, column, visibleData }: any) {
  const fields = ['groupId']
  const currentValue = row.groupId

  if (currentValue && fields.includes(column.field)) {
    const prevRow = visibleData[_rowIndex - 1]
    let nextRow = visibleData[_rowIndex + 1]
    if (prevRow && prevRow.groupId === currentValue) {
      return { rowspan: 0, colspan: 0 }
    }
    let countRowspan = 1
    while (nextRow && nextRow.groupId === currentValue) {
      nextRow = visibleData[++countRowspan + _rowIndex]
    }
    if (countRowspan > 1) {
      return { rowspan: countRowspan, colspan: 1 }
    }
  }
}

function handleClose() {
  visible.value = false
}

function copyText(text: string) {
  navigator.clipboard
    .writeText(text)
    .then(() => {
      message.success(t('copySuccess'))
    })
    .catch(() => {
      message.error(t('cmdb.ci.copyFailed'))
    })
}

defineExpose({ open })
</script>

<template>
  <CustomDrawer :title="t('cmdb.ciType.viewAllAttr')" :open="visible" placement="right" width="800" @close="handleClose">
    <vxe-table
      resizable
      size="mini"
      :span-method="mergeRowMethod"
      :data="tableData"
      show-overflow
      show-header-overflow
      border
      class="ops-stripe-table"
      :height="windowHeight - 160"
    >
      <vxe-column align="center" field="groupId" :title="t('cmdb.ciType.attrGroup')" :width="100">
        <template #default="{ row }">
          <span>{{ row.groupName }}</span>
        </template>
      </vxe-column>
      <vxe-column field="name" :title="t('cmdb.ciType.attrName')" :width="150" />
      <vxe-column field="alias" :title="t('cmdb.ciType.attrAlias')" :width="150" />
      <vxe-column field="typeText" :title="t('cmdb.common.type')" :width="100" />
      <vxe-column field="code" :title="t('cmdb.ciType.attrCode')">
        <template #default="{ row }">
          <a @click="copyText(row.code)">{{ row.code }}</a>
        </template>
      </vxe-column>
    </vxe-table>
  </CustomDrawer>
</template>

<style lang="less" scoped></style>
