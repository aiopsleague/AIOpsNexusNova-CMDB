import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Fetch the user's CI type preference (subscribed type ids). */
export function getPreference(instance = true, tree: unknown = null): Promise<any> {
  return request.get(`${urlPrefix}/preference/ci_types`, { params: { instance, tree } })
}

/** Fetch the relation views (service tree views). */
export function getRelationView(): Promise<any> {
  return request.get(`${urlPrefix}/preference/relation/view`)
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

/** Fetch the subscribed tree view levels for every CI type. */
export function getSubscribeTreeView(): Promise<any> {
  return request.get(`${urlPrefix}/preference/tree/view`)
}

/** Fetch the saved search-option preference list. */
export function getPreferenceSearch(payload?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/preference/search/option`, { params: payload })
}

/** Persist a search-option preference. */
export function savePreferenceSearch(payload: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/preference/search/option`, payload)
}

/** Delete a search-option preference by id. */
export function deletePreferenceSearch(id: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/preference/search/option/${id}`)
}

/** Fetch the auto-subscription config. */
export function getAutoSubscription(): Promise<any> {
  return request.get(`${urlPrefix}/preference/auto_subscription`)
}
