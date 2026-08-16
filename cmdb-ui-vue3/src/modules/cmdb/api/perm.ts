// src/modules/cmdb/api/perm.ts
import request from '@/utils/request'

export function getWX(): Promise<any> {
  return request.get('/v1/acl/users')
}
