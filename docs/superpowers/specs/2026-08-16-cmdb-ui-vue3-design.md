# cmdb-ui-vue3 迁移设计（Vue3 + Vite + Pinia + Ant Design Vue 4 + TypeScript）

> 日期：2026-08-16 | 状态：设计完成，待实现
> 关联：[旧前端 cmdb-ui](../../../cmdb-ui)（保持不变）

## 背景

`cmdb-ui` 是 Vue 2.6.11 + Ant Design Vue 1.6.x + Vuex 3 + Vue Router 3 + Webpack(Vue CLI 4) 的大型 SPA，规模约 **349 个 `.vue` 文件 + 170 个 `.js` 文件**，含 `acl`（36 视图）与 `cmdb`（175 视图）两个业务模块。技术栈已老化（Vue 2 已 EOL、axios 0.18、element-ui 2、jquery 混用），需要升级到现代化技术栈。

本次迁移目标：**保持 `cmdb-ui` 原样不动**，在 `cmdb-ui-vue3` 新目录中采用 **Vue 3 + Vite + Pinia + Ant Design Vue 4.x + TypeScript** 重新实现，采用**绞杀者式（strangler-fig）渐进迁移**——新应用与旧应用并行运行，按模块逐个迁移，最终整体切换。

## 目标

- 新应用技术栈：Vue 3 + Vite + Pinia + Ant Design Vue 4.x + TypeScript（strict）
- 旧 `cmdb-ui` 保持不变，继续可部署运行
- 按模块渐进迁移，首个里程碑 = 核心外壳 + `acl` 模块完整迁入
- 后端 API 契约完全复用，无需任何后端改动
- 主题（light / dark / system 三态）用 AntD 4 原生 token 重新实现

## 决策汇总

| 维度 | 决策 |
|------|------|
| 迁移策略 | 绞杀者式渐进迁移（方案 A：干净重写 + 绞杀者） |
| Element UI | 移除，统一用 AntD 4 |
| 数据表格 | 保留 vxe-table 4.x |
| TypeScript | strict + 迁移期允许显式 any / @ts-ignore（逐步收紧） |
| 首个模块 | acl |
| 主题 | 原生 token，继承 light / dark / system 三态 |
| 包管理器 | **pnpm** |
| 主题色默认值 | `#2f54eb`（统一旧版 `#2f54eb` 与 `#6c5ce7` 的分歧） |
| 过渡期部署路径 | 独立前缀（默认 `/v2`），可配置；最终 feature parity 后切换默认入口 |

## 目录结构（cmdb-ui-vue3）

```
cmdb-ui-vue3/
  index.html
  vite.config.ts
  tsconfig.json / tsconfig.node.json
  .env.development / .env.production / .env
  src/
    main.ts                 # 启动：Pinia → Router → i18n → AntD → 主题
    App.vue                 # 根组件（ConfigProvider + locale + theme）
    api/                    # 类型化 API 客户端（按域）
    router/                 # 路由配置 + 导航守卫
    stores/                 # Pinia：app / user / permission / routes / notice / company
    layouts/                # BasicLayout / BlankLayout / PageView / UserLayout
    components/             # 共享组件（typed）
    directives/             # v-action 等权限指令
    composables/            # 组合式函数（替代旧 mixins）
    utils/                  # request.ts / axios / theme.ts / filters
    config/                 # app.ts / setting.ts / theme token
    lang/                   # zh.ts / en.ts（vue-i18n 9）
    types/                  # 全局 TS 类型（API DTO、通用泛型）
    modules/
      acl/                  # 首个参考模块
        index.ts            # 模块清单 { name, routes, locales }
        api/ router/ stores/ views/ components/ constants/ types/
      cmdb/                 # 后续逐子域迁移
```

## 核心外壳（可复用地基）

- **构建**：Vite 5 + `@vitejs/plugin-vue`；`vue-tsc --noEmit` 做类型检查；别名 `@ -> src`；开发代理 `/api -> http://127.0.0.1:5000`，并设置 `X-Real-IP: 127.0.0.1` 请求头以通过后端 IP 白名单认证。
- **入口**：`main.ts` 顺序装配 Pinia → Router → i18n → AntD（`ConfigProvider` + `App` 上下文）→ 主题 → 挂载。
- **布局**：`BasicLayout`（Header + Sider 菜单 + Content + MultiTab）承载侧边栏暗/亮、面包屑、多标签页。
- **路由守卫**：白名单路径（login/logout/SSO）→ 校验 token → 按角色动态 `router.addRoute` 生成菜单/权限路由 → NProgress + 文档标题。

## 模块系统（Vuex 动态注册 → Pinia）

旧版每个模块导出 `{ name, route, store }`，用 `router.addRoutes()` + Vuex `registerModule` 动态装配。新架构简化：

- 每个模块的 `index.ts` 导出 `{ name, routes, locales }`（Pinia store 首次 `useXStore()` 即自动注册，无需显式注册）。
- 启动时 `loadModules()` 遍历模块清单，合并 `routes`（`router.addRoute`）与 `locales`（`i18n.mergeLocaleMessage`）。
- 权限点走 `v-action` 指令 + 后端返回的路由/权限元数据（逻辑对齐旧版，实现换成组合式 + Pinia getter）。

## 跨切面关注点

### 鉴权与请求层
- **请求层**：`axios` 1.x + 拦截器。请求拦截器附加 `Access-Token` 与 `Accept-Language`；响应拦截器自动解包 `response.data`。
- **错误处理**（对齐旧版）：5xx → `message.error`；401 → 跳转登出；412 → 倒计时通知；支持 `isShowMessage:false` 静默。
- **API 客户端**：每域一个模块（`api/login.ts`、`api/acl/*.ts`），函数签名带类型（入参 + 返回 DTO 类型）。

### i18n
- `vue-i18n` 9+（Composition API，关闭 legacy）。`zh` 默认、`en` 保留。
- 全局消息 + 模块消息合并；AntD locale 随语言联动（`ConfigProvider :locale`）。

### 主题（原生 token，三态）
- AntD 4 `ConfigProvider` + cssinjs token；主题色 `theme.token.colorPrimary`（默认 `#2f54eb`）。
- 三态 `light` / `dark` / `system`（`system` 走 `prefers-color-scheme`），暗色用 `theme.darkAlgorithm`。
- 状态持久化到 localStorage，切换即时生效；删除旧的 `webpack-theme-color-replacer` + `scripts/build-theme.js` 方案。

### 状态持久化
- `pinia-plugin-persistedstate` 替代 `vue-ls`（保留 `pro__` 命名空间前缀），持久化 `user`（token/角色）、`app`（主题/布局）等。

## 依赖映射（关键项）

| 旧 | 新 |
|----|----|
| vue 2.6 / vue-router 3 / vuex 3 | vue 3 / vue-router 4 / pinia |
| vue-cli-service + webpack | vite |
| ant-design-vue 1.6 | ant-design-vue 4.x |
| element-ui | **移除** → AntD 4 |
| vxe-table 3.7 | vxe-table 4.x |
| vue-i18n 8 / vue-ls | vue-i18n 9 / pinia-persistedstate |
| axios 0.18 / jquery | axios 1.x / **移除 jquery** |
| moment | dayjs（AntD 4 默认） |

> `relation-graph` / `butterfly-dag` / `viser-vue` / `monaco` / `@wangeditor` / `vue-treeselect` / `echarts` 等主要属于 `cmdb` 模块，**推迟到 cmdb 迁移阶段**再逐一确定 Vue3 等价物；首个里程碑不依赖它们。

## 首个里程碑交付物（外壳 + acl）

1. Vite dev server + 生产构建可运行。
2. 核心外壳：`App.vue` + `ConfigProvider`(主题/locale) + `BasicLayout` + 路由守卫 + 请求层 + 登录/登出 + `user`/`permission` store + `v-action` 指令。
3. `acl` 模块完整迁入（36 视图 → 类型化、Pinia、AntD4 表单/表格、vxe-table 4）：用户、角色（层级）、资源、权限 CRUD、应用 token、操作历史等。
4. 工程规范落地：ESLint + Prettier、`vue-tsc` 类型检查、Vitest 单测骨架、pnpm 脚本。

## 共存与切换（绞杀者机制）

- **开发期**：两个独立 dev server（旧 `:8000`、新 `:8001`），各自代理 `/api -> :5000`。
- **过渡期部署**：nginx 同时承载两套静态产物——旧 `cmdb-ui` 维持现有路径，新 `cmdb-ui-vue3` 挂独立路径前缀（默认 `/v2`，可配置）或子域名；按模块完成度逐步引导流量，feature parity 后一次性切换默认入口。
- **后端不动**：API 契约完全复用。

## 测试与工具链

- 单测：Vitest + `@vue/test-utils`(Vue3)（替代 Jest）。
- 类型：`vue-tsc --noEmit` 进 CI。
- Lint/格式：ESLint 8+ + `@typescript-eslint` + Prettier。
- E2E：Playwright（后续按需）。

## 非目标（YAGNI）

- 不迁移 `cmdb` 模块（175 视图，后续子域拆分迁移）。
- 不引入微前端（qiankun/single-spa）。
- 不改动后端 API 契约。
- 首个里程碑不做运行时动态换主色 UI（仅 token 化主色 + 三态主题）。
