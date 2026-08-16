// src/modules/cmdb/api/CIRelation.ts
import request from '@/utils/request'

const urlPrefix = '/v0.1'

export function getFirstCIsByCiId(ciId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci_relations/${ciId}/first_cis`)
}

export function getSecondCIsByCiId(ciId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci_relations/${ciId}/second_cis`)
}

export function searchCIRelation(params: string): Promise<any> {
  return request.get(`${urlPrefix}/ci_relations/s?${params}`)
}

export function statisticsCIRelation(params: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_relations/statistics`, { params })
}

/** Batch add child nodes. */
export function batchUpdateCIRelationChildren(
  ciIds: Array<string | number>,
  parents: unknown,
  ancestor_ids?: unknown
): Promise<any> {
  return request.post(`${urlPrefix}/ci_relations/batch`, { ci_ids: ciIds, parents, ancestor_ids })
}

/** Batch add parent nodes. */
export function batchUpdateCIRelationParents(
  ciIds: Array<string | number>,
  children: unknown
): Promise<any> {
  return request.post(`${urlPrefix}/ci_relations/batch`, { ci_ids: ciIds, children })
}

/** Batch delete relations. */
export function batchDeleteCIRelation(
  ciIds: Array<string | number>,
  parents: unknown,
  ancestor_ids?: unknown
): Promise<any> {
  return request.delete(`${urlPrefix}/ci_relations/batch`, {
    data: { ci_ids: ciIds, parents, ancestor_ids },
  })
}

export function addCIRelationView(
  firstCiId: string | number,
  secondCiId: string | number,
  data: Record<string, unknown>
): Promise<any> {
  return request.post(`${urlPrefix}/ci_relations/${firstCiId}/${secondCiId}`, data)
}

export function deleteCIRelationView(
  firstCiId: string | number,
  secondCiId: string | number,
  data: Record<string, unknown>
): Promise<any> {
  return request.delete(`${urlPrefix}/ci_relations/${firstCiId}/${secondCiId}`, { data })
}

export function searchCIRelationFull(params: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_relations/search/full`, { params })
}

export function searchCIRelationPath(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ci_relations/path/s`, data)
}
