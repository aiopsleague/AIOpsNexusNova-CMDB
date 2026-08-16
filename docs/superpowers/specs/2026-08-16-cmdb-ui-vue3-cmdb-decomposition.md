# cmdb 模块迁移拆解（cmdb-ui-vue3）

> 日期：2026-08-16 | 状态：拆解完成，待逐子域执行
> 关联：[迁移设计](./2026-08-16-cmdb-ui-vue3-design.md)、[外壳 plan](../plans/2026-08-16-cmdb-ui-vue3-shell.md)、[acl infra](../plans/2026-08-16-cmdb-ui-vue3-acl-infra.md)、[acl 视图](../plans/2026-08-16-cmdb-ui-vue3-acl-views.md)

## 背景

cmdb 是 Vue2 前端最大的业务模块（**175 视图 + 19 API 文件 + 1780 行 API**），涵盖配置项(CI)、CI 类型、DCIM、IPAM、自动发现、拓扑、资源搜索、仪表盘等。迁移沿用已批准的架构（Vue3 + Vite + Pinia + AntD4 + TS，绞杀者式逐子域迁移，复用已就位的外壳/模块加载/请求层/i18n/主题/共享组件）。

## 子域拆解（按视图数）

| 子域 | 视图数 | 说明 |
|------|-------|------|
| ci_type（CI 类型/模型） | 48 | 核心：属性/关系/类型分组/预设值/自动发现配置 |
| ci（CI 实例） | 21 | CI 详情/关系拓扑/回滚 |
| dcim | 20 | 机房/机柜/设备 |
| ipam | 17 | 子网/IP 地址 |
| resource_search | 14 | 资源搜索(1+2 两代) |
| discovery(+discoveryCI) | 11 | 自动发现 |
| dashboard + custom_dashboard | 13 | 仪表盘/自定义仪表盘/统计 |
| topology + relation(views/type/model) | 8 | 拓扑与关系 |
| 其余 | 23 | batch(5)/operation_history(7)/preference(2+3)/tree_views(2)/fullscreen(3)/mobile(1) |

## 依赖迁移（视图前置，先做）

| 依赖 | 文件数 | Vue3 方案 |
|------|-------|-----------|
| vxe-table / vxe-grid | 37 | vxe-table 4 + vxe-pc-ui |
| vue-treeselect | 18 | @riophae/vue-treeselect v3 |
| vue-json-editor | 8 | 换 monaco 或 @json-editor（评估后定） |
| echarts / viser | 7 | echarts 5（保持）+ 轻量 wrapper |
| element-ui（date/time/select） | 4 | 换 AntD 4（已定） |
| relation-graph | 2 | relation-graph Vue3 build |
| butterfly-dag | 2 | butterfly-dag Vue3 build |
| monaco | 2 | monaco（保持，框架无关） |
| wangeditor | 1 | @wangeditor/editor-for-vue@next |
| cmdb 共享组件（components/ 下 19 个） | — | 逐个体迁移（ciTable/ciIcon/cmdbTypeSelect/conditionFilter/searchForm/JsonEditor 等） |

> 说明：OpsTable 在 cmdb 视图内 0 引用，不在 cmdb 依赖内；vxe-table 4 是最大的单点依赖（37 个文件）。

## 迁移顺序

1. **共享依赖**（vxe-table 4、treeselect、monaco、echarts、json-editor、relation-graph/butterfly-dag/wangeditor 视子域按需引入）+ cmdb 共享组件
2. **ci_type**（48，核心，最大）
3. **ci**（21）
4. **dcim**（20）
5. **ipam**（17）
6. **resource_search**（14）
7. **discovery**（11）
8. **dashboard**（13）
9. **topology/relation**（8）
10. **其余**（23）

每个子域 = 一个独立 plan + 独立执行（同 acl 视图的流程）。子域内部依赖复杂（列表视图 ↔ 表单/详情组件），迁移时按「列表 → 表单 → 详情/子组件」顺序，先简后繁。

## 非目标

- 不迁移 mobile（1 视图，独立移动端，低价值，暂缓）。
- 不改后端 API 契约。
