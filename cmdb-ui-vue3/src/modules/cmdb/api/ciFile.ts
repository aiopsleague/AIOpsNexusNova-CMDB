// src/modules/cmdb/api/ciFile.ts
import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Upload a CI file attachment. */
export function uploadCiFile(formData: FormData, attrId?: string | number): Promise<any> {
  const params: Record<string, unknown> = {}
  if (attrId) {
    params.attr_id = attrId
  }
  return request.post(`${urlPrefix}/ci/files`, formData, {
    params,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** Delete CI files by path. */
export function deleteCiFiles(paths: Array<Record<string, unknown> | string>): Promise<any> {
  return request.delete(`${urlPrefix}/ci/files`, { data: { paths } })
}
