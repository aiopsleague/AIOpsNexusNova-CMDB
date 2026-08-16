// src/modules/acl/api/trigger.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function getTriggers(params: Record<string, unknown>) {
  return request.get(`${prefix}/triggers`, { params })
}
export function addTrigger(data: Record<string, unknown>) {
  return request.post(`${prefix}/triggers`, data)
}
export function updateTrigger(tid: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/triggers/${tid}`, data)
}
export function deleteTrigger(tid: number) {
  return request.delete(`${prefix}/triggers/${tid}`)
}
export function applyTrigger(tid: number) {
  return request.post(`${prefix}/triggers/${tid}/apply`)
}
export function cancelTrigger(tid: number) {
  return request.post(`${prefix}/triggers/${tid}/cancel`)
}
export function patternResults(data: Record<string, unknown>) {
  return request.post(`${prefix}/triggers/resources`, data)
}
