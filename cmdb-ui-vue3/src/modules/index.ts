// src/modules/index.ts
import type { Router } from 'vue-router'
import type { AppRouteRecord } from '@/stores/routeFilter'
import { aclManifest } from './acl'

export interface ModuleManifest {
  name: string
  routes: () => Promise<unknown>
  locales?: Record<string, Record<string, unknown>>
}

const manifests: ModuleManifest[] = [aclManifest]

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
