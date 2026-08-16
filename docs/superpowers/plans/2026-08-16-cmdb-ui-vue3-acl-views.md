# cmdb-ui-vue3 acl 视图迁移 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 acl 模块的 36 个 Vue2 视图迁移到 Vue3 `<script setup lang="ts">` + Ant Design Vue 4，复用已就位的类型化 API 客户端、i18n 键（`acl.*`）、共享组件（CustomDrawer/Pager/CustomTransfer）与 `v-action` 指令。目前这些视图是占位页。

**Architecture:** 每个视图独立迁移，放在 `cmdb-ui-vue3/src/modules/acl/views/` 对应位置，替换占位页。旧源码在 `cmdb-ui/src/modules/acl/views/`（逐文件对照）。

**迁移顺序（依赖优先，先简后繁）：**
1. `secretKey`（独立，101 行）
2. `apps` + `appForm`（独立，112+90）
3. `resource_types` + `resourceTypeForm`（213+153）
4. `users` + `userForm` + `usersUnderRoleForm` + `resourceUserForm` + `searchForm`
5. `roles` + `roleForm`
6. `resources` + `resourceForm` + `resourceGroupModal` + `resourceGroupMember` + `permissionForm` + `permCollectForm` + `resourcePermForm` + `resourcePermManageForm` + `resourceBatchPerm`（含 TagSelect）
7. `trigger` + `triggerForm` + `triggerPattern`
8. `history` + 5 历史表 + `operation_history`（index + 5 表）

---

## 通用迁移规则（每个视图都遵循）

**Vue2 → Vue3：**
- Options API → `<script setup lang="ts">`；`data/computed/methods/watch` → `ref/reactive/computed/watch`。
- `this.$message/$notification/$confirm` → `import { message, notification, Modal } from 'ant-design-vue'`；`Modal.confirm`。
- `this.$router/$route` → `useRouter()/useRoute()`；`this.$refs.x` → `const x = ref()`。
- `this.$t()` → `const { t } = useI18n()`。
- `.sync` → `v-model:prop`；`:visible.sync` → `v-model:open`（AntD4 用 `open` 而非 `visible`）。
- 事件：`this.$emit('x', v)` → `const emit = defineEmits(['x'])`。
- `v-decorator` 表单 → AntD4 `a-form :model="form" :rules="rules"` + 控件 `name="field"` + `v-model:value="form.field"`；提交校验 `formRef.value.validate()`。
- `a-form-model` → `a-form`。
- `a-table` 列 `scopedSlots` → `<template #bodyCell="{ column, record, text }">`。
- `a-select` 的 `<a-select-option>` 保持不变，或用 `:options`。
- `moment` → `dayjs`。
- `<a-icon type="x">` → `@ant-design/icons-vue` 命名图标。
- `<ops-icon type>` → 暂时用 AntD 图标替代（iconfont 迁移后续再做）。

**API 调用：** 用 `@/modules/acl/api/*` 已导出的类型化函数；响应用 `unknown`/局部类型断言（`as { users: AclUser[] }` 等）。

**i18n：** 文案统一 `t('acl.xxx')`；列表列标题用已存在的 `acl.*` 键。

**全局组件：** `CustomDrawer`/`Pager`/`CustomTransfer` 从 `@/components/*` 显式导入（不再全局注册）。`v-action` 指令已全局注册。

**验证标准：** 每个视图组迁移后 `pnpm typecheck` 必须通过（`noUnusedLocals` 严格，移除未用导入）；`pnpm build` 通过。单测按需（纯逻辑才写）。

---

## Task 结构（每个实体组一个 Task）

每个 Task 的步骤：读旧视图 → 迁移为新 Vue3 文件 → 更新 manifest/componentMap 若路径变化（本迁移视图路径不变，无需改）→ typecheck+build → 提交。

提交信息：`feat(ui): migrate acl <entity> views`（例如 `feat(ui): migrate acl secretKey view`）。

## 后续（不在本计划）
- iconfont（`ops-icon`）迁移。
- cmdb 模块迁移。
