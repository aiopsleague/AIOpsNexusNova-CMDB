// src/__tests__/routes.spec.ts
import { describe, it, expect } from 'vitest'
import { filterAsyncRoutes, type AppRouteRecord } from '@/stores/routeFilter'

const routes: AppRouteRecord[] = [
  { path: '/a', name: 'a', meta: { permission: ['admin'] } },
  { path: '/b', name: 'b', meta: { permission: ['user'] } },
  {
    path: '/parent',
    name: 'parent',
    children: [
      { path: '/parent/c', name: 'c', meta: { permission: ['admin'] } },
      { path: '/parent/d', name: 'd', meta: { permission: ['user'] } },
    ],
  },
  { path: '/public', name: 'public' },
]

describe('filterAsyncRoutes', () => {
  it('keeps routes the user has permission for', () => {
    const result = filterAsyncRoutes(routes, ['admin'])
    const names = result.map((r) => r.name)
    expect(names).toContain('a')
    expect(names).not.toContain('b')
  })

  it('keeps routes without permission meta', () => {
    const result = filterAsyncRoutes(routes, [])
    const names = result.map((r) => r.name)
    expect(names).toContain('public')
  })

  it('filters nested children recursively', () => {
    const result = filterAsyncRoutes(routes, ['user']) as AppRouteRecord[]
    const parent = result.find((r) => r.name === 'parent')!
    expect(parent.children!.map((c) => c.name)).toEqual(['d'])
  })
})
