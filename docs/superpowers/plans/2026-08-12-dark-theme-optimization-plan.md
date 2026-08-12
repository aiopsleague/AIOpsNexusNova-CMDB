# 暗色主题配色优化方案

> 日期：2026-08-12 | 状态：待实施 | 分支：`feat/theme-settings`
> 关联规范：[2026-08-12-dark-theme-color-spec.md](../specs/2026-08-12-dark-theme-color-spec.md)

## 目标

将 CMDB 暗色主题从纯灰色系（`#141414` / `#1f1f1f` / `#262626`）升级为蓝紫冷色调深色体系（`#1A1A1E` / `#1E1E24` / `#2A2A32`），同时更新主色（`#2f54eb` → `#4E6EE8`）、文字色阶、状态色、边框色，全面提升暗色模式下的视觉层次感和对比度。

## 现状分析

### 当前暗色主题架构（已实施）

```
dark-vars.less (变量覆盖)
     ↓
dark.less (编译入口：antd + global.less + dark-vars)
     ↓
build-theme.js (less 独立编译)
     ↓
public/themes/dark.css (运行时 <link> 注入)
     ↓
+ dark-overrides.less (手动覆盖，编译入 dark.css)
+ dark-business.less (自动生成，编译入 dark.css)
```

### 当前颜色体系问题

| 问题 | 影响 |
|------|------|
| 纯灰色缺乏冷色调 | 背景层级扁平、缺乏现代感 |
| 主文字 ~#D9D9D9 | 在暗色背景上对比度不足 |
| 次要文字 ~#737373 | 可读性偏低 |
| 主色 `#2f54eb` 偏暗 | 暗色背景下图标/按钮不够突出 |
| 边框 `#434343` / `#303030` | 分割感太强 |
| 状态色沿用亮色 antd 默认 | 暗色模式下显得暗淡 |

## 改动范围

### 文件清单

| 序号 | 文件 | 改动类型 | 行数估算 | 说明 |
|------|------|----------|----------|------|
| 1 | `src/style/themes/dark-vars.less` | **重写** | ~80 行 | 替换全部颜色变量值 |
| 2 | `src/style/themes/dark-overrides.less` | **批量替换** | ~60 行 | 更新所有硬编码色值 |
| 3 | `scripts/gen-dark-business.js` | **改映射表** | ~25 行 | 更新 COLOR_MAP 目标暗色值 |
| 4 | `src/style/themes/dark-business.less` | **重新生成** | 自动 | 运行 gen-dark-business.js |
| 5 | `public/themes/dark.css` | **重新编译** | 自动 | 运行 build-theme.js |
| 6 | `src/utils/theme.js` | **1 行** | 1 行 | body 背景色 |
| 7 | `src/style/global.less` | **少量** | ~5 行 | `.dark` 类选择器硬编码色 |
| 8 | `src/components/MultiTab/MultiTab.vue` | **1 行** | 1 行 | 硬编码暗色背景 |
| 9 | `src/config/setting.js` | **1 行** | 1 行 | 更新 primaryColor 默认值 |

### 不改动的文件

- `dark.less` — 编译入口逻辑不变
- `build-theme.js` — 编译流程不变
- `theme.js` — 除 1 行色值外逻辑不变
- `static.less` — 亮色模式变量不变
- 所有 `.vue` 业务组件 — 由 dark-business.less 重新生成覆盖
- 所有 `src/lang/*` — i18n 不变

## 颜色映射方案

### 全局替换规则

```
旧值          → 新值           用途
──────────────────────────────────────────
#141414       → #1A1A1E       页面主背景
#1f1f1f       → #1E1E24       卡片/容器/组件背景
#262626       → #2A2A32       Hover/选中态/浮层
#303030       → #2A2A32       分割线（与 Surface 2 合并）
#434343       → #3A3A45       常规边框（更柔和）
#1a1a1a       → #16161C       旧深色背景
#2a2a2a       → #2A2A32       旧 input-addon 背景
#001529       → #1E1E24       侧边栏 antd dark 默认值
#000c17       → #16161C       侧边栏子菜单 antd dark 默认值
```

### 主色相关替换

```
旧值          → 新值           用途
──────────────────────────────────────────
#2f54eb       → #4E6EE8       品牌主色
#7f97fa       → #7C8FFF       浅主色/侧边栏高亮
#b1c9ff       → #A29BFE       幽灵按钮色
#3f75ff       → #6C5CE7       深主色/行动按钮
#131629       → #151C30       @primary-1
#1a2342       → #1C2747       @primary-2
#1f2f57       → #223260       @primary-3
#253a6b       → #293E79       @primary-4
#4158c9       → #607DE9       @primary-7
#32408f       → #4055A8       @primary-8
#2a3566       → #33427D       @primary-9
#20284a       → #25305A       @primary-10
```

### 项目变量替换

```
旧值          → 新值           变量
──────────────────────────────────────────
#1a1f2e       → #1C2747       @primary-color_3
#1f2738       → #212F57       @primary-color_4
#171e2e       → #1A2342       @primary-color_5
#14181f       → #161C30       @primary-color_6
#e5e6eb       → #E6E6E6       @text-color_1
#a9aeb8       → #9999A6       @text-color_2
#5d606e       → #555562       @text-color_4
#3c3f4e       → #3A3A45       @text-color_5
#2a2d39       → #2A2A32       @text-color_6
#16181a       → #16161C       @text-color_7 / @layout-sidebar-sub-color
```

## 实施步骤

### 阶段 1：核心变量（dark-vars.less）

修改 `src/style/themes/dark-vars.less`，逐节替换：

**1.1 基础色（第 11-26 行）**
- `@body-background`: `#141414` → `#1A1A1E`
- `@component-background`: `#1f1f1f` → `#1E1E24`
- `@text-color`: `rgba(255,255,255,0.85)` → `#E6E6E6`
- `@text-color-secondary`: `rgba(255,255,255,0.45)` → `#9999A6`
- `@disabled-color`: `rgba(255,255,255,0.3)` → `#555562`
- `@heading-color`: `rgba(255,255,255,0.85)` → `#E6E6E6`
- `@icon-color-hover`: `rgba(255,255,255,0.75)` → `#E6E6E6`
- `@border-color-base`: `#434343` → `#3A3A45`
- `@border-color-split`: `#303030` → `#2A2A32`

**1.2 主色调色板（第 29-42 行）**
- 全量替换 `@primary-1` 至 `@primary-10`（见颜色映射表）
- `@primary-color`: `#2f54eb` → `#4E6EE8`

**1.3 组件变量（第 44-131 行）**
- 表单/输入：`@input-bg` → `#1E1E24`，`@input-addon-bg` → `#2A2A32`
- 按钮：`@btn-default-bg` → `#1E1E24`，`@btn-default-border` → `#3A3A45`
- 表格：`@table-header-bg` → `#1E1E24`，`@table-row-hover-bg` → `#2A2A32`
- 菜单：`@menu-bg` → `#1E1E24`，`@menu-dark-bg` → `#1E1E24`，`@menu-dark-submenu-bg` → `#16161C`
- 浮层：`@popover-bg` / `@modal-header-bg` → `#1E1E24`
- 卡片：`@card-background` → `#1E1E24`，`@card-actions-background` → `#16161C`
- 状态色：`@alert-success-bg-color` / `@alert-warning-bg-color` 更新
- 标签：`@tag-default-bg` → `rgba(255,255,255,0.06)`

**1.4 项目变量（第 133-166 行）**
- `@text-color_1..7`：全量替换（见颜色映射表）
- `@primary-color_2..9`：全量替换
- `@layout-sidebar-*`：全量替换
- `@scrollbar-color`: `rgba(47,122,235,0.5)` → `rgba(78,110,232,0.4)`

### 阶段 2：手动覆盖（dark-overrides.less）

修改 `src/style/themes/dark-overrides.less`，按全局替换规则更新所有硬编码色值：

**2.1 背景类**
- `.ant-layout-content` / `.ant-layout` → `#1A1A1E`
- `.ant-layout-header` → `#1E1E24`
- `.ant-layout-sider` → `#1E1E24`
- `.split-pane` → `#1A1A1E`
- 所有 `.ant-*` 组件背景 → `#1E1E24`

**2.2 交互态**
- hover 背景 `#262626` → `#2A2A32`
- 选中态 `#131629` → `#151C30`
- 主色浅背景 `#171e2e` / `#1a1f2e` → 对应新值

**2.3 Tag 预设色**
- 更新各 tag 文字色以匹配新的状态色规范

**2.4 渐变色卡片**
- 将渐变起止色映射到新调色板

**2.5 CSS 变量**
- `--ops-side-menu-search-bg`: `#1f1f1f` → `#1E1E24`
- `--ops-topo-canvas-bg`: `#141414` → `#1A1A1E`
- `--ops-pane-trigger-bg`: `#1f1f1f` → `#1E1E24`

### 阶段 3：自动生成（gen-dark-business.js + 重新生成）

**3.1 修改 `scripts/gen-dark-business.js`**
- 更新 `COLOR_MAP` 目标值（见配色规范文档第 10 节）
- 映射逻辑 `mapColor()` 不变

**3.2 重新生成 `dark-business.less`**
```bash
cd cmdb-ui && node scripts/gen-dark-business.js
```

**3.3 重新编译 `dark.css`**
```bash
cd cmdb-ui && node scripts/build-theme.js
```

### 阶段 4：运行时 + 全局样式

**4.1 `src/utils/theme.js` 第 46 行**
```js
// document.body.style.backgroundColor = dark ? '#141414' : ''
document.body.style.backgroundColor = dark ? '#1A1A1E' : ''
```

**4.2 `src/style/global.less`**
- 第 224-250 行（`.header.dark`）：更新色值
  - `rgba(255,255,255,0.85)` → `#E6E6E6`
  - `rgba(255,255,255,0.16)` 保留（半透明白色叠底不变）
- 第 397 行（`.drawer-sider.dark`）：`rgb(0, 21, 41)` → `#1E1E24`

**4.3 `src/components/MultiTab/MultiTab.vue` 第 37 行**
```js
// background: this.navTheme === 'dark' ? '#1f1f1f' : '#FFF'
background: this.navTheme === 'dark' ? '#1E1E24' : '#FFF'
```

**4.4 `src/config/setting.js`**
```js
// primaryColor: '#2f54eb'
primaryColor: '#4E6EE8'
```

### 阶段 5：验证

1. **编译验证**
   ```bash
   cd cmdb-ui
   node scripts/gen-dark-business.js   # 验证生成成功
   node scripts/build-theme.js         # 验证编译成功
   ```

2. **视觉回归**
   - 启动 `yarn serve`，切换 light / dark / system 三种模式
   - 验证页面：CMDB 管理、CI 详情、ACL、Dashboard、IPAM、DCIM、拓扑图
   - 检查要点：
     - [ ] 页面背景从 `#141414` 变为 `#1A1A1E`（微亮、微偏紫）
     - [ ] 卡片/输入框从 `#1f1f1f` 变为 `#1E1E24`
     - [ ] 主文字更亮（`#E6E6E6` vs 原 `rgba(255,255,255,0.85)`）
     - [ ] 主色按钮从深蓝变为亮蓝 `#4E6EE8`
     - [ ] 边框更柔和（`#3A3A45` vs 原 `#434343`）
     - [ ] 表格 hover 行从 `#262626` 变为 `#2A2A32`
     - [ ] 侧边栏配色统一
     - [ ] ECharts 图表正常渲染
     - [ ] 无刺眼白块残留

3. **切换验证**
   - [ ] dark → light 切换无残留暗色
   - [ ] light → dark 切换完整覆盖
   - [ ] system 模式跟随系统偏好

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 自动生成覆盖不全 | 低 | 个别组件背景未变 | 手动在 dark-overrides.less 补充 |
| `rgba(0,0,0,x)` 文字在暗色下不可见 | 中 | 部分文字显示异常 | 由 dark-vars.less 变量覆盖解决（antd 组件），项目自定义 scoped 样式需抽查 |
| 颜色变化过大引起用户不适 | 低 | 用户反馈 | 整体蓝紫色调偏移极小（ΔE ≤ 5），主视觉变化是文字更亮更清晰 |
| 新 primary palette 计算偏差 | 中 | 部分组件主色色调异常 | 保留回退能力（git revert 单个变量文件） |
| gen-dark-business.js re-run 错误 | 低 | 业务模块暗色覆盖丢失 | 提交前重新生成并 diff-review |

## 回滚方案

所有改动集中在 4 个主题文件 + 少量运行时文件，回滚简单：

```bash
git checkout HEAD -- cmdb-ui/src/style/themes/dark-vars.less
git checkout HEAD -- cmdb-ui/src/style/themes/dark-overrides.less
git checkout HEAD -- cmdb-ui/src/style/themes/dark-business.less
git checkout HEAD -- cmdb-ui/public/themes/dark.css
git checkout HEAD -- cmdb-ui/scripts/gen-dark-business.js
git checkout HEAD -- cmdb-ui/src/utils/theme.js
git checkout HEAD -- cmdb-ui/src/style/global.less
git checkout HEAD -- cmdb-ui/src/components/MultiTab/MultiTab.vue
git checkout HEAD -- cmdb-ui/src/config/setting.js
```
