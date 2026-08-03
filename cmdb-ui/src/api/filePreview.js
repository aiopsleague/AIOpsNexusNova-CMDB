import { axios } from '@/utils/request'

export function getFilePreviewConfig() {
  return axios({
    url: '/common-setting/v1/file_preview',
    method: 'get',
  })
}

export function updateFilePreviewConfig(data) {
  return axios({
    url: '/common-setting/v1/file_preview',
    method: 'put',
    data: { data },
  })
}

export function testFilePreviewConnection(data) {
  return axios({
    url: '/common-setting/v1/file_preview/test',
    method: 'post',
    data: { data },
  })
}
