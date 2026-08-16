<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { FilterOutlined } from '@ant-design/icons-vue'
import Expression from './expression.vue'
import { compareTypeList, type FilterRule, type FilterAttr } from './constants'

const props = withDefaults(
  defineProps<{
    canSearchPreferenceAttrList?: FilterAttr[]
    expression?: string
    regQ?: string
    placement?: string
    isDropdown?: boolean
    needAddHere?: boolean
    disabled?: boolean
  }>(),
  {
    canSearchPreferenceAttrList: () => [],
    expression: '',
    regQ: '(?<=q=).+(?=&)|(?<=q=).+$',
    placement: 'bottomRight',
    isDropdown: true,
    needAddHere: false,
    disabled: false,
  }
)

const emit = defineEmits<{ (e: 'setExpFromFilter', value: string): void }>()
const { t } = useI18n()

const visible = ref(false)
const ruleList = ref<FilterRule[]>([])
const filterExp = ref('')

let idCounter = 0
function genId(): string {
  idCounter += 1
  return `rule_${Date.now().toString(36)}_${idCounter}_${Math.random().toString(36).slice(2, 8)}`
}

/** Parse the persisted expression back into a rule list when the popover opens. */
function visibleChange(open: boolean, isInitOne = true) {
  const match = props.expression.match(new RegExp(props.regQ, 'g'))
  const exp = match ? match[0] : null
  if (open && exp) {
    const expArray = exp.split(',').map((item) => {
      let has_not = ''
      const key = item.split(':')[0]
      const val = item.split(':').slice(1).join(':')
      let type: string
      let property: string
      let expValue = ''
      let value: string | number | undefined
      let min: string | number | undefined
      let max: string | number | undefined
      let compareType: string | undefined
      if (key.includes('-')) {
        type = 'or'
        if (key.includes('~')) {
          property = key.substring(2)
          has_not = '~'
        } else {
          property = key.substring(1)
        }
      } else {
        type = 'and'
        if (key.includes('~')) {
          property = key.substring(1)
          has_not = '~'
        } else {
          property = key
        }
      }

      const inReg = /(?<=\().+(?=\))/g
      const rangeReg = /(?<=\[).+(?=\])/g
      const compareReg = /(?<=>=|<=|>(?!=)|<(?!=)).+/
      if (val === '*') {
        expValue = has_not + 'value'
        value = ''
      } else if (inReg.test(val)) {
        expValue = has_not + 'in'
        value = val.match(inReg)?.[0]
      } else if (rangeReg.test(val)) {
        expValue = has_not + 'range'
        value = val.match(rangeReg)?.[0]
        min = value?.split('_TO_')[0]
        max = value?.split('_TO_')[1]
      } else if (compareReg.test(val)) {
        expValue = has_not + 'compare'
        value = val.match(compareReg)?.[0]
        const compareTypeLabel = val.substring(0, val.match(compareReg)?.index)
        const idx = compareTypeList.findIndex((option) => option.label === compareTypeLabel)
        compareType = compareTypeList[idx].value
      } else if (!val.includes('*')) {
        expValue = has_not + 'is'
        value = val
      } else {
        const resList: Array<[string, RegExp]> = [
          ['contain', /(?<=\*).*(?=\*)/g],
          ['end_with', /(?<=\*).+/g],
          ['start_with', /.+(?=\*)/g],
        ]
        for (let i = 0; i < 3; i++) {
          const reg = resList[i]
          if (reg[1].test(val)) {
            expValue = has_not + reg[0]
            value = val.match(reg[1])?.[0]
            break
          }
        }
      }
      return { id: genId(), type, property, exp: expValue, value, min, max, compareType }
    })
    ruleList.value = [...expArray]
  } else if (open) {
    const available = props.canSearchPreferenceAttrList.filter((attr) => !attr.is_password)
    ruleList.value = isInitOne
      ? [
          {
            id: genId(),
            type: 'and',
            property: available && available.length ? available[0].name : undefined,
            exp: 'is',
            value: null,
          },
        ]
      : []
  }
}

function handleClear() {
  ruleList.value = [
    {
      id: genId(),
      type: 'and',
      property: props.canSearchPreferenceAttrList[0]?.name,
      exp: 'is',
      value: null,
    },
  ]
  filterExp.value = ''
  visible.value = false
  emit('setExpFromFilter', filterExp.value)
}

function handleSubmit() {
  if (ruleList.value && ruleList.value.length) {
    ruleList.value[0].type = 'and'
    filterExp.value = ''
    const expListResult = ruleList.value.map((rule) => {
      let singleRuleExp = ''
      let exp = rule.exp
      if (rule.type === 'or') {
        singleRuleExp += '-'
      }
      if (rule.exp.includes('~')) {
        singleRuleExp += '~'
        exp = rule.exp.split('~')[1]
      }
      singleRuleExp += `${rule.property}:`
      if (exp === 'is') {
        singleRuleExp += `${rule.value ?? ''}`
      } else if (exp === 'contain') {
        singleRuleExp += `*${rule.value ?? ''}*`
      } else if (exp === 'start_with') {
        singleRuleExp += `${rule.value ?? ''}*`
      } else if (exp === 'end_with') {
        singleRuleExp += `*${rule.value ?? ''}`
      } else if (exp === 'value') {
        singleRuleExp += '*'
      } else if (exp === 'in') {
        singleRuleExp += `(${rule.value ?? ''})`
      } else if (exp === 'range') {
        singleRuleExp += `[${rule.min}_TO_${rule.max}]`
      } else if (exp === 'compare') {
        const idx = compareTypeList.findIndex((option) => option.value === rule.compareType)
        singleRuleExp += `${compareTypeList[idx].label}${rule.value ?? ''}`
      }
      return singleRuleExp
    })
    filterExp.value = expListResult.join(',')
    emit('setExpFromFilter', filterExp.value)
  } else {
    emit('setExpFromFilter', '')
  }
  visible.value = false
}
</script>

<template>
  <div>
    <a-popover
      v-if="isDropdown"
      v-model:open="visible"
      trigger="click"
      :placement="placement"
      overlay-class-name="table-filter"
      @open-change="visibleChange"
    >
      <slot name="popover_item">
        <a-button type="primary" ghost>
          {{ t('cmdbFilterComp.conditionFilter') }}<FilterOutlined />
        </a-button>
      </slot>
      <template #content>
        <Expression
          :need-add-here="needAddHere"
          :value="ruleList"
          :can-search-preference-attr-list="canSearchPreferenceAttrList.filter((attr) => !attr.is_password)"
          :disabled="disabled"
          @change="(v) => (ruleList = v)"
        />
        <a-divider :style="{ margin: '10px 0' }" />
        <div style="width: 554px">
          <a-space :style="{ display: 'flex', justifyContent: 'flex-end' }">
            <a-button type="primary" size="small" @click="handleSubmit">{{ t('confirm') }}</a-button>
            <a-button size="small" @click="handleClear">{{ t('clear') }}</a-button>
          </a-space>
        </div>
      </template>
    </a-popover>
    <Expression
      v-else
      :need-add-here="needAddHere"
      :value="ruleList"
      :can-search-preference-attr-list="canSearchPreferenceAttrList.filter((attr) => !attr.is_password)"
      :disabled="disabled"
      @change="(v) => (ruleList = v)"
    />
  </div>
</template>

<style scoped>
.table-filter .table-filter-add {
  margin-top: 10px;
}
.table-filter .table-filter-add > a {
  padding: 2px 8px;
}
.table-filter .table-filter-add > a:hover {
  background-color: #d6e4ff;
  border-radius: 5px;
}
.table-filter .table-filter-extra-icon {
  padding: 0 2px;
}
.table-filter .table-filter-extra-icon:hover {
  display: inline-block;
  border-radius: 5px;
  background-color: #f0faff;
}
</style>

<style>
.table-filter-extra-operation .ant-popover-inner-content {
  padding: 3px 4px;
}
.table-filter-extra-operation .ant-popover-inner-content .operation {
  cursor: pointer;
  width: 90px;
  height: 30px;
  line-height: 30px;
  padding: 3px 4px;
  border-radius: 5px;
  transition: all 0.3s;
}
.table-filter-extra-operation .ant-popover-inner-content .operation:hover {
  background-color: #f0faff;
}
.table-filter-extra-operation .ant-popover-inner-content .operation > .anticon {
  margin-right: 10px;
}
</style>
