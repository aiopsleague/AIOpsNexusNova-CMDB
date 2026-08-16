// src/api/filePreview.ts
import request from '@/utils/request'

/** Fetch the kkFileView file preview configuration. */
export function getFilePreviewConfig(): Promise<any> {
  return request.get('/common-setting/v1/file_preview')
}

/** Update the kkFileView file preview configuration. */
export function updateFilePreviewConfig(data: Record<string, unknown>): Promise<any> {
  return request.put('/common-setting/v1/file_preview', { data })
}

/** Test the kkFileView file preview connection. */
export function testFilePreviewConnection(data: Record<string, unknown>): Promise<any> {
  return request.post('/common-setting/v1/file_preview/test', { data })
}
