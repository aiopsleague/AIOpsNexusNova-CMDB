import { axios } from '@/utils/request'

export function uploadCiFile(formData, attrId) {
  const params = {}
  if (attrId) {
    params.attr_id = attrId
  }
  return axios({
    url: '/v0.1/ci/files',
    method: 'POST',
    data: formData,
    params,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function deleteCiFiles(paths) {
  return axios({
    url: '/v0.1/ci/files',
    method: 'DELETE',
    data: { paths }
  })
}
