import { axios } from '@/utils/request'

export function getFileStorageConfig() {
  return axios({
    url: '/common-setting/v1/file_storage',
    method: 'get',
  })
}

export function updateFileStorageConfig(data) {
  return axios({
    url: '/common-setting/v1/file_storage',
    method: 'put',
    data: { data },
  })
}

export function testFileStorageConnection(data) {
  return axios({
    url: '/common-setting/v1/file_storage/test',
    method: 'post',
    data: { data },
  })
}
