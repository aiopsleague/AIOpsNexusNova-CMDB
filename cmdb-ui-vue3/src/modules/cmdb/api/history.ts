// src/modules/cmdb/api/history.ts
import request from '@/utils/request'

const urlPrefix = '/v0.1'

export function getCIHistory(ciId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/history/ci/${ciId}`)
}

export function getCIHistoryTable(params: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/history/records/attribute`, { params, timeout: 30 * 1000 })
}

export function getRelationTable(params: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/history/records/relation`, { params, timeout: 30 * 1000 })
}

export function getCITypesTable(params: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/history/ci_types`, { params, timeout: 30 * 1000 })
}

export function getUsers(params: Record<string, unknown>): Promise<any> {
  return request.get('/v1/acl/users/employee', { params })
}

export function getCiTriggers(params: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/history/ci_triggers`, { params })
}

export function getCiTriggersByCiId(
  ci_id: string | number,
  params?: Record<string, unknown>
): Promise<any> {
  return request.get(`${urlPrefix}/history/ci_triggers/${ci_id}`, { params })
}

export function getCIsBaseline(params: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci/baseline`, { params })
}

export function CIBaselineRollback(
  ciId: string | number,
  params: Record<string, unknown>
): Promise<any> {
  return request.post(`${urlPrefix}/ci/${ciId}/baseline/rollback`, params)
}
