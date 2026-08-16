// src/modules/acl/api/user.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function currentUser() {
  return request.get(`${prefix}/users/info`)
}
export function getOnDutyUser() {
  return request.get(`${prefix}/users/employee`)
}
export function searchUser(params: Record<string, unknown>) {
  return request.get(`${prefix}/users`, { params })
}
export function addUser(data: Record<string, unknown>) {
  return request.post(`${prefix}/users`, data)
}
export function updateUserById(id: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/users/${id}`, data)
}
export function deleteUserById(id: number) {
  return request.delete(`${prefix}/users/${id}`)
}
