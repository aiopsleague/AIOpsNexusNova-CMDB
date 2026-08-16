<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ApartmentOutlined,
  BulbFilled,
  FolderOutlined,
  FolderOpenOutlined,
  FontSizeOutlined,
  ReloadOutlined,
  TagsOutlined,
} from '@ant-design/icons-vue'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { getCITypes } from '@/modules/cmdb/api/CIType'

const props = defineProps<{
  config: Record<string, any>
  ciTypeId: number
}>()

const emit = defineEmits<{ (e: 'change', config: Record<string, any>): void }>()

const { t } = useI18n()

interface FolderRule {
  type: string
  parent_id?: number
  template?: string
  path?: string
}

interface SyncConfigInternal {
  asset_name_template: string
  folder_rule: FolderRule
}

const internalConfig = ref<SyncConfigInternal>({
  asset_name_template: '',
  folder_rule: {
    type: 'fixed',
    parent_id: 0,
  },
})

const ciTypeAttributes = ref<any[]>([])
const parentCITypes = ref<any[]>([])
const templatePreview = ref('')
const loadingAttributes = ref(false)
const onetermNodeTree = ref<any[]>([])

const pathTemplateExampleForAttribute = computed(() => {
  const example = t('cmdb.ciType.onetermSync.pathTemplateExample')
  const template = t('cmdb.ciType.onetermSync.attributeTemplateExample')
  return `${example} ${template}`
})

const pathTemplateExampleForRelation = computed(() => {
  const example = t('cmdb.ciType.onetermSync.pathTemplateExample')
  const template = t('cmdb.ciType.onetermSync.relationTemplateExample')
  return `${example} ${template}`
})

const commonVariables = computed(() => {
  if (!ciTypeAttributes.value || !ciTypeAttributes.value.length) {
    return []
  }
  // Filter out complex types that are not suitable for templates
  const simpleAttributes = ciTypeAttributes.value.filter((attr) => {
    // value_type: 0=INT, 1=FLOAT, 2=TEXT, 3=DATETIME, 4=DATE, 5=TIME, 6=JSON, 7=BOOL
    // Exclude: JSON(6), reference, attachment, multi-value, computed
    if (attr.value_type === '6' || attr.value_type === 6) return false
    if (attr.is_file) return false
    if (attr.is_list) return false
    if (attr.is_choice && attr.is_choice === 2) return false // multi-choice
    if (attr.is_link) return false
    if (attr.is_computed) return false
    return true
  })

  // Return attribute objects with name and alias, limit to 15 for display
  return simpleAttributes.slice(0, 15).map((attr) => ({
    name: attr.name,
    alias: attr.alias || attr.name,
    value_type: attr.value_type,
  }))
})

watch(
  () => props.config,
  (val) => {
    if (!val) return

    // Deep merge folder_rule to preserve user changes
    const mergedConfig: SyncConfigInternal = { ...internalConfig.value, ...val }
    if (val.folder_rule && internalConfig.value.folder_rule) {
      mergedConfig.folder_rule = {
        ...internalConfig.value.folder_rule,
        ...val.folder_rule,
      }
    }

    internalConfig.value = mergedConfig
    updateTemplatePreview()
  },
  { immediate: true, deep: true }
)

watch(
  () => internalConfig.value.asset_name_template,
  () => {
    updateTemplatePreview()
  }
)

function handleRuleTypeChange() {
  if (internalConfig.value.folder_rule.type === 'fixed' && !onetermNodeTree.value.length) {
    loadOnetermNodes()
  }
  emitChange()
}

async function loadOnetermNodes() {
  // Placeholder: directory tree loading is not yet implemented.
}

function reloadOnetermNodes() {
  onetermNodeTree.value = []
  loadOnetermNodes()
}

async function loadCITypeAttributes() {
  loadingAttributes.value = true
  try {
    const res = await getCITypeAttributesById(props.ciTypeId)
    ciTypeAttributes.value = res.attributes || []
  } catch (e) {
    console.error('Failed to load attributes:', e)
    ciTypeAttributes.value = []
  } finally {
    loadingAttributes.value = false
  }
}

async function loadParentCITypes() {
  try {
    const res = await getCITypes({ type_id: props.ciTypeId, parent_types: true })
    parentCITypes.value = res || []
  } catch (e) {
    console.error('Failed to load parent types:', e)
    // Fall back to loading all CI types if the endpoint is unavailable.
    loadAllCITypes()
  }
}

async function loadAllCITypes() {
  try {
    const res = await getCITypes()
    parentCITypes.value = (res.ci_types || []).filter((t: any) => t.id !== props.ciTypeId)
  } catch (e) {
    console.error('Failed to load CI types:', e)
  }
}

function insertVariable(variable: string) {
  const input = internalConfig.value.asset_name_template || ''
  internalConfig.value.asset_name_template = input + '{{ ' + variable + ' }}'
  emitChange()
}

function updateTemplatePreview() {
  const template = internalConfig.value.asset_name_template
  if (!template) {
    templatePreview.value = ''
    return
  }

  // Generate example data based on CI Type attributes
  const exampleData: Record<string, string> = {}
  ciTypeAttributes.value.forEach((attr) => {
    // Generate example values based on attribute type
    if (attr.value_type === 'int' || attr.value_type === 'float') {
      exampleData[attr.name] = '100'
    } else if (attr.name.includes('ip') || attr.name === 'ip_address') {
      exampleData[attr.name] = '10.0.1.100'
    } else if (attr.name.includes('port')) {
      exampleData[attr.name] = '3306'
    } else if (attr.name.includes('name') || attr.name === 'hostname') {
      exampleData[attr.name] = 'server-01'
    } else if (attr.name.includes('env') || attr.name === 'environment') {
      exampleData[attr.name] = 'production'
    } else {
      exampleData[attr.name] = 'example'
    }
  })

  try {
    let preview = template

    // Handle basic Jinja2 variable substitution
    Object.keys(exampleData).forEach((key) => {
      const regex = new RegExp('\\{\\{\\s*' + key + '\\s*\\}\\}', 'g')
      preview = preview.replace(regex, exampleData[key])
    })

    // Handle common Jinja2 filters
    preview = preview.replace(/\{\{\s*(\w+)\s*\|\s*upper\s*\}\}/g, (match, key: string) => {
      return exampleData[key] ? exampleData[key].toUpperCase() : match
    })
    preview = preview.replace(/\{\{\s*(\w+)\s*\|\s*lower\s*\}\}/g, (match, key: string) => {
      return exampleData[key] ? exampleData[key].toLowerCase() : match
    })

    templatePreview.value = preview
  } catch (e) {
    templatePreview.value = 'Template error: ' + (e as Error).message
  }
}

function emitChange() {
  emit('change', internalConfig.value)
}

onMounted(() => {
  loadCITypeAttributes()
  loadParentCITypes()
  loadOnetermNodes()
})
</script>

<template>
  <!-- eslint-disable vue/attributes-order, vue/no-v-html -->
  <div class="advanced-config">
    <a-form
      :model="internalConfig"
      :label-col="{ span: 4 }"
      :wrapper-col="{ span: 18 }"
    >
      <!-- Asset Naming Template -->
      <a-form-item required :label="t('cmdb.ciType.onetermSync.assetNameTemplate')">
        <a-input
          v-model:value="internalConfig.asset_name_template"
          :placeholder="t('cmdb.ciType.onetermSync.assetNameTemplatePlaceholder')"
          @blur="emitChange"
        >
          <template #prefix><FontSizeOutlined /></template>
        </a-input>
        <div class="ant-form-explain">
          {{ t('cmdb.ciType.onetermSync.assetNameTemplateDesc') }}
        </div>
        <div class="ant-form-explain">
          {{ t('cmdb.ciType.onetermSync.templateVariableTip') }}
        </div>
        <div v-if="loadingAttributes" style="margin-top: 8px;">
          <a-spin size="small" />
          <span style="margin-left: 8px;" class="ant-form-explain">{{ t('cmdb.ciType.onetermSync.loadingAttributes') }}</span>
        </div>
        <div v-else-if="commonVariables.length" style="margin-top: 8px; line-height: 24px;">
          <a-tooltip
            v-for="variable in commonVariables"
            :key="variable.name"
            :title="`${variable.alias} (${variable.name})`"
          >
            <a-tag
              color="blue"
              style="margin: 4px 4px 0 0; cursor: pointer;"
              @click="insertVariable(variable.name)"
            >
              {{ variable.alias }}
            </a-tag>
          </a-tooltip>
        </div>
        <div v-else style="margin-top: 8px; line-height: 24px;">
          <span class="ant-form-explain">{{ t('cmdb.ciType.onetermSync.noAvailableAttributes') }}</span>
        </div>
        <div v-if="templatePreview" style="margin-top: 8px;">
          <BulbFilled style="color: #faad14; margin-right: 4px;" />
          <span class="ant-form-explain">
            {{ t('cmdb.ciType.onetermSync.previewResult') }}: <span :style="{ fontWeight: 500 }">{{ templatePreview }}</span>
          </span>
        </div>
      </a-form-item>

      <!-- Asset Directory Rule -->
      <a-form-item required :label="t('cmdb.ciType.onetermSync.assetDirectoryRule')">
        <a-radio-group v-model:value="internalConfig.folder_rule.type" @change="handleRuleTypeChange">
          <a-radio value="fixed">
            <FolderOutlined style="margin-right: 4px;" />
            {{ t('cmdb.ciType.onetermSync.fixedDirectory') }}
          </a-radio>
          <a-radio value="ci_attribute" style="margin-left: 24px;">
            <TagsOutlined style="margin-right: 4px;" />
            {{ t('cmdb.ciType.onetermSync.byCIAttribute') }}
          </a-radio>
          <a-radio value="ci_relation" style="margin-left: 24px;">
            <ApartmentOutlined style="margin-right: 4px;" />
            {{ t('cmdb.ciType.onetermSync.byCIRelation') }}
          </a-radio>
        </a-radio-group>
        <div v-if="internalConfig.folder_rule.type === 'fixed'" class="ant-form-explain">
          {{ t('cmdb.ciType.onetermSync.fixedDirectoryDesc') }}
        </div>
        <div v-else-if="internalConfig.folder_rule.type === 'ci_attribute'" class="ant-form-explain">
          {{ t('cmdb.ciType.onetermSync.ciAttributeDesc') }}
        </div>
        <div v-else-if="internalConfig.folder_rule.type === 'ci_relation'" class="ant-form-explain">
          {{ t('cmdb.ciType.onetermSync.ciRelationDesc') }}
        </div>

        <!-- Fixed Directory Config -->
        <div v-if="internalConfig.folder_rule.type === 'fixed'" style="margin-top: 12px;">
          <a-tree-select
            v-model:value="internalConfig.folder_rule.parent_id"
            style="width: 400px;"
            :tree-data="onetermNodeTree"
            :placeholder="t('cmdb.ciType.onetermSync.selectDirectory')"
            :load-data="loadOnetermNodes"
            tree-default-expand-all
            @change="emitChange"
          >
            <template #suffixIcon><FolderOutlined /></template>
          </a-tree-select>
          <a-button
            type="link"
            size="small"
            @click="reloadOnetermNodes"
            style="margin-left: 8px;"
          >
            <template #icon><ReloadOutlined /></template>
            {{ t('cmdb.ciType.onetermSync.refreshDirectory') }}
          </a-button>
        </div>

        <!-- CI Attribute Config -->
        <div v-if="internalConfig.folder_rule.type === 'ci_attribute'" style="margin-top: 12px;">
          <a-input
            v-model:value="internalConfig.folder_rule.template"
            :placeholder="t('cmdb.ciType.onetermSync.pathTemplatePlaceholder')"
            style="width: 500px;"
            @blur="emitChange"
          >
            <template #prefix><FolderOpenOutlined /></template>
          </a-input>
          <div class="ant-form-explain">
            <span v-html="pathTemplateExampleForAttribute"></span>
          </div>
        </div>

        <!-- CI Relation Config -->
        <div v-if="internalConfig.folder_rule.type === 'ci_relation'" style="margin-top: 12px;">
          <a-input
            v-model:value="internalConfig.folder_rule.template"
            :placeholder="t('cmdb.ciType.onetermSync.relationTemplatePlaceholder')"
            style="width: 500px;"
            @blur="emitChange"
          >
            <template #prefix><FolderOpenOutlined /></template>
          </a-input>
          <div class="ant-form-explain">
            <span v-html="pathTemplateExampleForRelation"></span>
          </div>
        </div>
      </a-form-item>
    </a-form>
  </div>
</template>
