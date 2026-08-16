// src/modules/acl/api/app.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function searchApp(params: Record<string, unknown> = {}) {
  return request.get(`${prefix}/apps`, { params: { ...params, page_size: 9999 } })
}
export function addApp(data: Record<string, unknown>) {
  return request.post(`${prefix}/apps`, data)
}
export function updateApp(aid: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/apps/${aid}`, data)
}
export function getApp(aid: number) {
  return request.get(`${prefix}/apps/${aid}`)
}
export function deleteApp(aid: number) {
  return request.delete(`${prefix}/apps/${aid}`)
}
