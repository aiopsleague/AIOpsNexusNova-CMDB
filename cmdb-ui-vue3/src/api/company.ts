// src/api/company.ts
import request from '@/utils/request'
import type { Department } from '@/types'

export function getAllDepartmentList(params: Record<string, unknown>) {
  return request.get<unknown, Department[]>('/common-setting/v1/department/all', { params })
}
