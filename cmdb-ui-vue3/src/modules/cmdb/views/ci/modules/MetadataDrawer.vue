<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { CheckOutlined, SearchOutlined } from '@ant-design/icons-vue'
import { useI18n } from 'vue-i18n'
import { getCITypeAttributesByName } from '@/modules/cmdb/api/CITypeAttr'
import { valueTypeMap, getPropertyType } from '@/modules/cmdb/utils/helper'

const { t } = useI18n()

const visible = ref(false)
const list = ref<any[]>([])
const tableData = ref<any[]>([])
const loading = ref(false)
const valueTypeFilters = ref<Array<{ label: string; value: string }>>([])
const searchKey = ref('')
const typeId = ref<number | null>(null)

const windowHeight = computed(() => window.innerHeight)

const valueTypeMapOptions = computed(() => valueTypeMap())

interface MetadataColumn {
  field: string
  title: string
  width: number
  align?: 'left' | 'center' | 'right' | ''
  help: string | null
}

const columns = computed<MetadataColumn[]>(() => [
  { field: 'name', title: t('name'), width: 150, align: 'left', help: null },
  { field: 'alias', title: t('alias'), width: 150, align: 'left', help: null },
  { field: 'value_type', title: t('type'), width: 100, align: 'left', help: null },
  { field: 'is_index', title: t('cmdb.ciType.isIndex'), width: 110, help: t('cmdb.ci.tips6') },
  { field: 'default_show', title: t('cmdb.ciType.defaultShow'), width: 110, help: t('cmdb.ciType.defaultShowTips') },
  { field: 'is_unique', title: t('cmdb.ciType.isUnique'), width: 110, help: null },
  { field: 'is_choice', title: t('cmdb.ciType.isChoice'), width: 110, help: t('cmdb.ci.tips7') },
  { field: 'is_list', title: t('cmdb.ciType.list'), width: 110, help: t('cmdb.ci.tips8') },
  { field: 'is_sortable', title: t('cmdb.ciType.isSortable'), width: 100, help: t('cmdb.ci.tips9') },
  { field: 'is_computed', title: t('cmdb.ciType.computedAttribute'), width: 110, help: t('cmdb.ci.tips10') },
  { field: 'is_dynamic', title: t('cmdb.ciType.isDynamic'), width: 110, help: t('cmdb.ciType.dynamicTips') },
])

function getColumnFilters(index: number) {
  if (index < 2) return undefined
  if (index === 2) return valueTypeFilters.value
  return [
    { label: t('yes'), value: true },
    { label: t('no'), value: false },
  ]
}

function toValueString(value: any): string {
  return value === null || value === undefined ? '' : String(value)
}

function open(newTypeId: number) {
  visible.value = true
  typeId.value = newTypeId
  getAttrs()
}

async function getAttrs() {
  loading.value = true
  const { attributes = [] } = await getCITypeAttributesByName(typeId.value as number)
  tableData.value = attributes.map((attr: any) => {
    attr.value_type = getPropertyType(attr)
    return attr
  })
  loading.value = false
  searchAttributes()
}

function searchAttributes() {
  const filterName = toValueString(searchKey.value)
    .trim()
    .toLowerCase()
  if (filterName) {
    const searchProps = ['name', 'alias', 'value_type']
    list.value = tableData.value.filter((item) =>
      searchProps.some((key) => toValueString(item[key]).toLowerCase().indexOf(filterName) > -1)
    )
  } else {
    list.value = tableData.value
  }
}

onMounted(() => {
  valueTypeFilters.value = Object.keys(valueTypeMapOptions.value).map((key) => {
    return { label: valueTypeMapOptions.value[key], value: key }
  })
})

defineExpose({ open })
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <CustomDrawer
    v-model:open="visible"
    :has-footer="false"
    :title="t('cmdb.ci.attributeDesc')"
    width="72%"
    :body-style="{ height: '100vh', paddingTop: '16px' }"
  >
    <a-input
      v-model:value="searchKey"
      :style="{ display: 'inline-block', width: '244px', marginBottom: '16px' }"
      class="ops-input ops-input-radius"
      type="search"
      :placeholder="t('cmdb.ci.tips5')"
      @keyup="searchAttributes"
    >
      <template #suffix><SearchOutlined /></template>
    </a-input>

    <a-spin :spinning="loading">
      <vxe-table
        resizable
        border
        size="mini"
        :height="windowHeight - 160"
        :data="list"
        :scroll-x="{ enabled: true, gt: 0 }"
        show-overflow
        show-header-overflow
        align="center"
        highlight-hover-row
        class="ops-stripe-table"
      >
        <vxe-column
          v-for="(column, index) in columns"
          :key="column.field"
          :field="column.field"
          :title="column.title"
          :min-width="column.width"
          :align="column.align"
          :fixed="index < 3 ? 'left' : ''"
          :sortable="index < 3 ? true : false"
          :title-help="column.help !== null ? { message: column.help } : undefined"
          :filters="getColumnFilters(index)"
        >
          <template #default="{ row }">
            <span v-if="column.field !== 'name' && column.field !== 'alias' && column.field !== 'value_type'">
              <CheckOutlined :style="{ color: '#1fb51f' }" v-if="row[column.field]" />
            </span>
            <span v-else-if="column.field === 'value_type'">{{ valueTypeMapOptions[row.value_type] }}</span>
            <span v-else>{{ row[column.field] }}</span>
          </template>
        </vxe-column>
      </vxe-table>
    </a-spin>
  </CustomDrawer>
</template>
