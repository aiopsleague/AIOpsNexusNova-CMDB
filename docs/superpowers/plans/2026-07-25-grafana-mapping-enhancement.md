# Grafana 映射增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Grafana 映射升级为 namespace + dashboard_name + 变量映射（CI 属性↔Grafana 变量），仪表盘列表/变量从实例拉取选择，连接实例增加健康状态与启用开关。

**Architecture:** 后端 `GrafanaClient` 增加 k8s API 列表与变量获取；映射数据结构换代（不做旧格式兼容）；解析端点返回 `vars` 数组；前端配置页重做映射表单、连接表格加状态/启用列；iframe 按 vars 拼多变量。

**Tech Stack:** FastAPI（Flask-SQLAlchemy 兼容层）、requests、pytest；Vue2 + ant-design-vue 1.x。

**Spec:** `docs/superpowers/specs/2026-07-25-grafana-mapping-enhancement-design.md`

## Global Constraints

- 只修改 `cmdb-api-fastapi/` 和 `cmdb-ui/`；**不动** `cmdb-api/`。
- 后端视图遵循兼容层范式：`from api.core.context import request`；**静态路由必须注册在参数化路由之前**。
- 不新增任何 Python/前端依赖。
- 前端所有展示文案走 i18n（zh + en 双语），深度选择器用 `/deep/`（项目惯例）。
- Grafana HTTP 调用 5s 超时；解析端点中 Grafana 故障降级为空结果 + warning 日志，不抛 500。
- **不做旧映射格式兼容**：`dashboard_uid`/`var_name` 字段不再读取（用户确认重新配置）。
- 提交信息：`feat(grafana): ...` / `test(grafana): ...`。
- pytest：`cd cmdb-api-fastapi && .venv/bin/python -m pytest tests/ -v`（当前 10 passed）。
- 注意：工作区存在一个**未提交的** `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailGrafana.vue` 高度修复（用户要求暂不提交），实现时不得回滚该文件中的高度修复内容（`/deep/ .ant-spin-container` 等），各任务提交按文件精确 add。

## 关键接口约定（任务间契约）

- `GrafanaClient.list_dashboards(namespace="default") -> [{"name": str, "title": str}]`
- `GrafanaClient.get_dashboard_variables(name) -> [str]`（排除 datasource 类型）
- `pick_dashboard(connections, mappings, ci_type_id, unique_value, search_fn) -> {"connection", "uid", "slug", "mapping"|None} | None`（**返回结构变更**：不再返回 var_name/var_value，改为命中时的 mapping 或 None；内部跳过 `enable == 0` 的连接）
- `build_vars(mapping, ci, unique_value) -> [{"name": str, "value": any}]`（纯函数，grafana_client.py）
- resolve 响应：`{"configured": bool, "result": {"connection_id", "grafana_url", "uid", "slug", "vars": [...]} | None}`
- 映射记录：`{"id", "ci_type_id", "connection_id", "namespace", "dashboard_name", "dashboard_title", "var_mapping": [{"grafana_var", "ci_attr"}]}`
- 连接记录新增 `enable`（1/0，缺省视为 1）。
- 新端点：`GET /common-setting/v1/grafana/connections/health`、`GET .../connections/{id}/dashboards?namespace=`、`GET .../connections/{id}/dashboards/{name}/variables`

---

### Task 1: grafana_client 增强 + 测试重写（TDD）

**Files:**
- Modify: `cmdb-api-fastapi/api/lib/common_setting/grafana_client.py`
- Test: `cmdb-api-fastapi/tests/test_grafana_client.py`（整体重写）

**Interfaces:**
- Produces: `list_dashboards` / `get_dashboard_variables` / 新版 `pick_dashboard` / `build_vars`，签名见"关键接口约定"。Task 2/3 全部依赖。

- [ ] **Step 1: 整体重写测试文件（先确认失败）**

`cmdb-api-fastapi/tests/test_grafana_client.py` 完整替换为：

```python
# -*- coding:utf-8 -*-
from unittest import mock

import pytest

from api.lib.common_setting.grafana_client import GrafanaClient, build_vars, pick_dashboard

CONN1 = {"id": 1, "name": "g1", "url": "http://g1:3000", "api_key": "k1"}
CONN2 = {"id": 2, "name": "g2", "url": "http://g2:3000/", "api_key": "k2"}
CONN3_DISABLED = {"id": 3, "name": "g3", "url": "http://g3:3000", "api_key": "k3", "enable": 0}
DASH = {"uid": "abc123", "title": "host-01", "url": "/d/abc123/host-01"}


def _ok_search(dashboards):
    return lambda conn: dashboards


def _fail_search(conn):
    raise Exception("connection refused")


# ---------------- pick_dashboard ----------------

def test_pick_dashboard_mapping_with_name():
    mappings = [{"id": 1, "ci_type_id": 3, "connection_id": 2, "dashboard_name": "rYdddlPWo",
                 "var_mapping": [{"grafana_var": "instance", "ci_attr": "instance"}]}]
    picked = pick_dashboard([CONN1, CONN2], mappings, 3, "host-01", _fail_search)
    assert picked["connection"] is CONN2
    assert picked["uid"] == "rYdddlPWo"
    assert picked["slug"] is None
    assert picked["mapping"] is mappings[0]


def test_pick_dashboard_mapping_without_name_searches_that_instance():
    mappings = [{"id": 1, "ci_type_id": 3, "connection_id": 1, "dashboard_name": "", "var_mapping": []}]
    picked = pick_dashboard([CONN1, CONN2], mappings, 3, "host-01", _ok_search([DASH]))
    assert picked["connection"] is CONN1
    assert picked["uid"] == "abc123"
    assert picked["slug"] == "host-01"
    assert picked["mapping"] is mappings[0]


def test_pick_dashboard_mapping_miss_falls_back_to_global_search():
    mappings = [{"id": 1, "ci_type_id": 3, "connection_id": 1, "dashboard_name": "", "var_mapping": []}]
    calls = []

    def search_fn(conn):
        calls.append(conn["id"])
        return [DASH] if conn["id"] == 2 else []

    picked = pick_dashboard([CONN1, CONN2], mappings, 3, "host-01", search_fn)
    assert picked["connection"] is CONN2
    assert picked["mapping"] is None
    assert calls == [1, 2]


def test_pick_dashboard_no_mapping_searches_all_in_order():
    def search_fn(conn):
        return [DASH] if conn["id"] == 2 else []

    picked = pick_dashboard([CONN1, CONN2], [], 3, "host-01", search_fn)
    assert picked["connection"] is CONN2
    assert picked["mapping"] is None


def test_pick_dashboard_nothing_found():
    assert pick_dashboard([CONN1], [], 3, "host-01", _ok_search([])) is None
    assert pick_dashboard([CONN1], [], 3, "host-01", _fail_search) is None


def test_pick_dashboard_no_connections():
    assert pick_dashboard([], [], 3, "host-01", _ok_search([DASH])) is None


def test_pick_dashboard_skips_disabled_instances():
    # 映射指向停用实例 → 回退全局搜索启用实例
    mappings = [{"id": 1, "ci_type_id": 3, "connection_id": 3, "dashboard_name": "xyz", "var_mapping": []}]
    picked = pick_dashboard([CONN1, CONN3_DISABLED], mappings, 3, "host-01", _ok_search([DASH]))
    assert picked["connection"] is CONN1
    assert picked["mapping"] is None


def test_pick_dashboard_all_disabled():
    assert pick_dashboard([CONN3_DISABLED], [], 3, "host-01", _ok_search([DASH])) is None


# ---------------- build_vars ----------------

def test_build_vars_fallback_without_mapping():
    assert build_vars(None, {}, "host-01") == [{"name": "ci_name", "value": "host-01"}]


def test_build_vars_from_mapping():
    mapping = {"var_mapping": [{"grafana_var": "instance", "ci_attr": "ip"},
                               {"grafana_var": "maintype", "ci_attr": "os"}]}
    ci = {"ip": "10.0.0.1", "os": "linux"}
    assert build_vars(mapping, ci, "x") == [{"name": "instance", "value": "10.0.0.1"},
                                            {"name": "maintype", "value": "linux"}]


def test_build_vars_skips_empty_values():
    mapping = {"var_mapping": [{"grafana_var": "a", "ci_attr": "x"},
                               {"grafana_var": "b", "ci_attr": "y"},
                               {"grafana_var": "c", "ci_attr": "z"},
                               {"grafana_var": "d", "ci_attr": "w"}]}
    ci = {"x": "", "y": None, "z": [], "w": "keep"}
    assert build_vars(mapping, ci, "v") == [{"name": "d", "value": "keep"}]


# ---------------- http client ----------------

def test_search_dashboard_builds_request():
    client = GrafanaClient("http://g:3000/", "key")
    with mock.patch("api.lib.common_setting.grafana_client.requests.get") as m:
        m.return_value.json.return_value = [DASH]
        m.return_value.raise_for_status.return_value = None
        result = client.search_dashboard("host-01")
    assert result == [DASH]
    args, kwargs = m.call_args
    assert args[0] == "http://g:3000/api/search"
    assert kwargs["params"] == {"query": "host-01", "type": "dash-db"}
    assert kwargs["headers"]["Authorization"] == "Bearer key"
    assert kwargs["timeout"] == 5


def test_test_connection_raises_on_failure():
    client = GrafanaClient("http://g:3000", "bad-key")
    with mock.patch("api.lib.common_setting.grafana_client.requests.get") as m:
        m.return_value.raise_for_status.side_effect = Exception("401")
        with pytest.raises(Exception):
            client.test_connection()


def test_list_dashboards_k8s_api():
    client = GrafanaClient("http://g:3000/", "key")
    payload = {"items": [
        {"metadata": {"name": "rYdddlPWo"}, "spec": {"title": "Linux Dashboard"}},
        {"metadata": {"name": "abc"}, "spec": {}},
    ]}
    with mock.patch("api.lib.common_setting.grafana_client.requests.get") as m:
        m.return_value.status_code = 200
        m.return_value.json.return_value = payload
        m.return_value.raise_for_status.return_value = None
        result = client.list_dashboards("default")
    assert result == [{"name": "rYdddlPWo", "title": "Linux Dashboard"},
                      {"name": "abc", "title": "abc"}]
    args, kwargs = m.call_args
    assert args[0] == "http://g:3000/apis/dashboard.grafana.app/v2alpha1/namespaces/default/dashboards"


def test_list_dashboards_fallback_to_search_on_404():
    client = GrafanaClient("http://g:3000/", "key")
    with mock.patch("api.lib.common_setting.grafana_client.requests.get") as m:
        m.return_value.status_code = 404
        m.return_value.json.return_value = [DASH]
        m.return_value.raise_for_status.return_value = None
        result = client.list_dashboards("default")
    assert result == [{"name": "abc123", "title": "host-01"}]


def test_get_dashboard_variables_excludes_datasource():
    client = GrafanaClient("http://g:3000/", "key")
    payload = {"dashboard": {"templating": {"list": [
        {"name": "instance", "type": "query"},
        {"name": "datasource", "type": "datasource"},
        {"name": "maintype", "type": "query"},
        {"type": "query"},
    ]}}}
    with mock.patch("api.lib.common_setting.grafana_client.requests.get") as m:
        m.return_value.json.return_value = payload
        m.return_value.raise_for_status.return_value = None
        result = client.get_dashboard_variables("rYdddlPWo")
    assert result == ["instance", "maintype"]
    args, kwargs = m.call_args
    assert args[0] == "http://g:3000/api/dashboards/uid/rYdddlPWo"


def test_rewrite_dashboard_html():
    from api.lib.common_setting.grafana_client import rewrite_dashboard_html
    html = '<html><head><base href="/" /></head><body>{"settings":{"appSubUrl":""}}</body></html>'
    out = rewrite_dashboard_html(html, "/api/v0.1/grafana/proxy/1")
    assert '<base href="/api/v0.1/grafana/proxy/1/" />' in out
    assert '"appSubUrl":"/api/v0.1/grafana/proxy/1"' in out
    assert '<base href="/" />' not in out


def test_rewrite_dashboard_html_without_markers_is_noop():
    from api.lib.common_setting.grafana_client import rewrite_dashboard_html
    html = '<html><head></head><body>"appSubUrl":"/already"</body></html>'
    assert rewrite_dashboard_html(html, "/p") == html
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd cmdb-api-fastapi && .venv/bin/python -m pytest tests/ -v`
Expected: 新测试 FAIL（`ImportError: cannot import name 'build_vars'` 及 pick_dashboard 新契约断言失败）

- [ ] **Step 3: 实现 grafana_client.py 改动**

3a. `GrafanaClient` 新增两个方法（放在 `search_dashboard` 之后）：

```python
    def list_dashboards(self, namespace="default"):
        """Return [{"name", "title"}] via the k8s-style API; fall back to
        classic /api/search on 404 (older grafana)."""
        resp = requests.get(
            "{}/apis/dashboard.grafana.app/v2alpha1/namespaces/{}/dashboards".format(self.url, namespace),
            headers=self._headers(), timeout=self.timeout)
        if resp.status_code == 404:
            return [{"name": d.get("uid"), "title": d.get("title")} for d in self.search_dashboard("")]
        resp.raise_for_status()
        items = resp.json().get("items") or []
        return [{"name": i.get("metadata", {}).get("name"),
                 "title": i.get("spec", {}).get("title") or i.get("metadata", {}).get("name")}
                for i in items]

    def get_dashboard_variables(self, name):
        """Return template variable names of a dashboard (datasource excluded)."""
        resp = requests.get("{}/api/dashboards/uid/{}".format(self.url, name),
                            headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        templating = (resp.json().get("dashboard") or {}).get("templating") or {}
        return [v.get("name") for v in (templating.get("list") or [])
                if v.get("name") and v.get("type") != "datasource"]
```

3b. `pick_dashboard` 整体替换（返回 `mapping` 键，过滤 `enable == 0`）：

```python
def pick_dashboard(connections, mappings, ci_type_id, unique_value, search_fn):
    """Decide which grafana dashboard to show for a CI.

    :param connections: list of {"id", "name", "url", "api_key", "remark", "enable"?}
    :param mappings: list of {"id", "ci_type_id", "connection_id", "dashboard_name", "var_mapping"}
    :param ci_type_id: int, the CI's type id
    :param unique_value: str, the CI's unique attribute value (search keyword)
    :param search_fn: callable(connection) -> list of dashboard dicts; may raise
    :return: dict(connection=..., uid=..., slug=..., mapping=...|None) or None
    """
    enabled = [c for c in connections if c.get("enable", 1) != 0]
    if not enabled:
        return None

    searched_ids = set()
    mapping = next((m for m in mappings if m.get("ci_type_id") == ci_type_id), None)
    if mapping:
        conn = next((c for c in enabled if c.get("id") == mapping.get("connection_id")), None)
        if conn:
            name = (mapping.get("dashboard_name") or "").strip()
            if name:
                return dict(connection=conn, uid=name, slug=None, mapping=mapping)
            searched_ids.add(conn.get("id"))
            dash = _first_hit(search_fn, conn)
            if dash:
                return dict(connection=conn, uid=dash.get("uid"), slug=_slug_from(dash), mapping=mapping)
            # 映射实例搜不到 → 继续全局兜底

    for conn in enabled:
        if conn.get("id") in searched_ids:
            continue
        dash = _first_hit(search_fn, conn)
        if dash:
            return dict(connection=conn, uid=dash.get("uid"), slug=_slug_from(dash), mapping=None)

    return None
```

3c. 新增 `build_vars`（放在 `pick_dashboard` 之后）；同时**删除**不再使用的 `_result` 函数与 `DEFAULT_VAR_NAME` 改为仅在 `build_vars` 使用（保留常量定义）：

```python
def build_vars(mapping, ci, unique_value):
    """Build the template-var list for the iframe url.

    :param mapping: matched mapping dict or None
    :param ci: CI dict (attribute values keyed by attr name)
    :param unique_value: CI unique attr value (fallback value)
    """
    if not mapping:
        return [dict(name=DEFAULT_VAR_NAME, value=unique_value)]
    vars_ = []
    for vm in mapping.get("var_mapping") or []:
        value = ci.get(vm.get("ci_attr") or "")
        if value is None or value == "" or value == []:
            continue
        vars_.append(dict(name=vm.get("grafana_var"), value=value))
    return vars_
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd cmdb-api-fastapi && .venv/bin/python -m pytest tests/ -v`
Expected: 18 passed

- [ ] **Step 5: Commit**

```bash
git add cmdb-api-fastapi/api/lib/common_setting/grafana_client.py cmdb-api-fastapi/tests/test_grafana_client.py
git commit -m "feat(grafana): dashboard list/variables api, enable filter and var mapping in client"
```

---

### Task 2: 后端配置 CRUD + 端点（enable / health / dashboards / variables / 新映射字段）

**Files:**
- Modify: `cmdb-api-fastapi/api/lib/common_setting/grafana.py`
- Modify: `cmdb-api-fastapi/api/views/common_setting/grafana_config.py`

**Interfaces:**
- Consumes: Task 1 的 `GrafanaClient.list_dashboards/get_dashboard_variables`。
- Produces:
  - `GrafanaConfigCRUD.check_health() -> [{"id", "ok", "error"}]`
  - 连接 CRUD 接受/返回 `enable`；映射 CRUD 新字段（`namespace`/`dashboard_name`/`dashboard_title`/`var_mapping`）
  - 端点：`GET .../connections/health`、`GET .../connections/{_id:int}/dashboards`、`GET .../connections/{_id:int}/dashboards/{name}/variables`
- 前端 Task 4/5 按此调用。

- [ ] **Step 1: grafana.py 连接部分改动**

1. `_mask` 之后新增静态方法：

```python
    @staticmethod
    def _to_enable(value):
        return 0 if value in (0, "0", False) else 1
```

2. `list_connections` 改为（补 enable 缺省）：

```python
    def list_connections(self):
        result = []
        for c in self.get_config()["connections"]:
            masked = self._mask(c)
            masked["enable"] = self._to_enable(c.get("enable", 1))
            result.append(masked)
        return result
```

3. `create_connection` 的 `connection = dict(...)` 增加一行：`enable=self._to_enable(data.get("enable", 1)),`
4. `update_connection` 在 `if "remark" in data:` 块后增加：

```python
        if "enable" in data:
            connection["enable"] = self._to_enable(data["enable"])
```

5. `test_connection` 之后新增：

```python
    def check_health(self):
        """Per-connection liveness: [{"id", "ok", "error"}]. Never raises."""
        result = []
        for c in self.get_config()["connections"]:
            try:
                GrafanaClient(c["url"], c["api_key"]).test_connection()
                result.append({"id": c["id"], "ok": True, "error": ""})
            except Exception as e:
                result.append({"id": c["id"], "ok": False, "error": str(e)})
        return result
```

- [ ] **Step 2: grafana.py 映射部分整体替换**

`create_mapping` / `update_mapping` 替换为（`delete_mapping` 不变；新增 `_valid_var_mapping` 静态方法）：

```python
    @staticmethod
    def _valid_var_mapping(var_mapping):
        var_mapping = var_mapping or []
        if not isinstance(var_mapping, list):
            abort(400, ErrFormat.value_is_required)
        result = []
        for vm in var_mapping:
            grafana_var = str((vm or {}).get("grafana_var") or "").strip()
            ci_attr = str((vm or {}).get("ci_attr") or "").strip()
            if not grafana_var or not ci_attr:
                abort(400, ErrFormat.value_is_required)
            result.append({"grafana_var": grafana_var, "ci_attr": ci_attr})
        return result

    def create_mapping(self, data):
        ci_type_id = data.get("ci_type_id")
        connection_id = data.get("connection_id")
        dashboard_name = (data.get("dashboard_name") or "").strip()
        if not ci_type_id or not connection_id or not dashboard_name:
            abort(400, ErrFormat.value_is_required)
        ci_type_id = self._to_int(ci_type_id)
        connection_id = self._to_int(connection_id)

        config = self.get_config()
        if not any(c.get("id") == connection_id for c in config["connections"]):
            abort(404, ErrFormat.grafana_connection_not_found.format(connection_id))

        mapping = dict(id=self._next_id(config["mappings"]),
                       ci_type_id=ci_type_id,
                       connection_id=connection_id,
                       namespace=(data.get("namespace") or "").strip() or "default",
                       dashboard_name=dashboard_name,
                       dashboard_title=(data.get("dashboard_title") or "").strip(),
                       var_mapping=self._valid_var_mapping(data.get("var_mapping")))
        config["mappings"].append(mapping)
        self._save(config)
        return mapping

    def update_mapping(self, _id, data):
        _id = self._to_int(_id)
        config = self.get_config()
        mapping = next((m for m in config["mappings"] if m.get("id") == _id), None)
        if not mapping:
            abort(404, ErrFormat.grafana_mapping_not_found.format(_id))

        if "ci_type_id" in data and data["ci_type_id"]:
            mapping["ci_type_id"] = self._to_int(data["ci_type_id"])
        if "connection_id" in data and data["connection_id"]:
            connection_id = self._to_int(data["connection_id"])
            if not any(c.get("id") == connection_id for c in config["connections"]):
                abort(404, ErrFormat.grafana_connection_not_found.format(connection_id))
            mapping["connection_id"] = connection_id
        if "namespace" in data:
            mapping["namespace"] = (data["namespace"] or "").strip() or "default"
        if "dashboard_name" in data:
            if not (data["dashboard_name"] or "").strip():
                abort(400, ErrFormat.value_is_required)
            mapping["dashboard_name"] = data["dashboard_name"].strip()
        if "dashboard_title" in data:
            mapping["dashboard_title"] = (data["dashboard_title"] or "").strip()
        if "var_mapping" in data:
            mapping["var_mapping"] = self._valid_var_mapping(data["var_mapping"])

        self._save(config)
        return mapping
```

- [ ] **Step 3: 视图新增三个端点**

`cmdb-api-fastapi/api/views/common_setting/grafana_config.py`：

1. import 区增加：`from api.lib.common_setting.grafana_client import GrafanaClient`
2. `connections/test` 路由之后、`connections/{_id:int}` PUT 之前插入 health（静态先于参数化）：

```python
@router.get(f'{prefix}/connections/health')
@role_required("acl_admin")
def grafana_connections_health_get():
    return dict(health=GrafanaConfigCRUD().check_health())
```

3. `connections/{_id:int}` DELETE 路由之后插入 dashboards/variables：

```python
@router.get(f'{prefix}/connections/{{_id:int}}/dashboards')
@role_required("acl_admin")
def grafana_connection_dashboards_get(_id: int = None):
    namespace = request.values.get('namespace') or 'default'
    connection = GrafanaConfigCRUD().get_connection(_id)
    try:
        dashboards = GrafanaClient(connection["url"], connection["api_key"]).list_dashboards(namespace)
    except Exception as e:
        abort(400, ErrFormat.grafana_test_failed.format(str(e)))
    return dict(dashboards=dashboards)


@router.get(f'{prefix}/connections/{{_id:int}}/dashboards/{{name}}/variables')
@role_required("acl_admin")
def grafana_connection_dashboard_variables_get(_id: int = None, name: str = None):
    connection = GrafanaConfigCRUD().get_connection(_id)
    try:
        variables = GrafanaClient(connection["url"], connection["api_key"]).get_dashboard_variables(name)
    except Exception as e:
        abort(400, ErrFormat.grafana_test_failed.format(str(e)))
    return dict(variables=variables)
```

注意：该文件已有 `from api.core.errors import abort`？——**没有**，当前文件未 import abort，需要新增 `from api.core.errors import abort`；`ErrFormat` 也需要 import：`from api.lib.common_setting.resp_format import ErrFormat`。实现时先读文件头部确认。

- [ ] **Step 4: 验证导入 + 路由 + 回归测试**

Run: `cd cmdb-api-fastapi && SECRET_KEY=test-secret-key .venv/bin/python -c "
from api.views.common_setting.grafana_config import router
for r in router.routes:
    if 'grafana' in r.path: print(sorted(r.methods), r.path)
" && .venv/bin/python -m pytest tests/ -q 2>&1 | tail -1`
Expected: 列出 12 条路由（含 health、dashboards、variables），18 passed

- [ ] **Step 5: Commit**

```bash
git add cmdb-api-fastapi/api/lib/common_setting/grafana.py cmdb-api-fastapi/api/views/common_setting/grafana_config.py
git commit -m "feat(grafana): connection enable/health, dashboards and variables endpoints, new mapping schema"
```

---

### Task 3: 解析端点 vars 构建

**Files:**
- Modify: `cmdb-api-fastapi/api/lib/cmdb/grafana.py`

**Interfaces:**
- Consumes: Task 1 新版 `pick_dashboard`（返回 `mapping` 键）与 `build_vars`。
- Produces: resolve 响应 `result.vars` 数组（Task 6 前端依赖）。

- [ ] **Step 1: 修改 resolve_ci_grafana**

`cmdb-api-fastapi/api/lib/cmdb/grafana.py` 末尾的返回部分替换（import 增加 `build_vars`）：

```python
from api.lib.common_setting.grafana_client import build_vars
```

```python
    if not picked:
        return dict(configured=True, result=None)

    return dict(configured=True, result=dict(
        connection_id=picked["connection"]["id"],
        grafana_url=picked["connection"]["url"],
        uid=picked["uid"],
        slug=picked["slug"],
        vars=build_vars(picked["mapping"], ci, str(unique_value)),
    ))
```

（删除原 `var_name`/`var_value` 两行；其余逻辑不变。）

- [ ] **Step 2: 验证导入 + 回归测试**

Run: `cd cmdb-api-fastapi && SECRET_KEY=test-secret-key .venv/bin/python -c "from api.lib.cmdb.grafana import resolve_ci_grafana; print('ok')" && .venv/bin/python -m pytest tests/ -q 2>&1 | tail -1`
Expected: `ok`，18 passed

- [ ] **Step 3: Commit**

```bash
git add cmdb-api-fastapi/api/lib/cmdb/grafana.py
git commit -m "feat(grafana): resolve endpoint returns vars from mapping"
```

---

### Task 4: 前端 API 封装新增

**Files:**
- Modify: `cmdb-ui/src/api/grafana.js`

**Interfaces:**
- Produces（Task 5 依赖）：`getGrafanaConnectionsHealth()` → `{health: [...]}`；`getGrafanaDashboards(connectionId, namespace)` → `{dashboards: [...]}`；`getGrafanaDashboardVariables(connectionId, name)` → `{variables: [...]}`

- [ ] **Step 1: grafana.js 追加三个函数**

```js
export function getGrafanaConnectionsHealth() {
    return axios({
        url: `/common-setting/v1/grafana/connections/health`,
        method: 'get',
    })
}

export function getGrafanaDashboards(connectionId, namespace) {
    return axios({
        url: `/common-setting/v1/grafana/connections/${connectionId}/dashboards`,
        method: 'get',
        params: { namespace: namespace || 'default' },
    })
}

export function getGrafanaDashboardVariables(connectionId, name) {
    return axios({
        url: `/common-setting/v1/grafana/connections/${connectionId}/dashboards/${name}/variables`,
        method: 'get',
    })
}
```

注意：`/connections/health` 是静态路径，必须与 `putGrafanaConnection`/`deleteGrafanaConnection` 的 `/connections/${id}` 区分——URL 不同，无代码冲突。确认 axios 封装支持 `params`（`src/utils/request.js` 直接透传 axios 配置，支持）。

- [ ] **Step 2: lint**

Run: `cd cmdb-ui && npx eslint src/api/grafana.js`
Expected: 无 error

- [ ] **Step 3: Commit**

```bash
git add cmdb-ui/src/api/grafana.js
git commit -m "feat(grafana): add health/dashboards/variables api wrappers"
```

---

### Task 5: 前端配置页（连接状态/启用 + 映射表单重做）+ i18n

**Files:**
- Modify: `cmdb-ui/src/views/setting/grafana/index.vue`（大改）
- Modify: `cmdb-ui/src/views/setting/lang/zh.js`、`en.js` 的 `grafana` 块

**Interfaces:**
- Consumes: Task 4 三个新 API；`getCITypeAttributesById`（`@/modules/cmdb/api/CITypeAttr`，签名 `getCITypeAttributesById(typeId)` → `{attributes: [{name, alias, ...}]}`）。
- 后端映射字段契约见"关键接口约定"。

- [ ] **Step 1: i18n 更新**

`cmdb-ui/src/views/setting/lang/zh.js` 的 `grafana` 块：删除 `dashboardUid`、`varName` 两个 key，新增：

```js
    status: '状态',
    healthy: '正常',
    unhealthy: '异常',
    checking: '检测中',
    enable: '启用',
    namespace: '名称空间',
    dashboardName: '仪表盘名称',
    dashboardTitle: '仪表盘别名',
    varMapping: '变量映射',
    grafanaVar: 'Grafana变量',
    ciAttr: 'CI属性',
    addVarMapping: '添加变量映射',
    dashboardNameRequired: '请选择或输入仪表盘名称',
    varMappingIncomplete: '变量映射存在未填完整的行',
    dashboardLoadFailed: '仪表盘列表获取失败，可手工输入名称',
```

`en.js` 对应：`status: 'Status'`, `healthy: 'Healthy'`, `unhealthy: 'Unhealthy'`, `checking: 'Checking'`, `enable: 'Enable'`, `namespace: 'Namespace'`, `dashboardName: 'Dashboard Name'`, `dashboardTitle: 'Dashboard Title'`, `varMapping: 'Variable Mapping'`, `grafanaVar: 'Grafana Variable'`, `ciAttr: 'CI Attribute'`, `addVarMapping: 'Add Variable Mapping'`, `dashboardNameRequired: 'Please select or input dashboard name'`, `varMappingIncomplete: 'Some variable mapping rows are incomplete'`, `dashboardLoadFailed: 'Failed to load dashboards, you can input the name manually'`。

- [ ] **Step 2: 连接表格加状态/启用列 + 连接表单加启用开关**

template 连接表格内、`action` 模板前插入两个 slot 模板：

```html
        <template slot="statusTitle">
          {{ $t('cs.grafana.status') }}
          <a-icon type="reload" :style="{ marginLeft: '4px', cursor: 'pointer' }" @click="loadHealth" />
        </template>
        <template slot="status" slot-scope="text, record">
          <a-tooltip v-if="healthMap[record.id] && !healthMap[record.id].ok" :title="healthMap[record.id].error">
            <a-badge status="error" :text="$t('cs.grafana.unhealthy')" />
          </a-tooltip>
          <a-badge v-else-if="healthMap[record.id] && healthMap[record.id].ok" status="success" :text="$t('cs.grafana.healthy')" />
          <a-badge v-else status="default" :text="$t('cs.grafana.checking')" />
        </template>
        <template slot="enable" slot-scope="text, record">
          <a-switch :checked="record.enable !== 0" @change="(checked) => handleToggleEnable(record, checked)" />
        </template>
```

`connectionColumns` 在 remark 列后、action 列前插入：

```js
        { slots: { title: 'statusTitle' }, scopedSlots: { customRender: 'status' }, width: 110 },
        { title: this.$t('cs.grafana.enable'), scopedSlots: { customRender: 'enable' }, width: 80 },
```

data 增加 `healthMap: {}`；methods 增加：

```js
    async loadHealth() {
      this.healthMap = {}
      try {
        const res = await getGrafanaConnectionsHealth()
        const map = {}
        ;(res.health || []).forEach((h) => { map[h.id] = h })
        this.healthMap = map
      } catch (e) {}
    },
    async handleToggleEnable(record, checked) {
      await putGrafanaConnection(record.id, { enable: checked ? 1 : 0 })
      this.$set(record, 'enable', checked ? 1 : 0)
      this.$message.success(this.$t('saveSuccess'))
    },
```

`loadAll` 末尾追加 `this.loadHealth()`（不 await）。

import 增加 `getGrafanaConnectionsHealth`。

连接表单 modal：remark 表单项后增加：

```html
        <a-form-model-item :label="$t('cs.grafana.enable')" prop="enable">
          <a-switch :checked="connectionForm.enable !== 0" @change="(checked) => { connectionForm.enable = checked ? 1 : 0 }" />
        </a-form-model-item>
```

`connectionForm` 初始值与 `openConnectionModal` 两处对象都增加 `enable`（新建默认 `1`，编辑取 `record.enable === undefined ? 1 : record.enable`）。

- [ ] **Step 3: 映射 modal 整体重做**

映射 modal 的 form 部分替换为：

```html
      <a-form-model ref="mappingForm" :model="mappingForm" :rules="mappingRules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-model-item :label="$t('cs.grafana.ciType')" prop="ci_type_id">
          <a-select v-model="mappingForm.ci_type_id" show-search option-filter-prop="children" @change="handleCiTypeChange">
            <a-select-option v-for="t in ciTypes" :key="t.id" :value="t.id">
              {{ t.alias || t.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.connectionInstance')" prop="connection_id">
          <a-select v-model="mappingForm.connection_id" @change="handleMappingConnectionChange">
            <a-select-option v-for="c in connections" :key="c.id" :value="c.id">
              {{ c.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.namespace')" prop="namespace">
          <a-input v-model="mappingForm.namespace" placeholder="default" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.dashboardName')" prop="dashboard_name">
          <a-auto-complete
            v-model="mappingForm.dashboard_name"
            :data-source="dashboardOptions"
            :filter-option="filterDashboardOption"
            @select="handleDashboardSelect"
          />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.dashboardTitle')" prop="dashboard_title">
          <a-input v-model="mappingForm.dashboard_title" read-only />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.varMapping')">
          <div v-for="(vm, idx) in mappingForm.var_mapping" :key="idx" class="var-mapping-row">
            <a-auto-complete
              v-model="vm.grafana_var"
              :data-source="variableOptions"
              :placeholder="$t('cs.grafana.grafanaVar')"
              class="var-mapping-input"
              @change="(v) => handleVarChange(vm, v)"
            />
            <a-icon type="swap-right" class="var-mapping-arrow" />
            <a-select
              v-model="vm.ci_attr"
              show-search
              option-filter-prop="children"
              :placeholder="$t('cs.grafana.ciAttr')"
              class="var-mapping-input"
            >
              <a-select-option v-for="a in ciAttrOptions" :key="a.name" :value="a.name">
                {{ a.alias || a.name }}
              </a-select-option>
            </a-select>
            <a-icon type="minus-circle" class="var-mapping-delete" @click="mappingForm.var_mapping.splice(idx, 1)" />
          </div>
          <a-button type="dashed" size="small" icon="plus" @click="addVarMapping">
            {{ $t('cs.grafana.addVarMapping') }}
          </a-button>
        </a-form-model-item>
      </a-form-model>
```

script 改动：

1. import 增加 `getGrafanaDashboards`、`getGrafanaDashboardVariables`、`getCITypeAttributesById`（`from '@/modules/cmdb/api/CITypeAttr'`）。
2. data 中 `mappingForm` 替换为：

```js
      mappingForm: { id: null, ci_type_id: undefined, connection_id: undefined, namespace: 'default', dashboard_name: '', dashboard_title: '', var_mapping: [] },
      dashboards: [],
      variableOptions: [],
      ciAttrOptions: [],
```

3. `mappingColumns` 替换为：

```js
      mappingColumns: [
        { title: this.$t('cs.grafana.ciType'), scopedSlots: { customRender: 'ci_type' } },
        { title: this.$t('cs.grafana.connectionInstance'), scopedSlots: { customRender: 'connection' } },
        { title: this.$t('cs.grafana.namespace'), dataIndex: 'namespace', width: 100 },
        { title: this.$t('cs.grafana.dashboardTitle'), dataIndex: 'dashboard_title' },
        { title: this.$t('cs.grafana.dashboardName'), dataIndex: 'dashboard_name' },
        { title: this.$t('cs.grafana.varMapping'), scopedSlots: { customRender: 'var_mapping' } },
        { title: this.$t('cs.grafana.operation'), scopedSlots: { customRender: 'action' }, width: 160 },
      ],
```

映射表格增加 var_mapping slot 模板：

```html
        <template slot="var_mapping" slot-scope="text, record">
          {{ (record.var_mapping || []).map((vm) => `${vm.grafana_var}←${vm.ci_attr}`).join(', ') || '-' }}
        </template>
```

4. `mappingRules` 替换为：

```js
    mappingRules() {
      return {
        ci_type_id: [{ required: true, message: this.$t('cs.grafana.ciTypeRequired'), trigger: 'change' }],
        connection_id: [{ required: true, message: this.$t('cs.grafana.connectionRequired'), trigger: 'change' }],
        dashboard_name: [{ required: true, message: this.$t('cs.grafana.dashboardNameRequired'), trigger: 'blur' }],
      }
    },
```

5. computed 增加：

```js
    dashboardOptions() {
      return this.dashboards.map((d) => ({ value: d.name, text: `${d.title} (${d.name})` }))
    },
```

6. `openMappingModal` 替换为：

```js
    openMappingModal(record = null) {
      this.mappingForm = record
        ? {
            id: record.id,
            ci_type_id: record.ci_type_id,
            connection_id: record.connection_id,
            namespace: record.namespace || 'default',
            dashboard_name: record.dashboard_name,
            dashboard_title: record.dashboard_title,
            var_mapping: (record.var_mapping || []).map((vm) => ({ ...vm })),
          }
        : { id: null, ci_type_id: undefined, connection_id: undefined, namespace: 'default', dashboard_name: '', dashboard_title: '', var_mapping: [] }
      this.mappingModalVisible = true
      this.$nextTick(() => this.$refs.mappingForm && this.$refs.mappingForm.clearValidate())
      if (this.mappingForm.ci_type_id) this.handleCiTypeChange(this.mappingForm.ci_type_id)
      if (this.mappingForm.connection_id) this.handleMappingConnectionChange(this.mappingForm.connection_id)
      if (this.mappingForm.connection_id && this.mappingForm.dashboard_name) {
        this.loadVariables(this.mappingForm.connection_id, this.mappingForm.dashboard_name)
      }
    },
```

7. methods 增加：

```js
    async handleCiTypeChange(typeId) {
      try {
        const res = await getCITypeAttributesById(typeId)
        this.ciAttrOptions = res.attributes || []
      } catch (e) {
        this.ciAttrOptions = []
      }
    },
    async handleMappingConnectionChange(connectionId) {
      try {
        const res = await getGrafanaDashboards(connectionId, this.mappingForm.namespace || 'default')
        this.dashboards = res.dashboards || []
      } catch (e) {
        this.dashboards = []
        this.$message.warning(this.$t('cs.grafana.dashboardLoadFailed'))
      }
    },
    async loadVariables(connectionId, name) {
      try {
        const res = await getGrafanaDashboardVariables(connectionId, name)
        this.variableOptions = res.variables || []
      } catch (e) {
        this.variableOptions = []
      }
    },
    filterDashboardOption(input, option) {
      const text = (option.componentOptions.children[0].text || '').toLowerCase()
      return text.includes(input.toLowerCase())
    },
    handleDashboardSelect(value) {
      const d = this.dashboards.find((i) => i.name === value)
      this.mappingForm.dashboard_title = d ? d.title : ''
      this.loadVariables(this.mappingForm.connection_id, value)
    },
    handleVarChange(vm, value) {
      vm.grafana_var = value
      if (!vm.ci_attr && this.ciAttrOptions.some((a) => a.name === value)) {
        vm.ci_attr = value
      }
    },
    addVarMapping() {
      this.mappingForm.var_mapping.push({ grafana_var: undefined, ci_attr: undefined })
    },
```

8. `handleSaveMapping` 在 `validate` 回调内 `if (!valid) return` 之后增加变量映射完整性校验：

```js
        const incomplete = this.mappingForm.var_mapping.some((vm) => !vm.grafana_var || !vm.ci_attr)
        if (incomplete) {
          this.$message.error(this.$t('cs.grafana.varMappingIncomplete'))
          return
        }
```

9. style 增加：

```less
  .var-mapping-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    .var-mapping-input {
      flex: 1;
    }
    .var-mapping-arrow,
    .var-mapping-delete {
      flex-shrink: 0;
    }
    .var-mapping-delete {
      cursor: pointer;
      color: #f5222d;
    }
  }
```

- [ ] **Step 4: lint + 构建**

Run: `cd cmdb-ui && npx eslint src/views/setting/grafana/index.vue src/views/setting/lang/zh.js src/views/setting/lang/en.js`
Expected: 无 error

Run: `cd cmdb-ui && npx vue-cli-service build --mode development --no-clean 2>&1 | tail -2`
Expected: Build complete

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui/src/views/setting/grafana/index.vue cmdb-ui/src/views/setting/lang/zh.js cmdb-ui/src/views/setting/lang/en.js
git commit -m "feat(grafana): setting page with health/enable and new mapping form"
```

---

### Task 6: ciDetailGrafana vars 拼接 + E2E

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailGrafana.vue`（注意保留工作区已有的高度修复）

**Interfaces:**
- Consumes: Task 3 的 `result.vars` 数组。

- [ ] **Step 1: URL 构建改为遍历 vars**

`load()` 中的 URL 构建部分替换为：

```js
        const r = res.result
        if (r && r.connection_id && r.uid) {
          // iframe 指向后端代理，由后端注入 Service Account Token，
          // 浏览器无需 Grafana 匿名访问也拿不到 api_key
          const apiBase = String(process.env.VUE_APP_API_BASE_URL || '').replace(/\/+$/, '')
          let url = `${apiBase}/v0.1/grafana/proxy/${r.connection_id}/d/${r.uid}${r.slug ? '/' + r.slug : ''}?kiosk`
          ;(r.vars || []).forEach((v) => {
            if (v.name && v.value !== undefined && v.value !== null && v.value !== '') {
              url += `&var-${v.name}=${encodeURIComponent(v.value)}`
            }
          })
          this.iframeUrl = url
        }
```

- [ ] **Step 2: lint + 构建**

Run: `cd cmdb-ui && npx eslint src/modules/cmdb/views/ci/modules/ciDetailGrafana.vue && npx vue-cli-service build --mode development --no-clean 2>&1 | tail -2`
Expected: 无 error，Build complete

- [ ] **Step 3: E2E（真实 Grafana，运行中的后端自动重载）**

后端 `uvicorn --reload` 运行中（127.0.0.1:5000），真实 Grafana `http://172.30.6.231:3000`（连接 id=1，服务账户 token 见下）。用 admin/123456 登录取 token。

1. `GET /api/common-setting/v1/grafana/connections/health` → `health[0].ok == true`。
2. `GET .../connections/1/dashboards?namespace=default` → 列表含 `{"name": "rYdddlPWo", "title": "Linux Dashboard"}`。
3. `GET .../connections/1/dashboards/rYdddlPWo/variables` → 含 `instance`、`maintype` 等，不含 `datasource`。
4. 创建映射（bu 类型 id=1，dashboard_name=rYdddlPWo，var_mapping `[{"grafana_var": "name", "ci_attr": "bu_name"}]`）；创建 CI `{"ci_type": "bu", "bu_name": "e2e-vars"}`；`GET /api/v0.1/ci/{id}/grafana` → `result.uid == "rYdddlPWo"`，`result.vars == [{"name": "name", "value": "e2e-vars"}]`。
5. 停用连接（`PUT .../connections/1` `{data: {enable: 0}}`）→ 再查 resolve → `result == null`（映射指向停用实例且无其他实例可搜）；恢复 `enable: 1`。
6. 清理：删除测试映射与测试 CI。
7. 回归：`cd cmdb-api-fastapi && .venv/bin/python -m pytest tests/ -q` → 18 passed。

- [ ] **Step 4: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailGrafana.vue
git commit -m "feat(grafana): ci detail tab passes mapped vars to dashboard"
```

---

## Self-Review 结论

- Spec 覆盖：name 替代 uid（Task 1/2/3）、namespace/dashboard_title/var_mapping（Task 2/5）、仪表盘列表与变量拉取（Task 1/2/4/5）、健康状态（Task 2/4/5）、启用开关（Task 1 enable 过滤 / Task 2 CRUD / Task 5 UI）、vars 嵌入（Task 3/6）、测试（Task 1 单测 + Task 6 E2E）—— 无遗漏。
- 类型一致性：`pick_dashboard` 返回 `mapping` 键在 Task 1 测试与 Task 3 消费一致；`vars` 数组元素 `{name, value}` 在 Task 3 生产与 Task 6 消费一致；映射字段名全链一致。
- 已知取舍：手动输入仪表盘名称时不自动拉变量（variableOptions 为空，可手工输入变量名）；旧映射记录（虚拟机→旧 uid）在 E2E 环境中需用户按新格式重新配置（spec 已确认不做兼容）。
