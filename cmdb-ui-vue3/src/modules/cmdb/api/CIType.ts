import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Fetch the attribute groups of a CI type. */
export function getCITypeGroupById(CITypeId: string | number, data?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/${CITypeId}/attribute_groups`, { params: data })
}

/** Grant a role permissions on a CI type (model-level). */
export function grantCiType(type_id: string | number, rid: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ci_types/${type_id}/roles/${rid}/grant`, data)
}

/** Revoke a role's permissions on a CI type (model-level). */
export function revokeCiType(type_id: string | number, rid: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ci_types/${type_id}/roles/${rid}/revoke`, data)
}

/** Fetch the filter-level (read_attr / read_ci) permissions of a CI type. */
export function ciTypeFilterPermissions(type_id: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/${type_id}/filters/permissions`)
}
