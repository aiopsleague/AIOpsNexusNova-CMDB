// src/modules/cmdb/api/statistics.ts
import request from '@/utils/request'

const urlPrefix = '/v0.1'

export function getStatistics(): Promise<any> {
  return request.get(`${urlPrefix}/statistics`)
}
