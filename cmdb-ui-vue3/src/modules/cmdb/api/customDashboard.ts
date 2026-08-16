// src/modules/cmdb/api/customDashboard.ts
import request from '@/utils/request'

const urlPrefix = '/v0.1'

export function getCustomDashboard(): Promise<any> {
  return request.get(`${urlPrefix}/custom_dashboard`)
}

export function postCustomDashboard(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/custom_dashboard`, data)
}

export function putCustomDashboard(
  id: string | number,
  data: Record<string, unknown>
): Promise<any> {
  return request.put(`${urlPrefix}/custom_dashboard/${id}`, data)
}

export function deleteCustomDashboard(id: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/custom_dashboard/${id}`)
}

export function batchUpdateCustomDashboard(data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/custom_dashboard/batch`, data)
}

export function postCustomDashboardPreview(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/custom_dashboard/preview`, data)
}
