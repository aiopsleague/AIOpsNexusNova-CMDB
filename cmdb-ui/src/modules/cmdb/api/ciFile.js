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

/**
 * Delete files by path.
 * @param {Array} paths - list of { path, storage_backend } dicts, or plain path strings
 */
export function deleteCiFiles(paths) {
  return axios({
    url: '/v0.1/ci/files',
    method: 'DELETE',
    data: { paths }
  })
}
