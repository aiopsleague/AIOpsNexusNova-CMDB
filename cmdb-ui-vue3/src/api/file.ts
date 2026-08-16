import request from '@/utils/request'

 
export function postImageFile(parameter: FormData): Promise<any> {
  return request.post('/common-setting/v1/file', parameter)
}

 
export function getFileData(data_type: string): Promise<any> {
  return request.get(`/common-setting/v1/data/${data_type}`)
}

 
export function addFileData(data_type: string, data: Record<string, unknown>): Promise<any> {
  return request.post(`/common-setting/v1/data/${data_type}`, data)
}

 
export function deleteFileData(data_type: string, id: string | number): Promise<any> {
  return request.delete(`/common-setting/v1/data/${data_type}/${id}`)
}
