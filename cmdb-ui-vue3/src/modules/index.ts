// src/modules/index.ts
import type { Router } from 'vue-router'
import type { AppRouteRecord } from '@/stores/routeFilter'
import { aclManifest } from './acl'
import { cmdbManifest } from './cmdb'

export interface ModuleManifest {
  name: string
  routes: () => Promise<unknown>
  locales?: Record<string, Record<string, unknown>>
}

const manifests: ModuleManifest[] = [aclManifest, cmdbManifest]

/** i18n 实例的最小结构（legacy: false 时暴露 global Composer）。 */
interface I18nLike {
  global: {
    mergeLocaleMessage: (locale: string, message: Record<string, unknown>) => void
  }
}

/** 合并模块 i18n 文案。 */
export async function loadModules(_router: Router, i18n: I18nLike) {
  manifests.forEach((m) => {
    if (m.locales) {
      Object.entries(m.locales).forEach(([lang, msgs]) => i18n.global.mergeLocaleMessage(lang, msgs))
    }
  })
}

/** 构建所有模块的动态路由（供守卫按权限过滤后注册）。 */
export async function loadModuleRoutes(): Promise<unknown[]> {
  const routes = await Promise.all(manifests.map((m) => m.routes()))
  return routes.flat()
}

const componentMap: Record<string, () => Promise<unknown>> = {
  BasicLayout: () => import('@/layouts/BasicLayout.vue'),
  RouteView: () => import('@/layouts/RouteView.vue'),
  aclUsers: () => import('@/modules/acl/views/users.vue'),
  aclRoles: () => import('@/modules/acl/views/roles.vue'),
  aclResources: () => import('@/modules/acl/views/resources.vue'),
  aclResourceTypes: () => import('@/modules/acl/views/resource_types.vue'),
  aclTrigger: () => import('@/modules/acl/views/trigger.vue'),
  aclApps: () => import('@/modules/acl/views/apps.vue'),
  aclSecretKey: () => import('@/modules/acl/views/secretKey.vue'),
  aclHistory: () => import('@/modules/acl/views/history.vue'),
  aclOperationHistory: () => import('@/modules/acl/views/operation_history/index.vue'),
  // cmdb views are not yet migrated; all placeholders resolve to a stub.
  cmdbDashboard: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbTopologyView: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbRelationViews: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbResourceViews: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbTreeViews: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbResourceSearch: () => import('@/modules/cmdb/views/resource_search_2/index.vue'),
  cmdbDiscoveryCI: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbCiDetail: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbIpam: () => import('@/modules/cmdb/views/ipam/index.vue'),
  cmdbDcim: () => import('@/modules/cmdb/views/dcim/index.vue'),
  cmdbPreference: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbBatch: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbCiTypes: () => import('@/modules/cmdb/views/ci_types/index.vue'),
  cmdbCustomDashboard: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbPreferenceRelation: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbDiscovery: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbOperationHistory: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbModelRelation: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbRelationType: () => import('@/modules/cmdb/views/placeholder.vue'),
  cmdbMobileDetail: () => import('@/modules/cmdb/views/placeholder.vue'),
}

function resolveNode(node: AppRouteRecord): AppRouteRecord {
  const resolved = { ...node }
  if (typeof resolved.component === 'string' && componentMap[resolved.component]) {
    resolved.component = componentMap[resolved.component]
  }
  if (resolved.children) {
    resolved.children = resolved.children.map(resolveNode)
  }
  return resolved
}

/** 将路由树中的字符串 component 占位符解析为懒加载组件。 */
export function resolveRouteComponents(routes: unknown[]): unknown[] {
  return routes.map((r) => resolveNode(r as AppRouteRecord))
}
