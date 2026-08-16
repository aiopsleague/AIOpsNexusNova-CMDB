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

/** Update a single CI by id. */
export function updateCI(id: string | number, params: Record<string, unknown>, isShowMessage = true): Promise<any> {
  return request.put(`${urlPrefix}/ci/${id}`, params, { isShowMessage } as any)
}

/** Delete a single CI by id. */
export function deleteCI(ciId: string | number, isShowMessage = true): Promise<any> {
  return request.delete(`${urlPrefix}/ci/${ciId}`, { isShowMessage } as any)
}

/** Fetch a single CI instance by id. */
export function getCIById(ciId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci/s`, { params: { q: `_id:${ciId}` } })
}

/** Fetch the Grafana dashboard config for a CI. */
export function getCIGrafana(ciId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci/${ciId}/grafana`)
}

/** Check whether a CI type has monitoring configured. */
export function checkCITypeMonitoring(ciTypeId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci_type/${ciTypeId}/monitoring/check`)
}

/** Fetch Prometheus alerts for a CI. */
export function getCIPrometheusAlerts(ciId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci/${ciId}/prometheus/alerts`)
}

/** Check whether a CI type has Prometheus configured. */
export function checkCIPrometheus(ciTypeId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ci_type/${ciTypeId}/prometheus/check`)
}
