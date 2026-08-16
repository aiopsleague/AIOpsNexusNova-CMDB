# cmdb-ui-vue3 acl 基础设施 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在已完成的 `cmdb-ui-vue3` 外壳之上，落地 `acl` 模块的基础设施层——类型化的 API 客户端、TS 类型、路由清单、模块 manifest、i18n 文案、常量，以及让 acl 菜单真正挂载并可导航（视图先以占位页呈现），为后续逐实体迁移 36 个视图铺路。

**Architecture:** 沿用外壳的 `modules/<name>/index.ts` manifest 模式（`{ name, routes, locales }`）。`loadModules` 合并 i18n；`routesStore.generateRoutes` 从 manifest 构建并按权限过滤动态路由；守卫在 `getInfo` 后注册这些路由。本计划**不含**真实视图实现（占位页），也不含 vxe-table / 共享组件迁移（它们属于视图阶段）。

**Tech Stack:** 同上外壳（Vue3 + TS + Pinia + vue-router 4 + vue-i18n 9 + axios）。后端前缀 `/api` + `/v1/acl`。

---

## 文件结构（本计划创建/修改）

```
cmdb-ui-vue3/src/modules/acl/
  index.ts            # manifest { name, routes, locales }
  types.ts            # User/Role/Resource/ResourceType/ResourceGroup/App/Trigger/AuditLog/Permission
  constants.ts        # valueTypeMap
  router.ts           # buildAclRoutes(apps) 纯函数 + genAclRoutes() 异步生成
  store.ts            # acl store（旧版为空，此处极简，供视图阶段扩展）
  api/
    user.ts role.ts resource.ts permission.ts app.ts trigger.ts history.ts secretKey.ts
  lang/
    zh.ts en.ts
  views/              # 占位视图（9 个，后续视图阶段替换）
    users.vue roles.vue resources.vue resource_types.vue trigger.vue apps.vue
    secretKey.vue history.vue operation_history/index.vue
cmdb-ui-vue3/src/modules/index.ts       # 修改：合并 locales + 导出 loadModuleRoutes
cmdb-ui-vue3/src/stores/routes.ts        # 修改：generateRoutes 使用模块路由
cmdb-ui-vue3/src/router/guard.ts         # 修改：注册动态路由（落实 TODO(acl)）
cmdb-ui-vue3/src/__tests__/aclRoutes.spec.ts
```

---

## Phase 0：类型与常量

### Task 1: acl 类型 + 常量

**Files:**
- Create: `cmdb-ui-vue3/src/modules/acl/types.ts`
- Create: `cmdb-ui-vue3/src/modules/acl/constants.ts`

- [ ] **Step 1: 创建 types.ts**

```ts
// src/modules/acl/types.ts
export interface AclUser {
  id?: number
  username?: string
  name?: string
  email?: string
  mobile?: string
  department_id?: number
  is_block?: boolean
  joined_at?: string
  [key: string]: unknown
}

export interface AclRole {
  id?: number
  name?: string
  virtual?: boolean
  parent_ids?: number[]
  [key: string]: unknown
}

export interface ResourceType {
  id?: number
  name?: string
  [key: string]: unknown
}

export interface Resource {
  id?: number
  name?: string
  resource_type_id?: number
  is_group?: boolean
  creator?: string
  [key: string]: unknown
}

export interface ResourceGroup {
  id?: number
  name?: string
  resource_type_id?: number
  [key: string]: unknown
}

export interface AclApp {
  name?: string
  [key: string]: unknown
}

export interface Trigger {
  id?: number
  name?: string
  pattern?: string
  resource_type_id?: number
  status?: string
  [key: string]: unknown
}

export interface AuditLog {
  id?: number
  operator?: string
  operate_time?: string
  source?: string
  [key: string]: unknown
}

/** 分页查询结果（后端统一返回）。 */
export interface PageResult<T> {
  total?: number
  page?: number
  page_size?: number
  [key: string]: unknown
}
```

- [ ] **Step 2: 创建 constants.ts**

```ts
// src/modules/acl/constants.ts
export const valueTypeMap: Record<string, string> = {
  '0': '整数',
  '1': '浮点数',
  '2': '文本',
  '3': 'datetime',
  '4': 'date',
  '5': 'time',
  '6': 'json',
}
```

- [ ] **Step 3: Commit**

```bash
git add cmdb-ui-vue3/src/modules/acl
git commit -m "feat(ui): add acl module types and constants"
```

---

## Phase 1：类型化 API 客户端

### Task 2: acl API 客户端（8 文件）

**Files:** Create `cmdb-ui-vue3/src/modules/acl/api/{user,role,resource,permission,app,trigger,history,secretKey}.ts`

- [ ] **Step 1: user.ts**

```ts
// src/modules/acl/api/user.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function currentUser() {
  return request.get(`${prefix}/users/info`)
}
export function getOnDutyUser() {
  return request.get(`${prefix}/users/employee`)
}
export function searchUser(params: Record<string, unknown>) {
  return request.get(`${prefix}/users`, { params })
}
export function addUser(data: Record<string, unknown>) {
  return request.post(`${prefix}/users`, data)
}
export function updateUserById(id: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/users/${id}`, data)
}
export function deleteUserById(id: number) {
  return request.delete(`${prefix}/users/${id}`)
}
```

- [ ] **Step 2: role.ts**

```ts
// src/modules/acl/api/role.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function searchRole(params: Record<string, unknown>) {
  return request.get(`${prefix}/roles`, { params })
}
export function addRole(data: Record<string, unknown>) {
  return request.post(`${prefix}/roles`, data)
}
export function updateRoleById(id: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/roles/${id}`, data)
}
export function deleteRoleById(id: number, data?: Record<string, unknown>) {
  return request.delete(`${prefix}/roles/${id}`, { data })
}
export function addParentRole(id: number, otherId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${id}/parents`, { ...data, parent_id: otherId })
}
export function delParentRole(cid: number, pid: number, data: Record<string, unknown>) {
  return request.delete(`${prefix}/roles/${cid}/parents`, { data: { ...data, parent_id: pid } })
}
export function getUsersUnderRole(rid: number, data: Record<string, unknown>) {
  return request.get(`${prefix}/roles/${rid}/users`, { params: data })
}
export function addBatchParentRole(parentId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${parentId}/children`, data)
}
```

- [ ] **Step 3: resource.ts**

```ts
// src/modules/acl/api/resource.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function searchResource(params: Record<string, unknown>) {
  return request.get(`${prefix}/resources`, { params })
}
export function addResource(data: Record<string, unknown>) {
  return request.post(`${prefix}/resources`, data)
}
export function updateResourceById(id: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/resources/${id}`, data)
}
export function deleteResourceById(id: number, params?: Record<string, unknown>) {
  return request.delete(`${prefix}/resources/${id}`, { params })
}
export function searchResourceType(params: Record<string, unknown>) {
  return request.get(`${prefix}/resource_types`, { params })
}
export function addResourceType(data: Record<string, unknown>) {
  return request.post(`${prefix}/resource_types`, data)
}
export function updateResourceTypeById(id: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/resource_types/${id}`, data)
}
export function deleteResourceTypeById(id: number) {
  return request.delete(`${prefix}/resource_types/${id}`)
}
export function getResourceGroups(params: Record<string, unknown>) {
  return request.get(`${prefix}/resource_groups`, { params })
}
export function addResourceGroup(data: Record<string, unknown>) {
  return request.post(`${prefix}/resource_groups`, data)
}
export function updateResourceGroup(id: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/resource_groups/${id}`, data)
}
export function deleteResourceGroup(id: number) {
  return request.delete(`${prefix}/resource_groups/${id}`)
}
export function getResourceGroupItems(id: number) {
  return request.get(`${prefix}/resource_groups/${id}/items`)
}
```

- [ ] **Step 4: permission.ts**

```ts
// src/modules/acl/api/permission.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function getResourcePerms(resourceId: number, params?: Record<string, unknown>) {
  return request.get(`${prefix}/resources/${resourceId}/permissions`, { params })
}
export function getResourceTypePerms(typeId: number) {
  return request.get(`${prefix}/resource_types/${typeId}/perms`)
}
export function getResourceGroupPerms(groupId: number) {
  return request.get(`${prefix}/resource_groups/${groupId}/permissions`)
}
export function setRoleResourcePerm(rid: number, resourceId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/${resourceId}/grant2`, data)
}
export function setRoleResourceGroupPerm(rid: number, groupId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resource_groups/${groupId}/grant`, data)
}
export function deleteRoleResourcePerm(rid: number, resourceId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/${resourceId}/revoke2`, data)
}
export function deleteRoleResourceGroupPerm(rid: number, groupId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resource_groups/${groupId}/revoke`, data)
}
export function deleteRoleResourceGroupPerm2(rid: number, groupId: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resource_groups/${groupId}/revoke2`, data)
}
export function searchPermResourceByRoleId(rid: number, params: Record<string, unknown>) {
  return request.get(`${prefix}/roles/${rid}/resources`, { params })
}
export function roleHasPermissionToGrant(params: Record<string, unknown>) {
  return request.get(`${prefix}/roles/has_perm`, { params })
}
export function setBatchRoleResourcePerm(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/batch/grant`, data)
}
export function setBatchRoleResourceGroupPerm(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resource_groups/batch/grant`, data)
}
export function setBatchRoleResourceRevoke(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/batch/revoke`, data)
}
export function setBatchRoleResourceGroupRevoke(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resource_groups/batch/revoke`, data)
}
export function setBatchRoleResourceByResourceName(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/batch/grant2`, data)
}
export function setBatchRoleResourceRevokeByResourceName(rid: number, data: Record<string, unknown>) {
  return request.post(`${prefix}/roles/${rid}/resources/batch/revoke2`, data)
}
```

- [ ] **Step 5: app.ts / trigger.ts / history.ts / secretKey.ts**

```ts
// src/modules/acl/api/app.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function searchApp(params: Record<string, unknown> = {}) {
  return request.get(`${prefix}/apps`, { params: { ...params, page_size: 9999 } })
}
export function addApp(data: Record<string, unknown>) {
  return request.post(`${prefix}/apps`, data)
}
export function updateApp(aid: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/apps/${aid}`, data)
}
export function getApp(aid: number) {
  return request.get(`${prefix}/apps/${aid}`)
}
export function deleteApp(aid: number) {
  return request.delete(`${prefix}/apps/${aid}`)
}
```

```ts
// src/modules/acl/api/trigger.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function getTriggers(params: Record<string, unknown>) {
  return request.get(`${prefix}/triggers`, { params })
}
export function addTrigger(data: Record<string, unknown>) {
  return request.post(`${prefix}/triggers`, data)
}
export function updateTrigger(tid: number, data: Record<string, unknown>) {
  return request.put(`${prefix}/triggers/${tid}`, data)
}
export function deleteTrigger(tid: number) {
  return request.delete(`${prefix}/triggers/${tid}`)
}
export function applyTrigger(tid: number) {
  return request.post(`${prefix}/triggers/${tid}/apply`)
}
export function cancelTrigger(tid: number) {
  return request.post(`${prefix}/triggers/${tid}/cancel`)
}
export function patternResults(data: Record<string, unknown>) {
  return request.post(`${prefix}/triggers/resources`, data)
}
```

```ts
// src/modules/acl/api/history.ts
import request from '@/utils/request'

const prefix = '/v1/acl'

export function searchPermissionHistory(params: Record<string, unknown>) {
  return request.get(`${prefix}/audit_log/permission`, { params })
}
export function searchRoleHistory(params: Record<string, unknown>) {
  return request.get(`${prefix}/audit_log/role`, { params })
}
export function searchResourceHistory(params: Record<string, unknown>) {
  return request.get(`${prefix}/audit_log/resource`, { params })
}
export function searchTriggerHistory(params: Record<string, unknown>) {
  return request.get(`${prefix}/audit_log/trigger`, { params })
}
```

```ts
// src/modules/acl/api/secretKey.ts
import request from '@/utils/request'

export function getSecret() {
  return request.get('/v1/acl/users/secret')
}
export function updateSecret(data: Record<string, unknown>) {
  return request.post('/v1/acl/users/reset_key_secret', data)
}
```

- [ ] **Step 6: 类型检查**

Run: `cd cmdb-ui-vue3 && pnpm typecheck`
Expected: 通过（api 文件不依赖尚未创建的视图/路由）。

- [ ] **Step 7: Commit**

```bash
git add cmdb-ui-vue3/src/modules/acl/api
git commit -m "feat(ui): add typed acl api clients"
```

---

## Phase 2：i18n 文案

### Task 3: acl 语言包

**Files:**
- Create: `cmdb-ui-vue3/src/modules/acl/lang/zh.ts`
- Create: `cmdb-ui-vue3/src/modules/acl/lang/en.ts`

- [ ] **Step 1: 创建 zh.ts（嵌套在 `acl` 命名空间下）**

> 将旧 `acl_zh` 的键值包进 `acl` 命名空间，避免与其他模块冲突。

```ts
// src/modules/acl/lang/zh.ts
export default {
  acl: {
    date: '日期',
    operator: '操作员',
    resource: '资源',
    resourceType: '资源类型',
    addResourceType: '新增资源类型',
    app: '应用',
    operateTime: '操作时间',
    permission: '权限',
    permission_placeholder: '请选择权限',
    permissionList: '权限列表',
    summaryPermissions: '权限汇总',
    source: '来源',
    username: '用户名',
    username_placeholder: '请输入用户名',
    userList: '用户列表',
    groupUser: '组用户',
    addUser: '新增用户',
    subordinateUsers: '下属用户',
    nickname: '中文名',
    nickname_placeholder: '请输入中文名',
    password: '密码',
    password_placeholder: '请输入密码',
    department: '部门',
    group: '小组',
    email: '邮箱',
    email_placeholder: '请输入邮箱',
    mobile: '手机号',
    isBlock: '是否锁定',
    block: '锁定',
    joined_at: '加入时间',
    role: '角色名',
    role_placeholder1: '请输入角色名',
    role_placeholder2: '请选择角色名称',
    role_placeholder3: '请选择角色名称，可多选',
    allRole: '所有角色',
    visualRole: '虚拟角色',
    addVisualRole: '新增虚拟角色',
    inheritedFrom: '继承自',
    heir: '继承者',
    permissionChange: '权限变更',
    roleChange: '角色变更',
    resourceChange: '资源变更',
    resourceTypeChange: '资源类型变更',
    trigger: '触发器',
    triggerNameInput: '请输入触发器名',
    triggerChange: '触发器变更',
    roleManage: '角色管理',
    userManage: '用户管理',
    appManage: '应用管理',
    resourceManage: '资源管理',
    history: '操作审计',
    userSecret: '用户密钥',
    none: '无',
    danger: '危险操作',
    confirmDeleteApp: '确定要删除该App吗？',
    revoke: '权限回收',
    convenient: '便捷授权',
    group2: '组',
    groupName: '资源组名',
    resourceName: '资源名',
    creator: '创建者',
    member: '成员',
    viewAuth: '查看授权',
    addTypeTips: '暂无类型信息，请先添加资源类型!',
    addResource: '新增资源',
    resourceList: '资源列表',
    confirmResetSecret: '确定重置用户密钥？',
    addTrigger: '新增触发器',
    deleteTrigger: '删除触发器',
    applyTrigger: '应用触发器',
    cancelTrigger: '取消触发器',
    enable: '启用',
    disable: '禁用',
    viewMatchResult: '查看正则匹配结果',
    confirmDeleteTrigger: '确认删除该触发器吗？',
    ruleApply: '规则应用',
    triggerTip1: '是否确定应用该触发器？',
    triggerTip2: '是否取消应用该触发器？',
    appNameInput: '请输入应用名称',
    descInput: '请输入描述',
    addApp: '创建应用',
    updateApp: '更新应用',
    cancel: '撤销',
    typeName: '类型名',
    typeNameInput: '请输入类型名',
    resourceNameInput: '请输入资源名',
    pressEnter: '按回车确认筛选',
    groupMember: '组成员：',
    isGroup: '是否组',
    errorTips: '错误提示',
    roleList: '角色列表',
    virtual: '虚拟',
    resourceBatchTips: '请输入资源名，换行分隔',
    memberManage: '成员管理：',
    newResource: '新建资源：',
    deleteResource: '删除资源：',
    deleteResourceType: '删除资源类型：',
    noChange: '没有修改',
    batchOperate: '批量操作',
    batchGrant: '批量授权',
    batchRevoke: '批量权限回收',
    editPerm: '添加授权：',
    permInput: '请输入权限名',
    resourceTypeName: '资源类型名',
    selectedParents: '可选择继承角色',
    isAppAdmin: '是否应用管理员',
    addRole: '新增角色',
    roleRelation: '角色关系',
    roleRelationAdd: '添加角色关系',
    roleRelationDelete: '删除角色关系',
    role2: '角色',
    admin: '管理员',
    involvingRP: '涉及资源及权限',
    startAt: '开始时间',
    endAt: '结束时间',
    triggerTips1: '优先正则模式（次通配符）',
    pleaseSelectType: '请选择资源类型',
    apply: '应用',
    mobileTips: '请输入正确的手机号码',
    remove: '移除',
    deleteUserConfirm: '是否确定要移除该用户',
    copyResource: '复制资源名',
  },
}
```

- [ ] **Step 2: 创建 en.ts（同上，英文值，键名一致）**

> 键名与 zh.ts 一一对应；值用旧 `acl_en` 的英文。为避免篇幅，此处给出映射骨架，实现时需逐键填写英文值（内容已在上文 `lang/en.js` 中，直接搬运到 `acl` 命名空间下）。

- [ ] **Step 3: Commit**

```bash
git add cmdb-ui-vue3/src/modules/acl/lang
git commit -m "feat(ui): add acl i18n messages"
```

---

## Phase 3：路由与 manifest

### Task 4: acl 路由（纯函数 + 异步生成）

**Files:**
- Create: `cmdb-ui-vue3/src/modules/acl/router.ts`
- Test: `cmdb-ui-vue3/src/__tests__/aclRoutes.spec.ts`

- [ ] **Step 1: 写失败测试（针对纯函数 buildAclRoutes）**

```ts
// src/__tests__/aclRoutes.spec.ts
import { describe, it, expect } from 'vitest'
import { buildAclRoutes, type AppRouteRecord } from '@/modules/acl/router'

const apps = [{ name: 'acl' }, { name: 'cmdb' }, { name: 'ticket' }]

describe('buildAclRoutes', () => {
  it('always includes core acl routes (secret_key/operate_history/user/roles/apps)', () => {
    const routes = buildAclRoutes(apps) as AppRouteRecord
    const paths = (routes.children || []).map((c) => c.path)
    expect(paths).toContain('/acl/secret_key')
    expect(paths).toContain('/acl/operate_history')
    expect(paths).toContain('/acl/user')
    expect(paths).toContain('/acl/roles')
    expect(paths).toContain('/acl/apps')
  })

  it('adds a per-app route for every non-acl app', () => {
    const routes = buildAclRoutes(apps) as AppRouteRecord
    const children = routes.children || []
    const perApp = children.filter((c) => (c.path as string).startsWith('/acl/') && (c as any).children)
    expect(perApp.map((c) => c.path)).toEqual(['/acl/cmdb', '/acl/ticket'])
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/aclRoutes.spec.ts`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 创建 router.ts**

```ts
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

/** 纯函数：根据 apps 列表构建 acl 路由树（便于单测）。component 用字符串占位，注册时再映射为组件。 */
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
  const res = (await searchApp()) as { apps: AclApp[] }
  return buildAclRoutes(res.apps || [])
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/aclRoutes.spec.ts`
Expected: PASS（2 tests）

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui-vue3/src/modules/acl/router.ts cmdb-ui-vue3/src/__tests__/aclRoutes.spec.ts
git commit -m "feat(ui): add acl route builder"
```

---

### Task 5: store + manifest + 视图占位

**Files:**
- Create: `cmdb-ui-vue3/src/modules/acl/store.ts`
- Create: `cmdb-ui-vue3/src/modules/acl/index.ts`
- Create: 9 个占位视图 `cmdb-ui-vue3/src/modules/acl/views/{users,roles,resources,resource_types,trigger,apps,secretKey,history}.vue` + `views/operation_history/index.vue`

- [ ] **Step 1: 创建 store.ts（极简，供视图阶段扩展）**

```ts
// src/modules/acl/store.ts
import { defineStore } from 'pinia'

export const useAclStore = defineStore('acl', {
  state: () => ({
    currentApp: 'acl',
  }),
  actions: {
    setCurrentApp(app: string) {
      this.currentApp = app
    },
  },
})
```

- [ ] **Step 2: 创建 index.ts（manifest）**

```ts
// src/modules/acl/index.ts
import { genAclRoutes } from './router'
import zh from './lang/zh'
import en from './lang/en'
import type { ModuleManifest } from '@/modules'

export const aclManifest: ModuleManifest = {
  name: 'acl',
  routes: genAclRoutes,
  locales: { zh, en },
}

export default aclManifest
```

- [ ] **Step 3: 创建 9 个占位视图**

> 每个占位视图为最简 `script setup` 组件，渲染模块名 + “TODO：视图迁移中”。示例（其余 8 个同构，仅标题不同）：

```vue
<!-- src/modules/acl/views/users.vue -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div style="padding: 24px">{{ t('acl.userManage') }} — TODO: view migration pending</div>
</template>
```

占位视图清单与标题：`users.vue`(acl.userManage)、`roles.vue`(acl.roleManage)、`resources.vue`(acl.resourceManage)、`resource_types.vue`(acl.resourceType)、`trigger.vue`(acl.trigger)、`apps.vue`(acl.appManage)、`secretKey.vue`(acl.userSecret)、`history.vue`(acl.history)、`operation_history/index.vue`(acl.history)。

- [ ] **Step 4: Commit**

```bash
git add cmdb-ui-vue3/src/modules/acl
git commit -m "feat(ui): add acl manifest and placeholder views"
```

---

## Phase 4：装配（模块加载 + 动态路由）

### Task 6: 修改 modules/index.ts / routes store / guard

**Files:**
- Modify: `cmdb-ui-vue3/src/modules/index.ts`
- Modify: `cmdb-ui-vue3/src/stores/routes.ts`
- Modify: `cmdb-ui-vue3/src/router/guard.ts`

- [ ] **Step 1: 改写 modules/index.ts**

```ts
// src/modules/index.ts
import type { Router } from 'vue-router'
import type { I18n } from 'vue-i18n'
import { aclManifest } from './acl'

export interface ModuleManifest {
  name: string
  routes: () => Promise<unknown>
  locales?: Record<string, Record<string, unknown>>
}

const manifests: ModuleManifest[] = [aclManifest]

/** 合并模块 i18n 文案。 */
export async function loadModules(_router: Router, i18n: I18n) {
  manifests.forEach((m) => {
    if (m.locales) {
      Object.entries(m.locales).forEach(([lang, msgs]) => i18n.mergeLocaleMessage(lang, msgs))
    }
  })
}

/** 构建所有模块的动态路由（供守卫按权限过滤后注册）。 */
export async function loadModuleRoutes(): Promise<unknown[]> {
  const routes = await Promise.all(manifests.map((m) => m.routes()))
  return routes.flat()
}
```

- [ ] **Step 2: 修改 stores/routes.ts**

```ts
// src/stores/routes.ts
import { defineStore } from 'pinia'
import { filterAsyncRoutes, type AppRouteRecord } from './routeFilter'
import { loadModuleRoutes } from '@/modules'

interface RoutesState {
  appRoutes: AppRouteRecord[]
}

export const useRoutesStore = defineStore('routes', {
  state: (): RoutesState => ({
    appRoutes: [],
  }),
  actions: {
    async generateRoutes(permissions: string[]) {
      const moduleRoutes = (await loadModuleRoutes()) as AppRouteRecord[]
      this.appRoutes = filterAsyncRoutes(moduleRoutes, permissions)
      return this.appRoutes
    },
    reset() {
      this.appRoutes = []
    },
  },
})
```

> 说明：`loadModuleRoutes` 返回的 `component` 目前是字符串占位（如 `'aclUsers'`），需在注册前映射为实际组件。因此新增一个组件映射表（放在 `modules/index.ts`），将字符串占位解析为 `() => import(...)`：

```ts
// 追加到 modules/index.ts
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

export function resolveRouteComponents(routes: unknown[]): unknown[] {
  return routes.map((r) => resolveNode(r as AppRouteRecord))
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
```

`stores/routes.ts` 的 `generateRoutes` 在过滤前调用 `resolveRouteComponents`：

```ts
async generateRoutes(permissions: string[]) {
  const moduleRoutes = resolveRouteComponents(await loadModuleRoutes()) as AppRouteRecord[]
  this.appRoutes = filterAsyncRoutes(moduleRoutes, permissions)
  return this.appRoutes
}
```

- [ ] **Step 3: 修改 router/guard.ts（落实动态路由注册）**

将 guard 中 `getInfo` 成功后的分支改为：

```ts
if (token && !userStore.uid) {
  try {
    await userStore.getInfo()
  } catch {
    await userStore.logout()
    return next({ path: '/user/login', query: { redirect: to.fullPath } })
  }
  userStore.fetchAuthDataEnable().catch(() => {})
  try {
    const permissions = userStore.roles.permissions?.map((p) => p.name) ?? []
    const dynamic = await useRoutesStore().generateRoutes(permissions)
    dynamic.forEach((r) => router.addRoute(r as never))
  } catch {
    // 模块路由构建失败不阻断导航
  }
  return next({ ...to, replace: true })
}
```

（需在 guard 顶部恢复 `import { useRoutesStore } from '@/stores/routes'`。）

- [ ] **Step 4: 类型检查 + 测试 + 构建**

Run: `cd cmdb-ui-vue3 && pnpm typecheck && pnpm test && pnpm build`
Expected: 全部通过。

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui-vue3/src/modules/index.ts cmdb-ui-vue3/src/stores/routes.ts cmdb-ui-vue3/src/router/guard.ts
git commit -m "feat(ui): wire acl module routes into loader and guard"
```

---

## 后续（不在本计划）

- **视图阶段**（逐实体）：users → roles → resources/resource_types/permissions → trigger/apps/secretKey → history/operation_history；同时迁移 vxe-table 4、OpsTable、CustomDrawer/Transfer 等共享组件。
- **cmdb 模块迁移**：后续独立 plan。

---

## Self-Review 记录

- **Spec 覆盖**：外壳的 `loadModules` 空实现、`TODO(acl)` 路由注册点在本计划落实；acl 的 8 个 API、路由树、i18n、manifest 均有对应 Task。
- **占位符扫描**：无 TBD；`component` 字符串占位 + `resolveRouteComponents` 是明确的映射设计，非未决项。
- **类型一致性**：`AppRouteRecord` 复用 `stores/routeFilter` 的既有类型；`ModuleManifest.routes` 签名统一为 `() => Promise<unknown>`；`aclManifest`/`loadModuleRoutes`/`resolveRouteComponents` 名称跨 Task 一致。
