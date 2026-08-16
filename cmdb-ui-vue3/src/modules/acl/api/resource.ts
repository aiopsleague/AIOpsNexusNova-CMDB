// src/modules/acl/api/resource.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function searchResource(params: Record<string, unknown>) {
  return request.get(`${prefix}/resources`, { params })
}
export function addResource(data: Record<string, unknown>) {
  return request.post(`${prefix}/resources`, data)
}
export function updateResourceById(id: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/resources/${id}`, data)
}
export function deleteResourceById(id: number, params?: Record<string, unknown>) {
  return request.delete(`${prefix}/resources/${id}`, { params })
}
export function searchResourceType(params: Record<string, unknown>) {
  return request.get(`${prefix}/resource_types`, { params })
}
export function addResourceType(data: Record<string, unknown>) {
  return request.post(`${prefix}/resource_types`, data)
}
export function updateResourceTypeById(id: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/resource_types/${id}`, data)
}
export function deleteResourceTypeById(id: number) {
  return request.delete(`${prefix}/resource_types/${id}`)
}
export function getResourceGroups(params: Record<string, unknown>) {
  return request.get(`${prefix}/resource_groups`, { params })
}
export function addResourceGroup(data: Record<string, unknown>) {
  return request.post(`${prefix}/resource_groups`, data)
}
export function updateResourceGroup(id: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/resource_groups/${id}`, data)
}
export function deleteResourceGroup(id: number) {
  return request.delete(`${prefix}/resource_groups/${id}`)
}
export function getResourceGroupItems(id: number) {
  return request.get(`${prefix}/resource_groups/${id}/items`)
}
