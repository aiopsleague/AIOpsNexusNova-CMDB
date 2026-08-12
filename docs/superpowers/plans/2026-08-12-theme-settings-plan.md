# 主题设置功能（light / dark / system）方案

> 为 CMDB 前端新增全局主题设置，支持**浅色 / 深色 / 跟随系统**三选项；默认跟随系统；深色主题全面覆盖所有业务页面；登出保留主题偏好。

---

## 现状分析

### 当前主题机制

- ant-design-vue **1.7.8 整包引入**（`src/core/use.js`），组件样式通过 `src/style/global.less` 第 24 行 `@import '~ant-design-vue/dist/antd.less'` 在**构建期编译固化**，运行时无法简单换肤。
- **antd 1.x 无 dark 主题产物**：`dist/` 无 `antd.dark.css`，`lib/style/themes/` 只有 `default.less`。已装的 `webpack-theme-color-replacer` 仅构建期抽取主色，不处理暗色。
- 现有 `navTheme`（即 `state.app.theme`）**只是菜单暗色**：仅影响 topmenu 顶栏和移动端抽屉，桌面侧边栏被 `BasicLayout.vue:26` 硬编码 `theme="light"`。
- 状态层已就绪但无入口：`app` store 已有 `theme` state + `TOGGLE_THEME` mutation + `Vue.ls`（`pro__` 前缀）持久化 + `bootstrap.js` 启动回读，但**没有任何 UI 调用**。
- 无任何 `matchMedia('(prefers-color-scheme)')` 使用，无 SettingsDrawer。
- `src/views/setting/lang/zh.js` 有预留的 `cs.menu.theme` '主题配置' 文案（死代码）。

### 核心约束（已实测验证）

| 约束 | 结论 |
|------|------|
| antd less 是否依赖 JS 插值 | 是（`color(~"colorPalette(...)")`、`@functions: ~"(function(){...})"`），独立编译**必须 `javascriptEnabled: true`** |
| 暗色变量覆盖机制 | **在 `@import` antd 全量之后**重新定义变量才生效（末定义胜出）；前置定义被 default.less 覆盖 |
| `@primary-1..@primary-10` | 必须**显式覆盖**为暗色值，否则 colorPalette 按暗色 primary 重算出过亮的浅调 |
| 独立 less 编译的 import 路径 | less 原生解析**不认 `~`**，dark.less 写裸模块名 `ant-design-vue/lib/style/...`，配合 `less.render` 的 `paths:[node_modules]` |
| antd 1.7.8 变量名 | 与 antd 4 大体一致（`@body-background`、`@table-header-bg` 等均在），照抄前需逐个核对 default.less |

### 当前代码路径

- 样式入口：[global.less](cmdb-ui/src/style/global.less) / [static.less](cmdb-ui/src/style/static.less)（项目色板变量）
- 状态层：[app.js](cmdb-ui/src/store/global/app.js)（`theme` state + `TOGGLE_THEME`）、[mutation-types.js](cmdb-ui/src/store/global/mutation-types.js)（`DEFAULT_THEME`）、[bootstrap.js](cmdb-ui/src/core/bootstrap.js)（启动回读）
- `navTheme` 映射：[mixin.js:12](cmdb-ui/src/utils/mixin.js#L12)（`state => state.app.theme`，resolved 主题会自动驱动侧边栏/顶栏 class）
- UI 入口：[userPanel.vue](cmdb-ui/src/components/tools/userPanel.vue)（已有"切换语言"三段式结构可复用）
- 登出清空：[login.js:45-55](cmdb-ui/src/api/login.js#L45-L55)（`localStorage.clear()` 会清掉主题设置）

---

## 方案设计

### 技术路线

**构建期独立编译暗色 CSS + 运行时 `<link>` 切换 + `html[data-theme='dark']` 前缀覆盖项目样式**

1. `src/style/themes/dark.less`：`@import "ant-design-vue/lib/style/index.less"` + `components.less` → **其后**覆盖 antd 暗色变量（dark-vars.less）→ 项目自定义覆盖（dark-overrides.less，`html[data-theme='dark']` 前缀）。
2. `scripts/build-theme.js`：用 `less@3.13.1` 编译 dark.less → `public/themes/dark.css`（`javascriptEnabled:true`、`paths:[node_modules]`、`compress:true`）。经 npm `pre*` 钩子在 serve/build 前自动执行；产物提交进仓库（~100KB gzip）。
3. 运行时：Vuex `app` 模块新增 `themeMode`（'light'|'dark'|'system'）持久化到 `pro__THEME_MODE`；`state.app.theme` 继续存放**实际生效**的 resolved 主题（light/dark），`mixin` 的 `navTheme` 已映射它。
4. `src/utils/theme.js`：`getSystemDark()` / `resolveTheme()` / `applyTheme()` / `initThemeSystem()`。applyTheme 动态增删 `<link id="theme-style" href="themes/dark.css">` + 设 `html[data-theme]` + 同步 body 背景防白闪；注册 `matchMedia('(prefers-color-scheme: dark)')` change 监听，system 模式下系统偏好变化即时生效。
5. `public/index.html` 加**防闪内联脚本**：读 `pro__THEME_MODE` → 设 `data-theme` + 注入最小关键暗色内联样式，避免首屏白闪（dark.css 真正的 link 由 theme.js 在 head 解析完后 append，保证排在 webpack link 之后）。

> **为什么项目覆盖统一用 `html[data-theme='dark']` 前缀**：路由懒加载的分块 scoped CSS（特异性 0,2,0）晚于 dark.css 注入；加祖先前缀（特异性 0,2,1）后无论加载顺序都胜出，**无需 `!important`**。

### 文件清单

**新增**

| 文件 | 职责 |
|---|---|
| `scripts/build-theme.js` | 独立编译 dark.less → public/themes/dark.css |
| `src/style/themes/dark.less` | 暗色编译入口（antd 全量 + 暗色变量 + 项目覆盖） |
| `src/style/themes/dark-vars.less` | antd 暗色变量 + 项目暗色变量（镜像 static.less 语义） |
| `src/style/themes/dark-overrides.less` | 项目自定义样式暗色覆盖（按覆盖目录迭代追加） |
| `src/utils/theme.js` | matchMedia / resolve / apply / init 全逻辑 |
| `src/utils/echarts-theme.js` | ECharts dark theme 对象 |

**修改**

| 文件 | 改动 |
|---|---|
| `package.json` | scripts: `theme:build` + `preserve` / `prebuild` / `prebuild:preview` |
| `public/index.html` | 防闪内联脚本 |
| `src/store/global/mutation-types.js` | 新增 `THEME_MODE = 'THEME_MODE'` |
| `src/store/global/app.js` | state 加 `themeMode`；新增 `TOGGLE_THEME_MODE` mutation（持久化 + 按 mode 解析写 state.theme）、`ToggleThemeMode` action |
| `src/core/bootstrap.js` | 启动回读 `Vue.ls.get(THEME_MODE, 'system')`，解析出 resolved 写入 state.theme |
| `src/main.js` | mount 前调 `initThemeSystem(store)` |
| `src/config/setting.js` | 加默认值 `themeMode: 'system'` |
| `src/components/tools/userPanel.vue` | 新增"主题设置"行（复刻"切换语言"行结构，三段式） |
| `src/api/login.js` | `logout()` 清 localStorage 前保留 `pro__THEME_MODE`、`pro__DEFAULT_THEME` |
| `src/layouts/BasicLayout.vue` | 桌面侧边栏 `theme="light"` → `:theme="navTheme"` |
| `src/components/GlobalHeader/GlobalHeader.vue` | sidemenu 模式 header 加 theme class（`.header.dark` 才生效） |
| `src/components/MultiTab/MultiTab.vue` | 内联 `tabBarStyle` 背景跟随主题（#FFF ↔ #1f1f1f） |
| `src/lang/zh.js`、`src/lang/en.js` | `userPanel` 命名空间加 `themeSetting/themeLight/themeDark/themeSystem` |

### 暗色变量体系（dark-vars.less）

antd 变量值参考 antd 4.x dark 主题，品牌主色 `#2f54eb` 保持不变。关键几组：

```less
/* 基础 */
@body-background: #141414;
@component-background: #1f1f1f;
@text-color: rgba(255,255,255,0.85);
@text-color-secondary: rgba(255,255,255,0.45);
@border-color-base: #434343;
@border-color-split: #303030;
@shadow-color: rgba(0,0,0,0.45);

/* 主色渐变（必须显式覆盖，否则过亮） */
@primary-1: #131629; @primary-2: #1a2342; @primary-3: #1f2f57;
@primary-5: #2f54eb; @primary-6: #2f54eb;

/* 布局 */
@layout-body-background: #141414;
@layout-header-background: #1f1f1f;
@layout-sider-background: #001529;

/* 组件：表单/输入/按钮/表格/菜单/浮层 */
@input-bg: #1f1f1f; @select-background: #1f1f1f;
@table-header-bg: #1f1f1f; @table-row-hover-bg: #262626;
@menu-bg: #1f1f1f; @menu-dark-bg: #001529;
@popover-bg: #1f1f1f; @modal-header-bg: #1f1f1f; @tooltip-bg: #434343;
```

项目变量镜像 `static.less` 语义（`@layout-sidebar-color`、`@text-color_1..7`、`@primary-color_1..9` 的暗色版），供项目覆盖引用。

### 暗色覆盖目录清单（全面覆盖所有业务页）

按优先级分模块迭代，全部落在 `dark-overrides.less` 用 `html[data-theme='dark']` 前缀：

- **A. 布局骨架**：侧边栏（`.sider`/`.logo`/`.ops-side-bar` 暗色切 `.ant-menu-dark` 分支/折叠态/submenu 弹层）、顶栏（`.header.dark`/`.top-nav-header-index.dark`/`.user-wrapper`/`.trigger`）、内容区（`.ant-layout-content`/`.content`/`.ant-pro-multi-tab`/面包屑/`.table-alert`/`.table-operator`/`.custom-drawer-bottom-action`）
- **B. 共享组件**：OpsTable、PageHeader、MultiTab、SidebarList、TagSelect、CustomRadio、CustomTransfer、CustomDrawer、CardTitle、ops-input/ops-select/ops-tab/ops-form/ops-stripe-table（vxe 表头斑马纹）、`.ant-tree` selected/hover
- **C. 第三方库**：vue-treeselect、vxe-table 3.7（`.vxe-table` 系列）、element-ui（ops-crontab 用到的部分）、monaco（vs-dark 兜底容器）、wangeditor、jsoneditor、butterfly-dag、relation-graph
- **D. 业务模块（逐页）**：
  - `src/modules/cmdb/views/`（222 个 vue）：高频写死浅色 `#fff`(47)、`#f5f5f5`、`#fafafa`、`#f7f8fa`、`#f0f0f0`、`#e4e7ed` 等，逐个补 `html[data-theme='dark']` 覆盖。优先级：dashboard → list/detail → monitor → ipam → dcim → 其余
  - `src/modules/acl/views/`（36 个 vue）：同类处理
- **E. ECharts 暗色（canvas 无法用 CSS，必须走 init 主题参数）**：`src/utils/echarts-theme.js` 导出 dark theme；改造 8 处 `echarts.init`（fullscreen、dcimStatsChart、relation-graph、custom_dashboard/chart、dashboard 的 3 个 counter、ipam statsChart）

### 运行时状态设计

- `state.app.theme`：**实际生效** resolved（'light'|'dark'），沿用 `DEFAULT_THEME` 持久化 key（`mixin.navTheme` 已映射，侧边栏/顶栏 class 自动跟随）
- `state.app.themeMode`：用户三选项（'light'|'dark'|'system'），新 key `THEME_MODE` → `pro__THEME_MODE`
- `TOGGLE_THEME_MODE` mutation：写 state + 持久化，并按 mode 解析 resolved 写入 `state.theme` + 持久化 `DEFAULT_THEME`（向后兼容旧持久化）
- `initThemeSystem(store)`：首次 apply + `store.subscribe` 监听切换 + `matchMedia` change 监听（仅 system 模式触发重解析）。在 `main.js` mount 前调用一次；App 不销毁无需注销
- `bootstrap.js`：回读 `Vue.ls.get(THEME_MODE, 'system')`（默认 system，忽略旧 DEFAULT_THEME 残留值，resolved 一律由 themeMode 现算）

### UI 入口（userPanel.vue）

在"切换语言"行之后、绑定账号行之前插入"主题设置"行，复刻语言行三段式结构：浅色 / 深色 / 跟随系统，active 态高亮。

```html
<div class="user-panel-row">
  <div class="user-panel-row-label">{{ $t('userPanel.themeSetting') }}</div>
  <div class="user-panel-theme">
    <div v-for="t in themeList" :key="t.key"
         :class="['user-panel-theme-item', themeMode === t.key ? 'user-panel-theme-item_active' : '']"
         @click="changeTheme(t.key)">{{ t.title }}</div>
  </div>
</div>
```

### 登出保留（login.js）

`logout()` 在 `localStorage.clear()` 前，先备份 `pro__THEME_MODE` 与 `pro__DEFAULT_THEME` 两个 key，clear 后写回。`ops_auth_type` 仍在 clear 前读取，跳转逻辑不变。

---

## 实施影响评估

| 影响维度 | 说明 |
|----------|------|
| **向后兼容** | light 模式下 dark.css 不加载、`data-theme='light'`，页面与改动前完全一致；`state.theme` 仍是 light/dark 双值，mixin/布局组件无需破坏性改动 |
| **构建** | 新增独立编译脚本 + npm pre 钩子；dark.css（~100KB gzip）提交进仓库，静态部署不跑脚本也能用 |
| **运行时性能** | dark.css 仅在暗色时按需加载；matchMedia 监听仅 1 个，开销可忽略 |
| **登出行为** | `logout()` 从全清改为保留 2 个主题 key，其余清空行为不变 |
| **工作量** | 主要投入在阶段 5/6 业务页暗色覆盖（cmdb 222 + acl 36 个 vue） |

---

## 实施步骤（分阶段，可增量交付）

| 阶段 | 内容 | 验收 |
|---|---|---|
| **0 构建基础设施** | scripts/build-theme.js + dark.less（仅 antd 变量）+ package.json 脚本 | 编译出 dark.css，抽查表头/popover 颜色 |
| **1 运行时切换骨架** | mutation-types / app.js / bootstrap / main.js / config / theme.js / index.html 防闪 | dev 控制台 `dispatch('ToggleThemeMode','dark')` 组件切换；系统偏好变化即时跟随 |
| **2 UI 入口 + 登出保留** | userPanel 主题行 + i18n；login.js 保留逻辑 | 切换持久化、刷新保留、登出后仍保留 |
| **3 布局骨架暗色** | BasicLayout / GlobalHeader / MultiTab + dark-overrides A 目录 | 整体框架 dark 可用 |
| **4 共享组件 + 第三方库** | dark-overrides B、C 目录 | OpsTable/vxe/treeselect 等 dark 正常 |
| **5 cmdb 模块逐页** | D 目录 cmdb 逐子目录覆盖 | 各子目录视觉回归 |
| **6 acl 模块** | D 目录 acl 36 个 vue | 同上 |
| **7 图表暗色** | echarts-theme.js + 8 处 init | 图表 dark 正常 |
| **8 收尾 QA** | 弹窗/抽屉/下拉/全屏/移动端抽屉回归、体积确认 | 全场景通过 |

---

## 验证

1. **构建**：`cd cmdb-ui && yarn theme:build` 生成 `public/themes/dark.css`；`yarn serve` 正常
2. **运行时切换**：userPanel 切换浅色/深色/跟随系统 → antd 组件 + 项目样式即时切换；`pro__THEME_MODE` 写入 localStorage；刷新后保留
3. **system 模式**：系统切换深色/浅色 → 页面即时跟随（无需刷新）
4. **登出保留**：设置深色 → 登出 → 重新登录 → 仍是深色
5. **防闪**：暗色下刷新页面无白闪
6. **全面覆盖**：逐模块走查 cmdb/acl 主要页面在 dark 下无刺眼白块、文字对比度正常；ECharts 图表正常
7. **回归**：light 模式下所有页面与改动前一致（dark.css 未加载、`data-theme` 为 light）

---

## 风险

1. **FOUC 白闪** — 依赖 index.html 内联脚本先行设 data-theme + 最小暗色内联样式
2. **`@primary-1..10` 不显式覆盖会过亮** — 已在变量表强制覆盖
3. **业务页写死浅色遗漏** — 全面覆盖靠逐页迭代 + 视觉回归保证，阶段 5/6 明确列出
4. **ECharts 是 canvas** — CSS 无效，必须改 init 主题参数（8 处）
5. **顶栏 sidemenu 恒白** — 必须给 GlobalHeader 加 theme class；MultiTab 内联白底必须走 Vue 侧跟随
6. **antd 1.7.8 变量名与 antd4 有差异** — 照抄 antd4 dark 变量名会失效，需逐个核对 default.less
7. **dark.css ~100KB gzip** — 仅暗色时加载，可接受
