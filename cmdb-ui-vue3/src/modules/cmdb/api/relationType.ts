// src/modules/cmdb/api/relationType.ts
import request from '@/utils/request'

const urlPrefix = '/v0.1'

export function getRelationTypes(): Promise<any> {
  return request.get(`${urlPrefix}/relation_types`)
}

export function addRelationType(payload: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/relation_types`, payload)
}

export function updateRelationType(
  rtId: string | number,
  payload: Record<string, unknown>
): Promise<any> {
  return request.put(`${urlPrefix}/relation_types/${rtId}`, payload)
}

export function deleteRelationType(rtId: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/relation_types/${rtId}`)
}
