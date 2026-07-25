# Grafana 映射增强设计文档

日期：2026-07-25
状态：已确认
前置：`docs/superpowers/specs/2026-07-25-grafana-integration-design.md`（初版集成）+ 后端代理嵌入（commit a2993a38）

## 目标

1. 映射配置中的"仪表盘 UID"改为"仪表盘名称"（Grafana `metadata.name`，Grafana 12 统一存储下即 URL 中的 uid）。
2. 映射包含：CI 类型、连接实例、名称空间、仪表盘名称、仪表盘别名（title）、变量映射（CI 属性 ↔ Grafana 变量，多条，默认同名）。
3. 仪表盘名称/别名通过后端从 Grafana 实例拉取列表下拉选择；选中后自动拉取该仪表盘的模板变量供映射。
4. 连接实例增加**健康状态显示**（配置页加载时对每个连接调 Grafana `/api/health`，绿点健康/红点异常，异常时 tooltip 显示错误信息，支持手动刷新）。
5. 连接实例增加**启用开关**（`enable`，默认启用；停用的实例不参与解析与搜索兜底——映射指向已停用实例时按无映射走全局搜索启用实例）。

## 已验证的技术事实（真实 Grafana 12.1.1）

- `/api/dashboards/uid/{name}` 用 k8s `metadata.name` 可获取完整 dashboard JSON（含 `templating.list` 变量列表）；旧长 uid 返回 "Dashboard not found"。
- `/apis/dashboard.grafana.app/v2alpha1/namespaces/{namespace}/dashboards` 返回列表，`items[].metadata.name` + `items[].spec.title`。
- 嵌入 URL `/d/{name}/{slug}?kiosk&var-x=y` 经后端代理工作正常（初版代理已实现）。

## 数据模型

### 连接实例（connection 新增 `enable` 字段）

```json
{"id": 1, "name": "生产Grafana", "url": "https://g.example.com", "api_key": "...", "remark": "", "enable": 1}
```

- `enable`：1 启用 / 0 停用，缺省 1（旧记录无此字段按启用处理）。
- 停用的实例：`resolve_ci_grafana` 与 `pick_dashboard` 全部跳过；配置页仍可编辑/测试/重新启用。

### GrafanaMapping 新结构

```json
{
  "id": 1,
  "ci_type_id": 5,
  "connection_id": 1,
  "namespace": "default",
  "dashboard_name": "rYdddlPWo",
  "dashboard_title": "Linux Dashboard",
  "var_mapping": [{"grafana_var": "instance", "ci_attr": "instance"}]
}
```

- `namespace` 缺省 `"default"`。
- `dashboard_name` 必填；`dashboard_title` 仅展示用途。
- `var_mapping` 为空数组 = 不传变量。`ci_attr` 为 CI 属性名；解析时取 `ci[ci_attr]`，值为空（None/空串/空列表）的变量不拼入 URL。
- **不做旧格式兼容**：旧字段 `dashboard_uid`/`var_name` 不再读取，用户重新配置（已与用户确认）。

## 后端改动（cmdb-api-fastapi）

### `api/lib/common_setting/grafana_client.py` — GrafanaClient 新增

- `list_dashboards(namespace="default") -> [{"name", "title"}]`
  - 调 `GET {url}/apis/dashboard.grafana.app/v2alpha1/namespaces/{ns}/dashboards`，解析 `items[].metadata.name` / `items[].spec.title`。
  - 404（老版本 Grafana 无此 API）时回退 `GET /api/search?type=dash-db`，`uid` 作 name、`title` 照用。
- `get_dashboard_variables(name) -> [str]`
  - 调 `GET {url}/api/dashboards/uid/{name}`，返回 `dashboard.templating.list` 中 `type != "datasource"` 的变量 `name` 列表。

### 配置 API（`api/views/common_setting/grafana_config.py`，acl_admin）

- `GET /common-setting/v1/grafana/connections/{_id:int}/dashboards?namespace=xxx` → `{"dashboards": [{name, title}]}`
- `GET /common-setting/v1/grafana/connections/{_id:int}/dashboards/{name}/variables` → `{"variables": [str]}`
- `GET /common-setting/v1/grafana/connections/health` → `{"health": [{"id": 1, "ok": true, "error": ""}]}`：对每个连接调 `GET {url}/api/health`（5s 超时），逐实例容错不中断。
- 静态路由注册顺序注意：`/connections/health` 必须注册在 `/connections/{_id:int}` 之前（静态先于参数化）；`/connections/{_id:int}/dashboards` 与既有 `/connections/{_id:int}` 方法不同（GET vs PUT/DELETE），无冲突；`/dashboards/{name}/variables` 在 `/dashboards` 之后注册。
- 连接 CRUD：`create_connection`/`update_connection` 接受 `enable`（0/1，缺省 1）；列表返回含 `enable`。

### 映射 CRUD（`api/lib/common_setting/grafana.py`）

- `create_mapping`/`update_mapping` 字段改为：`ci_type_id`、`connection_id`、`namespace`（缺省 default）、`dashboard_name`（必填）、`dashboard_title`（可空）、`var_mapping`（list，元素 `{grafana_var, ci_attr}` 均必填非空，否则 400）。

### 解析端点（`api/lib/cmdb/grafana.py`）

- 映射命中且有 `dashboard_name` → 返回 `uid=dashboard_name`、`slug=None`、`vars=[{"name": grafana_var, "value": ci[ci_attr]}]`（跳过空值）。
- 响应结构变化：`result` 中 `var_name`/`var_value` 替换为 `vars` 数组；保留 `connection_id`、`grafana_url`、`uid`、`slug`。
- 无映射的搜索兜底保持现状：`vars=[{"name": "ci_name", "value": <唯一标识>}]`（取代原 var_name/var_value 单值）。
- 启用过滤：`pick_dashboard` 内部跳过 `enable == 0` 的连接（缺省视为启用）；映射指向已停用实例时视为未命中，继续全局搜索其余启用实例。`resolve_ci_grafana` 不做额外过滤。

## 前端改动（cmdb-ui）

### `src/api/grafana.js` 新增

- `getGrafanaDashboards(connectionId, namespace)` 
- `getGrafanaDashboardVariables(connectionId, name)`
- `getGrafanaConnectionsHealth()`

### 配置页 `src/views/setting/grafana/index.vue` 连接列表增强

- 连接表格新增两列：**状态**（加载列表后调 health 端点，绿点"正常"/红点"异常"，异常时 a-tooltip 显示 error，列头旁刷新图标可重查）和**启用**（a-switch，切换即调 `putGrafanaConnection(id, {enable})` 快速保存）。
- 连接编辑表单增加"启用"开关（默认开）。

### 配置页 `src/views/setting/grafana/index.vue` 映射表单

- 字段顺序：CI 类型（下拉）→ 连接实例（下拉）→ 名称空间（输入框，默认 `default`）→ 仪表盘名称（**下拉**：选中实例后调 dashboards 端点，选项显示 `{title} ({name})`，value 为 name；拉取失败降级为可手工输入的 a-auto-complete）→ 仪表盘别名（选中名称后自动带出 title，只读输入框）→ **变量映射**（选中仪表盘后调 variables 端点，a-table 逐行：Grafana 变量（下拉，已选变量置灰）+ CI 属性（下拉，候选为所选 CI 类型的属性列表，新增行时若有同名属性默认选中）+ 删除行；底部"添加变量映射"按钮）。
- CI 属性列表：选 CI 类型后调 `getCITypeAttributesById`（`@/modules/cmdb/api/CITypeAttr`），选项显示 `alias || name`，value 为 name。
- 映射表格列更新：CI类型 / 连接实例 / 名称空间 / 仪表盘别名 / 仪表盘名称 / 变量映射（显示 `var←attr` 摘要）/ 操作。

### `ciDetailGrafana.vue`

- `vars` 数组逐项拼 `&var-{name}={encodeURIComponent(value)}`；`vars` 为空则无变量参数。

## 错误处理

- dashboards/variables 端点：Grafana 不可达或 Key 失效 → abort 400 + 明确信息；配置页捕获后提示并允许手工输入名称/变量。
- 解析端点：var_mapping 中属性在 CI 上取不到值 → 静默跳过该变量（warning 日志）。

## 测试

- 后端单测（mock requests）：
  1. `list_dashboards` k8s API 正常解析（name/title）。
  2. `list_dashboards` 404 回退 `/api/search`。
  3. `get_dashboard_variables` 解析 templating 并排除 datasource 类型。
  4. 解析端点 vars 构建逻辑：映射命中 → 按 var_mapping 取值、空值跳过（纯函数化以便测试）。
  5. `pick_dashboard` 跳过 `enable=0` 实例（含映射指向停用实例时回退全局搜索）。
- E2E（真实 Grafana）：dashboards 列表拉取、variables 拉取、health 端点、启用/停用对解析的影响、嵌入 URL 带多变量、映射 CRUD。

## 涉及文件

**修改**
- `cmdb-api-fastapi/api/lib/common_setting/grafana_client.py`
- `cmdb-api-fastapi/api/lib/common_setting/grafana.py`
- `cmdb-api-fastapi/api/lib/cmdb/grafana.py`
- `cmdb-api-fastapi/api/views/common_setting/grafana_config.py`
- `cmdb-api-fastapi/tests/test_grafana_client.py`
- `cmdb-ui/src/api/grafana.js`
- `cmdb-ui/src/views/setting/grafana/index.vue`
- `cmdb-ui/src/views/setting/lang/zh.js`、`en.js`
- `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailGrafana.vue`
