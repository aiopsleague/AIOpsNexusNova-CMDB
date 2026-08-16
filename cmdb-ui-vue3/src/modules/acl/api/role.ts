// src/modules/acl/api/role.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function searchRole(params: Record<string, unknown>) {
  return request.get(`${prefix}/roles`, { params })
}
export function addRole(data: Record<string, unknown>) {
  return request.post(`${prefix}/roles`, data)
}
export function updateRoleById(id: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/roles/${id}`, data)
}
export function deleteRoleById(id: number, data?: Record<string, unknown>) {
  return request.delete(`${prefix}/roles/${id}`, { data })
}
export function addParentRole(id: number, otherId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${id}/parents`, { ...data, parent_id: otherId })
}
export function delParentRole(cid: number, pid: number, data: Record<string, unknown>) {
  return request.delete(`${prefix}/roles/${cid}/parents`, { data: { ...data, parent_id: pid } })
}
export function getUsersUnderRole(rid: number, data: Record<string, unknown>) {
  return request.get(`${prefix}/roles/${rid}/users`, { params: data })
}
export function addBatchParentRole(parentId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${parentId}/children`, data)
}
