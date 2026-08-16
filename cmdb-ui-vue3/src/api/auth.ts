// src/api/auth.ts
import request from '@/utils/request'
import type { AuthEnableResponse } from '@/types'

export function getAuthDataEnable() {
  return request.get<unknown, AuthEnableResponse>('/common-setting/v1/auth_config/enable_list')
}
