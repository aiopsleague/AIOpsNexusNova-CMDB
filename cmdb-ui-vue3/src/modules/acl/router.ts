// src/modules/acl/router.ts
import type { AppRouteRecord } from '@/stores/routeFilter'
import { searchApp } from './api/app'

export interface AclApp {
  name?: string
  [key: string]: unknown
}

/** 为某个非 acl 应用生成 acl 子路由（roles/resources/resource_types/trigger/history）。 */
function genAppRoute({ name }: { name: string }): AppRouteRecord {
  return {
    path: `/acl/${name}`,
    component: 'RouteView',
    meta: { title: name, icon: 'solution', permission: [`${name}_admin`, 'acl_admin'] },
    children: [
      { path: `/acl/${name}/roles`, name: `${name}_roles_acl`, component: 'aclRoles', meta: { title: 'acl.roleManage' } },
      { path: `/acl/${name}/resources`, name: `${name}_resources_acl`, component: 'aclResources', meta: { title: 'acl.resourceManage' } },
      { path: `/acl/${name}/resource_types`, name: `${name}_resource_types_acl`, component: 'aclResourceTypes', meta: { title: 'acl.resourceType' } },
      { path: `/acl/${name}/trigger`, name: `${name}_trigger_acl`, component: 'aclTrigger', meta: { title: 'acl.trigger' } },
      { path: `/acl/${name}/history`, name: `${name}_history_acl`, component: 'aclHistory', meta: { title: 'acl.history' } },
    ],
  }
}

/** 纯函数：根据 apps 列表构建 acl 路由树（便于单测）。component 用字符串占位。 */
export function buildAclRoutes(aclApps: AclApp[]): AppRouteRecord {
  const children: AppRouteRecord[] = [
    { path: '/acl/secret_key', name: 'acl_secret_key', component: 'aclSecretKey', meta: { title: 'acl.userSecret', icon: 'key' } },
    { path: '/acl/operate_history', name: 'acl_operate_history', component: 'aclOperationHistory', meta: { title: 'acl.history', icon: 'search', permission: ['acl_admin'] } },
    { path: '/acl/user', name: 'acl_user', component: 'aclUsers', meta: { title: 'acl.userManage', icon: 'user', permission: ['acl_admin'] } },
    { path: '/acl/roles', name: 'acl_roles', component: 'aclRoles', meta: { title: 'acl.roleManage', icon: 'team', keepAlive: true, permission: ['acl_admin'] } },
    { path: '/acl/apps', name: 'acl_apps', component: 'aclApps', meta: { title: 'acl.appManage', icon: 'appstore', permission: ['acl_admin'] } },
  ]

  aclApps.forEach((app) => {
    if (app.name && app.name !== 'acl') {
      children.push(genAppRoute({ name: app.name }))
    }
  })

  return {
    path: '/acl',
    name: 'acl',
    component: 'BasicLayout',
    meta: { title: 'ACL', keepAlive: true },
    redirect: '/acl/secret_key',
    children,
  }
}

/** 异步生成：拉取 apps 后调用纯函数。 */
export async function genAclRoutes(): Promise<AppRouteRecord> {
  const res = (await searchApp()) as unknown as { apps: AclApp[] }
  return buildAclRoutes(res.apps || [])
}
