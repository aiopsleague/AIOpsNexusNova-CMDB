// src/api/employee.ts
import request from '@/utils/request'
import type { Employee } from '@/types'

export function getEmployeeList(params: Record<string, unknown>) {
  return request.get<unknown, { data_list: unknown[] }>('/common-setting/v1/employee', { params })
}

export function getEmployeeByUid(uid: number) {
  return request.get<unknown, Employee>(`/common-setting/v1/employee/by_uid/${uid}`)
}

/** Resolve notice receivers for a set of employee ids. */
export function getNoticeByEmployeeIds(data: Record<string, unknown>) {
  return request.post('/common-setting/v1/employee/get_notice_by_ids', data)
}
