import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Fetch the user's CI type preference (subscribed type ids). */
export function getPreference(instance = true, tree: unknown = null): Promise<any> {
  return request.get(`${urlPrefix}/preference/ci_types`, { params: { instance, tree } })
}

/** Grant a role access to a relation view. */
export function grantRelationView(rid: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/preference/relation/view/roles/${rid}/grant`, data)
}

/** Revoke a role's access to a relation view. */
export function revokeRelationView(rid: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/preference/relation/view/roles/${rid}/revoke`, data)
}

/** Fetch the subscribed (visible) attributes of a CI type. */
export function getSubscribeAttributes(ciTypeId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/preference/ci_types/${ciTypeId}/attributes`)
}

/** Subscribe (set the visible attributes of) a CI type. */
export function subscribeCIType(ciTypeId: string | number, attrs: unknown): Promise<any> {
  return request.post(`${urlPrefix}/preference/ci_types/${ciTypeId}/attributes`, { attr: attrs })
}

/** Subscribe a CI type to the tree view. */
export function subscribeTreeView(ciTypeId: string | number, levels: unknown): Promise<any> {
  return request.post(`${urlPrefix}/preference/tree/view`, { type_id: ciTypeId, levels })
}

/** Fetch the auto-subscription config. */
export function getAutoSubscription(): Promise<any> {
  return request.get(`${urlPrefix}/preference/auto_subscription`)
}
