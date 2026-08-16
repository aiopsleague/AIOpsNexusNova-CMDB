<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CopyOutlined, DeleteOutlined, PlusCircleOutlined } from '@ant-design/icons-vue'
import ValueTypeMapIcon from '@/components/CMDBValueTypeMapIcon/index.vue'
import CIReferenceAttr from './CIReferenceAttr.vue'
import {
  ruleTypeList,
  expList,
  advancedExpList,
  compareTypeList,
  type FilterOption,
  type FilterRule,
  type FilterAttr,
} from './constants'

const props = withDefaults(
  defineProps<{
    value?: FilterRule[]
    canSearchPreferenceAttrList?: FilterAttr[]
    needAddHere?: boolean
    disabled?: boolean
  }>(),
  {
    value: () => [],
    canSearchPreferenceAttrList: () => [],
    needAddHere: false,
    disabled: false,
  }
)

const emit = defineEmits<{ (e: 'change', v: FilterRule[]): void }>()
const { t } = useI18n()

const ruleList = computed<FilterRule[]>({
  get: () => props.value,
  set: (val) => emit('change', val),
})

const ruleTypeListOptions = computed<FilterOption[]>(() => ruleTypeList(t))
const expListOptions = computed<FilterOption[]>(() => expList(t))
const advancedExpListOptions = computed<FilterOption[]>(() => advancedExpList(t))

let idCounter = 0
function genId(): string {
  idCounter += 1
  return `rule_${Date.now().toString(36)}_${idCounter}_${Math.random().toString(36).slice(2, 8)}`
}

function getAttr(property?: string): FilterAttr {
  return props.canSearchPreferenceAttrList.find((item) => item.name === property) || {}
}

function getExpListByProperty(property?: string): FilterOption[] {
  if (property) {
    const found = props.canSearchPreferenceAttrList.find((item) => item.name === property)
    if (found && (['0', '1', '3', '4', '5'].includes(found.value_type) || found.is_reference || found.is_bool)) {
      return [
        { value: 'is', label: t('cmdbFilterComp.is') },
        { value: '~is', label: t('cmdbFilterComp.~is') },
        { value: '~value', label: t('cmdbFilterComp.~value') },
        { value: 'value', label: t('cmdbFilterComp.value') },
      ]
    }
    return expListOptions.value
  }
  return expListOptions.value
}

function isChoiceByProperty(property?: string): boolean {
  const found = props.canSearchPreferenceAttrList.find((item) => item.name === property)
  return found ? Boolean(found.is_choice) : false
}

function getChoiceValueByProperty(property?: string): FilterOption[] {
  const found = props.canSearchPreferenceAttrList.find((item) => item.name === property)
  if (found?.choice_value?.length) {
    return found.choice_value.map((node: any) => ({
      id: String(node?.[0] ?? ''),
      label: node?.[1]?.label || node?.[0] || '',
      children: node?.children?.length ? node.children : undefined,
    }))
  }
  return []
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
    next.splice(idx, 0, {
      id: genId(),
      type: 'and',
      property: props.canSearchPreferenceAttrList[0]?.name,
      exp: 'is',
      value: null,
    })
    ruleList.value = next
  }
}

function handleChangeExp(node: { value: string }, _item: FilterRule, index: number) {
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
</script>

<template>
  <div>
    <a-space v-for="(item, index) in ruleList" :key="item.id" :style="{ display: 'flex', marginBottom: '10px' }">
      <div :style="{ width: '70px', height: '24px', position: 'relative' }">
        <treeselect
          v-if="index"
          v-model="item.type"
          class="custom-treeselect"
          :style="{ width: '70px', '--custom-height': '24px', position: 'absolute', top: '-17px', left: 0 }"
          :multiple="false"
          :clearable="false"
          :searchable="true"
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
        :style="{ width: '130px', '--custom-height': '24px' }"
        :multiple="false"
        :clearable="false"
        :searchable="true"
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
            :title="node.label"
            :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }"
          >
            <ValueTypeMapIcon :attr="node.raw" />
            {{ node.label }}
          </div>
        </template>
        <template #value-label="{ node }">
          <div :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }">
            <ValueTypeMapIcon :attr="node.raw" /> {{ node.label }}
          </div>
        </template>
      </treeselect>
      <treeselect
        v-model="item.exp"
        class="custom-treeselect"
        :style="{ width: '100px', '--custom-height': '24px' }"
        :multiple="false"
        :clearable="false"
        :searchable="true"
        :options="[...getExpListByProperty(item.property), ...advancedExpListOptions]"
        :normalizer="
          (node: any) => ({ id: node.value, label: node.label, children: node.children })
        "
        append-to-body
        :z-index="1050"
        :disabled="disabled"
        @select="(node: any) => handleChangeExp(node, item, index)"
      >
        <template #option-label="{ node }">
          <div
            :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }"
          >
            <a-tooltip :title="node.label">
              {{ node.label }}
            </a-tooltip>
          </div>
        </template>
        <template #value-label="{ node }">
          <div :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }">
            <a-tooltip :title="node.label">
              {{ node.label }}
            </a-tooltip>
          </div>
        </template>
      </treeselect>
      <CIReferenceAttr
        v-if="getAttr(item.property).is_reference && (item.exp === 'is' || item.exp === '~is')"
        :style="{ width: '175px' }"
        class="select-filter-component ops-select-bg"
        :reference-type-id="getAttr(item.property).reference_type_id"
        :disabled="disabled"
        :value="item.value"
        @change="(v) => (item.value = v)"
      />
      <a-select
        v-else-if="getAttr(item.property).is_bool && (item.exp === 'is' || item.exp === '~is')"
        v-model:value="item.value"
        class="select-filter-component ops-select-bg"
        :style="{ width: '175px' }"
        :disabled="disabled"
        :placeholder="t('placeholder2')"
      >
        <a-select-option key="1">true</a-select-option>
        <a-select-option key="0">false</a-select-option>
      </a-select>
      <treeselect
        v-else-if="isChoiceByProperty(item.property) && (item.exp === 'is' || item.exp === '~is')"
        v-model="item.value"
        class="custom-treeselect"
        :style="{ width: '175px', '--custom-height': '24px' }"
        :multiple="false"
        :clearable="false"
        :searchable="true"
        :options="getChoiceValueByProperty(item.property)"
        :placeholder="t('placeholder2')"
        :normalizer="
          (node: any) => ({ id: node.id, label: node.label, children: node.children })
        "
        append-to-body
        :z-index="1050"
        :disabled="disabled"
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
      <a-input-group v-else-if="item.exp === 'range' || item.exp === '~range'" size="small" compact :style="{ width: '175px' }">
        <a-input
          v-model:value="item.min"
          class="ops-input"
          size="small"
          :style="{ width: '78px' }"
          :placeholder="t('min')"
          :disabled="disabled"
        />
        ~
        <a-input
          v-model:value="item.max"
          class="ops-input"
          size="small"
          :style="{ width: '78px' }"
          :placeholder="t('max')"
          :disabled="disabled"
        />
      </a-input-group>
      <a-input-group v-else-if="item.exp === 'compare'" size="small" compact :style="{ width: '175px' }">
        <treeselect
          v-model="item.compareType"
          class="custom-treeselect"
          :style="{ width: '60px', '--custom-height': '24px' }"
          :multiple="false"
          :clearable="false"
          :searchable="true"
          :options="compareTypeList"
          :normalizer="
            (node: any) => ({ id: node.value, label: node.label, children: node.children })
          "
          append-to-body
          :z-index="1050"
          :disabled="disabled"
        />
        <a-input v-model:value="item.value" class="ops-input" size="small" style="width: 113px" />
      </a-input-group>
      <a-input
        v-else-if="item.exp !== 'value' && item.exp !== '~value'"
        v-model:value="item.value"
        size="small"
        :placeholder="item.exp === 'in' || item.exp === '~in' ? t('cmdbFilterComp.split', { separator: ';' }) : ''"
        class="ops-input"
        :style="{ width: '175px' }"
        :disabled="disabled"
      />
      <div v-else :style="{ width: '175px' }"></div>
      <template v-if="!disabled">
        <a-tooltip :title="t('copy')">
          <a class="operation" @click="handleCopyRule(item)"><CopyOutlined /></a>
        </a-tooltip>
        <a-tooltip :title="t('delete')">
          <a class="operation" @click="handleDeleteRule(item)"><DeleteOutlined /></a>
        </a-tooltip>
        <a-tooltip v-if="needAddHere" :title="t('cmdbFilterComp.addHere')">
          <a class="operation" @click="handleAddRuleAt(item)"><PlusCircleOutlined /></a>
        </a-tooltip>
      </template>
    </a-space>
    <div v-if="!disabled" class="table-filter-add">
      <a @click="handleAddRule">+ {{ t('new') }}</a>
    </div>
  </div>
</template>

<style scoped>
.select-filter-component {
  height: 24px;
}
</style>
