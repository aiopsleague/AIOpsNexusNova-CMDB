# cmdb-ui-vue3 共享组件迁移 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 迁移 acl 视图所依赖的共享组件到 Vue3 外壳，为后续 36 个 acl 视图迁移铺路。仅迁移实际被 acl 视图引用的组件（YAGNI）。

**Architecture:** 组件放 `cmdb-ui-vue3/src/components/`，用 `<script setup lang="ts">` + AntD 4。Vue2→Vue3 关键差异：`$listeners` 并入 `$attrs`；`a-icon type=` → `@ant-design/icons-vue`；`bodyStyle` → AntD4 的 `styles.body`；Less 的 `@primary-color` → `COLOR_PRIMARY` token。

**范围（依据实际引用统计）：**
- `CustomDrawer`（14 个 acl 视图引用）—— 必须
- `Pager`（10 个）—— 必须
- `CustomTransfer`（1 个）—— 必须
- `TagSelect`（1 个 `resourceBatchPerm.vue`）—— 本计划**暂缓**（Vue3 下需重写 `componentOptions` 逻辑，随该视图迁移时一并处理）
- 全局 i18n 键 `itemsPerPage`（Pager 依赖，值为 `/页`、`/page`）

---

## Task 1: 迁移 CustomDrawer / Pager / CustomTransfer + i18n 键

**Files:**
- Create: `cmdb-ui-vue3/src/components/CustomDrawer/index.vue`
- Create: `cmdb-ui-vue3/src/components/Pager/index.vue`
- Create: `cmdb-ui-vue3/src/components/CustomTransfer/index.vue`
- Modify: `cmdb-ui-vue3/src/lang/zh.ts` / `en.ts`（追加 `itemsPerPage` 到顶层）

**参考旧源码路径（供比对）：** `cmdb-ui/src/components/CustomDrawer/CustomDrawer.vue`、`cmdb-ui/src/components/Pager/index.vue`、`cmdb-ui/src/components/CustomTransfer/CustomTransfer.vue`。

### CustomDrawer（Vue3 重写要点）
- 用 `a-drawer`；`open` 用 `v-model:open` 双向（父组件控制显隐）。
- `closable=false` + 自绘关闭按钮；关闭图标按 `placement` 映射：`top→UpOutlined`、`bottom→DownOutlined`、`left→LeftOutlined`、`right/默认→RightOutlined`（`@ant-design/icons-vue`）。
- `bodyStyle` → AntD4 `:styles="{ body: { maxHeight, overflow: 'auto' } }"`。
- 主题色用 `@/theme/tokens` 的 `COLOR_PRIMARY`（关闭按钮背景）；hover 色用 `#597ef7`。
- 标题槽：`<template #title>`；保留 `hasTitle`/`hasFooter`/`title` props。
- 关闭：点按钮 emit `close` + `update:open=false`。

### Pager（Vue3 重写要点）
- props：`currentPage/pageSize/pageSizes/total/isLoading`；events：`change`(page)、`showSizeChange`(size)。
- 图标：`LeftOutlined/RightOutlined/DownOutlined`；`a-space`/`a-dropdown`/`a-menu`（AntD4 无 `slot=overlay`，改用 `<template #overlay>`）。
- `prevIsDisabled`/`nextIsDisabled`/`dropdownIsDisabled` 逻辑与旧版一致。
- 文案 `itemsPerPage` 用 `t('itemsPerPage')`（需新增 i18n 键）。

### CustomTransfer（Vue3 重写要点）
- 包装 `a-transfer`，透传 `$attrs`，绑定 `data-source`/`target-keys`。
- 保留双击穿梭的 `leftToRight`/`rightToLeft`/`dbClick` 方法，用 `defineExpose` 暴露（旧版父组件通过 `ref.dbClick(...)` 调用）。`e.toElement` → `e.target`。
- DOM 选择器沿用 `ant-transfer-list-content`（AntD4 transfer 类名一致）。

### i18n 追加
`zh.ts` 顶层加 `itemsPerPage: '/页'`；`en.ts` 顶层加 `itemsPerPage: '/page'`。

## 验证与提交
- `cd cmdb-ui-vue3 && pnpm typecheck && pnpm test && pnpm build && pnpm lint` 全通过。
- 提交：`feat(ui): migrate CustomDrawer, Pager and CustomTransfer shared components`。

## 后续（不在本计划）
- `TagSelect`（随 `resourceBatchPerm.vue` 迁移时处理）。
- acl 36 视图逐实体迁移。
