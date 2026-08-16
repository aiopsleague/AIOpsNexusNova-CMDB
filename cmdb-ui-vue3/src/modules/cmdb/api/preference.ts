import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Grant a role access to a relation view. */
export function grantRelationView(rid: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/preference/relation/view/roles/${rid}/grant`, data)
}

/** Revoke a role's access to a relation view. */
export function revokeRelationView(rid: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/preference/relation/view/roles/${rid}/revoke`, data)
}
