import request from '@/utils/request'

const urlPrefix = '/v0.1'

 
export function getCITypeAttributesById(CITypeId: string | number, parameter?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ci_types/${CITypeId}/attributes`, { params: parameter })
}
