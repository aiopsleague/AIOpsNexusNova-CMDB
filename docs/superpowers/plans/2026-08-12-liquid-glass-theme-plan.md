# 流体玻璃主题（Liquid Glass）实施方案

> 分支：`feat/theme-settings` | 日期：2026-08-12 | 状态：待审核  
> 关联 Spec：[2026-08-12-liquid-glass-theme-design.md](../specs/2026-08-12-liquid-glass-theme-design.md)

---

## 0. 现状分析

### 已有基础设施

当前 `feat/theme-settings` 分支已实施完整的 light / dark / system 主题体系：

- **编译链**: `scripts/build-theme.js` 编译 `dark.less` → `public/themes/dark.css`
- **运行时**: `src/utils/theme.js` 管理 CSS `<link>` 注入、`data-theme` 切换、`matchMedia` 监听
- **状态层**: `state.app.theme`（resolved） + `state.app.themeMode`（用户选择），`bootstrap.js` 回读
- **UI**: `userPanel.vue` 三段式按钮（浅色/深色/跟随系统）
- **覆盖**: `dark-vars.less`（140 行变量） + `dark-overrides.less`（760 行覆盖） + `dark-business.less`（自动生成的业务覆盖）

### 当前 dark-vars.less 关键变量（需要 LQ 覆盖的部分）

```less
// 需要改为半透明
@body-background: #121216;           → rgba(8,10,16,0.95) or 保持实色（body 不透明）
@component-background: #1e1e24;      → rgba(255,255,255,0.06)   ← 核心变化
@layout-sider-background: #1e1e24;   → rgba(20,20,30,0.5)       ← 核心变化
@layout-header-background: #1e1e24;  → rgba(20,20,30,0.5)
@card-background: #1e1e24;           → rgba(255,255,255,0.06)
@input-bg: #1e1e24;                  → rgba(255,255,255,0.07)
@popover-bg: #1e1e24;                → rgba(30,30,40,0.8)       ← 浮层需要更高不透明度
@modal-header-bg: #1e1e24;           → rgba(30,30,40,0.8)
@table-header-bg: #1e1e24;           → rgba(255,255,255,0.05)

// 需要改为更亮（玻璃边框）
@border-color-base: #2e2e38;         → rgba(255,255,255,0.12)
@border-color-split: #282830;        → rgba(255,255,255,0.08)

// 保持不变（文本/主色同 dark）
@text-color: #f0f0f3;                ← 同 dark
@text-color-secondary: #9999a6;      ← 同 dark
@primary-color: #6c5ce7;             ← 同 dark
@primary-1..@primary-10: ...;        ← 同 dark
```

### 当前 theme.js 关键函数（需要扩展的位置）

```js
// resolveTheme: 仅处理 system/light/dark
resolveTheme(mode) {
  if (mode === 'system') return getSystemDark() ? 'dark' : 'light'
  return mode === 'dark' ? 'dark' : 'light'
}

// syncDarkCss: 仅处理 dark.css
const DARK_CSS_PATH = `...themes/dark.css?v=...`
function syncDarkCss(dark) { ... }

// applyTheme: 仅切换 dark/light
function applyTheme(resolved) {
  const dark = resolved === 'dark'
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
  syncDarkCss(dark)
  document.body.style.backgroundColor = dark ? '#121216' : ''
}
```

---

## 1. 实施方案

### 阶段 1：构建基础设施 — liquid-glass.css 编译

#### 1.1 新建 `src/style/themes/liquid-glass-vars.less`

**策略：继承 dark-vars 全部变量，仅覆盖玻璃相关项。**

```less
// liquid-glass-vars.less
// 继承 dark 变量体系（文本色、主色、禁用色等保持不变）
@import "./dark-vars.less";

// ===== 覆盖为半透明玻璃变量 =====
// 面板/卡片 — 从实色改为半透明
@body-background: #080a10;
@component-background: rgba(255, 255, 255, 0.06);
@background-color-light: rgba(255, 255, 255, 0.12);
@background-color-base: rgba(255, 255, 255, 0.08);

// 边框 — 更亮
@border-color-base: rgba(255, 255, 255, 0.12);
@border-color-split: rgba(255, 255, 255, 0.08);

// 布局
@layout-body-background: #080a10;
@layout-header-background: rgba(20, 20, 30, 0.5);
@layout-sider-background: rgba(20, 20, 30, 0.5);

// 输入/表单
@input-bg: rgba(255, 255, 255, 0.07);
@input-border-color: rgba(255, 255, 255, 0.14);
@select-background: rgba(30, 30, 40, 0.6);
@select-dropdown-bg: rgba(30, 30, 40, 0.85);  // 下拉需要更高不透明度

// 按钮
@btn-default-bg: rgba(255, 255, 255, 0.06);
@btn-default-border: rgba(255, 255, 255, 0.16);
@btn-disable-bg: rgba(255, 255, 255, 0.04);
@btn-disable-border: rgba(255, 255, 255, 0.08);

// 表格
@table-header-bg: rgba(255, 255, 255, 0.05);
@table-row-hover-bg: rgba(255, 255, 255, 0.08);
@table-selected-row-bg: rgba(108, 92, 231, 0.15);

// 浮层（需要更高不透明度以保持可读性）
@popover-bg: rgba(30, 30, 40, 0.85);
@modal-header-bg: rgba(30, 30, 40, 0.85);
@tooltip-bg: rgba(40, 40, 50, 0.9);
@card-background: rgba(255, 255, 255, 0.06);

// 菜单
@menu-bg: rgba(20, 20, 30, 0.5);
@menu-popup-bg: rgba(30, 30, 40, 0.85);
@menu-dark-bg: rgba(20, 20, 30, 0.5);
@menu-dark-submenu-bg: rgba(10, 10, 16, 0.7);

// 项目变量（镜像 static.less，覆盖为半透明）
@primary-color_3: rgba(108, 92, 231, 0.15);
@primary-color_5: rgba(108, 92, 231, 0.18);
@primary-color_7: rgba(255, 255, 255, 0.08);
@layout-sidebar-color: rgba(20, 20, 30, 0.5);
@layout-sidebar-sub-color: rgba(10, 10, 16, 0.7);
@layout-sidebar-selected-color: rgba(108, 92, 231, 0.2);
```

#### 1.2 新建 `src/style/themes/liquid-glass.less`

```less
// liquid-glass.less — 编译入口
@import "./liquid-glass-vars.less";

html[data-theme='liquid-glass'] {
  @import "ant-design-vue/lib/style/index.less";
  @import "ant-design-vue/lib/style/components.less";
  @import "../global.less";
  @import (multiple) "./liquid-glass-vars.less";
}

@import "./dark-business.less";       // 复用 dark 业务覆盖
@import "./dark-overrides.less";      // 复用 dark 项目覆盖
@import "./liquid-glass-overrides.less";  // 玻璃专属覆盖
```

> **关键决策**：复用 `dark-business.less` 和 `dark-overrides.less`。它们的规则都在 `html[data-theme='dark']` 前缀下，对 `data-theme='liquid-glass'` 不生效。解决方案：在 `liquid-glass-overrides.less` 中处理。

#### 1.3 新建 `src/style/themes/liquid-glass-overrides.less`

仅写 dark 覆盖无法表达的内容：**backdrop-filter**、**box-shadow 增强**、**圆角变大**、**过渡动画**。同时将 dark-overrides.less 中 `html[data-theme='dark']` 的规则**复制一份**到 `html[data-theme='liquid-glass']`，但将其中的 `#1e1e24`/`#121216` 等实色值替换为相应的半透明 rgba 值。

**实际上**，更干净的方案是：将 dark-overrides.less 和 dark-business.less 中的选择器前缀从 `html[data-theme='dark']` 改为 `html[data-theme='dark'], html[data-theme='liquid-glass']`，这样两个主题共享所有业务覆盖。但这会改动 dark-overrides.less 的 760 行 — 成本大但有长期维护价值。

**折中方案**：在 liquid-glass-overrides.less 中用 CSS `:is()` 或直接复制关键覆盖。由于 dark-business.less 是自动生成的，我们可以：

1. 修改 `scripts/gen-dark-business.js` 让它同时生成两个前缀
2. 在 liquid-glass.less 中，通过 less 变量覆盖让 dark-overrides.less 编译出正确的半透明值

**推荐方案（最小改动）**：在 liquid-glass-overrides.less 中写：

```less
// 1. 核心 backdrop-filter（dark 没有的）
html[data-theme='liquid-glass'] {
  .ant-layout,
  .ant-layout-content,
  .ant-layout-sider,
  .ant-layout-header,
  .ant-card,
  .ant-table,
  .ant-menu,
  .ant-dropdown,
  .ant-select-dropdown,
  .ant-modal-content,
  .ant-popover-inner,
  .ant-drawer-content-wrapper,
  .sidebar,
  .topbar,
  .glass-panel,
  .stat-item,
  .search-form-bar,
  // ... 所有面板容器
  {
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
  }
  
  // 2. 增强内阴影高光（替代 dark 的单线高光）
  .ant-card,
  .ant-layout-sider,
  .ant-modal-content,
  .ant-popover-inner,
  // ...
  {
    box-shadow: 0 30px 60px rgba(0,0,0,0.4),
                0 10px 20px rgba(0,0,0,0.2),
                inset 0 1px 1px 0 rgba(255,255,255,0.35),
                inset 0 -1px 1px 0 rgba(0,0,0,0.2);
  }
  
  // 3. 大圆角
  --border-radius-base: 14px;
  --border-radius-box: 24px;
  
  // 4. 弹簧过渡
  * {
    transition-timing-function: cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }
  
  // 5. Hover 上浮效果
  .ant-card:hover,
  .glass-panel:hover {
    transform: translateY(-4px) scale(1.015);
  }
}
```

#### 1.4 修改 `scripts/build-theme.js`

通用化处理，接受 CLI 参数：

```js
// build-theme.js
const fs = require('fs')
const path = require('path')
const less = require('less')

const projectRoot = path.resolve(__dirname, '..')
const themeName = process.argv[2] || 'dark'  // 'dark' | 'liquid-glass'
const entryFile = path.join(projectRoot, `src/style/themes/${themeName}.less`)
const outputFile = path.join(projectRoot, `public/themes/${themeName}.css`)

async function main() {
  let source = fs.readFileSync(entryFile, 'utf8')

  // Inline ../global.less (same logic as before)
  source = source.replace(/@import\s+['"]\.\.\/global\.less['"];\s*/, () => {
    let globalLess = fs.readFileSync(path.join(projectRoot, 'src/style/global.less'), 'utf8')
    globalLess = globalLess.replace(/@import\s+['"]~ant-design-vue\/dist\/antd\.less['"];\s*/g, '')
    const staticLess = fs.readFileSync(path.join(projectRoot, 'src/style/static.less'), 'utf8')
    return globalLess.replace(/@import\s+['"]\.\/static\.less['"];\s*/g, () => staticLess + '\n')
  })

  const result = await less.render(source, {
    filename: entryFile,
    paths: [path.join(projectRoot, 'node_modules')],
    javascriptEnabled: true,
    compress: true
  })
  fs.mkdirSync(path.dirname(outputFile), { recursive: true })
  fs.writeFileSync(outputFile, result.css)
  console.log(`[build-theme] ${themeName}.css generated (${(result.css.length / 1024).toFixed(1)} KB)`)
}

main().catch(err => {
  console.error(`[build-theme] ${themeName} failed:`, err)
  process.exit(1)
})
```

#### 1.5 修改 `package.json`

```json
{
  "scripts": {
    "theme:build": "node scripts/build-theme.js dark && node scripts/build-theme.js liquid-glass",
    "preserve": "yarn theme:build",
    "prebuild": "yarn theme:build",
    "prebuild:preview": "yarn theme:build"
  }
}
```

### 阶段 2：运行时切换扩展

#### 2.1 修改 `src/utils/theme.js`

```js
// 新增 liquid-glass CSS 路径
const THEME_CSS = {
  dark: `${process.env.BASE_URL || '/'}themes/dark.css?v=${DARK_CSS_VERSION}`,
  'liquid-glass': `${process.env.BASE_URL || '/'}themes/liquid-glass.css?v=${DARK_CSS_VERSION}`
}

// resolveTheme 扩展
export function resolveTheme(mode) {
  if (mode === 'system') return getSystemDark() ? 'dark' : 'light'
  if (mode === 'liquid-glass') return 'liquid-glass'
  return mode === 'dark' ? 'dark' : 'light'
}

// 重命名 syncDarkCss → syncThemeCss，泛化
function syncThemeCss(theme) {
  const link = document.getElementById('theme-style')
  const cssPath = THEME_CSS[theme]  // undefined for 'light' → remove

  if (cssPath) {
    if (!link) {
      const el = document.createElement('link')
      el.id = 'theme-style'
      el.rel = 'stylesheet'
      el.href = cssPath
      document.head.appendChild(el)
    } else if (link.href !== cssPath) {
      // 从 dark 切换到 liquid-glass，更新 href
      link.href = cssPath
    }
  } else if (link) {
    link.remove()
  }
}

// applyTheme 扩展
export function applyTheme(resolved) {
  document.documentElement.setAttribute('data-theme', resolved)
  syncThemeCss(resolved)
  document.body.style.backgroundColor =
    resolved === 'liquid-glass' ? '#080a10' :
    resolved === 'dark' ? '#121216' : ''
  window.dispatchEvent(new CustomEvent('ops:theme-change', { detail: { theme: resolved } }))
}
```

#### 2.2 修改 `public/index.html` 防闪脚本

```js
// 新增 liquid-glass 识别
var dark = mode === 'dark' || mode === 'liquid-glass' ||
  (mode === 'system' && window.matchMedia('...dark').matches)
if (dark) {
  document.documentElement.setAttribute('data-theme', mode === 'liquid-glass' ? 'liquid-glass' : 'dark')
  // 注入最小关键暗色
  var bg = mode === 'liquid-glass' ? '#080a10' : '#141414'
  // ...
}
```

### 阶段 3：UI 入口

#### 3.1 修改 `src/components/tools/userPanel.vue`

```js
// themeList 加一项
themeList: [
  { title: 'userPanel.themeLight', key: 'light' },
  { title: 'userPanel.themeDark', key: 'dark' },
  { title: 'userPanel.themeLiquidGlass', key: 'liquid-glass' },  // 新增
  { title: 'userPanel.themeSystem', key: 'system' },
]
```

#### 3.2 i18n

```js
// zh.js
userPanel: {
  themeLiquidGlass: '流体',
  // ...existing entries
}
// en.js
userPanel: {
  themeLiquidGlass: 'Liquid',
  // ...existing entries
}
```

### 阶段 4：共享 dark 业务覆盖

#### 4.1 统一 dark/liquid-glass 业务覆盖前缀

**方案 A（推荐）**：修改 `scripts/gen-dark-business.js`，让它在生成 dark-business.less 时，选择器前缀写为：

```less
html[data-theme='dark'] .foo, html[data-theme='liquid-glass'] .foo {
  background-color: #1e1e24;  // 这个值在 liquid-glass 中会被变量覆盖
}
```

但这样 `#1e1e24` 是写死的 — 实际上 dark-business.less 就是写死的值。对于 liquid-glass，这些实色值不太对（应该更半透明）。

**方案 B（更实际）**：在 `liquid-glass-overrides.less` 中，对高频面板容器做一层更轻量的覆盖。不是逐类覆盖，而是用属性选择器匹配：

```less
// 将所有 dark-business 中写死的深色背景转为半透明
html[data-theme='liquid-glass'] {
  [class*="ci-"],
  [class*="cmdb-"],
  [class*="prom-"],
  [class*="ops-"],
  [class*="acl-"]
  {
    // 只覆盖背景色为半透明的情况，不碰文字色
    &[style*="background"],  // 内联样式的不处理
  }
}
```

**方案 C（务实选择）**：阶段 4 先跳过全量业务覆盖。优先确保：
1. antd 组件面板全变成玻璃（通过 liquid-glass-vars.less 覆盖 antd 变量即可覆盖 90%）
2. 布局骨架（侧边栏/顶栏/内容区）变成玻璃
3. 共享组件（OpsTable、vxe-table 等）通过 liquid-glass-overrides.less 手工覆盖

业务页面中的个别硬编码浅色背景，作为后续迭代优化项（与当初 dark 主题的迭代覆盖一样）。

> **推荐方案 C** 用于初始实现，方案 A/B 作为后续增强。

### 阶段 5：验证与收尾

| 验证项 | 方法 |
|--------|------|
| `yarn theme:build` 编译成功 | 检查 `public/themes/liquid-glass.css` 生成 |
| `yarn serve` 正常启动 | `localhost:8000` 可访问 |
| userPanel 切换为流体 | 页面即时变化 |
| 刷新保留 | `pro__THEME_MODE` = `liquid-glass` |
| 登出后再登录保留 | localStorage 检查 |
| 防闪 | 流体模式下刷新无白闪 |
| 面板模糊效果 | DevTools 检查 backdrop-filter 生效 |
| 浏览器兼容 | Chrome / Firefox / Safari 检查 |
| backdrop-filter 不支持时退化 | 面板仍为半透明（无模糊），可读性正常 |

---

## 2. 实施步骤（分阶段执行）

| 阶段 | 内容 | 文件 | 预计行数 |
|------|------|------|----------|
| **1 构建** | liquid-glass-vars.less + liquid-glass.less + liquid-glass-overrides.less + build-theme.js 改造 + package.json | 5 files | ~200 new |
| **2 运行时** | theme.js 泛化 + index.html 防闪扩展 | 2 files | ~30 modified |
| **3 UI** | userPanel.vue + i18n (zh/en) | 3 files | ~10 modified |
| **4 覆盖** | liquid-glass-overrides.less 补充（共享组件 + 业务高频面板） | 1 file | ~150 new |
| **5 验证** | 编译 + 运行时测试 + 多浏览器检查 | - | - |

总改动量：~350 行新增 + ~40 行修改，分布在 11 个文件中。

---

## 3. 风险

| 风险 | 缓解 |
|------|------|
| `backdrop-filter` 在旧浏览器不支持 | rgba 底色退化，面板仍可见可读 |
| `saturate(180%)` 使某些颜色过饱和 | 仅用于背景模糊，不作用于内容；可在 overrides 中调低 |
| liquid-glass.css 体积过大 | 复用 dark 变量体系，预计 ~800KB（与 dark.css 同量级） |
| 弹簧过渡让页面感觉"慢" | 仅在 hover 时触发，不影响加载性能 |
| 两个编译产物维护成本 | dark.css + liquid-glass.css 共享 90% 变量，liquid-glass 仅增量覆盖 |

---

## 4. 与现有 dark 主题的关系

```
dark.less  ──compile──► dark.css         ← 现有，不变
liquid-glass.less ──compile──► liquid-glass.css  ← 新增

dark-vars.less  ← 140 行变量
    ↓ (import)
liquid-glass-vars.less  ← 继承 dark-vars，覆盖 ~20 个变量为半透明

dark-overrides.less  ← 760 行覆盖（html[data-theme='dark']）
dark-business.less    ← 自动生成（html[data-theme='dark']）
    ↓ (在 liquid-glass.less 中 import)
    编译时 dark 变量被 LQ 变量覆盖 → 产出的 liquid-glass.css 中
    这些规则使用半透明 rgba 值
```

> 核心技巧：liquid-glass.less 中 import dark-overrides.less 和 dark-business.less **时**，由于 liquid-glass-vars.less 已经覆盖了 `@component-background` 等变量，dark-overrides 中使用的 `@layout-sidebar-color` 等变量会被解析为 LQ 的半透明版本。但这只对使用了 Less 变量的 dark-overrides 有效 — `dark-business.less` 中写死的 `#1e1e24` 不会被覆盖。因此阶段 4 需要在 liquid-glass-overrides.less 中处理这些写死值。
