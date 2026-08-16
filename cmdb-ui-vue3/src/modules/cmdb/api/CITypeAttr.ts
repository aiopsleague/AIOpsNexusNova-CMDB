import request from '@/utils/request'

const urlPrefix = '/v0.1'

 
export function getCITypeAttributesById(CITypeId: string | number, parameter?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/${CITypeId}/attributes`, { params: parameter })
}

/** Fetch attributes for one or more CI types at once (params: { type_ids }). */
export function getCITypeAttributesByTypeIds(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/attributes`, { params })
}

/** Fetch common attributes shared across multiple CI types (params: { type_ids }). */
export function getCITypeCommonAttributesByTypeIds(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/common_attributes`, { params })
}

/** Update an attribute by id. */
export function updateAttributeById(attrId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/attributes/${attrId}`, data)
}

/** Create a global attribute. */
export function createAttribute(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/attributes`, data)
}

/** Search / fetch all attributes. */
export function searchAttributes(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/attributes/s`, { params })
}

/** Delete a global attribute by id. */
export function deleteAttributesById(attrId: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/attributes/${attrId}`)
}

/** Link existing attributes to a CI type. */
export function createCITypeAttributes(CITypeId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ci_types/${CITypeId}/attributes`, data)
}

/** Update CI type attributes (order / flags). */
export function updateCITypeAttributesById(CITypeId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/ci_types/${CITypeId}/attributes`, data)
}

/** Unlink attributes from a CI type. */
export function deleteCITypeAttributesById(CITypeId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.delete(`${urlPrefix}/ci_types/${CITypeId}/attributes`, { data })
}

/** Transfer (reorder) attribute indexes within a CI type. */
export function transferCITypeAttrIndex(CITypeId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ci_types/${CITypeId}/attributes/transfer`, data)
}

/** Transfer (reorder) attribute group indexes within a CI type. */
export function transferCITypeGroupIndex(CITypeId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ci_types/${CITypeId}/attribute_groups/transfer`, data)
}

/** Check whether computed attributes can be defined. */
export function canDefineComputed(): Promise<any> {
  return request.head(`${urlPrefix}/ci_types/can_define_computed`)
}

/** Trigger recompute of a computed attribute. */
export function calcComputedAttribute(attrId: string | number): Promise<any> {
  return request.put(`${urlPrefix}/attributes/${attrId}/calc_computed_attribute`)
}

/** Fetch the decrypted value of a password attribute for a CI. */
export function getAttrPassword(ci_id: string | number, attr_id: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci/${ci_id}/attributes/${attr_id}/password`)
}
