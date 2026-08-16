export interface FilterOption {
  value: string | number
  label: string
}

export const ruleTypeList: FilterOption[] = [
  { value: '&', label: 'cs.components.and' },
  { value: '|', label: 'cs.components.or' },
]

export const expList: FilterOption[] = [
  { value: 1, label: 'cs.components.equal' },
  { value: 2, label: 'cs.components.notEqual' },
  { value: 7, label: 'cs.components.isEmpty' },
  { value: 8, label: 'cs.components.isNotEmpty' },
]

export const compareTypeList: FilterOption[] = [
  { value: 5, label: 'cs.components.moreThan' },
  { value: 6, label: 'cs.components.lessThan' },
]
