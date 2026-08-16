# cmdb-ui-vue3 共享依赖迁移 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 cmdb 视图迁移引入并注册核心第三方库，先解锁最重的 vxe-table（37 文件）与 vue-treeselect（18 文件）。

**Architecture:** 用 pnpm 添加依赖；在 `src/` 下建一个插件装配文件统一注册（vxe-table + vxe-pc-ui + treeselect），供 `main.ts` 调用。

## Task 1: 添加并注册 vxe-table 4 + treeselect v3

- [ ] 添加依赖：`pnpm add vxe-table@^4 vxe-pc-ui@^4 @riophae/vue-treeselect@^3`
- [ ] 建 `src/plugins/vxe.ts`：`VXETable` + `VxeUI` 装配（i18n 用 vue-i18n；样式 `import 'vxe-table/lib/style.css'` 与 `vxe-pc-ui/lib/style.css`）。
- [ ] 建 `src/plugins/treeselect.ts`：注册 `Treeselect` 组件 + 样式。
- [ ] `main.ts` 装配这两个插件。
- [ ] 验证：`pnpm typecheck && pnpm build && pnpm lint` 通过；`pnpm test` 仍 18 通过。

## Task 2: 添加 monaco + echarts（框架无关，按需）

- [ ] `pnpm add monaco-editor@^0.52 echarts@^5`（若后续子域需要再引入 wrapper；本阶段只装依赖，不强制装配）。

## 后续（不在本计划）
- cmdb 共享组件（components/ 19 个）分批迁移。
- ci_type 子域（48 视图）迁移。
