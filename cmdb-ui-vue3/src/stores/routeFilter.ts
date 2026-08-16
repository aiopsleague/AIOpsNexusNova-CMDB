// src/stores/routeFilter.ts
export interface AppRouteRecord {
  path: string
  name?: string
  meta?: { permission?: string[]; title?: string; [key: string]: unknown }
  children?: AppRouteRecord[]
  [key: string]: unknown
}

/**
 * 按权限过滤路由树：命中 meta.permission 且不满足任一权限的节点被剔除；
 * 无 meta.permission 的节点默认保留；children 递归过滤。
 */
export function filterAsyncRoutes(routes: AppRouteRecord[], permissions: string[]): AppRouteRecord[] {
  const result: AppRouteRecord[] = []
  for (const route of routes) {
    const required = route.meta?.permission
    if (required && required.length > 0 && !required.some((p) => permissions.includes(p))) {
      continue
    }
    const next: AppRouteRecord = { ...route }
    if (route.children && route.children.length > 0) {
      next.children = filterAsyncRoutes(route.children, permissions)
    }
    result.push(next)
  }
  return result
}
