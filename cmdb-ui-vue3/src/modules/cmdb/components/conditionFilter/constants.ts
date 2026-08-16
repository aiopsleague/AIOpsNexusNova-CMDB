export interface FilterOption {
  value: string
  label: string
}

// A single rule in the filter expression builder.
export interface FilterRule {
  id: string
  type: string
  property?: string
  exp: string
  value?: any
  min?: string | number
  max?: string | number
  compareType?: string
}

export type FilterAttr = Record<string, any>

/** Logical connectors between filter rules. */
export function ruleTypeList(t: (key: string) => string): FilterOption[] {
  return [
    { value: 'and', label: t('cmdbFilterComp.and') },
    { value: 'or', label: t('cmdbFilterComp.or') },
  ]
}

/** Basic expression operators for a filter rule. */
export function expList(t: (key: string) => string): FilterOption[] {
  return [
    { value: 'is', label: t('cmdbFilterComp.is') },
    { value: '~is', label: t('cmdbFilterComp.~is') },
    { value: 'contain', label: t('cmdbFilterComp.contain') },
    { value: '~contain', label: t('cmdbFilterComp.~contain') },
    { value: 'start_with', label: t('cmdbFilterComp.start_with') },
    { value: '~start_with', label: t('cmdbFilterComp.~start_with') },
    { value: 'end_with', label: t('cmdbFilterComp.end_with') },
    { value: '~end_with', label: t('cmdbFilterComp.~end_with') },
    { value: '~value', label: t('cmdbFilterComp.~value') },
    { value: 'value', label: t('cmdbFilterComp.value') },
  ]
}

/** Advanced expression operators appended to the basic list. */
export function advancedExpList(t: (key: string) => string): FilterOption[] {
  return [
    { value: 'in', label: t('cmdbFilterComp.in') },
    { value: '~in', label: t('cmdbFilterComp.~in') },
    { value: 'range', label: t('cmdbFilterComp.range') },
    { value: '~range', label: t('cmdbFilterComp.~range') },
    { value: 'compare', label: t('cmdbFilterComp.compare') },
  ]
}

export const compareTypeList: FilterOption[] = [
  { value: '1', label: '>' },
  { value: '2', label: '>=' },
  { value: '3', label: '<' },
  { value: '4', label: '<=' },
]
