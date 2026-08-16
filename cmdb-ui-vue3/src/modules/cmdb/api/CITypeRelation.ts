import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Fetch the child CI types of a CI type. */
export function getCITypeChildren(CITypeID: string | number, parameter?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_type_relations/${CITypeID}/children`, { params: parameter })
}

/** Fetch the parent CI types of a CI type. */
export function getCITypeParent(CITypeID: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci_type_relations/${CITypeID}/parents`)
}

/** Fetch all relation types. */
export function getRelationTypes(parameter?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/relation_types`, { params: parameter })
}

/** Create a relation between two CI types. */
export function createRelation(
  parentId: string | number,
  childrenId: string | number,
  data: Record<string, unknown>
): Promise<any> {
  return request.post(`${urlPrefix}/ci_type_relations/${parentId}/${childrenId}`, data)
}

/** Delete a relation between two CI types. */
export function deleteRelation(parentId: string | number, childrenId: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/ci_type_relations/${parentId}/${childrenId}`)
}

/** Grant a role permissions on a CI type relation. */
export function grantTypeRelation(
  first_type_id: string | number,
  second_type_id: string | number,
  rid: string | number,
  data: Record<string, unknown>
): Promise<any> {
  return request.post(`${urlPrefix}/ci_type_relations/${first_type_id}/${second_type_id}/roles/${rid}/grant`, data)
}

/** Revoke a role's permissions on a CI type relation. */
export function revokeTypeRelation(
  first_type_id: string | number,
  second_type_id: string | number,
  rid: string | number,
  data: Record<string, unknown>
): Promise<any> {
  return request.post(`${urlPrefix}/ci_type_relations/${first_type_id}/${second_type_id}/roles/${rid}/revoke`, data)
}
