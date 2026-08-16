import request from '@/utils/request'

const urlPrefix = '/v0.1'

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
