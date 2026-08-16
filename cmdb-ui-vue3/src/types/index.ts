// src/types/index.ts

/** 权限点（含 actionEntitySet 与展开后的 actionList）。 */
export interface Permission {
  id: number
  name: string
  actionEntitySet?: { action: string }[]
  actionList?: string[]
  [key: string]: unknown
}

export interface Role {
  id?: number
  name?: string
  permissions?: Permission[]
  [key: string]: unknown
}

/** getInfo 返回的 result 字段。 */
export interface UserInfoResult {
  name: string
  avatar?: string
  uid: number
  rid: number
  username: string
  role: Role
  [key: string]: unknown
}

export interface GetInfoResponse {
  result: UserInfoResult
}

export interface LoginResponse {
  token: string
}

export interface AuthEnableItem {
  auth_type: string
  [key: string]: unknown
}

export interface AuthEnableResponse {
  enable_list: AuthEnableItem[]
}

export interface Employee {
  employee_id?: number
  name?: string
  mobile?: string
  department_id?: number
  email?: string
  [key: string]: unknown
}

export interface Department {
  department_id?: number
  department_name?: string
  [key: string]: unknown
}
