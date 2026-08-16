import request from '@/utils/request'

const urlPrefix = '/v0.1'

 
export function getCITypeGroupsConfig(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/groups/config`, { params })
}
