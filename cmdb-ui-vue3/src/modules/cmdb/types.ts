// src/modules/cmdb/types.ts
// Lightweight entity interfaces for the CMDB domain. Fields are intentionally
// loose (optional + index signature) since the API responses are not yet
// strictly typed during the Vue 2 -> Vue 3 migration.

export interface CI {
  id?: number
  type_id?: number
  no?: string
  name?: string
  [key: string]: unknown
}

export interface CIType {
  id?: number
  name?: string
  alias?: string
  icon?: string
  unique_name?: string
  is_manual?: boolean
  [key: string]: unknown
}

export interface Attribute {
  id?: number
  name?: string
  alias?: string
  type?: string
  value_type?: string
  required?: boolean
  [key: string]: unknown
}

export interface Relation {
  id?: number
  first_ci_id?: number
  second_ci_id?: number
  relation_type_id?: number
  [key: string]: unknown
}

export interface RelationType {
  id?: number
  name?: string
  [key: string]: unknown
}
