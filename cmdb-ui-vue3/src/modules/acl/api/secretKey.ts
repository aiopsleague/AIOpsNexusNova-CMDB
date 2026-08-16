// src/modules/acl/api/secretKey.ts
import request from '@/utils/request'

export function getSecret() {
  return request.get('/v1/acl/users/secret')
}
export function updateSecret(data: Record<string, unknown>) {
  return request.post('/v1/acl/users/reset_key_secret', data)
}
