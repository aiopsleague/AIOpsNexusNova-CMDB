// src/modules/cmdb/api/dcim.ts
import request from '@/utils/request'

const urlPrefix = '/v0.1'

export function getDCIMTreeView(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/dcim/tree_view`, { params })
}

export function getDCIMById(type: string, id: string | number): Promise<any> {
  return request.get(`${urlPrefix}/dcim/${type}/${id}`)
}

export function postDCIM(type: string, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/dcim/${type}`, data)
}

export function putDCIM(
  type: string,
  id: string | number,
  data: Record<string, unknown>
): Promise<any> {
  return request.put(`${urlPrefix}/dcim/${type}/${id}`, data)
}

export function deleteDCIM(type: string, id: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/dcim/${type}/${id}`)
}

export function getDCIMRacks(
  id: string | number,
  params?: Record<string, unknown>
): Promise<any> {
  return request.get(`${urlPrefix}/dcim/server_room/${id}/racks`, { params })
}

export function postDevice(
  rackId: string | number,
  deviceId: string | number,
  data: Record<string, unknown>
): Promise<any> {
  return request.post(`${urlPrefix}/dcim/rack/${rackId}/device/${deviceId}`, data)
}

export function deleteDevice(rackId: string | number, deviceId: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/dcim/rack/${rackId}/device/${deviceId}`)
}

export function putDevice(
  rackId: string | number,
  deviceId: string | number,
  data: Record<string, unknown>
): Promise<any> {
  return request.put(`${urlPrefix}/dcim/rack/${rackId}/device/${deviceId}`, data)
}

export function migrateDevice(
  rackId: string | number,
  deviceId: string | number,
  data: Record<string, unknown>
): Promise<any> {
  return request.put(`${urlPrefix}/dcim/rack/${rackId}/device/${deviceId}/migrate`, data)
}

export function getDCIMHistoryOperate(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/dcim/history/operate`, { params })
}

export function calcUnitFreeCount(): Promise<any> {
  return request.post(`${urlPrefix}/dcim/rack/calc_u_free_count`)
}
