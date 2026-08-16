// src/api/employee.ts
import request from '@/utils/request'
import type { Employee } from '@/types'

export function getEmployeeList(params: Record<string, unknown>) {
  return request.get('/common-setting/v1/employee', { params })
}

export function getEmployeeByUid(uid: number) {
  return request.get<unknown, Employee>(`/common-setting/v1/employee/by_uid/${uid}`)
}
