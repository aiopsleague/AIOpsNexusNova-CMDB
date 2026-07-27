# Grafana 仪表板映射 — 过滤规则 设计文档

日期：2026-07-27
状态：待确认
前置：`2026-07-25-grafana-var-mapping-table-design.md`

## 问题

同一个 CI 类型（如"虚拟机"）可能对应多个 Dashboard（如"Linux Dashboard"和"Windows Dashboard"）。当前 `pick_dashboard` 仅按 `ci_type_id` 匹配第一条启用映射，无法根据 CI 实例的属性（如 `os_type`）区分应使用哪个 Dashboard。

## 目标

在映射表中增加可选的**过滤规则（filter_rules）**，使同一 CI 类型下的不同映射可按 CI 实例属性精确匹配。

## 数据模型

### 映射记录新增 `filter_rules`

```json
{
  "id": 1,
  "ci_type_id": 5,
  "connection_id": 1,
  "dashboard_name": "linux-dashboard",
  "dashboard_title": "Linux Dashboard",
  "var_mapping": [...],
  "enable": 1,
  "filter_rules": {
    "logic": "and",
    "rules": [
      { "field": "os_type", "operator": "equal", "value": "Linux" }
    ]
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `filter_rules` | `object` \| `null` | 可选，`null` 时匹配该 `ci_type_id` 下所有 CI（兜底） |
| `filter_rules.logic` | `"and"` \| `"or"` | 多条规则之间的组合逻辑 |
| `filter_rules.rules` | `array` | 规则列表，至少 1 条 |
| `rules[].field` | `string` | CI 实例的属性名，如 `os_type`、`main_type`、`sub_type` |
| `rules[].operator` | `string` | 匹配运算符（见下方） |
| `rules[].value` | `string` \| `string[]` | 比较值；`in` / `not_in` 时为数组 |

### 六种运算符

| 运算符 | 含义 | `value` 类型 | 示例 |
|--------|------|-------------|------|
| `equal` | 等于 | `string` | `"os_type" equal "Linux"` |
| `not_equal` | 不等于 | `string` | `"os_type" not_equal "Windows"` |
| `contains` | 包含子串 | `string` | `"hostname" contains "prod"` |
| `not_contains` | 不包含子串 | `string` | `"hostname" not_contains "test"` |
| `in` | 在列表中 | `string[]` | `"os_type" in ["Linux", "CentOS", "Ubuntu"]` |
| `not_in` | 不在列表中 | `string[]` | `"os_type" not_in ["Windows", "Win10"]` |

### 组合示例

**场景：Server 类型 + Linux 系统的 VM**

```json
{
  "logic": "and",
  "rules": [
    { "field": "main_type", "operator": "equal", "value": "Server" },
    { "field": "os_type",   "operator": "in",    "value": ["Linux", "CentOS", "Ubuntu"] }
  ]
}
```

**场景：排除测试环境**

```json
{
  "logic": "or",
  "rules": [
    { "field": "env", "operator": "equal", "value": "production" },
    { "field": "env", "operator": "equal", "value": "staging" }
  ]
}
```

### 向后兼容

`filter_rules` 为 `null` 或不存在的映射，行为与现有逻辑完全一致——匹配该 `ci_type_id` 下所有 CI。

## 匹配逻辑

### `pick_dashboard` 优先级

```
同一 ci_type_id 下（均启用）：

  1. filter_rules 不为空 + 规则评估通过  →  精确匹配，优先返回
  2. filter_rules 为空或不存在           →  兜底匹配（优先级低于精确匹配）
  3. 该 ci_type_id 无任何匹配            →  全局 Grafana 搜索兜底（现有逻辑）
```

### `evaluate_filter_rules(filter_rules, ci_attrs)` 伪代码

```python
def evaluate_filter_rules(filter_rules, ci_attrs):
    if not filter_rules or not filter_rules.get("rules"):
        return True  # 无过滤规则，匹配所有

    results = []
    for rule in filter_rules["rules"]:
        field_value = str(ci_attrs.get(rule["field"], ""))
        target = rule["value"]
        op = rule["operator"]

        if op == "equal":
            results.append(field_value == target)
        elif op == "not_equal":
            results.append(field_value != target)
        elif op == "contains":
            results.append(target in field_value)
        elif op == "not_contains":
            results.append(target not in field_value)
        elif op == "in":
            results.append(field_value in target)  # target is list
        elif op == "not_in":
            results.append(field_value not in target)

    if filter_rules["logic"] == "and":
        return all(results)
    else:  # "or"
        return any(results)
```

## 后端改动（cmdb-api-fastapi）

### `grafana_client.py`

- 新增 `evaluate_filter_rules(filter_rules, ci_attrs) -> bool`。
- `pick_dashboard(connections, mappings, ci_type_id, ci_attrs, unique_value, search_fn)`：
  - 参数变更：原 `ci` 属性字典 `ci_attrs` 替换部分场景不再需要独立传 `ci`；实际由调用方传入 CI 数据字典。
  - 先收集 `ci_type_id` 匹配且启用的映射。
  - 分为两组：有 `filter_rules` 的（精确匹配组）和无 `filter_rules` 的（兜底组）。
  - 精确匹配组按 `evaluate_filter_rules` 评估，命中即返回。
  - 精确匹配组未命中 → 兜底组取第一条。
  - 兜底组为空 → 走全局 Grafana 搜索（现有逻辑）。

### `grafana.py`（CRUD）

- 新增 `_valid_filter_rules(filter_rules)` 校验函数：
  - `None` → 合法（无过滤）。
  - 必须为 dict；`logic` 必须在 `("and", "or")`；`rules` 必须为非空数组。
  - 每条 rule：`field` 非空字符串；`operator` 在六种运算符中；`value` 非空（`in`/`not_in` 时须为数组且非空）。
  - 不合法 → `abort(400, ...)`。
- `create_mapping` / `update_mapping` 接受 `filter_rules`，写入前校验。
- `list_mappings` 返回 `filter_rules` 字段（`null` 或对象）。

### `grafana.py`（cmdb 视图）

- `resolve_ci_grafana`：将 CI 数据字典传入 `pick_dashboard` 的 `ci_attrs` 参数。

## 前端改动（cmdb-ui）

### 映射弹窗：过滤条件区（新增）

在 `dashboard_title` 下方增加可折叠区域：

```
┌─ 过滤条件（可选）[展开/收起] ─────────────────────┐
│ 组合逻辑:  [ AND ▼ ]                               │
│                                                    │
│  ┌──────────────┬──────────┬───────────────────┐   │
│  │ [field 下拉] │ [op 下拉]│ [value 输入]  [✕] │   │
│  └──────────────┴──────────┴───────────────────┘   │
│  ┌──────────────┬──────────┬───────────────────┐   │
│  │ [field 下拉] │ [op 下拉]│ [value 输入]  [✕] │   │
│  └──────────────┴──────────┴───────────────────┘   │
│                                                    │
│  [+ 添加条件]                                       │
└────────────────────────────────────────────────────┘
```

- **字段下拉**（`a-select`）：选项来自当前所选 CI 类型的属性列表（`ciAttrOptions`），支持搜索。
- **运算符下拉**（`a-select`）：`equal / not_equal / contains / not_contains / in / not_in`。
- **值输入**：`in` / `not_in` 时使用 `a-select` mode="tags" 输入多个值；其余使用 `a-input`。
- **AND / OR 切换**：`a-radio-group` 或 `a-select`。
- **行操作**：删除图标；表下方"+ 添加条件"按钮。
- 空状态：不配置过滤条件 = 默认行为（匹配该 CI 类型下所有 CI）。

### 映射列表

- `var_mapping` 摘要列后增加 `filter_rules` 摘要列（如 `os_type=Linux` / `os_type in (Linux,CentOS)` / `-` 表示无过滤）。

### ciDetailGrafana.vue

- **无需改动** — 只传 `ciId`，后端透明处理 Dashboard 选择。

### i18n（zh/en，cs.grafana 块）

新增 key：`filterRules`, `filterLogic`, `filterLogicAnd`, `filterLogicOr`, `filterField`, `filterOperator`, `filterValue`, `filterAddCondition`, `filterSummary`。

## 错误处理

- 前端保存时校验：至少一条规则时，每条 field / operator / value 必填。
- 后端 `_valid_filter_rules` 兜底校验，非法格式返回 400。
- `filter_rules` 引用不存在的 CI 属性：规则不匹配（`ci_attrs.get(field, "")` 返回空串），不抛异常——行为是"不命中"，走兜底逻辑。

## 涉及文件

**修改**
- `cmdb-api-fastapi/api/lib/common_setting/grafana_client.py`
- `cmdb-api-fastapi/api/lib/common_setting/grafana.py`
- `cmdb-api-fastapi/api/lib/cmdb/grafana.py`
- `cmdb-ui/src/views/setting/grafana/index.vue`
- `cmdb-ui/src/views/setting/lang/zh.js`、`en.js`

**不改**
- `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailGrafana.vue`（消费端透明）
