<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { CaretDownOutlined, FontSizeOutlined } from '@ant-design/icons-vue'
import CIReferenceAttr from '@/components/ciReferenceAttr/index.vue'
import { compareTypeList } from '../constants'

interface RuleValue {
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
    attrList?: any[]
    disabled?: boolean
    // Current model attributes
    curModelAttrList?: any[]
    // Row height
    rowHeight?: string
  }>(),
  { rule: () => ({}), attrList: () => [], disabled: false, curModelAttrList: () => [], rowHeight: '' }
)

const emit = defineEmits<{ (e: 'change', v: RuleValue): void }>()
const { t } = useI18n()

const controlType = ref<'input' | 'choice'>('input')

const choiceValue = computed(() => {
  const regex = /\{\{([^}]+)\}\}/g
  const val = regex.exec(props.rule?.value || '')
  return val ? val[1]?.trim() || '' : ''
})

function isChoiceByProperty(property?: string): boolean {
  const found = props.attrList.find((item) => item.name === property)
  return found ? Boolean(found.is_choice) : false
}

function getChoiceValueByProperty(property?: string): any[] {
  const found = props.attrList.find((item) => item.name === property)
  return found ? found.choice_value || [] : []
}

function handleControlType(type: 'input' | 'choice') {
  controlType.value = type
}

function handleChange(key: string, value: any) {
  let next = value
  if (controlType.value === 'choice' && key === 'value') {
    next = `{{ ${value} }}`
  }
  emit('change', { ...props.rule, [key]: next })
}

function getAttr(property?: string): any {
  return props.attrList.find((item) => item.name === property) || {}
}
</script>

<template>
  <div>
    <div v-if="controlType === 'choice'" class="control-group">
      <div class="choice-group" @click="handleControlType('input')">
        <CaretDownOutlined class="choice-group-icon" />
      </div>
      <treeselect
        class="custom-treeselect input-group"
        :style="{ '--custom-height': rowHeight }"
        :model-value="choiceValue"
        :multiple="false"
        :clearable="false"
        searchable
        :options="curModelAttrList"
        :placeholder="t('placeholder2')"
        :normalizer="
          (node: any) => ({ id: node.name, label: node.name, children: node.children })
        "
        append-to-body
        :z-index="1050"
        :disabled="disabled"
        @update:model-value="(value: any) => handleChange('value', value)"
      >
        <template #option-label="{ node }">
          <div
            :title="node.label"
            :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }"
          >
            {{ node.label }}
          </div>
        </template>
      </treeselect>
    </div>
    <div v-else class="control-group">
      <div class="text-group" @click="handleControlType('choice')">
        <FontSizeOutlined class="text-group-icon" />
      </div>
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
        <treeselect
          class="custom-treeselect"
          :style="{ '--custom-height': rowHeight }"
          :model-value="rule.value"
          :multiple="false"
          :clearable="false"
          searchable
          :options="getChoiceValueByProperty(rule.property)"
          :placeholder="t('placeholder2')"
          :normalizer="
            (node: any) => ({
              id: String(node[0] || ''),
              label: node[1] ? node[1].label || node[0] : node[0],
              children: node.children && node.children.length ? node.children : undefined,
            })
          "
          append-to-body
          :z-index="1050"
          :disabled="disabled"
          @update:model-value="(value: any) => handleChange('value', value)"
        >
          <template #option-label="{ node }">
            <div
              :title="node.label"
              :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }"
            >
              {{ node.label }}
            </div>
          </template>
        </treeselect>
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
          append-to-body
          :z-index="1050"
          :disabled="disabled"
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

.choice-group {
  width: 14px;
  height: 36px;
  flex-shrink: 0;
  background-color: #00b3cc;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;

  &-icon {
    font-size: 12px;
    color: #ffffff;
  }
}

.text-group {
  width: 14px;
  height: 36px;
  flex-shrink: 0;
  background-color: #2f54eb;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;

  &-icon {
    font-size: 12px;
    color: #ffffff;
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
}
</style>
