// src/modules/cmdb/api/system_config.ts
import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Save layout configuration. */
export function saveSystemConfig(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/system_config`, data)
}

/** Fetch layout configuration. */
export function getSystemConfig(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/system_config`, { params })
}
