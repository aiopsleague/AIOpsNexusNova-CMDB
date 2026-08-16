import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Search CIs via the full-text query endpoint. */
export function searchCI(params: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci/s`, { params })
}

/** Fetch a single CI type by id or unique name. */
export function getCIType(CITypeName: string | number, parameter?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/${CITypeName}`, { params: parameter })
}
