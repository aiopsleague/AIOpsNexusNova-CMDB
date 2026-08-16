import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Fetch all CI type relations (with the per-type attribute map). */
export function getCITypeRelations(): Promise<any> {
  return request.get(`${urlPrefix}/ci_type_relations`)
}

/** Fetch the child CI types of a CI type. */
export function getCITypeChildren(CITypeID: string | number, parameter?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_type_relations/${CITypeID}/children`, { params: parameter })
}

/** Fetch the parent CI types of a CI type. */
export function getCITypeParent(CITypeID: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci_type_relations/${CITypeID}/parents`)
}

/** Fetch the recursively-expanded second-level children of a CI type. */
export function getRecursive_level2children(type_id: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci_type_relations/${type_id}/recursive_level2children`)
}

/** Fetch the relation paths between a source CI type and target CI types. */
export function getCITypeRelationPath(params: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_type_relations/path`, { params })
}

/** Check whether a role can edit relations between two CI types. */
export function getCanEditByParentIdChildId(parent_id: string | number, child_id: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci_type_relations/${parent_id}/${child_id}/can_edit`)
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
