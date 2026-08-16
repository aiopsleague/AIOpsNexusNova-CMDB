// src/__tests__/aclRoutes.spec.ts
import { describe, it, expect } from 'vitest'
import { buildAclRoutes, type AclApp } from '@/modules/acl/router'

const apps: AclApp[] = [{ name: 'acl' }, { name: 'cmdb' }, { name: 'ticket' }]

describe('buildAclRoutes', () => {
  it('always includes core acl routes', () => {
    const routes = buildAclRoutes(apps)
    const paths = (routes.children || []).map((c) => c.path)
    expect(paths).toContain('/acl/secret_key')
    expect(paths).toContain('/acl/operate_history')
    expect(paths).toContain('/acl/user')
    expect(paths).toContain('/acl/roles')
    expect(paths).toContain('/acl/apps')
  })

  it('adds a per-app route for every non-acl app', () => {
    const routes = buildAclRoutes(apps)
    const perApp = (routes.children || []).filter((c) => (c.children || []).length > 0)
    expect(perApp.map((c) => c.path)).toEqual(['/acl/cmdb', '/acl/ticket'])
  })
})
