# 暗色主题配色规范

> 日期：2026-08-12 | 状态：待实施

## 背景

当前暗色主题采用纯灰色系（`#141414` / `#1f1f1f` / `#262626`）搭配 `rgba(255,255,255,x)` 文字色，存在以下不足：

1. **背景层级不够丰富** — 纯灰色缺乏冷色调带来的视觉深度
2. **文字对比度偏低** — 主文字 ~#D9D9D9，次要文字 ~#737373
3. **主色调不够突出** — `#2f54eb` 在暗色背景下饱和度不足
4. **状态色未针对暗色背景优化** — 沿用亮色模式 antd 默认值
5. **边框/分割线较重** — `#434343` / `#303030` 分割感过强

本规范定义一套新的暗色主题配色体系，以蓝紫冷色调为基调，提高各层级对比度与表现力。

## 设计原则

- **层级叠加感**：通过色阶变化（Z-index）而非纯黑建立 UI 视觉深度
- **适度提高明度**：暗色模式下状态色需提明度、降饱和度
- **蓝紫冷色调**：以微偏蓝紫的深灰替代纯灰，更符合现代暗色 UI 审美
- **可计算映射**：保持 hex 色值体系，自动生成脚本可直接映射

## 配色体系

### 一、背景体系（Background & Surface）

背景通过三个色阶建立 Z-index 视觉深度：

| 层级 | 变量 | 色值 | 用途说明 |
|------|------|------|----------|
| Base（最深） | `@body-background` | **`#1A1A1E`** | 页面主背景，比纯黑略亮，与浮层产生层级叠加 |
| Surface 1 | `@component-background` | **`#1E1E24`** | 卡片、输入框、下拉菜单、侧边栏、弹窗 |
| Surface 2（Hover / 浮起） | `@table-row-hover-bg` | **`#2A2A32`** | 表格行悬停、选中态、hover 高亮态 |

```
视觉深度示意：
  #1A1A1E  ← 页面背景（最深，衬托上层）
  #1E1E24  ← 卡片/容器（浮起一层）
  #2A2A32  ← Hover/选中态（再浮起一层）
```

### 二、文字体系（Text）

| 层级 | 变量 | 色值 | 不透明度等效 | 用途说明 |
|------|------|------|-------------|----------|
| 主文字 | `@text-color` / `@heading-color` | **`#E6E6E6`** | ~90% | 正文、标题，清晰可读且不刺眼 |
| 次要文字 | `@text-color-secondary` | **`#9999A6`** | ~60% | 辅助说明、标签、时间戳 |
| 禁用/提示 | `@disabled-color` | **`#555562`** | ~33% | 占位符、不可用状态 |

### 三、主功能色（Primary Palette）

品牌主色从 `#2f54eb`（暗蓝）升级为 `#4E6EE8`（高饱和中高明度蓝），在暗色背景下更醒目。

#### 3.1 核心主色

| 变量 | 色值 | 说明 |
|------|------|------|
| `@primary-color` | **`#4E6EE8`** | 主功能色/图标/链接 |
| `@primary-color_2` | **`#7C8FFF`** | 浅主色，侧边栏选中文字、高亮文本 |
| `@primary-color_9` | **`#6C5CE7`** | 较深主色，用于需要弱一级的主色场景 |

#### 3.2 按钮色

| 场景 | 色值 | 说明 |
|------|------|------|
| 主按钮背景 | **`#6C5CE7`** | Action Button，悬停叠加 10% 白色遮罩 |
| 幽灵按钮边框/文字 | **`#A29BFE`** | 非核心操作，减少视觉负担 |

#### 3.3 antd 色调色板（@primary-1 至 @primary-10）

基于 `#4E6EE8` 重新计算，必须显式覆盖（否则 antd colorPalette 会重算出过亮浅调）：

```less
@primary-1:  #151C30;   // 最深，选中行/悬停背景
@primary-2:  #1C2747;   // 树节点选中背景
@primary-3:  #223260;   // 浅色背景
@primary-4:  #293E79;   // 浅色背景（更亮）
@primary-5:  #4E6EE8;   // 品牌主色
@primary-6:  #4E6EE8;   // 品牌主色（hover 同色，通过 opacity 区分）
@primary-7:  #607DE9;   // 浅色主色（用于 hover 背景等）
@primary-8:  #4055A8;   // 深色主色
@primary-9:  #33427D;   // 更深
@primary-10: #25305A;   // 最深主色色调
```

### 四、状态色（Status Colors）

暗色模式下提高明度、降低饱和度：

| 状态 | 前景色 | Alert/Tag 背景色 | Alert/Tag 边框色 |
|------|--------|-----------------|-----------------|
| Success | **`#00E676`** | `#0A1F12` | `#144D24` |
| Warning | **`#FFB74D`** | `#2B1E11` | `#594214` |
| Error | **`#FF5252`** | `#2A1215` | `#58181C` |
| Info | `#4E6EE8` | `#111D2C` | `#15395B` |

### 五、边框与分割色

| 变量 | 色值 | 说明 |
|------|------|------|
| `@border-color-base` | **`#3A3A45`** | 常规边框（比旧值 `#434343` 更柔和） |
| `@border-color-split` | **`#2A2A32`** | 分割线（与 Surface 2 一致，融入背景层次） |
| `@border-color-inverse` | `#1E1E24` | 反色边框 |

### 六、项目文字色阶（@text-color_1 ~ @text-color_7）

镜像 `static.less` 语义的暗色版，用于项目自定义组件：

```less
@text-color_1: #E6E6E6;   // 主文字（替代 #e5e6eb）
@text-color_2: #9999A6;   // 次要文字（替代 #a9aeb8）
@text-color_3: #8F959E;   // 三级文字（替代 #8f959e）
@text-color_4: #555562;   // 禁用/提示（替代 #5d606e）
@text-color_5: #3A3A45;   // 最浅色文字（替代 #3c3f4e）
@text-color_6: #2A2A32;   // 极浅色/分割线（替代 #2a2d39）
@text-color_7: #1E1E24;   // 接近背景色（替代 #16181a）
```

### 七、项目主色色阶（@primary-color_3 ~ @primary-color_8）

```less
@primary-color_2: #7C8FFF;   // 浅主色高亮（替代 #7f97fa）
@primary-color_3: #1C2747;   // 主色调（替代 #1a1f2e）
@primary-color_4: #212F57;   // 主色调（替代 #1f2738）
@primary-color_5: #1A2342;   // 主色调（替代 #171e2e）
@primary-color_6: #161C30;   // 主色调（替代 #14181f）
@primary-color_7: #1A1A1E;   // 与 body-background 一致（替代 #141414）
@primary-color_8: #A29BFE;   // 幽灵按钮色（替代 #b1c9ff）
```

### 八、侧边栏变量

```less
@layout-sidebar-color:              #1E1E24;   // 侧边栏背景（替代 #1f1f1f）
@layout-sidebar-sub-color:          #16161C;   // 子菜单背景（替代 #16181a）
@layout-sidebar-selected-color:     #1C2747;   // 选中项背景（替代 #1a1f2e）
@layout-sidebar-arrow-color:        #555562;   // 箭头颜色
@layout-sidebar-font-color:         #9999A6;   // 菜单文字（替代 #a9aeb8）
@layout-sidebar-icon-color:         #555562;   // 图标颜色
@layout-sidebar-selected-font-color:#7C8FFF;   // 选中文字（替代 #7f97fa）
@layout-sidebar-disabled-font-color:#555562;   // 禁用文字
```

### 九、其他关键变量

```less
// 布局
@layout-body-background:     #1A1A1E;
@layout-header-background:   #1E1E24;
@layout-trigger-background:  #1E1E24;
@layout-trigger-color:       #E6E6E6;
@layout-content-background:  #1A1A1E;

// 输入控件
@input-bg:                   #1E1E24;
@input-addon-bg:             #2A2A32;
@input-placeholder-color:    #555562;

// 按钮
@btn-default-color:          #E6E6E6;
@btn-default-bg:             #1E1E24;
@btn-default-border:         #3A3A45;
@btn-disable-color:          #555562;
@btn-disable-bg:             rgba(255, 255, 255, 0.04);
@btn-disable-border:         #2A2A32;

// 表格
@table-header-bg:            #1E1E24;
@table-header-color:         #E6E6E6;
@table-row-hover-bg:         #2A2A32;
@table-selected-row-bg:      #2A2A32;
@table-expanded-row-bg:      #1E1E24;
@table-footer-bg:            #1E1E24;

// 浮层/弹窗
@popover-bg:                 #1E1E24;
@modal-header-bg:            #1E1E24;
@modal-mask-bg:              rgba(0, 0, 0, 0.65);
@tooltip-bg:                 #3A3A45;

// 卡片
@card-background:            #1E1E24;
@card-actions-background:    #16161C;
@card-skeleton-bg:           #2A2A32;

// 标签
@tag-default-bg:             rgba(255, 255, 255, 0.06);
@tag-default-color:          #E6E6E6;

// 菜单
@menu-bg:                    #1E1E24;
@menu-popup-bg:              #1E1E24;
@menu-item-color:            #E6E6E6;
@menu-highlight-color:       #4E6EE8;
@menu-dark-bg:               #1E1E24;
@menu-dark-submenu-bg:       #16161C;
@menu-dark-highlight-color:  #7C8FFF;

// 其他
@item-active-bg:             @primary-1;
@item-hover-bg:              @primary-1;
@link-hover-color:           @primary-5;
@scrollbar-color:            rgba(78, 110, 232, 0.4);
```

### 十、CSS 自定义属性

在 `html[data-theme='dark']` 下设置：

```css
--ops-side-menu-search-bg: #1E1E24;
--ops-topo-canvas-bg: #1A1A1E;
--ops-pane-trigger-bg: #1E1E24;
```

## 自动生成颜色映射表

`gen-dark-business.js` 的 `COLOR_MAP` 需更新，将亮色 hex 映射到新暗色调色板：

```js
const COLOR_MAP = {
  '#ffffff': '#1E1E24',
  '#f7f8fa': '#1E1E24',
  '#fafafa': '#1E1E24',
  '#f9fbff': '#161C30',
  '#f5f5f5': '#2A2A32',
  '#f5f7fa': '#2A2A32',
  '#f0f0f0': '#2A2A32',
  '#f0f2f5': '#1A1A1E',
  '#f0f1f5': '#1E1E24',
  '#ebeff8': '#1C2747',
  '#f0f5ff': '#1A2342',
  '#f4f9ff': '#1C2747',
  '#e8eaed': '#2A2A32',
  '#e4e7ed': '#2A2A32',
  '#e9e9e9': '#2A2A32',
  '#e1efff': '#212F57',
  '#eeeeee': '#2A2A32',
  '#f6f6f6': '#2A2A32',
  '#f2f3f5': '#2A2A32',
  '#f5f8fe': '#1C2747',
  '#e5e7eb': '#2A2A32',
  '#f8f9fd': '#1E1E24',
  '#f2f6fc': '#1C2747',
  '#fff1f0': '#2A1215',
  '#e6f7ff': '#111D2C',
  '#f0f7ff': '#1C2747',
  '#eff3fa': '#1E1E24',
}
```

## 对照总表

| 元素 | 旧值 | 新值 | 变更摘要 |
|------|------|------|----------|
| 页面背景 | `#141414` | `#1A1A1E` | 微亮、微偏蓝紫 |
| 卡片/容器 | `#1f1f1f` | `#1E1E24` | 微偏蓝紫 |
| Hover 浮层 | `#262626` | `#2A2A32` | 更亮、更偏蓝紫 |
| 主文字 | `rgba(255,255,255,0.85)` | `#E6E6E6` | 更亮更清晰 |
| 次要文字 | `rgba(255,255,255,0.45)` | `#9999A6` | 更亮、偏紫调 |
| 禁用文字 | `rgba(255,255,255,0.3)` | `#555562` | 接近不变 |
| 主功能色 | `#2f54eb` | `#4E6EE8` | 更高饱和度明度 |
| 主按钮 | (无独立) | `#6C5CE7` | 新增紫色调 CTA |
| 幽灵按钮 | (无独立) | `#A29BFE` | 新增、浅紫色 |
| 常规边框 | `#434343` | `#3A3A45` | 更柔和 |
| 分割线 | `#303030` | `#2A2A32` | 与 Surface 2 统一 |
| Success | antd default | `#00E676` | 高明度绿 |
| Warning | antd default | `#FFB74D` | 高明度橙 |
| Error | antd default | `#FF5252` | 高明度红 |

## 技术约束

- 所有色值使用 **hex 6 位小写**（`#1a1a1e` 格式），保持与生成脚本匹配的一致性
- antd 变量中的 `rgba(255,255,255,x)` 保留（部分 antd 内部计算依赖），仅项目层文字色改用 hex
- `@primary-1..10` 必须全部显式覆盖，防止 antd `colorPalette()` 自动重算出过亮 tint
- `gen-dark-business.js` 的 `COLOR_MAP` 中亮色阈值 `>= #e0e0e0` 保持不变，仅修改目标暗色值
