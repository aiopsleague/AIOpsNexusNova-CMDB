<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import CIReferenceAttr from '@/components/ciReferenceAttr/index.vue'
import { compareTypeList, type FilterAttr, type FilterRule } from './constants'

interface RuleValue {
  id?: string
  type?: string
  property?: string
  exp?: string
  value?: any
  min?: string | number
  max?: string | number
  compareType?: string
  [key: string]: any
}

const props = withDefaults(
  defineProps<{
    rule?: RuleValue
    attrList?: FilterAttr[]
    disabled?: boolean
    // Current model attributes
    curModelAttrList?: FilterAttr[]
    // Row height
    rowHeight?: string
  }>(),
  {
    rule: () => ({}),
    attrList: () => [],
    disabled: false,
    curModelAttrList: () => [],
    rowHeight: '',
  }
)

const emit = defineEmits<{ (e: 'change', v: FilterRule): void }>()
const { t } = useI18n()

function isChoiceByProperty(property?: string): boolean {
  const found = props.attrList.find((item) => item.name === property)
  return found ? Boolean(found.is_choice) : false
}

function getChoiceValueByProperty(property?: string): any[] {
  const found = props.attrList.find((item) => item.name === property)
  return found ? found.choice_value || [] : []
}

function handleChange(key: string, value: any) {
  emit('change', { ...props.rule, [key]: value } as FilterRule)
}

function getAttr(property?: string): FilterAttr {
  return props.attrList.find((item) => item.name === property) || {}
}
</script>

<template>
  <div class="control-group">
    <CIReferenceAttr
      v-if="getAttr(rule.property).is_reference && (rule.exp === 'is' || rule.exp === '~is')"
      class="select-filter"
      :reference-type-id="getAttr(rule.property).reference_type_id"
      :value="rule.value"
      :disabled="disabled"
      @change="(value: any) => handleChange('value', value)"
    />
    <a-select
      v-else-if="getAttr(rule.property).is_bool && (rule.exp === 'is' || rule.exp === '~is')"
      class="select-filter"
      :disabled="disabled"
      :placeholder="t('placeholder2')"
      :value="rule.value"
      @change="(value: any) => handleChange('value', value)"
    >
      <a-select-option key="1">true</a-select-option>
      <a-select-option key="0">false</a-select-option>
    </a-select>
    <div
      v-else-if="isChoiceByProperty(rule.property) && (rule.exp === 'is' || rule.exp === '~is')"
      class="input-group"
    >
      <a-select
        class="select-filter"
        :style="{ width: '175px' }"
        show-search
        :placeholder="t('placeholder2')"
        :disabled="disabled"
        :value="rule.value"
        @change="(value: any) => handleChange('value', value)"
      >
        <a-select-option
          v-for="node in getChoiceValueByProperty(rule.property)"
          :key="String(node[0])"
          :value="String(node[0])"
          :title="node[1] ? node[1].label || node[0] : node[0]"
        >
          <a-tooltip placement="topLeft" :title="node[1] ? node[1].label || node[0] : node[0]">
            {{ node[1] ? node[1].label || node[0] : node[0] }}
          </a-tooltip>
        </a-select-option>
      </a-select>
    </div>
    <div v-else-if="rule.exp === 'range' || rule.exp === '~range'" class="input-group">
      <a-input
        class="ops-input"
        :placeholder="t('min')"
        :disabled="disabled"
        :value="rule.min"
        @change="(e: any) => handleChange('min', e.target.value)"
      />
      <span class="input-group-range-icon">~</span>
      <a-input
        class="ops-input"
        :placeholder="t('max')"
        :disabled="disabled"
        :value="rule.max"
        @change="(e: any) => handleChange('max', e.target.value)"
      />
    </div>
    <div v-else-if="rule.exp === 'compare'" class="input-group">
      <treeselect
        class="custom-treeselect"
        :style="{ width: '70px', '--custom-height': rowHeight, 'flex-shrink': 0 }"
        :model-value="rule.compareType"
        :multiple="false"
        :clearable="false"
        searchable
        :options="compareTypeList"
        :normalizer="
          (node: any) => ({ id: node.value, label: node.label, children: node.children })
        "
        :z-index="1050"
        :disabled="disabled"
        append-to-body
        @update:model-value="(value: any) => handleChange('compareType', value)"
      />
      <a-input :value="rule.value" class="ops-input" @change="(e: any) => handleChange('value', e.target.value)" />
    </div>
    <div v-else-if="rule.exp !== 'value' && rule.exp !== '~value'" class="input-group">
      <a-input
        :value="rule.value"
        :placeholder="rule.exp === 'in' || rule.exp === '~in' ? t('cmdbFilterComp.split', { separator: ';' }) : ''"
        class="ops-input"
        :disabled="disabled"
        @change="(e: any) => handleChange('value', e.target.value)"
      />
    </div>
    <div v-else :style="{ width: '136px' }"></div>
  </div>
</template>

<style lang="less" scoped>
.control-group {
  display: flex;
}

.input-group {
  display: flex;
  align-items: center;
  width: 136px;

  &-range-icon {
    margin: 0 8px;
  }

  input {
    height: 36px;
  }
}

.select-filter {
  height: 36px;
  width: 136px;

  :deep(.ant-select-selector) {
    height: 36px;
    background: #f7f8fa;
    line-height: 36px;
    border: none;
  }

  :deep(.vue-treeselect__control) {
    background: #f7f8fa;
    border: none;
  }
}
</style>
