<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { ArrowRightOutlined, QuestionCircleOutlined } from '@ant-design/icons-vue'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { cloneDeep } from '../../../utils/helper'
import { DEFAULT_ATTR_MAPPING, type AttributeMapping } from './constants'

const props = withDefaults(
  defineProps<{
    ciTypeId?: number
    mappings?: AttributeMapping[]
    syncStrategy?: string
  }>(),
  { ciTypeId: undefined, mappings: () => [], syncStrategy: 'physical' }
)

const emit = defineEmits<{ (e: 'change', mappings: AttributeMapping[]): void }>()

const { t } = useI18n()

const allAttributes = ref<any[]>([])
const fixedMappings = ref<AttributeMapping[]>(cloneDeep(DEFAULT_ATTR_MAPPING))

const columns = computed(() => [
  {
    title: t('cmdb.ciType.onetermSync.cmdbAttribute'),
    dataIndex: 'cmdb_attr',
    key: 'cmdb_attr',
    width: '45%',
  },
  { title: '', key: 'arrow', width: '60px', align: 'center' },
  {
    title: t('cmdb.ciType.onetermSync.onetermField'),
    dataIndex: 'oneterm_field',
    key: 'oneterm_field',
    width: '45%',
  },
])

const availableAttributes = computed(() => {
  return allAttributes.value.filter((attr) => {
    // Exclude JSON type (value_type: 6)
    if (attr.value_type === '6' || attr.value_type === 6) return false
    // Exclude attachment type
    if (attr.is_file) return false
    // Exclude password type
    if (attr.is_password) return false
    // Exclude reference attributes (is_link=true)
    if (attr.is_link) return false
    // Exclude multi-value attributes
    if (attr.is_list) return false
    if (attr.is_choice && attr.is_choice === 2) return false
    // Exclude computed attributes
    if (attr.is_computed) return false
    return true
  })
})

watch(
  () => props.mappings,
  (val) => {
    if (val && val.length) {
      val.forEach((m) => {
        const fixed = fixedMappings.value.find((f) => f.oneterm_field === m.oneterm_field)
        if (fixed) {
          fixed.cmdb_attr = m.cmdb_attr
        }
      })
    }
  },
  { immediate: true, deep: true }
)

async function loadCITypeAttributes() {
  try {
    const res = await getCITypeAttributesById(props.ciTypeId as number)
    // API returns { attributes: [...] }
    allAttributes.value = res.attributes || []
  } catch (e) {
    console.error('Failed to load attributes:', e)
    message.error(t('cmdb.ciType.onetermSync.loadAttributesFailed'))
  }
}

function onetermFieldLabel(field: string) {
  const camelized = field.slice(1).replace(/_./g, (m) => m[1].toUpperCase())
  return field.charAt(0).toUpperCase() + camelized
}

function isAttributeUsed(attrName: string, currentIndex: number) {
  return fixedMappings.value.some((m, index) => index !== currentIndex && m.cmdb_attr === attrName)
}

function validateMapping(_index: number) {
  emitChange()
}

function emitChange() {
  emit('change', fixedMappings.value)
}

onMounted(() => {
  loadCITypeAttributes()
})
</script>

<template>
  <div class="attribute-mapping-table">
    <a-table
      :columns="columns"
      :data-source="fixedMappings"
      :pagination="false"
      size="small"
      row-key="oneterm_field"
    >
      <template #bodyCell="{ column, record, index }">
        <template v-if="column.key === 'cmdb_attr'">
          <a-select
            v-model:value="record.cmdb_attr"
            style="width: 100%"
            :placeholder="t('cmdb.ciType.onetermSync.selectAttribute')"
            show-search
            option-filter-prop="title"
            @change="() => validateMapping(index)"
          >
            <a-select-option
              v-for="attr in availableAttributes"
              :key="attr.name"
              :value="attr.name"
              :title="`${attr.alias || attr.name} (${attr.name})`"
              :disabled="isAttributeUsed(attr.name, index)"
            >
              <span>{{ attr.alias || attr.name }}</span>
              <span style="margin-left: 8px; color: #999; font-size: 12px;">({{ attr.name }})</span>
            </a-select-option>
          </a-select>
        </template>

        <template v-else-if="column.key === 'arrow'">
          <ArrowRightOutlined style="color: #999;" />
        </template>

        <template v-else-if="column.key === 'oneterm_field'">
          <span style="font-size: 13px; color: #666;">
            {{ t(`cmdb.ciType.onetermSync.onetermField${onetermFieldLabel(record.oneterm_field)}`) }}
            <span v-if="record.required" style="color: #f5222d; margin-left: 4px;">*</span>
            <a-tooltip v-if="record.oneterm_field === 'protocols'" placement="right">
              <template #title>
                <div style="max-width: 300px;">
                  <div>{{ t('cmdb.ciType.onetermSync.protocolsFormatHint') }}</div>
                  <div style="margin-top: 8px; font-family: 'Courier New', monospace; font-size: 12px;">
                    <div>• ssh</div>
                    <div>• ssh:2222</div>
                    <div>• rdp,vnc</div>
                    <div>• ssh:22,rdp:3389</div>
                  </div>
                </div>
              </template>
              <QuestionCircleOutlined :style="{ marginLeft: '4px', cursor: 'help' }" />
            </a-tooltip>
          </span>
        </template>
      </template>
    </a-table>
  </div>
</template>

<style lang="less" scoped>
.attribute-mapping-table {
  :deep(.ant-table) {
    .ant-table-thead > tr > th {
      background: #fafafa;
      font-weight: 500;
    }

    .ant-table-tbody > tr > td {
      padding: 12px 16px;
    }

    .ant-table-tbody > tr:hover > td {
      background: #f5f5f5;
    }
  }
}
</style>
