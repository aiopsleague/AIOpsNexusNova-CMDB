// src/modules/acl/api/permission.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function getResourcePerms(resourceId: number, params?: Record<string, unknown>) {
  return request.get(`${prefix}/resources/${resourceId}/permissions`, { params })
}
export function getResourceTypePerms(typeId: number) {
  return request.get(`${prefix}/resource_types/${typeId}/perms`)
}
export function getResourceGroupPerms(groupId: number) {
  return request.get(`${prefix}/resource_groups/${groupId}/permissions`)
}
export function setRoleResourcePerm(rid: number, resourceId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/${resourceId}/grant2`, data)
}
export function setRoleResourceGroupPerm(rid: number, groupId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resource_groups/${groupId}/grant`, data)
}
export function deleteRoleResourcePerm(rid: number, resourceId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/${resourceId}/revoke2`, data)
}
export function deleteRoleResourceGroupPerm(rid: number, groupId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resource_groups/${groupId}/revoke`, data)
}
export function deleteRoleResourceGroupPerm2(rid: number, groupId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resource_groups/${groupId}/revoke2`, data)
}
export function searchPermResourceByRoleId(rid: number, params: Record<string, unknown>) {
  return request.get(`${prefix}/roles/${rid}/resources`, { params })
}
export function roleHasPermissionToGrant(params: Record<string, unknown>) {
  return request.get(`${prefix}/roles/has_perm`, { params })
}
export function setBatchRoleResourcePerm(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/batch/grant`, data)
}
export function setBatchRoleResourceGroupPerm(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resource_groups/batch/grant`, data)
}
export function setBatchRoleResourceRevoke(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/batch/revoke`, data)
}
export function setBatchRoleResourceGroupRevoke(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resource_groups/batch/revoke`, data)
}
export function setBatchRoleResourceByResourceName(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/batch/grant2`, data)
}
export function setBatchRoleResourceRevokeByResourceName(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/batch/revoke2`, data)
}
