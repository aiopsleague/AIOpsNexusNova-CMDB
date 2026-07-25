# Grafana 集成 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 CMDB 中集成 Grafana：后台管理页配置多实例连接（URL + Service Account API Key）与 CI 类型→仪表板映射，CI 详情页新增 tab_6 嵌入对应该 CI 的 Grafana 仪表板。

**Architecture:** 后端（cmdb-api-fastapi）加密存储配置于 `common_data` 表（`data_type='Grafana'`，整条 AES 加密），提供配置 CRUD API 与 `GET /api/v0.1/ci/{ci_id}/grafana` 解析端点（映射优先、名称搜索兜底）；前端 iframe 直连 Grafana（kiosk 模式 + 模板变量）。API Key 永不出后端。

**Tech Stack:** FastAPI（Flask-SQLAlchemy 兼容层）、requests、pytest；Vue2 + ant-design-vue 1.x。

**Spec:** `docs/superpowers/specs/2026-07-25-grafana-integration-design.md`

## Global Constraints

- 只修改 `cmdb-api-fastapi/` 和 `cmdb-ui/`；**不动** `cmdb-api/`（旧 Flask 后端）。
- 后端视图遵循现有兼容层范式：`from api.core.context import request`，用 `request.json` / `request.values`；**静态路由必须注册在参数化路由之前**（见 `api/views/common_setting/auth_config.py` 头注释）。
- 不新增 Python 依赖（用已有 `requests`）；不新增前端依赖。
- 前端所有展示文案走 i18n（zh + en 双语）。
- API Key：AES 加密存储（复用 `api.lib.utils.AESCrypto`）；GET 接口脱敏为 `"******"`；PUT 时 `api_key` 为空则保留原值。
- 所有对 Grafana 的 HTTP 调用 5s 超时；解析端点中 Grafana 调用失败一律降级为空结果 + `current_app.logger.warning`，**不得抛 500**。
- 提交信息遵循仓库惯例：`feat(grafana): ...` / `test(grafana): ...`。
- 后端 pytest 运行方式：`cd cmdb-api-fastapi && .venv/bin/python -m pytest tests/ -v`。

## 存储格式（关键约定，后续任务依赖）

`common_data` 表一条记录，`data_type='Grafana'`，`data` 为 AES 加密的 JSON 字符串，解密后结构：

```json
{
  "connections": [{"id": 1, "name": "生产Grafana", "url": "https://g.example.com", "api_key": "glsa_xxx", "remark": ""}],
  "mappings": [{"id": 1, "ci_type_id": 3, "connection_id": 1, "dashboard_uid": "abc123", "var_name": "ci_name"}]
}
```

`id` 为列表内自增整数（`max(existing) + 1`，空列表从 1 开始）。`dashboard_uid` 可空字符串；`var_name` 缺省 `"ci_name"`。

解析端点响应：

```json
{"configured": true, "result": {"grafana_url": "https://g.example.com", "uid": "abc123", "slug": "host-01", "var_name": "ci_name", "var_value": "host-01"}}
```

未配置任何连接时 `configured=false, result=null`；配置了但无匹配时 `configured=true, result=null`。

---

### Task 1: 后端纯逻辑模块 grafana_client.py + 单元测试

**Files:**
- Create: `cmdb-api-fastapi/api/lib/common_setting/grafana_client.py`
- Test: `cmdb-api-fastapi/tests/test_grafana_client.py`
- Create: `cmdb-api-fastapi/tests/conftest.py`

**Interfaces:**
- Consumes: 仅 `requests`（无 app/db 依赖，`api/__init__.py` 与 `api/lib/common_setting/__init__.py` 均为空，可直接 import）。
- Produces:
  - `GrafanaClient(url, api_key, timeout=5)`：`.test_connection() -> True`（失败抛异常）；`.search_dashboard(query) -> list[dict]`（元素含 `uid`/`title`/`url`）。
  - `pick_dashboard(connections, mappings, ci_type_id, unique_value, search_fn) -> dict | None`，返回 `{"connection": conn, "uid": str, "slug": str|None, "var_name": str, "var_value": str}`。
  - Task 4 的 `resolve_ci_grafana` 依赖这两个接口。

- [ ] **Step 1: 写 conftest（让 pytest 能 import api 包）**

`cmdb-api-fastapi/tests/conftest.py`：

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

- [ ] **Step 2: 写失败测试**

`cmdb-api-fastapi/tests/test_grafana_client.py`：

```python
# -*- coding:utf-8 -*-
from unittest import mock

import pytest

from api.lib.common_setting.grafana_client import GrafanaClient, pick_dashboard

CONN1 = {"id": 1, "name": "g1", "url": "http://g1:3000", "api_key": "k1"}
CONN2 = {"id": 2, "name": "g2", "url": "http://g2:3000/", "api_key": "k2"}
DASH = {"uid": "abc123", "title": "host-01", "url": "/d/abc123/host-01"}


def _ok_search(dashboards):
    return lambda conn: dashboards


def _fail_search(conn):
    raise Exception("connection refused")


def test_pick_dashboard_mapping_with_uid():
    mappings = [{"id": 1, "ci_type_id": 3, "connection_id": 2, "dashboard_uid": "abc123", "var_name": "host"}]
    picked = pick_dashboard([CONN1, CONN2], mappings, 3, "host-01", _fail_search)
    assert picked["connection"] is CONN2
    assert picked["uid"] == "abc123"
    assert picked["slug"] is None
    assert picked["var_name"] == "host"
    assert picked["var_value"] == "host-01"


def test_pick_dashboard_mapping_without_uid_searches_that_instance():
    mappings = [{"id": 1, "ci_type_id": 3, "connection_id": 1, "dashboard_uid": "", "var_name": ""}]
    picked = pick_dashboard([CONN1, CONN2], mappings, 3, "host-01", _ok_search([DASH]))
    assert picked["connection"] is CONN1
    assert picked["uid"] == "abc123"
    assert picked["slug"] == "host-01"
    assert picked["var_name"] == "ci_name"  # 空 var_name 回退默认


def test_pick_dashboard_mapping_miss_falls_back_to_global_search():
    mappings = [{"id": 1, "ci_type_id": 3, "connection_id": 1, "dashboard_uid": "", "var_name": "ci_name"}]
    calls = []

    def search_fn(conn):
        calls.append(conn["id"])
        return [DASH] if conn["id"] == 2 else []

    picked = pick_dashboard([CONN1, CONN2], mappings, 3, "host-01", search_fn)
    assert picked["connection"] is CONN2
    assert calls == [1, 2]


def test_pick_dashboard_no_mapping_searches_all_in_order():
    def search_fn(conn):
        return [DASH] if conn["id"] == 2 else []

    picked = pick_dashboard([CONN1, CONN2], [], 3, "host-01", search_fn)
    assert picked["connection"] is CONN2
    assert picked["var_name"] == "ci_name"


def test_pick_dashboard_nothing_found():
    assert pick_dashboard([CONN1], [], 3, "host-01", _ok_search([])) is None
    assert pick_dashboard([CONN1], [], 3, "host-01", _fail_search) is None


def test_pick_dashboard_no_connections():
    assert pick_dashboard([], [], 3, "host-01", _ok_search([DASH])) is None


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
```

- [ ] **Step 3: 跑测试确认失败**

Run: `cd cmdb-api-fastapi && .venv/bin/python -m pytest tests/test_grafana_client.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'api.lib.common_setting.grafana_client'`）

- [ ] **Step 4: 实现 grafana_client.py**

`cmdb-api-fastapi/api/lib/common_setting/grafana_client.py`：

```python
# -*- coding:utf-8 -*-
"""Grafana HTTP client and dashboard-picking logic.

This module is intentionally free of app/db imports so it can be unit
tested without a Flask/FastAPI application context.
"""

import requests

DEFAULT_VAR_NAME = "ci_name"
REQUEST_TIMEOUT = 5


class GrafanaClient(object):
    def __init__(self, url, api_key, timeout=REQUEST_TIMEOUT):
        self.url = (url or "").rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self):
        return {"Authorization": "Bearer {}".format(self.api_key)}

    def test_connection(self):
        """Raise on failure, return True on success."""
        resp = requests.get("{}/api/user".format(self.url),
                            headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return True

    def search_dashboard(self, query):
        """Return list of dashboard dicts ({uid, title, url, ...})."""
        resp = requests.get("{}/api/search".format(self.url),
                            params={"query": query, "type": "dash-db"},
                            headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()


def _slug_from(dash):
    # grafana /api/search returns "url" like "/d/<uid>/<slug>"
    parts = (dash.get("url") or "").strip("/").split("/")
    return parts[-1] if len(parts) >= 3 else None


def _first_hit(search_fn, connection):
    try:
        dashboards = search_fn(connection) or []
    except Exception:
        return None
    return dashboards[0] if dashboards else None


def _result(connection, uid, slug, var_name, var_value):
    return dict(connection=connection,
                uid=uid,
                slug=slug,
                var_name=(var_name or "").strip() or DEFAULT_VAR_NAME,
                var_value=var_value)


def pick_dashboard(connections, mappings, ci_type_id, unique_value, search_fn):
    """Decide which grafana dashboard to show for a CI.

    :param connections: list of {"id", "name", "url", "api_key", "remark"}
    :param mappings: list of {"id", "ci_type_id", "connection_id", "dashboard_uid", "var_name"}
    :param ci_type_id: int, the CI's type id
    :param unique_value: str, the CI's unique attribute value (search keyword)
    :param search_fn: callable(connection) -> list of dashboard dicts; may raise
    :return: dict(connection=..., uid=..., slug=..., var_name=..., var_value=...) or None
    """
    if not connections:
        return None

    mapping = next((m for m in mappings if m.get("ci_type_id") == ci_type_id), None)
    if mapping:
        conn = next((c for c in connections if c.get("id") == mapping.get("connection_id")), None)
        if conn:
            uid = (mapping.get("dashboard_uid") or "").strip()
            if uid:
                return _result(conn, uid, None, mapping.get("var_name"), unique_value)
            dash = _first_hit(search_fn, conn)
            if dash:
                return _result(conn, dash.get("uid"), _slug_from(dash),
                               mapping.get("var_name"), unique_value)
            # 映射实例搜不到 → 继续全局兜底

    for conn in connections:
        dash = _first_hit(search_fn, conn)
        if dash:
            return _result(conn, dash.get("uid"), _slug_from(dash), None, unique_value)

    return None
```

- [ ] **Step 5: 跑测试确认通过**

Run: `cd cmdb-api-fastapi && .venv/bin/python -m pytest tests/test_grafana_client.py -v`
Expected: 8 passed

- [ ] **Step 6: Commit**

```bash
git add cmdb-api-fastapi/api/lib/common_setting/grafana_client.py cmdb-api-fastapi/tests/
git commit -m "feat(grafana): add grafana client and dashboard picking logic"
```

---

### Task 2: 后端配置 CRUD（common_setting/grafana.py）+ 错误文案

**Files:**
- Create: `cmdb-api-fastapi/api/lib/common_setting/grafana.py`
- Modify: `cmdb-api-fastapi/api/lib/common_setting/resp_format.py`（在 `ErrFormat` 类内追加，建议加在 `email_already_exists` 行之后）

**Interfaces:**
- Consumes: `api.models.common_setting.CommonData`、`api.lib.utils.AESCrypto`（参照 `AuthenticateDataCRUD` 的用法）、Task 1 的 `GrafanaClient`。
- Produces: `GrafanaConfigCRUD`，方法：
  - `get_config() -> {"connections": [...], "mappings": [...]}`（解密，api_key 明文，仅供后端内部使用）
  - `list_connections() -> [...]`（api_key 脱敏为 `"******"`）
  - `create_connection(data) -> dict`（脱敏后的新记录）
  - `update_connection(_id, data) -> dict`（api_key 空则保留原值）
  - `delete_connection(_id) -> None`（级联删除引用它的 mappings）
  - `list_mappings() -> [...]`
  - `create_mapping(data) / update_mapping(_id, data) / delete_mapping(_id)`
  - `test_connection(url, api_key) -> True`（失败 `abort(400, ...)`）
- Task 3/4 依赖全部方法。

- [ ] **Step 1: 追加 ErrFormat 文案**

在 `cmdb-api-fastapi/api/lib/common_setting/resp_format.py` 的 `ErrFormat` 类中 `email_already_exists` 行后追加：

```python
    grafana_connection_not_found = _l("Grafana connection [{}] not found")  # Grafana连接 [{}] 不存在
    grafana_mapping_not_found = _l("Grafana mapping [{}] not found")  # Grafana映射 [{}] 不存在
    grafana_name_required = _l("Grafana name is required")  # Grafana名称是必须的
    grafana_url_required = _l("Grafana url is required")  # Grafana地址是必须的
    grafana_api_key_required = _l("Grafana api key is required")  # Grafana API Key是必须的
    grafana_test_failed = _l("Grafana connection test failed: {}")  # Grafana连接测试失败: {}
```

- [ ] **Step 2: 实现 grafana.py**

`cmdb-api-fastapi/api/lib/common_setting/grafana.py`：

```python
# -*- coding:utf-8 -*-
import json

from api.core.errors import abort
from api.extensions import db
from api.lib.common_setting.grafana_client import GrafanaClient
from api.lib.common_setting.resp_format import ErrFormat
from api.lib.utils import AESCrypto
from api.models.common_setting import CommonData

DATA_TYPE = "Grafana"
API_KEY_MASK = "******"


class GrafanaConfigCRUD(object):
    """All grafana config lives in ONE common_data record (data_type='Grafana'),
    AES-encrypted as a whole, shaped: {"connections": [...], "mappings": [...]}.
    """

    @staticmethod
    def _get_record(to_dict=False):
        return CommonData.get_by(first=True, data_type=DATA_TYPE, to_dict=to_dict)

    def get_config(self):
        record = self._get_record(to_dict=True)
        if not record:
            return {"connections": [], "mappings": []}
        try:
            config = json.loads(AESCrypto().decrypt(record.get("data") or ""))
        except Exception:
            return {"connections": [], "mappings": []}
        config.setdefault("connections", [])
        config.setdefault("mappings", [])
        return config

    def _save(self, config):
        encrypted = AESCrypto().encrypt(json.dumps(config))
        record = self._get_record(to_dict=False)
        try:
            if record:
                return record.update(data=encrypted)
            return CommonData.create(data_type=DATA_TYPE, data=encrypted)
        except Exception as e:
            db.session.rollback()
            abort(400, str(e))

    @staticmethod
    def _next_id(items):
        return max([i.get("id", 0) for i in items] or [0]) + 1

    @staticmethod
    def _mask(connection):
        masked = dict(connection)
        masked["api_key"] = API_KEY_MASK if connection.get("api_key") else ""
        return masked

    # ---------------- connections ----------------

    def list_connections(self):
        return [self._mask(c) for c in self.get_config()["connections"]]

    def create_connection(self, data):
        if not (data.get("name") or "").strip():
            abort(400, ErrFormat.grafana_name_required)
        if not (data.get("url") or "").strip():
            abort(400, ErrFormat.grafana_url_required)
        if not (data.get("api_key") or "").strip():
            abort(400, ErrFormat.grafana_api_key_required)

        config = self.get_config()
        connection = dict(id=self._next_id(config["connections"]),
                          name=data["name"].strip(),
                          url=data["url"].strip().rstrip("/"),
                          api_key=data["api_key"].strip(),
                          remark=(data.get("remark") or "").strip())
        config["connections"].append(connection)
        self._save(config)
        return self._mask(connection)

    def update_connection(self, _id, data):
        config = self.get_config()
        connection = next((c for c in config["connections"] if c.get("id") == _id), None)
        if not connection:
            abort(404, ErrFormat.grafana_connection_not_found.format(_id))

        if "name" in data:
            if not (data["name"] or "").strip():
                abort(400, ErrFormat.grafana_name_required)
            connection["name"] = data["name"].strip()
        if "url" in data:
            if not (data["url"] or "").strip():
                abort(400, ErrFormat.grafana_url_required)
            connection["url"] = data["url"].strip().rstrip("/")
        if (data.get("api_key") or "").strip():
            connection["api_key"] = data["api_key"].strip()
        if "remark" in data:
            connection["remark"] = (data["remark"] or "").strip()

        self._save(config)
        return self._mask(connection)

    def delete_connection(self, _id):
        config = self.get_config()
        before = len(config["connections"])
        config["connections"] = [c for c in config["connections"] if c.get("id") != _id]
        if len(config["connections"]) == before:
            abort(404, ErrFormat.grafana_connection_not_found.format(_id))
        # 级联删除引用该实例的映射
        config["mappings"] = [m for m in config["mappings"] if m.get("connection_id") != _id]
        self._save(config)

    def test_connection(self, url, api_key):
        if not (url or "").strip():
            abort(400, ErrFormat.grafana_url_required)
        if not (api_key or "").strip():
            abort(400, ErrFormat.grafana_api_key_required)
        try:
            return GrafanaClient(url.strip(), api_key.strip()).test_connection()
        except Exception as e:
            abort(400, ErrFormat.grafana_test_failed.format(str(e)))

    # ---------------- mappings ----------------

    def list_mappings(self):
        return self.get_config()["mappings"]

    def create_mapping(self, data):
        ci_type_id = data.get("ci_type_id")
        connection_id = data.get("connection_id")
        if not ci_type_id or not connection_id:
            abort(400, ErrFormat.value_is_required)

        config = self.get_config()
        if not any(c.get("id") == connection_id for c in config["connections"]):
            abort(404, ErrFormat.grafana_connection_not_found.format(connection_id))

        mapping = dict(id=self._next_id(config["mappings"]),
                       ci_type_id=int(ci_type_id),
                       connection_id=int(connection_id),
                       dashboard_uid=(data.get("dashboard_uid") or "").strip(),
                       var_name=(data.get("var_name") or "").strip() or "ci_name")
        config["mappings"].append(mapping)
        self._save(config)
        return mapping

    def update_mapping(self, _id, data):
        config = self.get_config()
        mapping = next((m for m in config["mappings"] if m.get("id") == _id), None)
        if not mapping:
            abort(404, ErrFormat.grafana_mapping_not_found.format(_id))

        if "ci_type_id" in data and data["ci_type_id"]:
            mapping["ci_type_id"] = int(data["ci_type_id"])
        if "connection_id" in data and data["connection_id"]:
            if not any(c.get("id") == data["connection_id"] for c in config["connections"]):
                abort(404, ErrFormat.grafana_connection_not_found.format(data["connection_id"]))
            mapping["connection_id"] = int(data["connection_id"])
        if "dashboard_uid" in data:
            mapping["dashboard_uid"] = (data["dashboard_uid"] or "").strip()
        if "var_name" in data:
            mapping["var_name"] = (data["var_name"] or "").strip() or "ci_name"

        self._save(config)
        return mapping

    def delete_mapping(self, _id):
        config = self.get_config()
        before = len(config["mappings"])
        config["mappings"] = [m for m in config["mappings"] if m.get("id") != _id]
        if len(config["mappings"]) == before:
            abort(404, ErrFormat.grafana_mapping_not_found.format(_id))
        self._save(config)
```

注意：`ErrFormat.value_is_required` 已存在于 `resp_format.py`（第 31 行），直接复用。

- [ ] **Step 3: 验证模块可导入 + Task 1 测试不破**

Run: `cd cmdb-api-fastapi && .venv/bin/python -c "from api.lib.common_setting.grafana import GrafanaConfigCRUD; print('ok')" && .venv/bin/python -m pytest tests/ -v`
Expected: 输出 `ok`，8 passed

- [ ] **Step 4: Commit**

```bash
git add cmdb-api-fastapi/api/lib/common_setting/grafana.py cmdb-api-fastapi/api/lib/common_setting/resp_format.py
git commit -m "feat(grafana): add encrypted grafana config CRUD"
```

---

### Task 3: 后端配置 API 视图（common_setting/grafana_config.py）

**Files:**
- Create: `cmdb-api-fastapi/api/views/common_setting/grafana_config.py`

**Interfaces:**
- Consumes: Task 2 的 `GrafanaConfigCRUD`。路由自动注册（`api/views/entry.py` walk 包挂载到 `/api/common-setting/v1`），无需改 entry.py。
- Produces: REST 端点（全部 `@role_required("acl_admin")`）：
  - `GET/POST /common-setting/v1/grafana/connections`
  - `POST /common-setting/v1/grafana/connections/test`
  - `PUT/DELETE /common-setting/v1/grafana/connections/{_id:int}`
  - `GET/POST /common-setting/v1/grafana/mappings`
  - `PUT/DELETE /common-setting/v1/grafana/mappings/{_id:int}`
  - 请求体均为 `{"data": {...}}`（与 auth_config 一致）；前端 Task 5 按此调用。

- [ ] **Step 1: 实现视图**

`cmdb-api-fastapi/api/views/common_setting/grafana_config.py`：

```python
# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request

from api.lib.common_setting.grafana import GrafanaConfigCRUD
from api.lib.perm.acl.acl import role_required
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/grafana'

# NOTE(fastapi-port): static routes must be registered before parameterized
# ones ("/grafana/connections/{_id}" etc.), otherwise FastAPI matches them
# first and returns 422.


@router.get(f'{prefix}/connections')
@role_required("acl_admin")
def grafana_connections_get():
    return dict(connections=GrafanaConfigCRUD().list_connections())


@router.post(f'{prefix}/connections')
@role_required("acl_admin")
def grafana_connections_post():
    data = (request.json or {}).get('data', {})
    return GrafanaConfigCRUD().create_connection(data)


@router.post(f'{prefix}/connections/test')
@role_required("acl_admin")
def grafana_connections_test_post():
    data = (request.json or {}).get('data', {})
    GrafanaConfigCRUD().test_connection(data.get('url'), data.get('api_key'))
    return dict()


@router.put(f'{prefix}/connections/{{_id:int}}')
@role_required("acl_admin")
def grafana_connections_put(_id: int = None):
    data = (request.json or {}).get('data', {})
    return GrafanaConfigCRUD().update_connection(_id, data)


@router.delete(f'{prefix}/connections/{{_id:int}}')
@role_required("acl_admin")
def grafana_connections_delete(_id: int = None):
    GrafanaConfigCRUD().delete_connection(_id)
    return dict()


@router.get(f'{prefix}/mappings')
@role_required("acl_admin")
def grafana_mappings_get():
    return dict(mappings=GrafanaConfigCRUD().list_mappings())


@router.post(f'{prefix}/mappings')
@role_required("acl_admin")
def grafana_mappings_post():
    data = (request.json or {}).get('data', {})
    return GrafanaConfigCRUD().create_mapping(data)


@router.put(f'{prefix}/mappings/{{_id:int}}')
@role_required("acl_admin")
def grafana_mappings_put(_id: int = None):
    data = (request.json or {}).get('data', {})
    return GrafanaConfigCRUD().update_mapping(_id, data)


@router.delete(f'{prefix}/mappings/{{_id:int}}')
@role_required("acl_admin")
def grafana_mappings_delete(_id: int = None):
    GrafanaConfigCRUD().delete_mapping(_id)
    return dict()
```

- [ ] **Step 2: 验证路由注册成功**

Run: `cd cmdb-api-fastapi && .venv/bin/python -c "
from main import app
routes = [r.path for r in app.routes if 'grafana' in getattr(r, 'path', '')]
print('\n'.join(sorted(routes)))
"`
Expected: 列出 8 条 `/api/common-setting/v1/grafana/...` 路由（connections ×3 + connections/test + mappings ×3 + connections/{_id} ×2… 共 9 条含 test）

- [ ] **Step 3: Commit**

```bash
git add cmdb-api-fastapi/api/views/common_setting/grafana_config.py
git commit -m "feat(grafana): add grafana config REST API"
```

---

### Task 4: 后端 CI 解析端点（lib/cmdb/grafana.py + views/cmdb/grafana.py）

**Files:**
- Create: `cmdb-api-fastapi/api/lib/cmdb/grafana.py`
- Create: `cmdb-api-fastapi/api/views/cmdb/grafana.py`

**Interfaces:**
- Consumes: Task 1 `pick_dashboard`/`GrafanaClient`；Task 2 `GrafanaConfigCRUD.get_config()`；`CIManager.get_ci_by_id(ci_id, need_children=False)`（返回 dict，含 `_type` 与按属性名平铺的值，404 时内部 abort）；`CITypeCache.get(type_id).unique_id`；`AttributeCache.get(unique_id).name`。
- Produces: `resolve_ci_grafana(ci_id) -> {"configured": bool, "result": {...}|None}`；端点 `GET /api/v0.1/ci/{ci_id:int}/grafana`（普通登录用户，带 CI 读权限校验）。前端 Task 7 依赖响应格式（见"存储格式"一节）。

- [ ] **Step 1: 实现 lib/cmdb/grafana.py**

`cmdb-api-fastapi/api/lib/cmdb/grafana.py`：

```python
# -*- coding:utf-8 -*-
from api.core.context import current_app
from api.core.errors import abort

from api.lib.cmdb.cache import AttributeCache
from api.lib.cmdb.cache import CITypeCache
from api.lib.cmdb.ci import CIManager
from api.lib.cmdb.resp_format import ErrFormat
from api.lib.common_setting.grafana import GrafanaConfigCRUD
from api.lib.common_setting.grafana_client import GrafanaClient
from api.lib.common_setting.grafana_client import pick_dashboard
from api.models.cmdb import CI


def resolve_ci_grafana(ci_id):
    """Return {"configured": bool, "result": {...}|None} for the CI detail grafana tab."""
    ci_obj = CI.get_by_id(ci_id) or abort(404, ErrFormat.ci_not_found.format("id={}".format(ci_id)))
    CIManager.valid_ci_only_read(ci_obj)

    config = GrafanaConfigCRUD().get_config()
    connections = config["connections"]
    if not connections:
        return dict(configured=False, result=None)

    ci = CIManager.get_ci_by_id(ci_id, need_children=False)
    ci_type_id = ci["_type"]
    ci_type = CITypeCache.get(ci_type_id)
    unique_attr = AttributeCache.get(ci_type.unique_id) if ci_type else None
    unique_value = ci.get(unique_attr.name) if unique_attr else None
    if not unique_value:
        current_app.logger.warning("ci {} has no unique value, skip grafana resolve".format(ci_id))
        return dict(configured=True, result=None)

    def search_fn(connection):
        return GrafanaClient(connection["url"], connection["api_key"]).search_dashboard(str(unique_value))

    try:
        picked = pick_dashboard(connections, config["mappings"], ci_type_id, str(unique_value), search_fn)
    except Exception as e:
        current_app.logger.warning("grafana resolve failed for ci {}: {}".format(ci_id, e))
        return dict(configured=True, result=None)

    if not picked:
        return dict(configured=True, result=None)

    return dict(configured=True, result=dict(
        grafana_url=picked["connection"]["url"],
        uid=picked["uid"],
        slug=picked["slug"],
        var_name=picked["var_name"],
        var_value=picked["var_value"],
    ))
```

注意：`pick_dashboard` 内部已吞掉 search_fn 的异常，外层 try/except 是兜底。

- [ ] **Step 2: 实现 views/cmdb/grafana.py**

`cmdb-api-fastapi/api/views/cmdb/grafana.py`：

```python
# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.lib.cmdb.grafana import resolve_ci_grafana
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/ci/{ci_id:int}/grafana")
def ci_grafana_view_get(ci_id: int):
    return resolve_ci_grafana(ci_id)
```

- [ ] **Step 3: 验证路由注册 + 测试不破**

Run: `cd cmdb-api-fastapi && .venv/bin/python -c "
from main import app
print([r.path for r in app.routes if 'grafana' in getattr(r, 'path', '') and 'v0.1' in getattr(r, 'path', '')])
" && .venv/bin/python -m pytest tests/ -v`
Expected: `['/api/v0.1/ci/{ci_id}/grafana']`，8 passed

- [ ] **Step 4: Commit**

```bash
git add cmdb-api-fastapi/api/lib/cmdb/grafana.py cmdb-api-fastapi/api/views/cmdb/grafana.py
git commit -m "feat(grafana): add ci grafana dashboard resolve endpoint"
```

---

### Task 5: 前端 API 封装

**Files:**
- Create: `cmdb-ui/src/api/grafana.js`
- Modify: `cmdb-ui/src/modules/cmdb/api/ci.js`（在 `getCIById` 函数后追加）

**Interfaces:**
- Produces（Task 6/7 依赖这些函数名）：
  - `getGrafanaConnections()` → `{connections: [...]}`
  - `postGrafanaConnection(data)` / `putGrafanaConnection(id, data)` / `deleteGrafanaConnection(id)`
  - `testGrafanaConnection(data)`
  - `getGrafanaMappings()` → `{mappings: [...]}`
  - `postGrafanaMapping(data)` / `putGrafanaMapping(id, data)` / `deleteGrafanaMapping(id)`
  - `getCIGrafana(ciId)` → `{configured, result}`

- [ ] **Step 1: 创建 cmdb-ui/src/api/grafana.js**

```js
import { axios } from '@/utils/request'

export function getGrafanaConnections() {
    return axios({
        url: `/common-setting/v1/grafana/connections`,
        method: 'get',
    })
}

export function postGrafanaConnection(data) {
    return axios({
        url: `/common-setting/v1/grafana/connections`,
        method: 'post',
        data: { data },
    })
}

export function putGrafanaConnection(id, data) {
    return axios({
        url: `/common-setting/v1/grafana/connections/${id}`,
        method: 'put',
        data: { data },
    })
}

export function deleteGrafanaConnection(id) {
    return axios({
        url: `/common-setting/v1/grafana/connections/${id}`,
        method: 'delete',
    })
}

export function testGrafanaConnection(data) {
    return axios({
        url: `/common-setting/v1/grafana/connections/test`,
        method: 'post',
        data: { data },
    })
}

export function getGrafanaMappings() {
    return axios({
        url: `/common-setting/v1/grafana/mappings`,
        method: 'get',
    })
}

export function postGrafanaMapping(data) {
    return axios({
        url: `/common-setting/v1/grafana/mappings`,
        method: 'post',
        data: { data },
    })
}

export function putGrafanaMapping(id, data) {
    return axios({
        url: `/common-setting/v1/grafana/mappings/${id}`,
        method: 'put',
        data: { data },
    })
}

export function deleteGrafanaMapping(id) {
    return axios({
        url: `/common-setting/v1/grafana/mappings/${id}`,
        method: 'delete',
    })
}
```

- [ ] **Step 2: ci.js 追加 getCIGrafana**

在 `cmdb-ui/src/modules/cmdb/api/ci.js` 的 `getCIById` 函数（约 47 行）之后追加：

```js
export function getCIGrafana(ciId) {
    return axios({
        url: `/v0.1/ci/${ciId}/grafana`,
        method: 'get',
    })
}
```

先读该文件确认 `axios` 的 import 方式与现有函数风格，保持一致。

- [ ] **Step 3: 验证 lint/构建**

Run: `cd cmdb-ui && npx eslint src/api/grafana.js src/modules/cmdb/api/ci.js`
Expected: 无 error（warning 可接受）

- [ ] **Step 4: Commit**

```bash
git add cmdb-ui/src/api/grafana.js cmdb-ui/src/modules/cmdb/api/ci.js
git commit -m "feat(grafana): add frontend api wrappers"
```

---

### Task 6: 前端配置页 + 路由 + setting i18n

**Files:**
- Create: `cmdb-ui/src/views/setting/grafana/index.vue`
- Modify: `cmdb-ui/src/router/config.js:86-91`（在 `company_auth` 路由后追加）
- Modify: `cmdb-ui/src/views/setting/lang/zh.js`（`menu` 块加 `grafana`，文件末尾对象内加 `grafana` 块）
- Modify: `cmdb-ui/src/views/setting/lang/en.js`（同上）

**Interfaces:**
- Consumes: Task 5 的 `getGrafanaConnections/postGrafanaConnection/putGrafanaConnection/deleteGrafanaConnection/testGrafanaConnection/getGrafanaMappings/postGrafanaMapping/putGrafanaMapping/deleteGrafanaMapping`；`getCITypes`（`@/modules/cmdb/api/CIType`，返回 `{ci_types: [{id, name, alias, ...}]}`）。
- Produces: 页面路由 `/setting/grafana`（`name: 'setting_grafana'`，`permission: ['acl_admin']`）。

- [ ] **Step 1: 注册路由**

在 `cmdb-ui/src/router/config.js` 的 `company_auth` 路由对象（86-91 行）之后追加：

```js
        {
          path: '/setting/grafana',
          name: 'setting_grafana',
          meta: { title: 'cs.menu.grafana', appName: 'backend', icon: 'ops-setting-basic', selectedIcon: 'ops-setting-basic-selected', permission: ['acl_admin'] },
          component: () => import(/* webpackChunkName: "setting" */ '@/views/setting/grafana/index')
        },
```

（iconfont 中无 grafana 专用图标，复用 `ops-setting-basic`。）

- [ ] **Step 2: setting i18n 词条**

`cmdb-ui/src/views/setting/lang/zh.js`：`menu` 块中 `auth: '认证设置',` 后加 `grafana: 'Grafana设置',`；在返回对象中（如 `auth` 块附近）新增：

```js
  grafana: {
    connection: '连接实例',
    mapping: '仪表板映射',
    name: '名称',
    url: 'Grafana地址',
    apiKey: 'API Key',
    remark: '备注',
    ciType: 'CI类型',
    connectionInstance: '连接实例',
    dashboardUid: '仪表板UID',
    varName: '变量名',
    testConnect: '测试连接',
    testSuccess: '连接成功',
    addConnection: '新增连接',
    editConnection: '编辑连接',
    addMapping: '新增映射',
    editMapping: '编辑映射',
    nameRequired: '请输入名称',
    urlRequired: '请输入Grafana地址',
    apiKeyRequired: '请输入API Key',
    apiKeyKeepTip: '留空则不修改',
    ciTypeRequired: '请选择CI类型',
    connectionRequired: '请选择连接实例',
    operation: '操作',
    edit: '编辑',
    delete: '删除',
  },
```

`cmdb-ui/src/views/setting/lang/en.js`：对应英文版本（`grafana: 'Grafana'` 于 menu；块内 `connection: 'Connections'`、`mapping: 'Dashboard Mappings'` 等，逐 key 翻译）。

先读两个 lang 文件确认导出结构（`cs_zh` / `cs_en` 对象），在其内部追加。

- [ ] **Step 3: 实现配置页 index.vue**

`cmdb-ui/src/views/setting/grafana/index.vue`（完整代码）：

```vue
<template>
  <div class="ops-setting-grafana">
    <a-card :title="$t('cs.grafana.connection')" :bordered="false" class="grafana-card">
      <a-button slot="extra" type="primary" @click="openConnectionModal()">
        {{ $t('cs.grafana.addConnection') }}
      </a-button>
      <a-table
        :columns="connectionColumns"
        :data-source="connections"
        :pagination="false"
        rowKey="id"
        size="small"
      >
        <template slot="action" slot-scope="text, record">
          <a-space>
            <a @click="handleTest(record)">{{ $t('cs.grafana.testConnect') }}</a>
            <a @click="openConnectionModal(record)">{{ $t('cs.grafana.edit') }}</a>
            <a-popconfirm :title="$t('confirmDelete')" @confirm="handleDeleteConnection(record)">
              <a :style="{ color: '#f5222d' }">{{ $t('cs.grafana.delete') }}</a>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <a-card :title="$t('cs.grafana.mapping')" :bordered="false" class="grafana-card">
      <a-button slot="extra" type="primary" @click="openMappingModal()">
        {{ $t('cs.grafana.addMapping') }}
      </a-button>
      <a-table
        :columns="mappingColumns"
        :data-source="mappings"
        :pagination="false"
        rowKey="id"
        size="small"
      >
        <template slot="ci_type" slot-scope="text, record">
          {{ ciTypeName(record.ci_type_id) }}
        </template>
        <template slot="connection" slot-scope="text, record">
          {{ connectionName(record.connection_id) }}
        </template>
        <template slot="action" slot-scope="text, record">
          <a-space>
            <a @click="openMappingModal(record)">{{ $t('cs.grafana.edit') }}</a>
            <a-popconfirm :title="$t('confirmDelete')" @confirm="handleDeleteMapping(record)">
              <a :style="{ color: '#f5222d' }">{{ $t('cs.grafana.delete') }}</a>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <a-modal
      :title="connectionForm.id ? $t('cs.grafana.editConnection') : $t('cs.grafana.addConnection')"
      :visible="connectionModalVisible"
      :confirm-loading="saving"
      @ok="handleSaveConnection"
      @cancel="connectionModalVisible = false"
    >
      <a-form-model ref="connectionForm" :model="connectionForm" :rules="connectionRules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-model-item :label="$t('cs.grafana.name')" prop="name">
          <a-input v-model="connectionForm.name" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.url')" prop="url">
          <a-input v-model="connectionForm.url" placeholder="https://grafana.example.com" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.apiKey')" prop="api_key">
          <a-input-password v-model="connectionForm.api_key" :placeholder="connectionForm.id ? $t('cs.grafana.apiKeyKeepTip') : ''" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.remark')" prop="remark">
          <a-input v-model="connectionForm.remark" />
        </a-form-model-item>
      </a-form-model>
    </a-modal>

    <a-modal
      :title="mappingForm.id ? $t('cs.grafana.editMapping') : $t('cs.grafana.addMapping')"
      :visible="mappingModalVisible"
      :confirm-loading="saving"
      @ok="handleSaveMapping"
      @cancel="mappingModalVisible = false"
    >
      <a-form-model ref="mappingForm" :model="mappingForm" :rules="mappingRules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-model-item :label="$t('cs.grafana.ciType')" prop="ci_type_id">
          <a-select v-model="mappingForm.ci_type_id" show-search option-filter-prop="children">
            <a-select-option v-for="t in ciTypes" :key="t.id" :value="t.id">
              {{ t.alias || t.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.connectionInstance')" prop="connection_id">
          <a-select v-model="mappingForm.connection_id">
            <a-select-option v-for="c in connections" :key="c.id" :value="c.id">
              {{ c.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.dashboardUid')" prop="dashboard_uid">
          <a-input v-model="mappingForm.dashboard_uid" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.varName')" prop="var_name">
          <a-input v-model="mappingForm.var_name" placeholder="ci_name" />
        </a-form-model-item>
      </a-form-model>
    </a-modal>
  </div>
</template>

<script>
import {
  getGrafanaConnections,
  postGrafanaConnection,
  putGrafanaConnection,
  deleteGrafanaConnection,
  testGrafanaConnection,
  getGrafanaMappings,
  postGrafanaMapping,
  putGrafanaMapping,
  deleteGrafanaMapping,
} from '@/api/grafana'
import { getCITypes } from '@/modules/cmdb/api/CIType'

export default {
  name: 'SettingGrafana',
  data() {
    return {
      connections: [],
      mappings: [],
      ciTypes: [],
      saving: false,
      connectionModalVisible: false,
      mappingModalVisible: false,
      connectionForm: { id: null, name: '', url: '', api_key: '', remark: '' },
      mappingForm: { id: null, ci_type_id: undefined, connection_id: undefined, dashboard_uid: '', var_name: 'ci_name' },
      connectionColumns: [
        { title: this.$t('cs.grafana.name'), dataIndex: 'name' },
        { title: this.$t('cs.grafana.url'), dataIndex: 'url' },
        { title: this.$t('cs.grafana.remark'), dataIndex: 'remark' },
        { title: this.$t('cs.grafana.operation'), scopedSlots: { customRender: 'action' }, width: 220 },
      ],
      mappingColumns: [
        { title: this.$t('cs.grafana.ciType'), scopedSlots: { customRender: 'ci_type' } },
        { title: this.$t('cs.grafana.connectionInstance'), scopedSlots: { customRender: 'connection' } },
        { title: this.$t('cs.grafana.dashboardUid'), dataIndex: 'dashboard_uid' },
        { title: this.$t('cs.grafana.varName'), dataIndex: 'var_name' },
        { title: this.$t('cs.grafana.operation'), scopedSlots: { customRender: 'action' }, width: 160 },
      ],
    }
  },
  computed: {
    connectionRules() {
      return {
        name: [{ required: true, message: this.$t('cs.grafana.nameRequired'), trigger: 'blur' }],
        url: [{ required: true, message: this.$t('cs.grafana.urlRequired'), trigger: 'blur' }],
        api_key: [{ required: !this.connectionForm.id, message: this.$t('cs.grafana.apiKeyRequired'), trigger: 'blur' }],
      }
    },
    mappingRules() {
      return {
        ci_type_id: [{ required: true, message: this.$t('cs.grafana.ciTypeRequired'), trigger: 'change' }],
        connection_id: [{ required: true, message: this.$t('cs.grafana.connectionRequired'), trigger: 'change' }],
      }
    },
  },
  mounted() {
    this.loadAll()
  },
  methods: {
    async loadAll() {
      const [connRes, mapRes, typeRes] = await Promise.all([
        getGrafanaConnections(),
        getGrafanaMappings(),
        getCITypes(),
      ])
      this.connections = connRes.connections || []
      this.mappings = mapRes.mappings || []
      this.ciTypes = typeRes.ci_types || []
    },
    ciTypeName(id) {
      const t = this.ciTypes.find((i) => i.id === id)
      return t ? t.alias || t.name : id
    },
    connectionName(id) {
      const c = this.connections.find((i) => i.id === id)
      return c ? c.name : id
    },
    openConnectionModal(record = null) {
      this.connectionForm = record
        ? { id: record.id, name: record.name, url: record.url, api_key: '', remark: record.remark }
        : { id: null, name: '', url: '', api_key: '', remark: '' }
      this.connectionModalVisible = true
      this.$nextTick(() => this.$refs.connectionForm && this.$refs.connectionForm.clearValidate())
    },
    openMappingModal(record = null) {
      this.mappingForm = record
        ? { id: record.id, ci_type_id: record.ci_type_id, connection_id: record.connection_id, dashboard_uid: record.dashboard_uid, var_name: record.var_name }
        : { id: null, ci_type_id: undefined, connection_id: undefined, dashboard_uid: '', var_name: 'ci_name' }
      this.mappingModalVisible = true
      this.$nextTick(() => this.$refs.mappingForm && this.$refs.mappingForm.clearValidate())
    },
    handleSaveConnection() {
      this.$refs.connectionForm.validate(async (valid) => {
        if (!valid) return
        this.saving = true
        try {
          const { id, ...data } = this.connectionForm
          if (id) {
            await putGrafanaConnection(id, data)
          } else {
            await postGrafanaConnection(data)
          }
          this.$message.success(this.$t('saveSuccess'))
          this.connectionModalVisible = false
          await this.loadAll()
        } finally {
          this.saving = false
        }
      })
    },
    handleSaveMapping() {
      this.$refs.mappingForm.validate(async (valid) => {
        if (!valid) return
        this.saving = true
        try {
          const { id, ...data } = this.mappingForm
          if (id) {
            await putGrafanaMapping(id, data)
          } else {
            await postGrafanaMapping(data)
          }
          this.$message.success(this.$t('saveSuccess'))
          this.mappingModalVisible = false
          await this.loadAll()
        } finally {
          this.saving = false
        }
      })
    },
    async handleDeleteConnection(record) {
      await deleteGrafanaConnection(record.id)
      this.$message.success(this.$t('deleteSuccess'))
      await this.loadAll()
    },
    async handleDeleteMapping(record) {
      await deleteGrafanaMapping(record.id)
      this.$message.success(this.$t('deleteSuccess'))
      await this.loadAll()
    },
    async handleTest(record) {
      await testGrafanaConnection({ url: record.url, api_key: record.api_key })
      this.$message.success(this.$t('cs.grafana.testSuccess'))
    },
  },
}
</script>

<style lang="less" scoped>
.ops-setting-grafana {
  padding: 20px;
  background-color: #f5f7fa;
  height: calc(100vh - 64px);
  overflow: auto;
  .grafana-card {
    margin-bottom: 16px;
  }
}
</style>
```

注意：`handleTest` 对已保存连接用列表中脱敏的 api_key（`"******"`）无法真正测试 —— 因此测试按钮只在**编辑弹窗内输入了 API Key** 或新建时才有意义。修正方案：把"测试连接"按钮从表格行移到连接弹窗底部（`a-modal` 的 footer slot），用当前表单值测试：

将连接 `a-modal` 改为：

```html
    <a-modal
      :title="connectionForm.id ? $t('cs.grafana.editConnection') : $t('cs.grafana.addConnection')"
      :visible="connectionModalVisible"
      :confirm-loading="saving"
      @ok="handleSaveConnection"
      @cancel="connectionModalVisible = false"
    >
      <!-- form 内容不变 -->
      <template slot="footer">
        <a-button :loading="testing" @click="handleTest">{{ $t('cs.grafana.testConnect') }}</a-button>
        <a-button @click="connectionModalVisible = false">{{ $t('cancel') }}</a-button>
        <a-button type="primary" :loading="saving" @click="handleSaveConnection">{{ $t('save') }}</a-button>
      </template>
    </a-modal>
```

同时从连接表格的 action 列移除"测试连接"链接（只保留编辑/删除），data 加 `testing: false`，方法改为：

```js
    handleTest() {
      this.$refs.connectionForm.validate(async (valid) => {
        if (!valid) return
        this.testing = true
        try {
          await testGrafanaConnection({ url: this.connectionForm.url, api_key: this.connectionForm.api_key })
          this.$message.success(this.$t('cs.grafana.testSuccess'))
        } finally {
          this.testing = false
        }
      })
    },
```

实现时以"修正方案"为准（弹窗内测试按钮）。

- [ ] **Step 4: 验证 lint + 全局词条存在**

Run: `cd cmdb-ui && npx eslint src/views/setting/grafana/index.vue src/router/config.js src/views/setting/lang/zh.js src/views/setting/lang/en.js`
Expected: 无 error

并确认 `$t('saveSuccess')`、`$t('deleteSuccess')`、`$t('confirmDelete')`、`$t('save')`、`$t('cancel')` 这些全局词条已存在于 `cmdb-ui/src/lang/zh.js`（已核实存在），若实现时某个不存在则改用已存在的近义词条。

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui/src/views/setting/grafana/ cmdb-ui/src/router/config.js cmdb-ui/src/views/setting/lang/
git commit -m "feat(grafana): add grafana setting page"
```

---

### Task 7: CI 详情 Grafana tab + cmdb i18n + 端到端验证

**Files:**
- Create: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailGrafana.vue`
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailTab.vue`（import + components 注册 + tab_5 后追加 tab_6）
- Modify: `cmdb-ui/src/modules/cmdb/lang/zh.js`（`ci:` 块，`relITSM` 行附近追加）
- Modify: `cmdb-ui/src/modules/cmdb/lang/en.js`（同上）

**Interfaces:**
- Consumes: Task 5 的 `getCIGrafana(ciId)` → `{configured, result: {grafana_url, uid, slug, var_name, var_value} | null}`；`ciDetailTab.vue` 的 `ciId` data 字段。
- Produces: `CiDetailGrafana` 组件（props: `ciId: Number`）。

- [ ] **Step 1: cmdb i18n 词条**

`cmdb-ui/src/modules/cmdb/lang/zh.js` 的 `ci:` 块中 `relITSM: '关联工单',`（约 912 行）后追加：

```js
        grafana: 'Grafana',
        grafanaNoDashboard: '未找到关联的 Grafana 仪表板',
        grafanaNotConfigured: '尚未配置 Grafana，请先在后台管理中配置',
```

`cmdb-ui/src/modules/cmdb/lang/en.js` 对应位置（`relITSM: 'Related Tickets',` 约 916 行）：

```js
        grafana: 'Grafana',
        grafanaNoDashboard: 'No associated Grafana dashboard found',
        grafanaNotConfigured: 'Grafana is not configured. Please configure it in System Settings first',
```

- [ ] **Step 2: 创建 ciDetailGrafana.vue**

`cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailGrafana.vue`（完整代码）：

```vue
<template>
  <div class="ci-detail-grafana">
    <a-spin :spinning="loading" :style="{ width: '100%', height: '100%' }">
      <iframe
        v-if="iframeUrl"
        :src="iframeUrl"
        class="ci-detail-grafana-iframe"
        frameborder="0"
      ></iframe>
      <a-empty
        v-else-if="!loading"
        :image-style="{ height: '100px' }"
        :style="{ paddingTop: '10%' }"
      >
        <img slot="image" :src="require('@/assets/data_empty.png')" />
        <span slot="description">
          {{ notConfigured ? $t('cmdb.ci.grafanaNotConfigured') : $t('cmdb.ci.grafanaNoDashboard') }}
        </span>
      </a-empty>
    </a-spin>
  </div>
</template>

<script>
import { getCIGrafana } from '@/modules/cmdb/api/ci'

export default {
  name: 'CiDetailGrafana',
  props: {
    ciId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      notConfigured: false,
      iframeUrl: '',
    }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      this.loading = true
      try {
        const res = await getCIGrafana(this.ciId)
        this.notConfigured = !res.configured
        const r = res.result
        if (r && r.grafana_url && r.uid) {
          const base = String(r.grafana_url).replace(/\/+$/, '')
          let url = `${base}/d/${r.uid}${r.slug ? '/' + r.slug : ''}?kiosk`
          if (r.var_name && r.var_value !== undefined && r.var_value !== null && r.var_value !== '') {
            url += `&var-${r.var_name}=${encodeURIComponent(r.var_value)}`
          }
          this.iframeUrl = url
        }
      } catch (e) {
        this.iframeUrl = ''
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style lang="less" scoped>
.ci-detail-grafana {
  height: 100%;
  .ci-detail-grafana-iframe {
    width: 100%;
    height: 100%;
    min-height: 600px;
    border: none;
  }
}
</style>
```

- [ ] **Step 3: ciDetailTab.vue 接入 tab_6**

三处修改（先 Read 确认现状再 Edit）：

1. script import 区（约 231 行 `import QRCodeButton ...` 后）：
```js
import CiDetailGrafana from './ciDetailGrafana.vue'
```
2. `components` 注册（`QRCodeButton` 后）：
```js
    QRCodeButton,
    CiDetailGrafana
```
3. template 中 `tab_5` 的 `</a-tab-pane>`（约 198 行）之后追加：

```html
      <a-tab-pane key="tab_6">
        <span slot="tab"><a-icon type="dashboard" />{{ $t('cmdb.ci.grafana') }}</span>
        <div :style="{ padding: '24px', height: '100%' }">
          <CiDetailGrafana v-if="ciId" :ciId="ciId" />
        </div>
      </a-tab-pane>
```

（ant-design-vue 1.x tab pane 内容懒渲染：首次激活才挂载，因此 `mounted` 里发请求即为"tab 激活时加载"。）

- [ ] **Step 4: 验证 lint + 前端整体编译**

Run: `cd cmdb-ui && npx eslint src/modules/cmdb/views/ci/modules/ciDetailGrafana.vue src/modules/cmdb/views/ci/modules/ciDetailTab.vue src/modules/cmdb/lang/zh.js src/modules/cmdb/lang/en.js`
Expected: 无 error

Run: `cd cmdb-ui && npx vue-cli-service build --mode development --no-clean 2>&1 | tail -5`（或项目现有的 dev 构建命令；若太慢可跳过，以 eslint + 手动页面验证为准）

- [ ] **Step 5: 端到端手动验证（需要运行中的服务）**

1. 启动后端：`cd cmdb-api-fastapi && .venv/bin/python main.py`（或 `./dev.sh`），前端 `cd cmdb-ui && npm run serve`。
2. 以 `acl_admin` 用户登录，进入 系统设置 → Grafana设置：
   - 新增连接（真实 Grafana 地址 + Service Account Token），点"测试连接" → 成功提示。
   - 新增映射：选一个 CI 类型、连接实例、填一个已知 dashboard UID、变量名 `ci_name`。
3. 打开该类型任一 CI 的详情页 → Grafana tab：
   - 显示嵌入仪表板，URL 含 `?kiosk&var-ci_name=<该CI唯一标识值>`。
   - 打开一个无映射、Grafana 中也搜不到同名仪表板的 CI → 显示"未找到关联的 Grafana 仪表板"。
4. 删除全部连接后刷新 CI 详情 → 显示"尚未配置 Grafana"。
5. 后端单测回归：`cd cmdb-api-fastapi && .venv/bin/python -m pytest tests/ -v` → 8 passed。

如环境里没有可用的 Grafana 实例，用 `docker run -d -p 3000:3000 -e GF_SECURITY_ALLOW_EMBEDDING=true -e GF_AUTH_ANONYMOUS_ENABLED=true -e GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer grafana/grafana` 起一个临时实例，并在其 UI 中创建 Service Account + Token + 一个以 CI 唯一标识命名的仪表板。

- [ ] **Step 6: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailGrafana.vue cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailTab.vue cmdb-ui/src/modules/cmdb/lang/
git commit -m "feat(grafana): add grafana dashboard tab in ci detail"
```

---

## Self-Review 结论

- Spec 覆盖：配置存储（Task 2）、配置 API（Task 3）、解析端点（Task 4）、前端 API（Task 5）、配置页+路由+i18n（Task 6）、CI tab+组件+i18n（Task 7）、后端测试（Task 1）、手动 E2E（Task 7 Step 5）—— 无遗漏。Spec 中 `api/lib/common_setting/grafana.py` 的职责拆为 `grafana_client.py`（纯逻辑，可测）+ `grafana.py`（CRUD），解析逻辑放 `api/lib/cmdb/grafana.py`，偏差已在 Task 中注明。
- 类型一致性：`pick_dashboard` 返回 dict 的 key（connection/uid/slug/var_name/var_value）在 Task 1 测试、Task 4 消费处一致；前端 `getCIGrafana` 响应 `{configured, result}` 与 Task 4 返回一致；`cs.grafana.*` 词条在 Task 6 组件与 lang 文件中一致。
- 已知取舍：脱敏 api_key 无法用于"测试连接"，故测试按钮放在弹窗内用表单明文测试（Task 6 修正方案）；Grafana 嵌入需 Grafana 侧 `allow_embedding` + 匿名访问，已在 E2E 步骤注明。
