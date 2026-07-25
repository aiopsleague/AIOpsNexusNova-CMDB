# Grafana 集成设计文档

日期：2026-07-25
状态：已确认

## 目标

1. 后台管理提供 Grafana 配置页面：管理多个 Grafana 连接实例（URL + Service Account API Key）及 CI 类型 → 仪表板的映射。
2. CI 详情页（`cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailTab.vue`）新增 `tab_6` "Grafana"，嵌入显示对应该 CI 的 Grafana 仪表板。

## 关键决策（已与用户确认）

- **CI ↔ 仪表板关联**：两者结合 —— 先按 CI 类型映射查找，找不到再按 CI 唯一标识值在 Grafana 中按名称搜索。
- **展示形式**：单个仪表板，取匹配到的第一个，iframe + kiosk 模式全屏嵌入。
- **模板变量**：把 CI 唯一标识值作为模板变量拼到 iframe URL（`var-{var_name}={value}`），变量名在映射中可配，默认 `ci_name`。
- **配置范围**：支持多 Grafana 实例；连接与映射都在同一配置页管理。
- **技术方案**：后端代理 —— API Key 只存后端（AES 加密），后端代调 Grafana API，前端 iframe 直连 Grafana 展示。

## 架构

```
浏览器                        CMDB FastAPI 后端                  Grafana
  │  GET /v0.1/ci/{id}/grafana  │                                  │
  │────────────────────────────>│  1. 查 GrafanaMapping (ci._type)  │
  │                             │  2. 必要时 GET /api/search?query= │
  │                             │─────────────────────────────────>│
  │  {grafana_url, uid, slug,   │<─────────────────────────────────│
  │   var_name, var_value}      │                                  │
  │<────────────────────────────│                                  │
  │  iframe src={grafana_url}/d/{uid}/{slug}?kiosk&var-x=y         │
  │──────────────────────────────────────────────────────────────> │
```

## 数据模型

复用 `common_data` 表（`cmdb-api-fastapi/api/models/common_setting.py` 的 `CommonData`），新增两种 `data_type`：

- **`Grafana`** — 每条记录一个连接实例：
  ```json
  {"name": "生产Grafana", "url": "https://grafana.example.com", "api_key": "<AES加密>", "remark": ""}
  ```
  `api_key` 经 `AuthenticateDataCRUD` AES 加密存储，API 响应永不回显明文（返回掩码或空）。
- **`GrafanaMapping`** — 每条记录一个 CI 类型映射：
  ```json
  {"ci_type_id": 3, "connection_id": 1, "dashboard_uid": "abc123", "var_name": "ci_name"}
  ```
  - `dashboard_uid` 可空：为空表示只指定实例，仪表板靠搜索确定。
  - `var_name` 缺省 `ci_name`。

## 后端 API（cmdb-api-fastapi）

### 配置接口（common-setting，`@role_required("acl_admin")`，照 `auth_config.py` 范式）

新文件 `cmdb-api-fastapi/api/views/common_setting/grafana_config.py`：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/common-setting/v1/grafana/connections` | 连接列表（api_key 脱敏） |
| POST | `/common-setting/v1/grafana/connections` | 新增连接 |
| PUT | `/common-setting/v1/grafana/connections/{_id}` | 更新；api_key 不传则保持原值 |
| DELETE | `/common-setting/v1/grafana/connections/{_id}` | 删除（同时清理引用它的映射） |
| POST | `/common-setting/v1/grafana/connections/test` | 测试连通性：`requests` + `Authorization: Bearer <key>` 调 `{url}/api/user`，5s 超时 |
| GET | `/common-setting/v1/grafana/mappings` | 映射列表 |
| POST | `/common-setting/v1/grafana/mappings` | 新增映射 |
| PUT | `/common-setting/v1/grafana/mappings/{_id}` | 更新映射 |
| DELETE | `/common-setting/v1/grafana/mappings/{_id}` | 删除映射 |

注意文件头注释约定：静态路由必须注册在参数化路由之前。

### 解析接口（cmdb 侧，普通登录用户）

`GET /api/v0.1/ci/{ci_id}/grafana`（新文件 `cmdb-api-fastapi/api/views/cmdb/grafana.py`）：

1. 取 CI：`_id` 查 CI，取 `ci._type` 与该 CIType 的 unique 属性值（`var_value`）。
2. 按 `ci._type` 查 `GrafanaMapping`：
   - 命中且有 `dashboard_uid` → 用该连接的 url 直接返回。
   - 命中但无 uid → 在该实例调 `GET {url}/api/search?query={var_value}&type=dash-db`，取第一个结果。
3. 无映射 → 遍历所有连接实例依次搜索，第一个命中胜出。
4. 返回：
   ```json
   {"grafana_url": "...", "uid": "...", "slug": "...", "var_name": "ci_name", "var_value": "host-01"}
   ```
   全部未命中返回 `{"result": null}`（HTTP 200，由前端显示空状态）。

调 Grafana 用现有 `requests` 依赖，仿 `api/lib/webhook.py` 的 `BearerAuth`。所有 Grafana 调用 5s 超时、异常捕获，失败降级为空结果 + 警告日志，不影响 CMDB 主流程（不抛 500）。

## 前端（cmdb-ui）

### API 封装

- 新文件 `cmdb-ui/src/api/grafana.js`：连接/映射/test 接口（前缀 `/common-setting/v1/grafana`，`import { axios } from '@/utils/request'`）。
- `cmdb-ui/src/modules/cmdb/api/ci.js` 增加 `getCIGrafana(ciId)` → `GET /v0.1/ci/${ciId}/grafana`。

### 配置页

- 新文件 `cmdb-ui/src/views/setting/grafana/index.vue`，照 `setting/auth/index.vue` 模式：
  - 上半区：连接实例列表（表格：名称、URL、备注、操作），新增/编辑弹窗（名称、URL、API Key 密码框、备注），行内"测试连接"按钮。
  - 下半区：CI 类型映射表（CI 类型下拉、连接实例下拉、仪表板 UID、变量名），增删改。
- 路由：`cmdb-ui/src/router/config.js` 的 `/setting` children 增加：
  ```js
  { path: '/setting/grafana', name: 'setting_grafana', component: () => import('@/views/setting/grafana/index.vue'),
    meta: { title: 'cs.menu.grafana', appName: 'backend', icon: 'ops-setting-grafana', selectedIcon: 'ops-setting-grafana', permission: ['acl_admin'] } }
  ```
  （icon 若不存在则复用现有 setting 图标。）
- i18n：`cmdb-ui/src/views/setting/lang/zh.js`、`en.js` 增加 `cs.menu.grafana` 及页面词条。

### CI 详情 tab

- `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailTab.vue`：`<a-tabs>` 内新增第 6 个 `<a-tab-pane key="tab_6">`，标题 `$t('cmdb.ci.grafana')`（或类似 key），内容为子组件 `ciDetailGrafana.vue`（同目录新建）：
  - tab 首次激活（懒加载）时调 `getCIGrafana(ciId)`。
  - 有结果：`<iframe :src="url" style="width:100%;height:600px;border:none">`，url = `{grafana_url}/d/{uid}/{slug}?kiosk&var-{var_name}={encodeURIComponent(var_value)}`。
  - 无结果：a-empty 空状态，文案"未找到关联的 Grafana 仪表板"。
  - 后端返回未配置任何连接：提示"请先在后台管理中配置 Grafana"。
- 前端其他页面零改动。

## 错误处理与安全

- API Key：AES 加密存储；GET 接口脱敏（不回显明文）；PUT 不传 api_key 字段则保留原值。
- Grafana 不可达 / Key 失效：test 接口返回明确错误信息；解析接口降级为空结果。
- 删除连接时级联删除引用它的 `GrafanaMapping`，避免悬空引用。
- 部署前提（写入用户文档/页面提示）：Grafana 需设置 `allow_embedding = true` 并开启匿名访问（`auth.anonymous`），否则 iframe 无法展示。

## 测试

- 后端：pytest 覆盖解析逻辑（mock `requests`）。FastAPI 后端目前无 tests 目录，新建 `cmdb-api-fastapi/tests/test_grafana.py`：
  1. 映射命中且有 uid → 直接返回。
  2. 映射命中无 uid → 该实例搜索返回第一个。
  3. 无映射 → 遍历实例搜索。
  4. 实例不可达 / 全部未命中 → 返回空结果。
- 前端：项目无单测现状，手动验证配置页 CRUD、测试连接按钮、CI 详情 tab 嵌入与空状态。

## 涉及文件清单

**新增**
- `cmdb-api-fastapi/api/views/common_setting/grafana_config.py`
- `cmdb-api-fastapi/api/views/cmdb/grafana.py`
- `cmdb-api-fastapi/api/lib/common_setting/grafana.py`（业务逻辑：搜索/解析，供视图调用）
- `cmdb-api-fastapi/tests/test_grafana.py`（新建 tests 目录）
- `cmdb-ui/src/api/grafana.js`
- `cmdb-ui/src/views/setting/grafana/index.vue`
- `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailGrafana.vue`

**修改**
- `cmdb-ui/src/router/config.js`（+1 路由）
- `cmdb-ui/src/views/setting/lang/zh.js`、`en.js`（i18n 词条）
- `cmdb-ui/src/modules/cmdb/api/ci.js`（+1 接口）
- `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailTab.vue`（+1 tab）
- `cmdb-ui/src/modules/cmdb/lang/`（tab 标题词条，按实际位置）
