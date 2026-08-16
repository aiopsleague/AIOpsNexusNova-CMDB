// src/api/login.ts
import request from '@/utils/request'
import type { GetInfoResponse, LoginResponse } from '@/types'

export function login(data: { username: string; password: string; remember_me?: boolean }) {
  return request.post<unknown, LoginResponse>('/v1/acl/login', data)
}

export function getInfo() {
  return request.get<unknown, GetInfoResponse>('/v1/acl/users/info')
}

export function logout() {
  const authType = localStorage.getItem('ops_auth_type')
  const url = authType ? `/${authType.toLowerCase()}/logout` : '/v1/acl/logout'
  return authType ? request.get(url) : request.post(url)
}

export function getAllUsers(params: Record<string, unknown>) {
  return request.get('/v1/acl/users', { params })
}
