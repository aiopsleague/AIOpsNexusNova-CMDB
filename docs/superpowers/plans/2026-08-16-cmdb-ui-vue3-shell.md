# cmdb-ui-vue3 核心外壳 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 `cmdb-ui-vue3` 核心外壳——一个可运行的 Vue3 + Vite + Pinia + Ant Design Vue 4 + TypeScript 应用，具备登录/登出、布局、明/暗/系统三态主题、i18n、路由守卫与鉴权请求层，作为后续 `acl`/`cmdb` 模块迁移的地基。

**Architecture:** 干净重写 + 绞杀者式渐进迁移。新工程 `cmdb-ui-vue3` 独立于旧 `cmdb-ui`，后端 API 契约完全复用（baseURL `/api`，代理到 `:5000`）。本计划只交付「外壳」层：脚手架 → 主题 → 配置/类型 → 请求层 → API → Pinia stores → 路由守卫 → 布局 → i18n → 指令 → 登录视图 → 装配。业务模块（acl）在后续 plan 中叠加。

**Tech Stack:** Vue 3（`<script setup lang="ts">`）、Vite 5、Pinia 2（+ persistedstate）、Vue Router 4、Ant Design Vue 4、vue-i18n 9、axios 1、dayjs、nprogress、Vitest + @vue/test-utils、vue-tsc、ESLint(flat) + Prettier、包管理器 **pnpm**。

**关键约定：**
- 后端 API 前缀：`/api`（nginx/vite 代理到 `:5000`），业务路径沿用旧前端（如 `/v1/acl/login`、`/common-setting/v1/...`）。
- 鉴权 token 存 `localStorage`，key 常量 `TOKEN_KEY = 'pro__Access-Token'`（沿用旧 `vue-ls` 的 `pro__` 命名空间）。
- 所有代码注释与标识符用英文；文档/提交信息按仓库规范。

---

## 文件结构（本计划创建/修改的全部文件）

```
cmdb-ui-vue3/
  package.json                 # 依赖与脚本
  vite.config.ts               # Vite：@ 别名、:8001、/api 代理 + X-Real-IP
  tsconfig.json                # TS 主配置（strict，@/* 路径）
  tsconfig.node.json           # vite.config.ts 的 TS 配置
  index.html                   # SPA 入口 html
  .env / .env.development / .env.production
  .gitignore
  eslint.config.js             # ESLint flat config
  .prettierrc
  src/
    main.ts                    # 装配：pinia → router → i18n → antd → 指令 → 模块 → 守卫 → 挂载
    App.vue                    # ConfigProvider（theme token + locale）+ router-view
    env.d.ts                   # Vite 客户端类型 + .vue 模块声明
    types/index.ts             # 共享类型（UserInfo/Role/AuthEnable/Employee/Department...）
    config/app.ts              # buildModules / redirectTo 等
    config/setting.ts          # 默认主题/布局配置
    theme/tokens.ts            # COLOR_PRIMARY 等 token 常量
    theme/resolveTheme.ts      # 纯函数 resolveTheme/getSystemDark（可测）
    theme/useTheme.ts          # 组合式：themeMode + resolvedTheme 响应式
    utils/request.ts           # axios 实例 + 拦截器 + 纯函数 extractErrorMessage/getAccessToken
    utils/dom.ts               # setDocumentTitle / domTitle
    api/login.ts               # login/getInfo/logout/getAllUsers
    api/auth.ts                # getAuthDataEnable
    api/employee.ts            # getEmployeeList/getEmployeeByUid
    api/company.ts             # getAllDepartmentList
    stores/index.ts            # pinia 实例 + persistedstate 插件
    stores/app.ts              # 主题模式/布局（持久化）
    stores/user.ts             # token/roles/info + login/getInfo/logout/loadAll*
    stores/routes.ts           # 动态路由 + filterAsyncRoutes（可测）
    router/constant.ts         # constantRouterMap
    router/index.ts            # createRouter + resetRouter
    router/guard.ts            # 导航守卫
    modules/index.ts           # loadModules（外壳阶段为空清单）
    layouts/BasicLayout.vue    # Header + Sider 菜单 + Content
    layouts/UserLayout.vue     # 登录页外壳
    layouts/BlankLayout.vue    # 空布局
    layouts/RouteView.vue      # <router-view> 透传
    layouts/PageView.vue       # keep-alive 页面视图
    directives/action.ts       # v-action 权限指令
    lang/index.ts              # createI18n
    lang/zh.ts / lang/en.ts    # 消息（骨架）
    views/user/Login.vue       # 登录
    views/user/Logout.vue      # 登出
    views/home/index.vue       # 占位首页
    views/exception/404.vue    # 404
    __tests__/                 # Vitest 单测
      resolveTheme.spec.ts
      routes.spec.ts
      appStore.spec.ts
      userStore.spec.ts
      request.spec.ts
      app.spec.ts              # App 冒烟测试
```

---

## Phase 0：脚手架

### Task 1: 工程脚手架（package.json / 配置 / 入口）

**Files:**
- Create: `cmdb-ui-vue3/package.json`
- Create: `cmdb-ui-vue3/vite.config.ts`
- Create: `cmdb-ui-vue3/tsconfig.json`
- Create: `cmdb-ui-vue3/tsconfig.node.json`
- Create: `cmdb-ui-vue3/index.html`
- Create: `cmdb-ui-vue3/.env`
- Create: `cmdb-ui-vue3/.env.development`
- Create: `cmdb-ui-vue3/.env.production`
- Create: `cmdb-ui-vue3/.gitignore`
- Create: `cmdb-ui-vue3/src/env.d.ts`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "cmdb-ui-vue3",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview",
    "typecheck": "vue-tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write ."
  },
  "dependencies": {
    "@ant-design/icons-vue": "^7.0.1",
    "ant-design-vue": "^4.2.6",
    "axios": "^1.7.9",
    "dayjs": "^1.11.13",
    "nprogress": "^0.2.0",
    "pinia": "^2.3.0",
    "pinia-plugin-persistedstate": "^4.2.0",
    "vue": "^3.5.13",
    "vue-i18n": "^9.14.2",
    "vue-router": "^4.5.0"
  },
  "devDependencies": {
    "@types/node": "^22.10.2",
    "@types/nprogress": "^0.2.3",
    "@vitejs/plugin-vue": "^5.2.1",
    "@vue/test-utils": "^2.4.6",
    "eslint": "^9.17.0",
    "eslint-config-prettier": "^9.1.0",
    "eslint-plugin-vue": "^9.32.0",
    "jsdom": "^25.0.1",
    "prettier": "^3.4.2",
    "typescript": "~5.6.3",
    "typescript-eslint": "^8.18.1",
    "vite": "^5.4.11",
    "vitest": "^2.1.8",
    "vue-tsc": "^2.1.10"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.ts**

```ts
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 8001,
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_API_TARGET || 'http://127.0.0.1:5000',
        changeOrigin: true,
        configure(proxy) {
          proxy.on('proxyReq', (proxyReq) => {
            // 模拟 nginx 的 X-Real-IP，使开发环境 IP 白名单认证可用
            proxyReq.setHeader('X-Real-IP', '127.0.0.1')
          })
        },
      },
    },
  },
})
```

- [ ] **Step 3: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 4: 创建 tsconfig.node.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 5: 创建 index.html**

```html
<!doctype html>
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>CMDB</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 6: 创建 env 文件**

`.env` / `.env.development` / `.env.production` 三个文件内容相同：

```dotenv
VITE_API_BASE_URL=/api
```

- [ ] **Step 7: 创建 .gitignore**

```gitignore
node_modules
dist
dist-ssr
*.local
.DS_Store
.vite
```

- [ ] **Step 8: 创建 src/env.d.ts**

```ts
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
```

- [ ] **Step 9: 安装依赖并验证**

Run: `cd cmdb-ui-vue3 && pnpm install`
Expected: 依赖安装成功，无 peer 依赖报错。

- [ ] **Step 10: Commit**

```bash
cd /home/abelit/Documents/code/github/AIOpsNexusNova-CMDB
git add cmdb-ui-vue3
git commit -m "chore(ui): scaffold cmdb-ui-vue3 with vite + vue3 + typescript"
```

---

### Task 2: Lint 与格式化配置

**Files:**
- Create: `cmdb-ui-vue3/eslint.config.js`
- Create: `cmdb-ui-vue3/.prettierrc`

- [ ] **Step 1: 创建 eslint.config.js**

```js
import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'
import prettier from 'eslint-config-prettier'

export default [
  { ignores: ['dist/**', 'node_modules/**'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: { parser: tseslint.parser },
    },
  },
  {
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      'vue/multi-word-component-names': 'off',
    },
  },
  prettier,
]
```

- [ ] **Step 2: 创建 .prettierrc**

```json
{
  "semi": false,
  "singleQuote": true,
  "printWidth": 100,
  "trailingComma": "es5"
}
```

- [ ] **Step 3: Commit**

```bash
git add cmdb-ui-vue3/eslint.config.js cmdb-ui-vue3/.prettierrc
git commit -m "chore(ui): add eslint flat config and prettier"
```

---

## Phase 1：主题纯逻辑（TDD）

### Task 3: resolveTheme / getSystemDark（TDD）

**Files:**
- Create: `cmdb-ui-vue3/src/theme/tokens.ts`
- Create: `cmdb-ui-vue3/src/theme/resolveTheme.ts`
- Test: `cmdb-ui-vue3/src/__tests__/resolveTheme.spec.ts`

- [ ] **Step 1: 写失败测试**

```ts
// src/__tests__/resolveTheme.spec.ts
import { describe, it, expect, vi, afterEach } from 'vitest'
import { resolveTheme, getSystemDark } from '@/theme/resolveTheme'

describe('resolveTheme', () => {
  it("resolves 'system' to OS preference", () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true }))
    expect(resolveTheme('system')).toBe('dark')
    vi.stubGlobal('matchMedia', () => ({ matches: false }))
    expect(resolveTheme('system')).toBe('light')
  })

  it("resolves 'light' and 'dark' literally", () => {
    expect(resolveTheme('light')).toBe('light')
    expect(resolveTheme('dark')).toBe('dark')
  })

  it('maps unknown/legacy values to dark', () => {
    expect(resolveTheme('liquid-glass')).toBe('dark')
  })
})

describe('getSystemDark', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('returns true when prefers-color-scheme is dark', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true }))
    expect(getSystemDark()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/resolveTheme.spec.ts`
Expected: FAIL（`Cannot find module '@/theme/resolveTheme'`）

- [ ] **Step 3: 创建 tokens.ts 与 resolveTheme.ts**

```ts
// src/theme/tokens.ts
/** 统一主题色（旧版 vue.config.js 中为 #2f54eb）。 */
export const COLOR_PRIMARY = '#2f54eb'
```

```ts
// src/theme/resolveTheme.ts
export type ThemeMode = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

/** 当前系统是否偏好深色。 */
export function getSystemDark(): boolean {
  return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)
}

/**
 * 将用户选择的 themeMode 解析为实际主题：
 * - 'system' → 跟随系统偏好
 * - 'light' → 'light'
 * - 其余（含旧 'liquid-glass' 等）→ 'dark'
 */
export function resolveTheme(mode: ThemeMode): ResolvedTheme {
  if (mode === 'system') return getSystemDark() ? 'dark' : 'light'
  if (mode === 'light') return 'light'
  return 'dark'
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/resolveTheme.spec.ts`
Expected: PASS（4 tests）

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui-vue3/src/theme cmdb-ui-vue3/src/__tests__/resolveTheme.spec.ts
git commit -m "feat(ui): add theme resolution logic (light/dark/system)"
```

---

## Phase 2：配置与类型

### Task 4: 应用配置 + 共享类型

**Files:**
- Create: `cmdb-ui-vue3/src/config/app.ts`
- Create: `cmdb-ui-vue3/src/config/setting.ts`
- Create: `cmdb-ui-vue3/src/types/index.ts`

- [ ] **Step 1: 创建 config/app.ts**

```ts
// src/config/app.ts
export interface AppConfig {
  /** 需要编译/加载的业务模块（shell 阶段为空，后续加 'acl'）。 */
  buildModules: string[]
  /** 首页重定向路径。 */
  redirectTo: string
}

const appConfig: AppConfig = {
  buildModules: [],
  redirectTo: '/home',
}

export default appConfig
```

- [ ] **Step 2: 创建 config/setting.ts**

```ts
// src/config/setting.ts
import { COLOR_PRIMARY } from '@/theme/tokens'

export interface AppSetting {
  primaryColor: string
  navTheme: 'dark' | 'light'
  themeMode: 'light' | 'dark' | 'system'
  layout: 'sidemenu' | 'topmenu'
  contentWidth: 'Fluid' | 'Fixed'
  fixedHeader: boolean
  fixSiderbar: boolean
  autoHideHeader: boolean
  colorWeak: boolean
  multiTab: boolean
}

const setting: AppSetting = {
  primaryColor: COLOR_PRIMARY,
  navTheme: 'dark',
  themeMode: 'system',
  layout: 'sidemenu',
  contentWidth: 'Fixed',
  fixedHeader: true,
  fixSiderbar: true,
  autoHideHeader: true,
  colorWeak: false,
  multiTab: false,
}

export default setting
```

- [ ] **Step 3: 创建 types/index.ts**

```ts
// src/types/index.ts

/** 权限点（含 actionEntitySet 与展开后的 actionList）。 */
export interface Permission {
  id: number
  name: string
  actionEntitySet?: { action: string }[]
  actionList?: string[]
  [key: string]: unknown
}

export interface Role {
  id?: number
  name?: string
  permissions?: Permission[]
  [key: string]: unknown
}

/** getInfo 返回的 result 字段。 */
export interface UserInfoResult {
  name: string
  avatar?: string
  uid: number
  rid: number
  username: string
  role: Role
  [key: string]: unknown
}

export interface GetInfoResponse {
  result: UserInfoResult
}

export interface LoginResponse {
  token: string
}

export interface AuthEnableItem {
  auth_type: string
  [key: string]: unknown
}

export interface AuthEnableResponse {
  enable_list: AuthEnableItem[]
}

export interface Employee {
  employee_id?: number
  name?: string
  mobile?: string
  department_id?: number
  email?: string
  [key: string]: unknown
}

export interface Department {
  department_id?: number
  department_name?: string
  [key: string]: unknown
}
```

- [ ] **Step 4: 类型检查**

Run: `cd cmdb-ui-vue3 && pnpm typecheck`
Expected: 通过（或仅有后续待创建文件的引用报错，当前无）。

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui-vue3/src/config cmdb-ui-vue3/src/types
git commit -m "feat(ui): add app config, setting and shared types"
```

---

## Phase 3：请求层（TDD 于纯函数）

### Task 5: axios 实例 + 拦截器 + 纯函数

**Files:**
- Create: `cmdb-ui-vue3/src/utils/request.ts`
- Test: `cmdb-ui-vue3/src/__tests__/request.spec.ts`

- [ ] **Step 1: 写失败测试（针对纯函数）**

```ts
// src/__tests__/request.spec.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { extractErrorMessage, getAccessToken, TOKEN_KEY } from '@/utils/request'

describe('getAccessToken', () => {
  beforeEach(() => localStorage.clear())

  it('returns token from localStorage', () => {
    localStorage.setItem(TOKEN_KEY, 'abc123')
    expect(getAccessToken()).toBe('abc123')
  })

  it('returns null when absent', () => {
    expect(getAccessToken()).toBeNull()
  })
})

describe('extractErrorMessage', () => {
  it('prefers server-provided message', () => {
    const err = { response: { data: { message: 'server said no' } } }
    expect(extractErrorMessage(err, 'fallback')).toBe('server said no')
  })

  it('falls back when no message', () => {
    const err = { response: { data: {} } }
    expect(extractErrorMessage(err, 'fallback')).toBe('fallback')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/request.spec.ts`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 创建 utils/request.ts**

```ts
// src/utils/request.ts
import axios, { type AxiosError } from 'axios'
import { message, notification } from 'ant-design-vue'
import i18n from '@/lang'

export const TOKEN_KEY = 'pro__Access-Token'

/** 从 localStorage 读取鉴权 token（与旧 vue-ls 的 pro__ 命名空间一致）。 */
export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

/** 提取错误描述：优先服务端 message，否则回退到 fallbackKey 的 i18n 文案。 */
export function extractErrorMessage(error: unknown, fallbackKey: string): string {
  const data = (error as AxiosError)?.response?.data as { message?: string } | undefined
  return data?.message || i18n.global.t(fallbackKey)
}

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 6000,
  withCredentials: true,
})

// 请求拦截器：附加 Access-Token 与 Accept-Language
service.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers['Access-Token'] = token
  }
  config.headers['Accept-Language'] = localStorage.getItem('ops_locale') || 'zh'
  return config
})

// 响应拦截器：解包 response.data
service.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError) => {
    const status = error.response?.status
    if (status && /^5\d{2}$/.test(String(status))) {
      message.error(extractErrorMessage(error, 'requestServiceError'))
    } else if (status === 412) {
      notification.warning({
        key: 'rate-limit',
        message: 'WARNING',
        description: i18n.global.t('requestWait', { time: 5 }),
        duration: 5,
      })
    } else if ((error.config as { isShowMessage?: boolean })?.isShowMessage === false) {
      // 静默：调用方显式关闭错误提示
    } else {
      message.error(extractErrorMessage(error, 'requestError'))
    }
    return Promise.reject(error)
  }
)

export default service
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/request.spec.ts`
Expected: PASS（4 tests）。若 `@/lang` 尚未创建导致导入失败，先按 Task 13 创建最小 `lang/index.ts`（含 `requestServiceError`/`requestError`/`requestWait` 文案）再重跑。

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui-vue3/src/utils/request.ts cmdb-ui-vue3/src/__tests__/request.spec.ts
git commit -m "feat(ui): add axios request layer with auth token and error handling"
```

---

## Phase 4：API 客户端

### Task 6: 类型化 API 客户端

**Files:**
- Create: `cmdb-ui-vue3/src/api/login.ts`
- Create: `cmdb-ui-vue3/src/api/auth.ts`
- Create: `cmdb-ui-vue3/src/api/employee.ts`
- Create: `cmdb-ui-vue3/src/api/company.ts`

- [ ] **Step 1: 创建 api/login.ts**

```ts
// src/api/login.ts
import request from '@/utils/request'
import type { GetInfoResponse, LoginResponse } from '@/types'

export function login(data: { username: string; password: string; remember_me?: boolean }) {
  return request.post<unknown, LoginResponse>('/v1/acl/login', data)
}

export function getInfo() {
  return request.get<unknown, GetInfoResponse>('/v1/acl/users/info')
}

export function logout() {
  const authType = localStorage.getItem('ops_auth_type')
  const url = authType ? `/${authType.toLowerCase()}/logout` : '/v1/acl/logout'
  return authType ? request.get(url) : request.post(url)
}

export function getAllUsers(params: Record<string, unknown>) {
  return request.get('/v1/acl/users', { params })
}
```

- [ ] **Step 2: 创建 api/auth.ts**

```ts
// src/api/auth.ts
import request from '@/utils/request'
import type { AuthEnableResponse } from '@/types'

export function getAuthDataEnable() {
  return request.get<unknown, AuthEnableResponse>('/common-setting/v1/auth_config/enable_list')
}
```

- [ ] **Step 3: 创建 api/employee.ts**

```ts
// src/api/employee.ts
import request from '@/utils/request'
import type { Employee } from '@/types'

export function getEmployeeList(params: Record<string, unknown>) {
  return request.get('/common-setting/v1/employee', { params })
}

export function getEmployeeByUid(uid: number) {
  return request.get<unknown, Employee>(`/common-setting/v1/employee/by_uid/${uid}`)
}
```

- [ ] **Step 4: 创建 api/company.ts**

```ts
// src/api/company.ts
import request from '@/utils/request'
import type { Department } from '@/types'

export function getAllDepartmentList(params: Record<string, unknown>) {
  return request.get<unknown, Department[]>('/common-setting/v1/department/all', { params })
}
```

- [ ] **Step 5: 类型检查**

Run: `cd cmdb-ui-vue3 && pnpm typecheck`
Expected: 通过。

- [ ] **Step 6: Commit**

```bash
git add cmdb-ui-vue3/src/api
git commit -m "feat(ui): add typed api clients (login/auth/employee/company)"
```

---

## Phase 5：Pinia Stores（TDD）

### Task 7: 路由过滤纯函数（TDD）

> 先做可测的路由过滤逻辑，供 `stores/routes.ts` 使用。

**Files:**
- Create: `cmdb-ui-vue3/src/stores/routeFilter.ts`
- Test: `cmdb-ui-vue3/src/__tests__/routes.spec.ts`

- [ ] **Step 1: 写失败测试**

```ts
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/routes.spec.ts`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 创建 stores/routeFilter.ts**

```ts
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
  return routes.filter((route) => {
    const required = route.meta?.permission
    if (required && required.length > 0 && !required.some((p) => permissions.includes(p))) {
      return false
    }
    if (route.children && route.children.length > 0) {
      route.children = filterAsyncRoutes(route.children, permissions)
    }
    return true
  })
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/routes.spec.ts`
Expected: PASS（3 tests）

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui-vue3/src/stores/routeFilter.ts cmdb-ui-vue3/src/__tests__/routes.spec.ts
git commit -m "feat(ui): add permission-based route filtering"
```

---

### Task 8: app store（主题模式，TDD）

**Files:**
- Create: `cmdb-ui-vue3/src/stores/index.ts`
- Create: `cmdb-ui-vue3/src/stores/app.ts`
- Test: `cmdb-ui-vue3/src/__tests__/appStore.spec.ts`

- [ ] **Step 1: 创建 stores/index.ts（pinia 实例 + 插件）**

```ts
// src/stores/index.ts
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

export default pinia
```

- [ ] **Step 2: 写失败测试**

```ts
// src/__tests__/appStore.spec.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from '@/stores/app'

describe('useAppStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('defaults themeMode to system', () => {
    const store = useAppStore()
    expect(store.themeMode).toBe('system')
  })

  it('setThemeMode updates themeMode and resolvedTheme', () => {
    const store = useAppStore()
    store.setThemeMode('dark')
    expect(store.themeMode).toBe('dark')
    expect(store.resolvedTheme).toBe('dark')
  })
})
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/appStore.spec.ts`
Expected: FAIL（`@/stores/app` 不存在）

- [ ] **Step 4: 创建 stores/app.ts**

```ts
// src/stores/app.ts
import { defineStore } from 'pinia'
import { resolveTheme, type ThemeMode, type ResolvedTheme } from '@/theme/resolveTheme'
import setting from '@/config/setting'

interface AppState {
  themeMode: ThemeMode
  sidebar: boolean
  layout: 'sidemenu' | 'topmenu'
  fixedHeader: boolean
  fixSiderbar: boolean
  contentWidth: 'Fluid' | 'Fixed'
  colorWeak: boolean
  multiTab: boolean
}

export const useAppStore = defineStore('app', {
  state: (): AppState => ({
    themeMode: setting.themeMode,
    sidebar: true,
    layout: setting.layout,
    fixedHeader: setting.fixedHeader,
    fixSiderbar: setting.fixSiderbar,
    contentWidth: setting.contentWidth,
    colorWeak: setting.colorWeak,
    multiTab: setting.multiTab,
  }),
  getters: {
    resolvedTheme(state): ResolvedTheme {
      return resolveTheme(state.themeMode)
    },
  },
  actions: {
    setThemeMode(mode: ThemeMode) {
      this.themeMode = mode
    },
    toggleSidebar() {
      this.sidebar = !this.sidebar
    },
  },
  persist: {
    key: 'pro__app',
    pick: ['themeMode', 'sidebar', 'layout', 'fixedHeader', 'fixSiderbar', 'contentWidth', 'colorWeak', 'multiTab'],
  },
})
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/appStore.spec.ts`
Expected: PASS（2 tests）

- [ ] **Step 6: Commit**

```bash
git add cmdb-ui-vue3/src/stores/index.ts cmdb-ui-vue3/src/stores/app.ts cmdb-ui-vue3/src/__tests__/appStore.spec.ts
git commit -m "feat(ui): add app store with theme mode"
```

---

### Task 9: user store（login/getInfo/logout，TDD）

**Files:**
- Create: `cmdb-ui-vue3/src/stores/user.ts`
- Test: `cmdb-ui-vue3/src/__tests__/userStore.spec.ts`

- [ ] **Step 1: 写失败测试（mock API）**

```ts
// src/__tests__/userStore.spec.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'
import { TOKEN_KEY } from '@/utils/request'

vi.mock('@/api/login', () => ({
  login: vi.fn(async () => ({ token: 'tok-1' })),
  getInfo: vi.fn(async () => ({ result: { name: 'Alice', uid: 1, rid: 1, username: 'alice', role: {} } })),
  logout: vi.fn(async () => undefined),
}))

describe('useUserStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('login stores token to state and localStorage', async () => {
    const store = useUserStore()
    await store.login({ username: 'alice', password: 'x' })
    expect(store.token).toBe('tok-1')
    expect(localStorage.getItem(TOKEN_KEY)).toBe('tok-1')
  })

  it('logout clears token', async () => {
    const store = useUserStore()
    await store.login({ username: 'alice', password: 'x' })
    await store.logout()
    expect(store.token).toBe('')
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/userStore.spec.ts`
Expected: FAIL（`@/stores/user` 不存在）

- [ ] **Step 3: 创建 stores/user.ts**

```ts
// src/stores/user.ts
import { defineStore } from 'pinia'
import { login as apiLogin, getInfo as apiGetInfo, logout as apiLogout, getAllUsers } from '@/api/login'
import { getEmployeeByUid, getEmployeeList } from '@/api/employee'
import { getAllDepartmentList } from '@/api/company'
import { getAuthDataEnable } from '@/api/auth'
import { TOKEN_KEY } from '@/utils/request'
import type { Role, UserInfoResult, AuthEnableResponse } from '@/types'

interface UserState {
  token: string
  name: string
  avatar: string
  uid: number
  rid: number
  username: string
  roles: Role
  info: Partial<UserInfoResult>
  allUsers: unknown[]
  allEmployees: unknown[]
  allDepartments: unknown[]
  authEnable: AuthEnableResponse | null
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: '',
    name: '',
    avatar: '',
    uid: 0,
    rid: 0,
    username: '',
    roles: {},
    info: {},
    allUsers: [],
    allEmployees: [],
    allDepartments: [],
    authEnable: null,
  }),
  getters: {
    isAuthed: (state) => !!state.token,
  },
  actions: {
    async login(userInfo: { username: string; password: string; remember_me?: boolean }) {
      const res = await apiLogin(userInfo)
      this.token = res.token
      localStorage.setItem(TOKEN_KEY, res.token)
    },
    async getInfo() {
      const res = await apiGetInfo()
      const result = res.result
      this.roles = result.role
      this.info = result
      this.name = result.name
      this.avatar = result.avatar || ''
      this.uid = result.uid
      this.rid = result.rid
      this.username = result.username
      try {
        const emp = await getEmployeeByUid(result.uid)
        this.info = { ...this.info, ...emp }
      } catch {
        // 员工信息为可选增强，失败不阻断
      }
      return res
    },
    async logout() {
      try {
        await apiLogout()
      } catch {
        // 登出失败也继续清理本地状态
      }
      this.token = ''
      localStorage.removeItem(TOKEN_KEY)
    },
    async fetchAuthDataEnable() {
      this.authEnable = await getAuthDataEnable()
    },
    async loadAllUsers() {
      const res = (await getAllUsers({ page_size: 9999 })) as { users: unknown[] }
      this.allUsers = res.users
    },
    async loadAllEmployees() {
      const res = (await getEmployeeList({ page_size: 99999 })) as { data_list: unknown[] }
      this.allEmployees = res.data_list
    },
    async loadAllDepartments() {
      this.allDepartments = await getAllDepartmentList({ is_tree: 0 })
    },
  },
  persist: {
    key: 'pro__user',
    pick: ['name', 'avatar', 'uid', 'rid', 'username', 'roles', 'info'],
  },
})
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/userStore.spec.ts`
Expected: PASS（2 tests）

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui-vue3/src/stores/user.ts cmdb-ui-vue3/src/__tests__/userStore.spec.ts
git commit -m "feat(ui): add user store with login/logout and profile loading"
```

---

### Task 10: routes store

**Files:**
- Create: `cmdb-ui-vue3/src/stores/routes.ts`

- [ ] **Step 1: 创建 stores/routes.ts**

```ts
// src/stores/routes.ts
import { defineStore } from 'pinia'
import { constantRouterMap } from '@/router/constant'
import { filterAsyncRoutes, type AppRouteRecord } from './routeFilter'

interface RoutesState {
  appRoutes: AppRouteRecord[]
}

export const useRoutesStore = defineStore('routes', {
  state: (): RoutesState => ({
    appRoutes: [],
  }),
  actions: {
    /** 由登录用户的权限动态生成可访问路由。 */
    generateRoutes(permissions: string[]) {
      const dynamic = filterAsyncRoutes([...constantRouterMap], permissions)
      this.appRoutes = dynamic
      return dynamic
    },
    reset() {
      this.appRoutes = []
    },
  },
})
```

- [ ] **Step 2: 类型检查**

Run: `cd cmdb-ui-vue3 && pnpm typecheck`
Expected: 通过（需先有 `@/router/constant`，见 Task 11；若缺失先创建之）。

- [ ] **Step 3: Commit**

```bash
git add cmdb-ui-vue3/src/stores/routes.ts
git commit -m "feat(ui): add routes store with dynamic route generation"
```

---

## Phase 6：路由与守卫

### Task 11: 常量路由 + router 实例

**Files:**
- Create: `cmdb-ui-vue3/src/router/constant.ts`
- Create: `cmdb-ui-vue3/src/router/index.ts`

- [ ] **Step 1: 创建 router/constant.ts**

```ts
// src/router/constant.ts
import type { AppRouteRecord } from '@/stores/routeFilter'

export const constantRouterMap: AppRouteRecord[] = [
  { path: '/', redirect: '/home' },
  {
    path: '/user/login',
    name: 'login',
    component: () => import('@/views/user/Login.vue'),
    meta: { hidden: true },
  },
  {
    path: '/user/logout',
    name: 'logout',
    component: () => import('@/views/user/Logout.vue'),
    meta: { hidden: true },
  },
  {
    path: '/home',
    name: 'home',
    component: () => import('@/layouts/BasicLayout.vue'),
    children: [
      {
        path: '',
        name: 'home_index',
        component: () => import('@/views/home/index.vue'),
        meta: { title: 'Home' },
      },
    ],
  },
  {
    path: '/404',
    name: 'not_found',
    component: () => import('@/views/exception/404.vue'),
    meta: { hidden: true },
  },
  { path: '/:pathMatch(.*)*', redirect: '/404', meta: { hidden: true } },
]
```

- [ ] **Step 2: 创建 router/index.ts**

```ts
// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { constantRouterMap } from './constant'

function createAppRouter() {
  return createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    scrollBehavior: () => ({ top: 0 }),
    routes: constantRouterMap as never,
  })
}

export const router = createAppRouter()

export function resetRouter() {
  const fresh = createAppRouter()
  router.options.routes = fresh.options.routes
}
```

- [ ] **Step 3: Commit**

```bash
git add cmdb-ui-vue3/src/router/constant.ts cmdb-ui-vue3/src/router/index.ts
git commit -m "feat(ui): add constant routes and router instance"
```

---

### Task 12: 导航守卫 + 模块加载器

**Files:**
- Create: `cmdb-ui-vue3/src/router/guard.ts`
- Create: `cmdb-ui-vue3/src/modules/index.ts`

- [ ] **Step 1: 创建 modules/index.ts（外壳阶段为空清单）**

```ts
// src/modules/index.ts
import type { Router } from 'vue-router'
import type { I18n } from 'vue-i18n'

export interface ModuleManifest {
  name: string
  routes: unknown[]
  locales?: Record<string, unknown>
}

/**
 * 加载业务模块清单并装配路由与 i18n。
 * shell 阶段清单为空；acl/cmdb 迁移时在此追加注册。
 */
export async function loadModules(_router: Router, _i18n: I18n) {
  // TODO(acl): register module manifests here
}
```

- [ ] **Step 2: 创建 router/guard.ts**

```ts
// src/router/guard.ts
import type { Router } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { useUserStore } from '@/stores/user'
import { useRoutesStore } from '@/stores/routes'
import { TOKEN_KEY } from '@/utils/request'
import { setDocumentTitle } from '@/utils/dom'

NProgress.configure({ showSpinner: false })

const whiteList = ['/user/login', '/user/logout', '/user/register']

export function setupRouterGuard(router: Router) {
  router.beforeEach(async (to, _from, next) => {
    NProgress.start()
    if (to.meta?.title) {
      setDocumentTitle(to.meta.title as string)
    }

    const userStore = useUserStore()
    const routesStore = useRoutesStore()
    const token = localStorage.getItem(TOKEN_KEY)

    if (whiteList.includes(to.path)) {
      return next()
    }

    if (token && !userStore.isAuthed) {
      try {
        await userStore.getInfo()
        await userStore.fetchAuthDataEnable()
        const permissions = userStore.roles.permissions?.map((p) => p.name) ?? []
        const dynamic = routesStore.generateRoutes(permissions)
        dynamic.forEach((r) => router.addRoute(r as never))
        return next({ ...to, replace: true })
      } catch {
        await userStore.logout()
        return next({ path: '/user/login', query: { redirect: to.fullPath } })
      }
    }

    if (!token) {
      return next({ path: '/user/login', query: { redirect: to.fullPath } })
    }

    next()
  })

  router.afterEach(() => NProgress.done())
}
```

- [ ] **Step 3: 创建 utils/dom.ts（守卫依赖）**

```ts
// src/utils/dom.ts
export const domTitle = 'CMDB'

export function setDocumentTitle(title: string) {
  document.title = `${title} - ${domTitle}`
}
```

- [ ] **Step 4: 类型检查**

Run: `cd cmdb-ui-vue3 && pnpm typecheck`
Expected: 通过（或仅有尚未创建的视图/布局引用报错，后续 Task 补齐后通过）。

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui-vue3/src/router/guard.ts cmdb-ui-vue3/src/modules/index.ts cmdb-ui-vue3/src/utils/dom.ts
git commit -m "feat(ui): add navigation guard and module loader"
```

---

## Phase 7：布局

### Task 13: 布局组件

**Files:**
- Create: `cmdb-ui-vue3/src/layouts/BlankLayout.vue`
- Create: `cmdb-ui-vue3/src/layouts/RouteView.vue`
- Create: `cmdb-ui-vue3/src/layouts/PageView.vue`
- Create: `cmdb-ui-vue3/src/layouts/UserLayout.vue`
- Create: `cmdb-ui-vue3/src/layouts/BasicLayout.vue`

- [ ] **Step 1: 创建 BlankLayout.vue**

```vue
<template>
  <router-view />
</template>
```

- [ ] **Step 2: 创建 RouteView.vue**

```vue
<template>
  <router-view />
</template>
```

- [ ] **Step 3: 创建 PageView.vue**

```vue
<script setup lang="ts"></script>

<template>
  <router-view v-slot="{ Component }">
    <keep-alive>
      <component :is="Component" />
    </keep-alive>
  </router-view>
</template>
```

- [ ] **Step 4: 创建 UserLayout.vue**

```vue
<script setup lang="ts"></script>

<template>
  <div class="user-layout">
    <router-view />
  </div>
</template>

<style scoped>
.user-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}
</style>
```

- [ ] **Step 5: 创建 BasicLayout.vue（Header + Sider + Content）**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Layout, Menu, Dropdown, Avatar } from 'ant-design-vue'
import { LogoutOutlined, UserOutlined } from '@ant-design/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { useRoutesStore } from '@/stores/routes'

const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()
const routesStore = useRoutesStore()

const menuItems = computed(() =>
  routesStore.appRoutes
    .filter((r) => r.children && r.children.length)
    .map((r) => ({
      key: r.path,
      label: (r.meta?.title as string) || r.name,
      children: (r.children || [])
        .filter((c) => !c.meta?.hidden)
        .map((c) => ({ key: c.path, label: (c.meta?.title as string) || c.name })),
    }))
)

const themeLabel = computed(() => {
  if (appStore.themeMode === 'system') return 'System'
  return appStore.themeMode === 'dark' ? 'Dark' : 'Light'
})

function onMenuClick({ key }: { key: string }) {
  router.push(key)
}

function cycleTheme() {
  const order = ['light', 'dark', 'system'] as const
  const idx = order.indexOf(appStore.themeMode)
  appStore.setThemeMode(order[(idx + 1) % order.length])
}

function onLogout() {
  router.push('/user/logout')
}
</script>

<template>
  <Layout class="basic-layout">
    <Layout.Sider :theme="appStore.themeMode === 'dark' ? 'dark' : 'light'" width="220">
      <div class="logo">CMDB</div>
      <Menu
        theme="dark"
        mode="inline"
        :selected-keys="[router.currentRoute.value.path]"
        :items="menuItems"
        @click="onMenuClick"
      />
    </Layout.Sider>
    <Layout>
      <Layout.Header class="header">
        <button class="theme-toggle" @click="cycleTheme">{{ themeLabel }}</button>
        <Dropdown>
          <span class="user">
            <Avatar size="small" :icon="h(UserOutlined)" />
            <span class="name">{{ userStore.name || userStore.username }}</span>
          </span>
          <template #overlay>
            <Menu @click="onLogout">
              <Menu.Item key="logout">
                <LogoutOutlined /> Logout
              </Menu.Item>
            </Menu>
          </template>
        </Dropdown>
      </Layout.Header>
      <Layout.Content class="content">
        <router-view />
      </Layout.Content>
    </Layout>
  </Layout>
</template>

<style scoped>
.basic-layout {
  min-height: 100vh;
}
.logo {
  height: 32px;
  margin: 16px;
  color: #fff;
  font-weight: 600;
  text-align: center;
  line-height: 32px;
}
.header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  background: #fff;
  padding: 0 16px;
}
.theme-toggle {
  cursor: pointer;
}
.user {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.content {
  padding: 16px;
}
</style>
```

> 说明：`h(UserOutlined)` 需要 `import { h } from 'vue'`。请在本文件 script 顶部补 `import { h } from 'vue'`（与 `computed` 同源导入）。

- [ ] **Step 6: 类型检查**

Run: `cd cmdb-ui-vue3 && pnpm typecheck`
Expected: 通过（视图尚未创建时会有 import 报错，待 Task 15 补齐后通过）。

- [ ] **Step 7: Commit**

```bash
git add cmdb-ui-vue3/src/layouts
git commit -m "feat(ui): add basic/user/blank/page layouts"
```

---

## Phase 8：i18n

### Task 14: vue-i18n 装配

**Files:**
- Create: `cmdb-ui-vue3/src/lang/zh.ts`
- Create: `cmdb-ui-vue3/src/lang/en.ts`
- Create: `cmdb-ui-vue3/src/lang/index.ts`

- [ ] **Step 1: 创建 lang/zh.ts**

```ts
// src/lang/zh.ts
export default {
  requestServiceError: '服务端错误，请稍后重试',
  requestError: '请求错误，请稍后重试',
  requestWait: '请求过于频繁，请 {time} 秒后重试',
  menu: {
    home: '首页',
  },
}
```

- [ ] **Step 2: 创建 lang/en.ts**

```ts
// src/lang/en.ts
export default {
  requestServiceError: 'Server error, please try again later',
  requestError: 'Request error, please try again later',
  requestWait: 'Too many requests, please retry in {time}s',
  menu: {
    home: 'Home',
  },
}
```

- [ ] **Step 3: 创建 lang/index.ts**

```ts
// src/lang/index.ts
import { createI18n } from 'vue-i18n'
import zh from './zh'
import en from './en'

const saved = localStorage.getItem('ops_locale') || 'zh'

const i18n = createI18n({
  legacy: false,
  locale: saved,
  fallbackLocale: 'zh',
  messages: { zh, en },
  silentTranslationWarn: true,
})

export default i18n
```

- [ ] **Step 4: Commit**

```bash
git add cmdb-ui-vue3/src/lang
git commit -m "feat(ui): add vue-i18n setup with zh/en messages"
```

---

## Phase 9：指令

### Task 15: v-action 权限指令

**Files:**
- Create: `cmdb-ui-vue3/src/directives/action.ts`

- [ ] **Step 1: 创建 directives/action.ts**

```ts
// src/directives/action.ts
import type { App, Directive } from 'vue'
import { useUserStore } from '@/stores/user'

function hasAction(el: HTMLElement, value: unknown): boolean {
  if (value === undefined || value === null || value === '') return true
  const userStore = useUserStore()
  const permissions = userStore.roles.permissions?.map((p) => p.name) ?? []
  const required = Array.isArray(value) ? value : [value]
  return required.some((p) => permissions.includes(String(p)))
}

const actionDirective: Directive = {
  mounted(el, binding) {
    if (!hasAction(el, binding.value)) {
      el.parentNode?.removeChild(el)
    }
  },
}

export function setupActionDirective(app: App) {
  app.directive('action', actionDirective)
}
```

- [ ] **Step 2: Commit**

```bash
git add cmdb-ui-vue3/src/directives/action.ts
git commit -m "feat(ui): add v-action permission directive"
```

---

## Phase 10：视图

### Task 16: 登录/登出/首页/404

**Files:**
- Create: `cmdb-ui-vue3/src/views/user/Login.vue`
- Create: `cmdb-ui-vue3/src/views/user/Logout.vue`
- Create: `cmdb-ui-vue3/src/views/home/index.vue`
- Create: `cmdb-ui-vue3/src/views/exception/404.vue`

- [ ] **Step 1: 创建 Login.vue**

```vue
<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Form, Input, Button, message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)

const form = reactive({ username: '', password: '' })

async function onSubmit() {
  if (!form.username || !form.password) {
    message.error('Please enter username and password')
    return
  }
  loading.value = true
  try {
    await userStore.login({ username: form.username, password: form.password })
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (e) {
    // 错误提示由 request 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login">
    <a-card title="Login" style="width: 360px">
      <a-form layout="vertical" @submit.prevent="onSubmit">
        <a-form-item>
          <a-input v-model:value="form.username" size="large" placeholder="Username">
            <template #prefix><UserOutlined /></template>
          </a-input>
        </a-form-item>
        <a-form-item>
          <a-input-password v-model:value="form.password" size="large" placeholder="Password">
            <template #prefix><LockOutlined /></template>
          </a-input-password>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit" size="large" block :loading="loading">
            Login
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<style scoped>
.login {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
```

> 说明：`a-*` 组件依赖全局 `app.use(Antd)`（Task 17 装配）；`Input`/`Button`/`Form` 的显式 import 用于类型与局部注册可省略，此处仅保留 `message` 使用。

- [ ] **Step 2: 创建 Logout.vue**

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

onMounted(async () => {
  await userStore.logout()
  router.replace('/user/login')
})
</script>

<template>
  <div />
</template>
```

- [ ] **Step 3: 创建 home/index.vue**

```vue
<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div>{{ t('menu.home') }}</div>
</template>
```

- [ ] **Step 4: 创建 exception/404.vue**

```vue
<template>
  <a-result status="404" title="404" sub-title="Page not found">
    <template #extra>
      <a-button type="primary" @click="$router.push('/')">Back Home</a-button>
    </template>
  </a-result>
</template>
```

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui-vue3/src/views
git commit -m "feat(ui): add login/logout/home/404 views"
```

---

## Phase 11：装配

### Task 17: main.ts + App.vue + 主题 Provider

**Files:**
- Create: `cmdb-ui-vue3/src/theme/useTheme.ts`
- Create: `cmdb-ui-vue3/src/App.vue`
- Create: `cmdb-ui-vue3/src/main.ts`

- [ ] **Step 1: 创建 theme/useTheme.ts**

```ts
// src/theme/useTheme.ts
import { computed } from 'vue'
import { theme as antdTheme } from 'ant-design-vue'
import { useAppStore } from '@/stores/app'
import { COLOR_PRIMARY } from './tokens'

/** 提供响应式的 antd 主题配置（明/暗算法 + 主题色 token）。 */
export function useTheme() {
  const appStore = useAppStore()
  const themeConfig = computed(() => ({
    algorithm: appStore.resolvedTheme === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
    token: { colorPrimary: COLOR_PRIMARY },
  }))
  return { themeConfig }
}
```

- [ ] **Step 2: 创建 App.vue**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { ConfigProvider } from 'ant-design-vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import enUS from 'ant-design-vue/es/locale/en_US'
import { useI18n } from 'vue-i18n'
import { useTheme } from '@/theme/useTheme'

const { locale } = useI18n()
const { themeConfig } = useTheme()

const antdLocale = computed(() => (locale.value === 'en' ? enUS : zhCN))
</script>

<template>
  <ConfigProvider :theme="themeConfig" :locale="antdLocale">
    <router-view />
  </ConfigProvider>
</template>
```

- [ ] **Step 3: 创建 main.ts**

```ts
// src/main.ts
import { createApp } from 'vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import App from './App.vue'
import pinia from '@/stores'
import { router } from '@/router'
import i18n from '@/lang'
import { setupRouterGuard } from '@/router/guard'
import { setupActionDirective } from '@/directives/action'
import { loadModules } from '@/modules'

async function bootstrap() {
  const app = createApp(App)

  app.use(pinia)
  app.use(router)
  app.use(i18n)
  app.use(Antd)

  setupActionDirective(app)

  await loadModules(router, i18n)
  setupRouterGuard(router)

  app.mount('#app')
}

bootstrap()
```

- [ ] **Step 4: 冒烟测试（App 可挂载）**

创建 `src/__tests__/app.spec.ts`：

```ts
// src/__tests__/app.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '@/App.vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { createRouter, createMemoryHistory } from 'vue-router'

describe('App', () => {
  it('mounts without error', () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [] })
    const i18n = createI18n({ legacy: false, messages: { zh: {}, en: {} } })
    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), router, i18n],
        stubs: { 'router-view': true, 'a-config-provider': true },
      },
    })
    expect(wrapper.exists()).toBe(true)
  })
})
```

Run: `cd cmdb-ui-vue3 && pnpm vitest run src/__tests__/app.spec.ts`
Expected: PASS（1 test）

- [ ] **Step 5: 类型检查 + 构建**

Run: `cd cmdb-ui-vue3 && pnpm typecheck && pnpm build`
Expected: 类型检查通过；构建产出 `dist/`。

- [ ] **Step 6: Commit**

```bash
git add cmdb-ui-vue3/src/main.ts cmdb-ui-vue3/src/App.vue cmdb-ui-vue3/src/theme/useTheme.ts cmdb-ui-vue3/src/__tests__/app.spec.ts
git commit -m "feat(ui): wire app entry with theme provider and config provider"
```

---

## Phase 12：整体验证

### Task 18: 全量验证与收尾

- [ ] **Step 1: 类型检查**

Run: `cd cmdb-ui-vue3 && pnpm typecheck`
Expected: 无报错。

- [ ] **Step 2: 全量单测**

Run: `cd cmdb-ui-vue3 && pnpm test`
Expected: 全部 PASS（resolveTheme 4 + routes 3 + appStore 2 + userStore 2 + request 4 + app 1）。

- [ ] **Step 3: Lint**

Run: `cd cmdb-ui-vue3 && pnpm lint`
Expected: 无 error（如有可 `pnpm lint:fix` 自动修复）。

- [ ] **Step 4: 生产构建**

Run: `cd cmdb-ui-vue3 && pnpm build`
Expected: `dist/` 产出成功。

- [ ] **Step 5: 开发服务器冒烟**

Run: `cd cmdb-ui-vue3 && pnpm dev`
Expected: 访问 `http://localhost:8001`，未登录跳转 `/user/login`；登录后进入 `/home` 布局，主题切换可用。（需后端 `:5000` 在运行；如无后端，验证到「跳转登录页」即止。）

- [ ] **Step 6: 更新 Makefile 与 dev 脚本（可选，便于统一入口）**

在仓库根 `Makefile` 增加：

```makefile
ui3: ## start new UI dev server (vue3)
	cd cmdb-ui-vue3 && pnpm run dev
.PHONY: ui3
```

- [ ] **Step 7: Commit**

```bash
cd /home/abelit/Documents/code/github/AIOpsNexusNova-CMDB
git add Makefile
git commit -m "chore(ui): add make ui3 target for cmdb-ui-vue3 dev server"
```

---

## 后续（不在本计划）

- **acl 模块迁移 plan**：在此外壳之上，注册 `acl` 模块清单，迁移 36 视图（用户/角色/资源/权限/应用 token/操作历史），引入 vxe-table 4。
- **cmdb 模块迁移**：拆分子域（ci/ci_type/dcim/ipam/discovery/topology 等）逐个 plan，逐一确定 relation-graph/butterfly-dag/monaco 等 Vue3 等价物。
- **共存切换**：nginx 将新应用挂 `/v2` 前缀与旧应用并行，按模块完成度切流。

---

## Self-Review 记录

- **Spec 覆盖**：外壳四类交付物（脚手架 / 核心外壳 / 主题三态 / 工程规范）均有对应 Task；acl 迁移按 spec 明确列为后续 plan（spec 的「首个里程碑」在本计划拆分为「外壳 plan + acl plan」两个可独立交付单元，符合「一个 plan 一个子系统」）。
- **占位符扫描**：无 TBD/TODO/「后续实现」类占位（`modules/index.ts` 内的 TODO 是明确的下阶段注册点，属设计意图而非未决项）。
- **类型一致性**：`resolveTheme`/`getSystemDark`/`filterAsyncRoutes`/`TOKEN_KEY`/`useUserStore`/`useAppStore` 等跨 Task 名称一致；`AppRouteRecord` 统一在 `stores/routeFilter.ts` 定义。
