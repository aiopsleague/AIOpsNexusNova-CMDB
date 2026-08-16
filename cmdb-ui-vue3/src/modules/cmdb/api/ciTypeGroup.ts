import request from '@/utils/request'

const urlPrefix = '/v0.1'

export function getCITypeGroups(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/groups`, { params })
}

export function postCITypeGroup(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ci_types/groups`, data)
}

export function putCITypeGroupByGId(gid: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/ci_types/groups/${gid}`, data)
}

export function deleteCITypeGroup(gid: string | number, data?: Record<string, unknown>): Promise<any> {
  return request.delete(`${urlPrefix}/ci_types/groups/${gid}`, { data })
}

export function getCITypeGroupsConfig(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/groups/config`, { params })
}

/** Update the ordering of CI type config groups. */
export function putCITypeGroups(data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/ci_types/groups/order`, data)
}

/** Export CI type groups (template). */
export function exportCITypeGroups(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/template/export`, { params, timeout: 30 * 1000 })
}
