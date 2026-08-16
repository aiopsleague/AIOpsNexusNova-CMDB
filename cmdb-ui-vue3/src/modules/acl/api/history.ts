// src/modules/acl/api/history.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function searchPermissionHistory(params: Record<string, unknown>) {
  return request.get(`${prefix}/audit_log/permission`, { params })
}
export function searchRoleHistory(params: Record<string, unknown>) {
  return request.get(`${prefix}/audit_log/role`, { params })
}
export function searchResourceHistory(params: Record<string, unknown>) {
  return request.get(`${prefix}/audit_log/resource`, { params })
}
export function searchTriggerHistory(params: Record<string, unknown>) {
  return request.get(`${prefix}/audit_log/trigger`, { params })
}
