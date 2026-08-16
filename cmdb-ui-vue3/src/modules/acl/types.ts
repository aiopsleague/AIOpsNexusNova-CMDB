// src/modules/acl/types.ts
export interface AclUser {
  id?: number
  username?: string
  name?: string
  email?: string
  mobile?: string
  department_id?: number
  is_block?: boolean
  joined_at?: string
  [key: string]: unknown
}

export interface AclRole {
  id?: number
  name?: string
  virtual?: boolean
  parent_ids?: number[]
  [key: string]: unknown
}

export interface ResourceType {
  id?: number
  name?: string
  [key: string]: unknown
}

export interface Resource {
  id?: number
  name?: string
  resource_type_id?: number
  is_group?: boolean
  creator?: string
  [key: string]: unknown
}

export interface ResourceGroup {
  id?: number
  name?: string
  resource_type_id?: number
  [key: string]: unknown
}

export interface AclApp {
  name?: string
  [key: string]: unknown
}

export interface Trigger {
  id?: number
  name?: string
  pattern?: string
  resource_type_id?: number
  status?: string
  [key: string]: unknown
}

export interface AuditLog {
  id?: number
  operator?: string
  operate_time?: string
  source?: string
  [key: string]: unknown
}
