# 流体玻璃主题（Liquid Glass）设计

> 日期：2026-08-12 | 状态：待审核
> 更新：2026-08-13 — 独立 dark 主题已移除，流体玻璃成为唯一暗色主题。其继承的 dark-vars/overrides/business.less 已重命名为 base-dark-*；system 在 OS 暗色下解析为 liquid-glass。

## 背景

CMDB 前端已具备 light / dark / system 三选项主题体系（见 [[2026-08-12-theme-settings-design]]）。当前深色主题采用实色面板（`#1e1e24` / `#121216`），视觉风格偏传统扁平。用户希望引入一种**流体玻璃（Liquid Glass）**毛玻璃主题，参考了 HTML 预览原型 [glass-preview.html](../brainstorms/glass-preview.html) 中的 `liquid` 方案。

## 目标

- 在现有三选项基础上新增 **"流体玻璃"** 作为第四种主题模式
- 流体玻璃以暗色为基底，叠加毛玻璃效果：半透明面板 + backdrop-filter 模糊 + 饱和度增强 + 液态弹簧微交互
- 覆盖所有业务页面（与 dark 主题同范围）
- 运行时即时切换，刷新/登出保留
- 不影响现有 light / dark / system 的行为

## 视觉定义

### 与现有 Dark 主题对比

| 属性 | Dark 主题 | Liquid Glass 主题 |
|------|-----------|-------------------|
| 基底背景 | `#121216` 纯色 | `#080a10` 纯色 + 径向渐变光斑（CSS background） |
| 面板背景 | `#1e1e24` 不透明 | `rgba(255,255,255,0.06)` 半透明 |
| 模糊滤镜 | 无 | `blur(24px) saturate(180%)` |
| 边框 | `1px solid #2e2e38` | `1px solid rgba(255,255,255,0.16)` 更亮 |
| 内阴影高光 | `inset 0 1px 0 rgba(255,255,255,0.05)` | `inset 0 1px 1px rgba(255,255,255,0.35)` + `inset 0 -1px 1px rgba(0,0,0,0.2)` 双面折射 |
| 面板投影 | `0 8px 32px rgba(0,0,0,0.2)` | `0 30px 60px rgba(0,0,0,0.4)` 更深 |
| 圆角 | `2px` (antd base) / `4px` (box) | `24px` 大盘面 / `14px` 小组件 |
| Hover 过渡 | `ease` | `cubic-bezier(0.175, 0.885, 0.32, 1.275)` 弹簧曲线 |
| Hover 效果 | 背景色变 | 面板上浮 `translateY(-4px) scale(1.015)` + 高光增强 |

### 颜色体系

```
Base background:   #080a10
Glass panel bg:    rgba(255, 255, 255, 0.06)
Glass panel hover: rgba(255, 255, 255, 0.12)
Glass border:      rgba(255, 255, 255, 0.16)
Text primary:      #f0f0f3 (同 dark)
Text secondary:    #9999a6 (同 dark)
Primary brand:     #6c5ce7 (同 dark)
Primary accent:    #a78bfa (lighter, for glass highlights)
```

背景光斑采用 CSS `radial-gradient` 叠加在 body 上，通过面板 `backdrop-filter` 产生透光折射效果。

## 技术路线

**复用现有主题基础设施**，新增第四种模式 `liquid-glass`：

```
现有:  light ← static.less 基础变量（默认）
       dark  ← public/themes/dark.css（独立编译）
       system → 解析为 light 或 dark

新增:  liquid-glass ← public/themes/liquid-glass.css（独立编译，基于 dark 变量 + 玻璃特效）
```

### 核心 CSS 差异

Liquid Glass 相比 dark 主题，CSS 层面的核心变化只有三处：

```less
// 1. 面板底色改为半透明
@component-background: rgba(255, 255, 255, 0.06);  // 替代 #1e1e1e

// 2. 开启 backdrop-filter
html[data-theme='liquid-glass'] .ant-layout,
html[data-theme='liquid-glass'] .ant-card,
html[data-theme='liquid-glass'] .ant-layout-sider, ... {
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
}

// 3. 增强高光边框
html[data-theme='liquid-glass'] ... {
  box-shadow: ...,
              inset 0 1px 1px rgba(255,255,255,0.35),
              inset 0 -1px 1px rgba(0,0,0,0.2);
}
```

## 运行时设计

### 状态扩展

```js
// setting.js 默认值不变
themeMode: 'system',  // 'light' | 'dark' | 'system' | 'liquid-glass'

// resolveTheme() 扩展
resolveTheme(mode) {
  if (mode === 'system') return getSystemDark() ? 'dark' : 'light'
  if (mode === 'liquid-glass') return 'liquid-glass'
  return mode === 'dark' ? 'dark' : 'light'
}
```

- `data-theme` 属性值新增 `'liquid-glass'`
- `resolveTheme('liquid-glass')` → `'liquid-glass'`（不跟随系统，始终玻璃）

### applyTheme() 扩展

```js
function syncGlassCss(theme) {
  const link = document.getElementById('theme-style')
  if (theme === 'dark') {
    // 加载 dark.css（现有逻辑）
  } else if (theme === 'liquid-glass') {
    // 加载 liquid-glass.css
  } else {
    // 移除 link
  }
}
```

### 系统模式行为

| themeMode | 解析结果 | 跟随系统变化 |
|-----------|----------|-------------|
| `system` | `light` 或 `dark` | 是 |
| `light` | `light` | 否 |
| `dark` | `dark` | 否 |
| `liquid-glass` | `liquid-glass` | 否（手动模式） |

> Liquid Glass 不与 system 模式产生交集 — 用户显式选择后恒定不变。

## UI 设计（userPanel.vue）

主题行从三段式扩展为四段式：

```
主题设置    [浅色 | 深色 | 流体 | 跟随系统]
```

```js
themeList: [
  { title: '浅色', key: 'light' },
  { title: '深色', key: 'dark' },
  { title: '流体', key: 'liquid-glass' },        // 新增
  { title: '跟随系统', key: 'system' },
]
```

## 构建

### build-theme.js 扩展

现有脚本编译 `dark.less` → `dark.css`。改为通用化：接受参数编译多个主题产物。

```bash
node scripts/build-theme.js dark          # → public/themes/dark.css（现有）
node scripts/build-theme.js liquid-glass  # → public/themes/liquid-glass.css（新增）
```

### liquid-glass.less 结构

```less
@import "./liquid-glass-vars.less";           // 玻璃变量（基于 dark-vars 覆盖为半透明）

html[data-theme='liquid-glass'] {
  @import "ant-design-vue/lib/style/index.less";
  @import "ant-design-vue/lib/style/components.less";
  @import "../global.less";
  @import (multiple) "./liquid-glass-vars.less";
}

@import "./liquid-glass-overrides.less";      // 玻璃专属覆盖
```

### key insight：减少重复代码

Liquid Glass 的 80% 变量值与 dark 相同（文本色、图标色、禁用色等），仅面板背景/边框/阴影不同。方案：

- `liquid-glass-vars.less` **从 dark-vars.less 继承**所有变量，仅覆盖玻璃相关的 ~20 个变量
- `liquid-glass-overrides.less` **仅写玻璃独有的** backdrop-filter / box-shadow 增强 / 圆角 / 过渡动画，不重复 dark-overrides.less 的 760 行业务覆盖

## 兼容性

### backdrop-filter 浏览器支持

| 浏览器 | 支持版本 |
|--------|---------|
| Chrome / Edge | 76+ |
| Safari | 9+ (需 `-webkit-` 前缀) |
| Firefox | 103+ |
| IE | 不支持 |

> CMDB 目标用户为现代浏览器，backdrop-filter 覆盖率 > 95%。对不支持的浏览器，面板退化为实色半透明（rgba 底色仍生效），视觉效果降级但功能正常。

### 性能影响

- `backdrop-filter: blur()` 会触发 GPU 合成层，增加内存占用
- `saturate()` 影响较小
- 单页面 ~20 个玻璃面板，实测性能影响可接受（与 dark 主题同量级）

## 改动范围

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `scripts/build-theme.js` | 修改 | 通用化支持多主题编译 |
| `src/style/themes/liquid-glass.less` | **新增** | 玻璃主题编译入口 |
| `src/style/themes/liquid-glass-vars.less` | **新增** | 玻璃变量（基于 dark-vars 覆盖） |
| `src/style/themes/liquid-glass-overrides.less` | **新增** | 玻璃专属覆盖 |
| `src/utils/theme.js` | 修改 | resolveTheme/applyTheme/syncDarkCss 扩展 |
| `src/store/global/app.js` | 修改 | TOGGLE_THEME_MODE 扩展 |
| `src/config/setting.js` | 修改 | 默认值不变 |
| `src/components/tools/userPanel.vue` | 修改 | 主题行增加"流体"按钮 |
| `src/lang/zh.js`、`src/lang/en.js` | 修改 | i18n: `themeLiquidGlass` |
| `public/index.html` | 修改 | 防闪脚本扩展 |
| `package.json` | 修改 | `theme:build` 扩展 |

**不需要**逐业务页覆盖 — 因为复用 `html[data-theme='liquid-glass']` 前缀 + dark 已有的业务覆盖（dark-business.less / dark-overrides.less 中 80% 的 `#1e1e24` 等实色值替换为半透明变量即可被 liquid-glass 覆盖）。

## 技术约束

- 复用现有主题编译链路（less@3.13.1 + javascriptEnabled + paths）
- `data-theme='liquid-glass'` 前缀特异性与 dark 相同（0,2,1）
- 不引入额外 npm 依赖
- Vue 2.6 Options API
- 产物 `liquid-glass.css` 与 `dark.css` 互斥加载（不同时存在）
