# 主题设置功能设计

> 日期：2026-08-12 | 状态：待确认

## 背景

CMDB 前端仅有"菜单暗色"（navTheme），无全局主题能力。ant-design-vue 1.7.8 无内置 dark 产物，组件样式在构建期通过 Less 变量固化，无法运行时简单换肤。需要自建一套可切换的 light / dark / system 主题体系。

## 目标

- 提供 **浅色 / 深色 / 跟随系统** 三选项，默认跟随系统
- 深色主题**全面覆盖**所有业务页面（cmdb/acl 模块写死浅色）
- 运行时即时切换，刷新保留，登出保留
- light 模式下与现有表现完全一致（零回归）

## 功能定义

| 模式 | 生效主题 | 行为 |
|------|----------|------|
| `light` | light | 恒定浅色，不加载 dark.css |
| `dark` | dark | 恒定深色，加载 dark.css |
| `system` | 按 `matchMedia('(prefers-color-scheme: dark)')` 解析 | 系统偏好变化时**即时**跟随，无需刷新 |

## 技术路线

**构建期独立编译暗色 CSS + 运行时 `<link>` 切换 + `html[data-theme='dark']` 前缀覆盖**

```
antd less (亮色, 构建期编译)     ← 现有，global.less 引入
        │
dark.less (独立编译)  ──►  public/themes/dark.css   (~100KB gzip, 提交进仓库)
        │
运行时:  <link id="theme-style" href="themes/dark.css">  动态增删
        html[data-theme="dark"]  属性切换
        matchMedia 监听 (system 模式)
```

### 关键机制验证结论

1. **antd less 依赖 JS 插值** → 独立编译必须 `javascriptEnabled: true`
2. **变量覆盖**：`@import` antd 全量**之后**重新定义才生效（末定义胜出）
3. **`@primary-1..@primary-10` 必须显式覆盖**为暗色值，否则 colorPalette 重算出过亮浅调
4. **import 路径**：less 原生不认 `~`，dark.less 写裸模块名 + `paths:[node_modules]`
5. **CSS 加载顺序**：dark.css 由 `theme.js` 在 head 解析完后 `appendChild`，排在 webpack link 之后；项目覆盖用 `html[data-theme='dark']` 前缀（特异性 0,2,1）压过 scoped（0,2,0），无需 `!important`

## 暗色 CSS 构建

### dark.less 结构（编译入口）

```less
@import "ant-design-vue/lib/style/index.less";
@import "ant-design-vue/lib/style/components.less";
@import "./dark-vars.less";       // antd 暗色变量 + 项目暗色变量（后定义覆盖 antd）
@import "./dark-overrides.less";  // 项目自定义样式暗色覆盖（html[data-theme='dark'] 前缀）
```

### build-theme.js

```js
// 用 less@3.13.1 独立编译，不经过 webpack
less.render(source, {
  filename: entryFile,
  paths: [path.resolve(__dirname, '../node_modules')],
  javascriptEnabled: true,
  compress: true
})  // → fs.mkdirSync + writeFileSync(public/themes/dark.css)
```

### 暗色变量核心表（dark-vars.less）

```less
/* 基础 */
@body-background: #141414;
@component-background: #1f1f1f;
@text-color: rgba(255,255,255,0.85);
@text-color-secondary: rgba(255,255,255,0.45);
@border-color-base: #434343;
@border-color-split: #303030;
@shadow-color: rgba(0,0,0,0.45);
@background-color-light: rgba(255,255,255,0.08);
@background-color-base: rgba(255,255,255,0.04);

/* 主色渐变（强制覆盖） */
@primary-1: #131629; @primary-2: #1a2342; @primary-3: #1f2f57;
@primary-4: #253a6b; @primary-5: #2f54eb; @primary-6: #2f54eb;
@primary-7: #4158c9; @primary-8: #32408f; @primary-9: #2a3566; @primary-10: #20284a;

/* 布局 */
@layout-body-background: #141414;
@layout-header-background: #1f1f1f;
@layout-header-height: 40px;          // 覆盖项目已有值，勿被 antd 64px 覆盖
@layout-sider-background: #001529;
@layout-trigger-background: #1f1f1f;

/* 表单/输入/按钮 */
@input-bg: #1f1f1f; @input-addon-bg: #2a2a2a;
@select-background: #1f1f1f; @select-dropdown-bg: #1f1f1f;
@btn-default-bg: #1f1f1f; @btn-default-border: #434343;
@tag-default-bg: rgba(255,255,255,0.08);

/* 表格 */
@table-header-bg: #1f1f1f;
@table-header-color: rgba(255,255,255,0.85);
@table-row-hover-bg: #262626;
@table-selected-row-bg: #262626;
@table-expanded-row-bg: #1f1f1f;
@table-footer-bg: #1f1f1f;

/* 菜单 */
@menu-bg: #1f1f1f; @menu-popup-bg: #1f1f1f;
@menu-dark-bg: #001529; @menu-dark-submenu-bg: #000c17;

/* 浮层 */
@popover-bg: #1f1f1f; @modal-header-bg: #1f1f1f;
@modal-mask-bg: rgba(0,0,0,0.65); @tooltip-bg: #434343;

/* 其它 */
@card-background: #1f1f1f; @card-actions-background: #1a1a1a;
@tabs-card-head-background: #1f1f1f;
@tree-node-hover-bg: rgba(255,255,255,0.08);
@descriptions-bg: #1a1a1a;
@breadcrumb-base-color: rgba(255,255,255,0.45);
@slider-rail-background-color: #262626;
```

项目暗色变量镜像 `static.less` 语义（`@text-color_1..7`、`@primary-color_1..9`、`@layout-sidebar-*` 暗色版），供 dark-overrides.less 引用。

## 运行时设计

### 状态模型

```js
state.app.theme       // 'light' | 'dark'  —— 实际生效的 resolved 主题（沿用 DEFAULT_THEME 持久化）
state.app.themeMode   // 'light' | 'dark' | 'system' —— 用户三选项（新 key THEME_MODE → pro__THEME_MODE）
```

- `mixin.js` 的 `navTheme` 已映射 `state.app.theme` → 侧边栏/顶栏 class 自动跟随，**无需改 mixin**
- `bootstrap.js` 回读 `Vue.ls.get(THEME_MODE, 'system')`，resolved 一律由 themeMode 现算（忽略旧 DEFAULT_THEME 残留值）

### Vuex 新增

```js
// mutation-types.js
THEME_MODE = 'THEME_MODE'

// app.js
TOGGLE_THEME_MODE: (state, mode) => {
  Vue.ls.set(THEME_MODE, mode)
  state.themeMode = mode
  state.theme = resolveTheme(mode)      // 依赖 utils/theme.js
  Vue.ls.set(DEFAULT_THEME, state.theme)  // 派生值，向后兼容
}
// action: ToggleThemeMode({ commit }, mode) { commit('TOGGLE_THEME_MODE', mode) }
```

### theme.js API

```js
getSystemDark()      // matchMedia('(prefers-color-scheme: dark)').matches ?? false
resolveTheme(mode)   // 'system' → getSystemDark() ? 'dark' : 'light'；否则原样
applyTheme(resolved) // ① html.setAttribute('data-theme', resolved)
                     // ② dark → appendChild <link id="theme-style" href=BASE_URL+'themes/dark.css'>（不存在时）；light → remove
                     // ③ 同步 body 背景色防路由切换白闪
initThemeSystem(store)
  // ① 首次 applyTheme(store.state.app.theme)
  // ② store.subscribe: TOGGLE_THEME / TOGGLE_THEME_MODE → applyTheme
  // ③ matchMedia change listener: 若 themeMode==='system' → 重解析并 apply
```

生命周期：`main.js` mount 前调用一次；App 不销毁无需注销。

### index.html 防闪内联脚本

```html
<script>
  // Vue.ls 存储格式: JSON.stringify({value, expire})，需 JSON.parse 取 value
  const themeMode = ... // 读 pro__THEME_MODE
  const dark = themeMode === 'dark' ||
    (themeMode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  if (dark) {
    document.documentElement.setAttribute('data-theme', 'dark')
    // 注入最小关键暗色：body / #loading-mask 背景 #141414
  }
</script>
```

## UI 设计（userPanel.vue）

在"切换语言"行（`userPanel.vue:48-63`）之后、绑定账号行之前插入"主题设置"行：

```
┌─────────────────────────────────────┐
│  主题设置          [浅色|深色|跟随系统] │   ← 三段式，active 高亮
│  切换语言          [简中|EN]          │   ← 现有
└─────────────────────────────────────┘
```

- `themeList`: `[{title:'浅色',key:'light'},{title:'深色',key:'dark'},{title:'跟随系统',key:'system'}]`
- computed: `themeMode: state => state.app.themeMode`
- methods: `changeTheme(mode){ this.$store.dispatch('ToggleThemeMode', mode) }`
- 样式复刻 `.user-panel-lang`，active 用 `@primary-color_3` 背景 + `@primary-color` 文字；该行在 dark-overrides.less 补暗色覆盖（popover 挂载 body，带 data-v 属性，前缀选择器可压过）

## 暗色覆盖策略（dark-overrides.less）

统一结构：`html[data-theme='dark'] { .选择器 { ... } }`

| 目录 | 覆盖范围 |
|------|----------|
| **A 布局骨架** | `.sider`/`.logo`/`.ops-side-bar`（暗色切 `.ant-menu-dark` 分支）/折叠态/submenu、`.header.dark`/`.top-nav-header-index.dark`/`.user-wrapper`/`.trigger`、`.ant-layout-content`/`.content`/`.ant-pro-multi-tab`/面包屑/`.table-alert`/`.table-operator`/`.table-page-search-wrapper`/`.custom-drawer-bottom-action` |
| **B 共享组件** | OpsTable、PageHeader、MultiTab、SidebarList、TagSelect、CustomRadio、CustomTransfer、CustomDrawer、CardTitle、ops-input/ops-select/ops-tab/ops-form/ops-stripe-table（vxe 表头斑马纹）、`.ant-tree` selected/hover |
| **C 第三方库** | vue-treeselect（`.vue-treeselect__control/__menu/__option/__multi-value-item`）、vxe-table 3.7（`.vxe-table` 系列）、element-ui（ops-crontab 部分）、monaco（vs-dark 兜底容器）、wangeditor、jsoneditor、butterfly-dag、relation-graph |
| **D 业务模块** | `cmdb/views`（222 个 vue，高频 `#fff`/`#f5f5f5`/`#fafafa`/`#f7f8fa`/`#f0f0f0`/`#e4e7ed` 逐个覆盖，优先级 dashboard→list/detail→monitor→ipam→dcim→其余）、`acl/views`（36 个 vue） |
| **E ECharts** | canvas 无法 CSS 覆盖 → `echarts-theme.js` 导出 dark theme，改 8 处 `echarts.init` 传主题参数 |

## 登出保留（login.js）

```js
export function logout() {
  const auth_type = localStorage.getItem('ops_auth_type')
  // 保留主题偏好（Vue.ls 前缀 pro__），其余照旧清空
  const keepKeys = ['pro__THEME_MODE', 'pro__DEFAULT_THEME']
  const kept = {}
  keepKeys.forEach(k => { const v = localStorage.getItem(k); if (v !== null) kept[k] = v })
  localStorage.clear()
  Object.keys(kept).forEach(k => localStorage.setItem(k, kept[k]))
  // ...原 axios 逻辑不变
}
```

## 布局组件改造

| 组件 | 改动 | 原因 |
|------|------|------|
| `BasicLayout.vue:26` | `theme="light"` → `:theme="navTheme"` | 桌面侧边栏跟随 resolved 主题 |
| `GlobalHeader.vue` | sidemenu 模式 header `:class="['header', theme]"` | 当前恒白，`.header.dark` 才有暗色 |
| `MultiTab.vue` | 内联 `tabBarStyle` 背景跟随主题 | 内联样式优先级高于外部 CSS，必须走 Vue 侧 |

## i18n 新增键值

```js
// src/lang/zh.js / en.js（userPanel 命名空间）
userPanel: {
  themeSetting: '主题设置' / 'Theme',
  themeLight: '浅色' / 'Light',
  themeDark: '深色' / 'Dark',
  themeSystem: '跟随系统' / 'System'
}
```

## 改动范围

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `scripts/build-theme.js` | 新增 | 独立编译 dark.css |
| `src/style/themes/dark.less` | 新增 | 暗色编译入口 |
| `src/style/themes/dark-vars.less` | 新增 | antd + 项目暗色变量 |
| `src/style/themes/dark-overrides.less` | 新增 | 项目自定义暗色覆盖 |
| `src/utils/theme.js` | 新增 | 运行时主题逻辑 |
| `src/utils/echarts-theme.js` | 新增 | ECharts dark theme |
| `package.json` | 修改 | `theme:build` + pre 钩子 |
| `public/index.html` | 修改 | 防闪内联脚本 |
| `src/store/global/mutation-types.js` | 修改 | `THEME_MODE` |
| `src/store/global/app.js` | 修改 | `themeMode` state + mutation/action |
| `src/core/bootstrap.js` | 修改 | 回读 themeMode |
| `src/main.js` | 修改 | 调 `initThemeSystem` |
| `src/config/setting.js` | 修改 | `themeMode: 'system'` 默认值 |
| `src/components/tools/userPanel.vue` | 修改 | 主题设置行 |
| `src/api/login.js` | 修改 | 登出保留主题 key |
| `src/layouts/BasicLayout.vue` | 修改 | 侧边栏跟随主题 |
| `src/components/GlobalHeader/GlobalHeader.vue` | 修改 | header theme class |
| `src/components/MultiTab/MultiTab.vue` | 修改 | tabBarStyle 跟随 |
| `src/lang/zh.js`、`src/lang/en.js` | 修改 | i18n 文案 |
| `src/modules/cmdb/views/**` | 迭代覆盖 | 业务页暗色 |
| `src/modules/acl/views/**` | 迭代覆盖 | 业务页暗色 |

## 技术约束

- Vue 2.6 Options API（不引入 Composition API）
- Ant Design Vue 1.6.x，样式走 Less 变量体系
- 独立编译用 `less@3.13.1`（项目已装），`javascriptEnabled: true`
- 项目覆盖统一 `html[data-theme='dark']` 前缀，不用 `!important`
- 复用现有 `state.app.theme` / `TOGGLE_THEME` / `Vue.ls`（`pro__` 前缀）/ `mixin.navTheme` 机制
- ECharts 走 init 主题参数（canvas 无法 CSS 覆盖）
