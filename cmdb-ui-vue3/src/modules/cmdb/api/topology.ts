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
