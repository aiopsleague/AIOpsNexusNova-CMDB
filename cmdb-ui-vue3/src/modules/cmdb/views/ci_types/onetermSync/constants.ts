export interface AttributeMapping {
  cmdb_attr: string
  oneterm_field: string
  required: boolean
}

export const DEFAULT_ATTR_MAPPING: AttributeMapping[] = [
  { cmdb_attr: '', oneterm_field: 'ip', required: true },
  { cmdb_attr: '', oneterm_field: 'comment', required: false },
  { cmdb_attr: '', oneterm_field: 'protocols', required: false },
]
