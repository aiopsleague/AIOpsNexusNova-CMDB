<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CopyOutlined, MinusCircleOutlined, PlusCircleOutlined } from '@ant-design/icons-vue'
import ValueTypeMapIcon from '@/components/CMDBValueTypeMapIcon/index.vue'
import ValueControls from './valueControls.vue'
import { ruleTypeList, expList, advancedExpList, type FilterOption } from '../constants'

interface FilterRule {
  id: string
  type: string
  property?: string
  exp: string
  value?: any
  min?: string | number
  max?: string | number
  compareType?: string
  [key: string]: any
}

const props = withDefaults(
  defineProps<{
    value?: FilterRule[]
    canSearchPreferenceAttrList?: any[]
    disabled?: boolean
    curModelAttrList?: any[]
  }>(),
  { value: () => [], canSearchPreferenceAttrList: () => [], disabled: false, curModelAttrList: () => [] }
)

const emit = defineEmits<{ (e: 'change', v: FilterRule[]): void }>()
const { t } = useI18n()

const isOpenSource = import.meta.env.VITE_APP_IS_OPEN_SOURCE === 'true'
const rowHeight = '36px'

const ruleList = computed<FilterRule[]>({
  get: () => props.value,
  set: (val) => emit('change', val),
})

const ruleTypeListOptions = computed<FilterOption[]>(() => ruleTypeList(t))
const expListOptions = computed<FilterOption[]>(() => expList(t))
const advancedExpListOptions = computed<FilterOption[]>(() => advancedExpList(t))

function genId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

function getExpListByProperty(property?: string): FilterOption[] {
  if (property === '$count') {
    return [
      { value: 'is', label: t('cmdbFilterComp.is') },
      { value: '~is', label: t('cmdbFilterComp.~is') },
      { value: 'compare', label: t('cmdbFilterComp.compare') },
    ]
  }
  if (property) {
    const found = props.canSearchPreferenceAttrList.find((item) => item.name === property)
    if (found && ['0', '1', '3', '4', '5'].includes(found.value_type)) {
      return [
        { value: 'is', label: t('cmdbFilterComp.is') },
        { value: '~is', label: t('cmdbFilterComp.~is') },
        { value: '~value', label: t('cmdbFilterComp.~value') },
        { value: 'value', label: t('cmdbFilterComp.value') },
        ...advancedExpListOptions.value,
      ]
    }
  }
  return [...expListOptions.value, ...advancedExpListOptions.value]
}

function handleAddRule() {
  ruleList.value = [
    ...props.value,
    {
      id: genId(),
      type: 'and',
      property: props.canSearchPreferenceAttrList[0]?.name,
      exp: 'is',
      value: null,
    },
  ]
}

function handleCopyRule(item: FilterRule) {
  ruleList.value = [...props.value, { ...item, id: genId() }]
}

function handleDeleteRule(item: FilterRule) {
  ruleList.value = props.value.filter((r) => r.id !== item.id)
}

function handleAddRuleAt(item: FilterRule) {
  const idx = props.value.findIndex((r) => r.id === item.id)
  if (idx > -1) {
    const next = [...props.value]
    next.splice(idx + 1, 0, {
      id: genId(),
      type: 'and',
      property: props.canSearchPreferenceAttrList[0]?.name,
      exp: 'is',
      value: null,
    })
    ruleList.value = next
  }
}

function handleChangeExp(node: { value: string }, index: number) {
  const value = node.value
  const next = props.value.map((rule, i) => {
    if (i !== index) {
      return rule
    }
    if (value === 'range') {
      return { ...rule, min: '', max: '', exp: value }
    }
    if (value === 'compare') {
      return { ...rule, compareType: '1', exp: value }
    }
    return { ...rule, exp: value }
  })
  ruleList.value = next
}

function handleChangeValue(value: any, index: number) {
  const next = props.value.map((rule, i) => (i === index ? value : rule))
  emit('change', next)
}
</script>

<template>
  <div>
    <a-space v-for="(item, index) in ruleList" :key="item.id" :style="{ display: 'flex', marginBottom: '10px' }">
      <div v-if="ruleList.length > 1" :style="{ width: '60px', height: rowHeight, position: 'relative' }">
        <treeselect
          v-if="index !== 0"
          v-model="item.type"
          class="custom-treeselect"
          :style="{ width: '60px', '--custom-height': rowHeight, position: 'absolute', top: '-24px' }"
          :multiple="false"
          :clearable="false"
          searchable
          :options="ruleTypeListOptions"
          :normalizer="
            (node: any) => ({ id: node.value, label: node.label, children: node.children })
          "
          :disabled="disabled"
        />
      </div>
      <treeselect
        v-model="item.property"
        class="custom-treeselect"
        :style="{ width: '120px', '--custom-height': rowHeight }"
        :multiple="false"
        :clearable="false"
        searchable
        :options="canSearchPreferenceAttrList"
        :normalizer="
          (node: any) => ({ id: node.name, label: node.alias || node.name, children: node.children })
        "
        append-to-body
        :z-index="1050"
        :disabled="disabled"
      >
        <template #option-label="{ node }">
          <div
            v-if="node.id !== '$count'"
            :title="node.label"
            class="property-label"
          >
            <ValueTypeMapIcon :attr="node.raw" />
            {{ node.label }}
          </div>
          <div
            v-else
            :title="node.label"
            class="property-label"
            :style="{ borderBottom: '1px solid #E4E7ED', marginBottom: '8px' }"
          >
            <ValueTypeMapIcon :attr="node.raw" />
            {{ node.label }}
          </div>
        </template>
        <template #value-label="{ node }">
          <div class="property-label">
            <ValueTypeMapIcon :attr="node.raw" /> {{ node.label }}
          </div>
        </template>
      </treeselect>
      <treeselect
        v-model="item.exp"
        class="custom-treeselect"
        :style="{ width: '90px', '--custom-height': rowHeight }"
        :multiple="false"
        :clearable="false"
        searchable
        :options="getExpListByProperty(item.property)"
        :normalizer="
          (node: any) => ({ id: node.value, label: node.label, children: node.children })
        "
        append-to-body
        :z-index="1050"
        :disabled="disabled"
        @select="(node: any) => handleChangeExp(node, index)"
      />
      <ValueControls
        :rule="ruleList[index]"
        :attr-list="canSearchPreferenceAttrList"
        :disabled="disabled"
        :cur-model-attr-list="curModelAttrList"
        :row-height="rowHeight"
        @change="(value) => handleChangeValue(value, index)"
      />
      <template v-if="!disabled">
        <a-tooltip :title="t('copy')">
          <a class="operation" @click="handleCopyRule(item)"><CopyOutlined /></a>
        </a-tooltip>
        <a-tooltip :title="t('delete')">
          <a class="operation" @click="handleDeleteRule(item)"><MinusCircleOutlined /></a>
        </a-tooltip>
        <a-tooltip :title="t('cmdbFilterComp.addHere')">
          <a class="operation" @click="handleAddRuleAt(item)"><PlusCircleOutlined /></a>
        </a-tooltip>
      </template>
    </a-space>
    <div v-if="!disabled && ruleList.length === 0" class="table-filter-add">
      <a @click="handleAddRule">+ {{ t('new') }}</a>
    </div>
    <div class="attr-filter-tip">{{ t('cmdb.ciType.attrFilterTip') }}{{ isOpenSource ? ` (${t('cmdb.enterpriseVersionTip')})` : '' }}</div>
  </div>
</template>

<style lang="less" scoped>
.input-group {
  display: flex;
  align-items: center;
  width: 150px;

  &-range-icon {
    margin: 0 8px;
  }

  input {
    height: 36px;
  }
}

.property-label {
  width: 100%;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.attr-filter-tip {
  color: #86909c;
  font-size: 12px;
  font-weight: 400;
}
</style>
