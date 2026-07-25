# Grafana 变量映射表格化 + 映射条目启用 设计文档

日期：2026-07-25
状态：已确认
前置：`2026-07-25-grafana-integration-design.md`、`2026-07-25-grafana-mapping-enhancement-design.md`

## 目标

1. 映射弹窗中的变量映射改为表格展示（区域滚动），列：源、映射类型（固定值/字段）、目标、说明。
2. 映射类型=固定值 → 目标手填字面量；=字段 → 目标为当前 CI 类型属性（显示 `alias(name)`）。
3. 变量映射的源（Grafana 变量）在同一映射内不可重复。
4. 说明列：选中变量时自动带出 Grafana 变量的 description，无描述可手填。
5. 映射记录增加"是否启用"，停用的映射解析时跳过。

## 数据模型

### var_mapping 元素（新结构）

```json
{"grafana_var": "instance", "map_type": "field", "value": "ip", "remark": "实例IP"}
```

- `map_type`：`"field"`（value 为 CI 属性名）或 `"fixed"`（value 为字面量，原样传给 Grafana）。
- `grafana_var` 同一映射内唯一（前端选择时禁用已选项 + 后端 400 校验）。
- `remark` 可空字符串。
- **轻量兼容**：上一版 `{grafana_var, ci_attr}` 旧行在 `build_vars` 读取时按 `map_type="field", value=ci_attr` 处理；下次编辑保存时归一化为新结构。不做 UI 层旧格式展示兼容之外的迁移。

### 映射记录新增 `enable`

- `enable`：1 启用 / 0 停用，缺省 1（旧记录按启用）。
- `pick_dashboard` 跳过 `enable == 0` 的映射（视同无映射，继续全局搜索兜底）。

## 后端改动（cmdb-api-fastapi）

### `grafana_client.py`

- `get_dashboard_variables(name)` 返回 `[{"name": str, "description": str}]`（description 取 templating 变量的 `description` 或空串；仍排除 datasource 类型与无名变量）。
- `build_vars(mapping, ci, unique_value)`：
  - 每行：`map_type = vm.get("map_type") or "field"`；`value_ref = vm.get("value", vm.get("ci_attr"))`（兼容旧键）。
  - `fixed` → `{"name": grafana_var, "value": value_ref}` 原样加入（空字符串也跳过）。
  - `field` → 取 `ci[value_ref]`，None/""/[] 跳过。
  - `mapping is None` 时保持 `ci_name=unique_value` 兜底。
- `pick_dashboard`：`mappings` 过滤 `m.get("enable", 1) != 0` 后再匹配 ci_type。

### `grafana.py`（CRUD）

- `_valid_var_mapping` 升级：
  - 每元素必须 dict；`grafana_var` 非空；`map_type` 缺省 `"field"` 且必须在 `("field", "fixed")`；`value` 非空（兼容读 `ci_attr`）；`remark` 取字符串（缺省 `""`）。
  - `grafana_var` 重复 → `abort(400, ErrFormat.value_is_required)`。
  - 输出归一化新结构（写入不再有 `ci_attr` 键）。
- 映射 create/update 接受 `enable`（复用 `_to_enable`），`list_mappings` 返回的记录补 `enable` 缺省 1。

### 视图

- variables 端点响应改为 `{"variables": [{"name", "description"}]}`（结构变化，前端同步改）。

## 前端改动（cmdb-ui）

### 映射弹窗：变量映射 a-table

- `a-table`：`:data-source="mappingForm.var_mapping"`、`:pagination="false"`、`:scroll="{ y: 240 }"`、size small，行 key 用 index。
- 列：
  - **源**：`a-auto-complete`，options 来自 variables 端点（显示 name），`:filter-option` 按 name 过滤；已被其他行选中的变量 option `disabled`；选中后若该行说明为空且变量有 description 自动填入。
  - **映射类型**：`a-select`，选项 `字段(field)` / `固定值(fixed)`，默认 field；切换时清空目标。
  - **目标**：`map_type==='field'` → `a-select`（show-search，候选为 CI 属性，选项文案 `alias(name)`，无 alias 时只显示 name）；`==='fixed'` → `a-input`。
  - **说明**：`a-input`。
  - **操作**：删除图标。
- 表下方"添加变量映射"按钮：新增行 `{grafana_var: undefined, map_type: 'field', value: undefined, remark: ''}`。
- 保存校验：每行源/目标非空；源不重复（前端先提示，后端兜底 400）。

### 映射列表 + 连接外其他

- 映射表格新增**启用列**（a-switch，`putGrafanaMapping(id, {enable})` 快速切换）。
- 映射表单增加启用开关（新建默认 1，编辑取 record.enable ?? 1）。
- `var_mapping` 摘要列更新为新结构（`instance←ip` / `env=prod` 形式：field 用 `←`，fixed 用 `=`）。

### i18n（zh/en，cs.grafana 块）

新增：`source: '源'`, `mapType: '映射类型'`, `mapTypeField: '字段'`, `mapTypeFixed: '固定值'`, `target: '目标'`, `remark: '说明'`, `duplicateSource: '变量映射的源不能重复'`（en 对应翻译）。复用已有 `enable`。

## 错误处理

- variables 端点现在返回对象数组；前端 `variableOptions` 结构同步（`{name, description}`），拉取失败仍可手填变量名（说明为空）。
- 变量列表用于"源"下拉与说明自动填充；变量描述缺失时说明留空可手填。

## 测试

- 后端单测（mock）：
  1. `get_dashboard_variables` 返回 name+description、排除 datasource。
  2. `build_vars`：field 取值、fixed 原样、旧格式 ci_attr 兼容、空值跳过、无映射兜底。
  3. `pick_dashboard`：跳过 `enable=0` 的映射（该类型视同无映射走全局搜索）。
  4. `_valid_var_mapping` 重复源 400（如可测——DB 依赖则改为人工核验，优先保持纯函数可测部分）。
- E2E（真实 Grafana）：variables 带 description；建映射含一行 field 一行 fixed，resolve 返回对应 vars；停用映射后 resolve 走兜底；清理。

## 涉及文件

**修改**
- `cmdb-api-fastapi/api/lib/common_setting/grafana_client.py`
- `cmdb-api-fastapi/api/lib/common_setting/grafana.py`
- `cmdb-api-fastapi/tests/test_grafana_client.py`
- `cmdb-ui/src/views/setting/grafana/index.vue`
- `cmdb-ui/src/views/setting/lang/zh.js`、`en.js`
