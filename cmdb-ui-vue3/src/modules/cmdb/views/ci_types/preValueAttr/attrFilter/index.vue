<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { ref } from 'vue'
import { compareTypeList } from '../constants'
import Expression from './expression.vue'

interface FilterRule {
  id: string
  type: string
  property?: string
  exp: string
  value?: any
  min?: string | number
  max?: string | number
  compareType?: string
}

const props = withDefaults(
  defineProps<{
    canSearchPreferenceAttrList?: any[]
    expression?: string
    regQ?: string
    CITypeId?: number | null
    curModelAttrList?: any[]
  }>(),
  {
    canSearchPreferenceAttrList: () => [],
    expression: '',
    regQ: '(?<=q=).+(?=&)|(?<=q=).+$',
    CITypeId: null,
    curModelAttrList: () => [],
  }
)

const emit = defineEmits<{ (e: 'setExpFromFilter', v: string): void }>()

const ruleList = ref<FilterRule[]>([])

function genId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

function init(open: boolean, isInitOne = true) {
  // When isInitOne is true, if the parsed expression is empty the rule list gets a default entry.
  const match = props.expression.match(new RegExp(props.regQ, 'g'))
  const exp = match ? match[0] : null
  if (open && exp) {
    const expArray = exp.split(',').map((item) => {
      let hasNot = ''
      const key = item.split(':')[0]
      const val = item.split(':').slice(1).join(':')
      let type: string
      let property: string
      let expValue = ''
      let value: any
      let min: string | number | undefined
      let max: string | number | undefined
      let compareType: string | undefined
      if (key.includes('-')) {
        type = 'or'
        if (key.includes('~')) {
          property = key.substring(2)
          hasNot = '~'
        } else {
          property = key.substring(1)
        }
      } else {
        type = 'and'
        if (key.includes('~')) {
          property = key.substring(1)
          hasNot = '~'
        } else {
          property = key
        }
      }

      const inReg = /(?<=\().+(?=\))/g
      const rangeReg = /(?<=\[).+(?=\])/g
      const compareReg = /(?<=>=|<=|>(?!=)|<(?!=)).+/
      if (val === '*') {
        expValue = hasNot + 'value'
        value = ''
      } else if (inReg.test(val)) {
        expValue = hasNot + 'in'
        value = val.match(inReg)?.[0]
      } else if (rangeReg.test(val)) {
        expValue = hasNot + 'range'
        value = val.match(rangeReg)?.[0]
        min = value?.split('_TO_')[0]
        max = value?.split('_TO_')[1]
      } else if (compareReg.test(val)) {
        expValue = hasNot + 'compare'
        value = val.match(compareReg)?.[0]
        const compareTypeLabel = val.substring(0, val.match(compareReg)?.index)
        const idx = compareTypeList.findIndex((option) => option.label === compareTypeLabel)
        compareType = compareTypeList[idx].value
      } else if (!val.includes('*')) {
        expValue = hasNot + 'is'
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
            expValue = hasNot + reg[0]
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

function handleSubmit() {
  if (ruleList.value && ruleList.value.length) {
    ruleList.value[0].type = 'and' // Ensure the first rule is always an "and" connector.
    const expList = ruleList.value.map((rule) => {
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
    emit('setExpFromFilter', expList.join(','))
  } else {
    emit('setExpFromFilter', '')
  }
}

defineExpose({ init, handleSubmit })
</script>

<template>
  <div>
    <Expression
      :value="ruleList"
      :can-search-preference-attr-list="canSearchPreferenceAttrList.filter((attr) => !attr.is_password)"
      :disabled="false"
      :cur-model-attr-list="curModelAttrList"
      @change="(v) => (ruleList = v)"
    />
  </div>
</template>

<style lang="less" scoped></style>
