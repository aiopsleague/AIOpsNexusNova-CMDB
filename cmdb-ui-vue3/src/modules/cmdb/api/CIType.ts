import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Fetch all ci_types. */
export function getCITypes(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types`, { params })
}

/** Fetch a single ci_type by id or unique name. */
export function getCIType(CITypeName: string | number, params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/${CITypeName}`, { params })
}

/** Create a ci_type. */
export function createCIType(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ci_types`, data)
}

/** Update a ci_type. */
export function updateCIType(CITypeId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/ci_types/${CITypeId}`, data)
}

/** Delete a ci_type. */
export function deleteCIType(CITypeId: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/ci_types/${CITypeId}`)
}

/** Fetch the attribute groups of a CI type. */
export function getCITypeGroupById(CITypeId: string | number, data?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/${CITypeId}/attribute_groups`, { params: data })
}

/** Create an attribute group of a CI type. */
export function createCITypeGroupById(CITypeId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ci_types/${CITypeId}/attribute_groups`, data)
}

/** Update an attribute group by group id. */
export function updateCITypeGroupById(groupId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/ci_types/attribute_groups/${groupId}`, data)
}

/** Delete an attribute group by group id. */
export function deleteCITypeGroupById(groupId: string | number, data?: Record<string, unknown>): Promise<any> {
  return request.delete(`${urlPrefix}/ci_types/attribute_groups/${groupId}`, { data })
}

/** Fetch the trigger list of a CI type. */
export function getTriggerList(typeId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/${typeId}/triggers`)
}

/** Add inheritance: { parent_ids, child_id }. */
export function postCiTypeInheritance(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ci_types/inheritance`, data)
}

/** Remove inheritance: { parent_id, child_id }. */
export function deleteCiTypeInheritance(data: Record<string, unknown>): Promise<any> {
  return request.delete(`${urlPrefix}/ci_types/inheritance`, { data })
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
