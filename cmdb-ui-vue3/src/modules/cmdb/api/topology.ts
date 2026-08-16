import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Grant a role access to a topology view. */
export function grantTopologyView(viewId: string | number, rid: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/topology_views/${viewId}/roles/${rid}/grant`, data)
}

/** Revoke a role's access to a topology view. */
export function revokeTopologyView(viewId: string | number, rid: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/topology_views/${viewId}/roles/${rid}/revoke`, data)
}

/** Fetch the topology view groups (with their views). */
export function getTopoGroups(): Promise<any> {
  return request.get(`${urlPrefix}/topology_views`)
}

/** Fetch a single topology view by id. */
export function getTopoView(id: string | number): Promise<any> {
  return request.get(`${urlPrefix}/topology_views/${id}`)
}

/** Create a topology view group. */
export function postTopoGroup(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/topology_views/groups`, data)
}

/** Update a topology view group by id. */
export function putTopoGroupByGId(gid: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/topology_views/groups/${gid}`, data)
}

/** Reorder topology view groups. */
export function putTopoGroupsOrder(data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/topology_views/groups/order`, data)
}

/** Delete a topology view group by id. */
export function deleteTopoGroup(gid: string | number, data?: Record<string, unknown>): Promise<any> {
  return request.delete(`${urlPrefix}/topology_views/groups/${gid}`, { data })
}

/** Create a topology view. */
export function addTopoView(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/topology_views`, data)
}

/** Update a topology view by id. */
export function updateTopoView(id: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/topology_views/${id}`, data)
}

/** Delete a topology view by id. */
export function deleteTopoView(id: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/topology_views/${id}`)
}

/** Fetch the relation graph of a CI type (used when composing a view path). */
export function getRelationsByTypeId(id: string | number): Promise<any> {
  return request.get(`${urlPrefix}/topology_views/relations/ci_types/${id}`)
}

/** Preview a topology view. */
export function previewTopoView(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/topology_views/preview`, data)
}

/** Render a topology view (fetch nodes + links). */
export function showTopoView(id: string | number): Promise<any> {
  return request.get(`${urlPrefix}/topology_views/${id}/view`)
}
