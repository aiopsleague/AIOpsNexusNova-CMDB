# Prometheus Alert Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Prometheus alert integration to the CMDB CI detail page, with a configurable settings page under Observability Settings.

**Architecture:** Follow the existing Grafana integration pattern — Prometheus config stored in `CommonData` table (AES encrypted JSON), `PrometheusConfigCRUD` for admin settings, `PrometheusClient` for HTTP calls to Prometheus API, new tab_7 in `ciDetailTab.vue` for alert display.

**Tech Stack:** Python 3.12+ / FastAPI / SQLAlchemy 1.4 / Vue 2.6 / Ant Design Vue 1.6

## Global Constraints

- Python files: `# -*- coding:utf-8 -*-` header, imports order stdlib → third-party → project
- Backend: views never contain business logic; route → lib CRUD → model
- `request.values` for accessing merged query + JSON body params
- AES encrypt/decrypt via `AESCrypto` for all Prometheus config
- Frontend: Options API only, Less scoped styles, single quotes, 2-space indent
- API wrapper patterns match existing `src/api/grafana.js` and `api/lib/common_setting/grafana.py`

---

### Task 1: Add Prometheus error keys to resp_format

**Files:**
- Modify: `cmdb-api/api/lib/common_setting/resp_format.py`

**Interfaces:**
- Produces: `ErrFormat.prometheus_connection_not_found`, `.prometheus_mapping_not_found`, `.prometheus_name_required`, `.prometheus_url_required`, `.prometheus_test_failed`, `.prometheus_config_broken`, `.prometheus_label_mapping_required`

- [ ] **Step 1: Add Prometheus error keys to ErrFormat class**

In `cmdb-api/api/lib/common_setting/resp_format.py`, after the Grafana error keys (after line 41), add:

```python
prometheus_connection_not_found = _l("Prometheus connection [{}] not found")  # Prometheus连接 [{}] 不存在
prometheus_mapping_not_found = _l("Prometheus mapping [{}] not found")  # Prometheus映射 [{}] 不存在
prometheus_name_required = _l("Prometheus name is required")  # Prometheus名称是必须的
prometheus_url_required = _l("Prometheus url is required")  # Prometheus地址是必须的
prometheus_test_failed = _l("Prometheus connection test failed: {}")  # Prometheus连接测试失败: {}
prometheus_config_broken = _l("Prometheus config is broken, please check SECRET_KEY or contact admin")  # Prometheus配置解析失败，请检查SECRET_KEY或联系管理员
prometheus_label_mapping_required = _l("Prometheus label mapping is required")  # Prometheus标签映射是必须的
```

- [ ] **Step 2: Verify the file has no syntax errors**

Run: `cd cmdb-api && uv run python -c "from api.lib.common_setting.resp_format import ErrFormat; print('OK')"`
Expected: `OK`

---

### Task 2: Create PrometheusClient (HTTP client)

**Files:**
- Create: `cmdb-api/api/lib/common_setting/prometheus_client.py`

**Interfaces:**
- Produces: `class PrometheusClient(url, auth_type='none', auth_data=None, timeout=5)` with methods `health_check() -> bool`, `query_alerts(labels: dict) -> list[dict]`

- [ ] **Step 1: Create the PrometheusClient class**

Create `cmdb-api/api/lib/common_setting/prometheus_client.py`:

```python
# -*- coding:utf-8 -*-
import base64

import requests


class PrometheusClient(object):
    """Lightweight HTTP client for the Prometheus HTTP API.

    Parameters
    ----------
    url : str
        Prometheus base URL, e.g. ``http://localhost:9090``.
    auth_type : str
        ``none`` (default), ``bearer``, or ``basic``.
    auth_data : dict | None
        Required keys depend on auth_type:
        - bearer: ``{"token": "..."}``
        - basic: ``{"username": "...", "password": "..."}``
    timeout : int
        Request timeout in seconds (default 5).
    """

    def __init__(self, url, auth_type='none', auth_data=None, timeout=5):
        self.url = url.rstrip('/')
        self.auth_type = auth_type or 'none'
        self.auth_data = auth_data or {}
        self.timeout = timeout

    def _headers(self):
        """Build request headers with auth."""
        headers = {'Accept': 'application/json'}
        if self.auth_type == 'bearer':
            token = self.auth_data.get('token', '')
            headers['Authorization'] = 'Bearer {}'.format(token)
        elif self.auth_type == 'basic':
            username = self.auth_data.get('username', '')
            password = self.auth_data.get('password', '')
            if username or password:
                creds = base64.b64encode('{}:{}'.format(username, password).encode('utf-8')).decode('utf-8')
                headers['Authorization'] = 'Basic {}'.format(creds)
        return headers

    def health_check(self):
        """Return True if Prometheus is reachable and healthy.

        Calls ``GET /-/healthy``.
        """
        resp = requests.get(
            '{}/-/healthy'.format(self.url),
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return True

    def query_alerts(self, labels):
        """Query firing alerts matching the given label matchers.

        Parameters
        ----------
        labels : dict
            Label matchers, e.g. ``{"instance": "10.0.0.1", "job": "node"}``.

        Returns
        -------
        list[dict]
            Normalised alert dicts from ``/api/v1/alerts``.
            Returns empty list on any error (never raises).
        """
        if not labels:
            return []

        matchers = []
        for k, v in labels.items():
            matchers.append('{}="{}"'.format(k, v))
        filter_expr = '{' + ','.join(matchers) + '}'

        try:
            resp = requests.get(
                '{}/api/v1/alerts'.format(self.url),
                headers=self._headers(),
                params={'filter': filter_expr},
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except Exception:
            return []

        data = resp.json()
        if data.get('status') != 'success':
            return []

        alerts = data.get('data', {}).get('alerts', [])
        result = []
        for a in alerts:
            if a.get('state') != 'firing':
                continue
            result.append({
                'fingerprint': a.get('fingerprint', ''),
                'labels': a.get('labels', {}),
                'annotations': a.get('annotations', {}),
                'state': a.get('state', 'firing'),
                'activeAt': a.get('activeAt', ''),
                'value': a.get('value', ''),
            })
        return result
```

- [ ] **Step 2: Verify the module imports correctly**

Run: `cd cmdb-api && uv run python -c "from api.lib.common_setting.prometheus_client import PrometheusClient; c = PrometheusClient('http://localhost:9090'); print('OK')"`
Expected: `OK`

---

### Task 3: Create PrometheusConfigCRUD

**Files:**
- Create: `cmdb-api/api/lib/common_setting/prometheus.py`

**Interfaces:**
- Consumes: `CommonData` model, `AESCrypto`, `ErrFormat`, `PrometheusClient`
- Produces: `class PrometheusConfigCRUD` with `get_config()`, `_save(config)`, `list_connections()`, `get_connection(_id)`, `create_connection(data)`, `update_connection(_id, data)`, `delete_connection(_id)`, `test_connection(url, auth_type, auth_data)`, `check_health()`, `list_mappings()`, `create_mapping(data)`, `update_mapping(_id, data)`, `delete_mapping(_id)`

- [ ] **Step 1: Create PrometheusConfigCRUD**

Create `cmdb-api/api/lib/common_setting/prometheus.py`:

```python
# -*- coding:utf-8 -*-
import json

from api.core.context import current_app
from api.core.errors import abort
from api.extensions import db
from api.lib.common_setting.prometheus_client import PrometheusClient
from api.lib.common_setting.resp_format import ErrFormat
from api.lib.utils import AESCrypto
from api.models.common_setting import CommonData

DATA_TYPE = "Prometheus"
AUTH_MASK = "******"

VALID_AUTH_TYPES = {"none", "bearer", "basic"}
VALID_MAP_TYPES = {"field", "fixed"}


class PrometheusConfigCRUD(object):
    """All Prometheus config lives in ONE common_data record
    (data_type='Prometheus'), AES-encrypted as a whole, shaped:
    {"connections": [...], "mappings": [...]}.
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
        except Exception as e:
            current_app.logger.error("Failed to decrypt prometheus config: %s", e)
            abort(400, ErrFormat.prometheus_config_broken)
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
    def _to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            abort(400, ErrFormat.value_is_required)

    @staticmethod
    def _to_enable(value):
        return 0 if value in (0, "0", False) else 1

    @staticmethod
    def _mask_auth(connection):
        masked = dict(connection)
        if connection.get("auth_type") in ("bearer", "basic"):
            masked.setdefault("auth_data", {})
            masked["auth_data"] = dict(masked["auth_data"] or {})
            if masked["auth_data"]:
                masked["auth_data"]["token"] = AUTH_MASK if masked["auth_data"].get("token") else ""
                masked["auth_data"]["password"] = AUTH_MASK if masked["auth_data"].get("password") else ""
        return masked

    # ---------------- connections ----------------

    def list_connections(self):
        result = []
        for c in self.get_config()["connections"]:
            masked = self._mask_auth(c)
            masked["enable"] = self._to_enable(c.get("enable", 1))
            result.append(masked)
        return result

    def get_connection(self, _id):
        _id = self._to_int(_id)
        connection = next((c for c in self.get_config()["connections"] if c.get("id") == _id), None)
        if not connection:
            abort(404, ErrFormat.prometheus_connection_not_found.format(_id))
        return connection

    def create_connection(self, data):
        if not (data.get("name") or "").strip():
            abort(400, ErrFormat.prometheus_name_required)
        if not (data.get("url") or "").strip():
            abort(400, ErrFormat.prometheus_url_required)

        auth_type = (data.get("auth_type") or "none").strip()
        if auth_type not in VALID_AUTH_TYPES:
            abort(400, "invalid auth_type: {}".format(auth_type))

        connection = dict(
            id=self._next_id(self.get_config()["connections"]),
            name=data["name"].strip(),
            url=data["url"].strip().rstrip("/"),
            auth_type=auth_type,
            auth_data=data.get("auth_data") or {},
            enable=self._to_enable(data.get("enable", 1)),
            remark=(data.get("remark") or "").strip(),
        )
        config = self.get_config()
        config["connections"].append(connection)
        self._save(config)
        return self._mask_auth(connection)

    def update_connection(self, _id, data):
        _id = self._to_int(_id)
        config = self.get_config()
        connection = next((c for c in config["connections"] if c.get("id") == _id), None)
        if not connection:
            abort(404, ErrFormat.prometheus_connection_not_found.format(_id))

        if "name" in data:
            if not (data["name"] or "").strip():
                abort(400, ErrFormat.prometheus_name_required)
            connection["name"] = data["name"].strip()
        if "url" in data:
            if not (data["url"] or "").strip():
                abort(400, ErrFormat.prometheus_url_required)
            connection["url"] = data["url"].strip().rstrip("/")
        if "auth_type" in data:
            auth_type = (data["auth_type"] or "none").strip()
            if auth_type not in VALID_AUTH_TYPES:
                abort(400, "invalid auth_type: {}".format(auth_type))
            connection["auth_type"] = auth_type
        if "auth_data" in data and data["auth_data"]:
            connection.setdefault("auth_data", {})
            if isinstance(data["auth_data"], dict):
                for k, v in data["auth_data"].items():
                    if v:
                        connection["auth_data"][k] = v
        if "remark" in data:
            connection["remark"] = (data["remark"] or "").strip()
        if "enable" in data:
            connection["enable"] = self._to_enable(data["enable"])

        self._save(config)
        return self._mask_auth(connection)

    def delete_connection(self, _id):
        _id = self._to_int(_id)
        config = self.get_config()
        before = len(config["connections"])
        config["connections"] = [c for c in config["connections"] if c.get("id") != _id]
        if len(config["connections"]) == before:
            abort(404, ErrFormat.prometheus_connection_not_found.format(_id))
        config["mappings"] = [m for m in config["mappings"] if m.get("connection_id") != _id]
        self._save(config)

    def test_connection(self, url, auth_type, auth_data):
        if not (url or "").strip():
            abort(400, ErrFormat.prometheus_url_required)
        try:
            PrometheusClient(url.strip(), auth_type or 'none', auth_data or {}).health_check()
        except Exception as e:
            abort(400, ErrFormat.prometheus_test_failed.format(str(e)))

    def check_health(self):
        result = []
        for c in self.get_config()["connections"]:
            try:
                PrometheusClient(c["url"], c.get("auth_type"), c.get("auth_data")).health_check()
                result.append({"id": c["id"], "ok": True, "error": ""})
            except Exception as e:
                result.append({"id": c["id"], "ok": False, "error": str(e)})
        return result

    # ---------------- mappings ----------------

    @staticmethod
    def _valid_label_mapping(label_mapping):
        label_mapping = label_mapping or []
        if not isinstance(label_mapping, list):
            abort(400, ErrFormat.value_is_required)
        result = []
        for lm in label_mapping:
            if not isinstance(lm, dict):
                abort(400, ErrFormat.value_is_required)
            prom_label = str((lm or {}).get("prom_label") or "").strip()
            if not prom_label:
                abort(400, ErrFormat.prometheus_label_mapping_required)
            map_type = lm.get("map_type") or "field"
            if map_type not in VALID_MAP_TYPES:
                abort(400, ErrFormat.value_is_required)
            value = str(lm.get("value") or "").strip()
            if not value:
                abort(400, ErrFormat.value_is_required)
            result.append({"prom_label": prom_label, "map_type": map_type, "value": value})
        return result

    def list_mappings(self):
        mappings = self.get_config()["mappings"]
        result = []
        for m in mappings:
            entry = dict(m)
            entry["enable"] = self._to_enable(m.get("enable", 1))
            result.append(entry)
        return result

    def create_mapping(self, data):
        ci_type_id = data.get("ci_type_id")
        connection_id = data.get("connection_id")
        if not ci_type_id or not connection_id:
            abort(400, ErrFormat.value_is_required)
        ci_type_id = self._to_int(ci_type_id)
        connection_id = self._to_int(connection_id)

        config = self.get_config()
        if not any(c.get("id") == connection_id for c in config["connections"]):
            abort(404, ErrFormat.prometheus_connection_not_found.format(connection_id))

        mapping = dict(
            id=self._next_id(config["mappings"]),
            ci_type_id=ci_type_id,
            connection_id=connection_id,
            label_mapping=self._valid_label_mapping(data.get("label_mapping")),
            enable=self._to_enable(data.get("enable", 1)),
        )
        config["mappings"].append(mapping)
        self._save(config)
        return mapping

    def update_mapping(self, _id, data):
        _id = self._to_int(_id)
        config = self.get_config()
        mapping = next((m for m in config["mappings"] if m.get("id") == _id), None)
        if not mapping:
            abort(404, ErrFormat.prometheus_mapping_not_found.format(_id))

        if "ci_type_id" in data and data["ci_type_id"]:
            mapping["ci_type_id"] = self._to_int(data["ci_type_id"])
        if "connection_id" in data and data["connection_id"]:
            connection_id = self._to_int(data["connection_id"])
            if not any(c.get("id") == connection_id for c in config["connections"]):
                abort(404, ErrFormat.prometheus_connection_not_found.format(connection_id))
            mapping["connection_id"] = connection_id
        if "label_mapping" in data:
            mapping["label_mapping"] = self._valid_label_mapping(data["label_mapping"])
        if "enable" in data:
            mapping["enable"] = self._to_enable(data["enable"])

        self._save(config)
        return mapping

    def delete_mapping(self, _id):
        _id = self._to_int(_id)
        config = self.get_config()
        before = len(config["mappings"])
        config["mappings"] = [m for m in config["mappings"] if m.get("id") != _id]
        if len(config["mappings"]) == before:
            abort(404, ErrFormat.prometheus_mapping_not_found.format(_id))
        self._save(config)
```

- [ ] **Step 2: Verify the module imports**

Run: `cd cmdb-api && uv run python -c "from api.lib.common_setting.prometheus import PrometheusConfigCRUD; print('OK')"`
Expected: `OK`

---

### Task 4: Create admin config API routes (settings CRUD)

**Files:**
- Create: `cmdb-api/api/views/common_setting/prometheus_config.py`

**Interfaces:**
- Consumes: `PrometheusConfigCRUD`, `authenticate`, `role_required`, `request`
- Produces: `router = APIRouter(dependencies=[Depends(authenticate)])` with routes at prefix `/prometheus`

- [ ] **Step 1: Create the settings route module**

Create `cmdb-api/api/views/common_setting/prometheus_config.py`:

```python
# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.lib.common_setting.prometheus import PrometheusConfigCRUD
from api.lib.perm.acl.acl import role_required
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/prometheus'


# ---- connections ----

@router.get(f'{prefix}/connections')
@role_required("acl_admin")
def prometheus_connections_get():
    return dict(connections=PrometheusConfigCRUD().list_connections())


@router.post(f'{prefix}/connections')
@role_required("acl_admin")
def prometheus_connections_post():
    data = (request.json or {}).get('data', {})
    return PrometheusConfigCRUD().create_connection(data)


@router.post(f'{prefix}/connections/test')
@role_required("acl_admin")
def prometheus_connections_test_post():
    data = (request.json or {}).get('data', {})
    PrometheusConfigCRUD().test_connection(
        data.get('url'), data.get('auth_type'), data.get('auth_data'))
    return dict()


@router.get(f'{prefix}/connections/health')
@role_required("acl_admin")
def prometheus_connections_health_get():
    return dict(health=PrometheusConfigCRUD().check_health())


@router.put(f'{prefix}/connections/{{_id:int}}')
@role_required("acl_admin")
def prometheus_connections_put(_id: int = None):
    data = (request.json or {}).get('data', {})
    return PrometheusConfigCRUD().update_connection(_id, data)


@router.delete(f'{prefix}/connections/{{_id:int}}')
@role_required("acl_admin")
def prometheus_connections_delete(_id: int = None):
    PrometheusConfigCRUD().delete_connection(_id)
    return dict()


# ---- mappings ----

@router.get(f'{prefix}/mappings')
@role_required("acl_admin")
def prometheus_mappings_get():
    return dict(mappings=PrometheusConfigCRUD().list_mappings())


@router.post(f'{prefix}/mappings')
@role_required("acl_admin")
def prometheus_mappings_post():
    data = (request.json or {}).get('data', {})
    return PrometheusConfigCRUD().create_mapping(data)


@router.put(f'{prefix}/mappings/{{_id:int}}')
@role_required("acl_admin")
def prometheus_mappings_put(_id: int = None):
    data = (request.json or {}).get('data', {})
    return PrometheusConfigCRUD().update_mapping(_id, data)


@router.delete(f'{prefix}/mappings/{{_id:int}}')
@role_required("acl_admin")
def prometheus_mappings_delete(_id: int = None):
    PrometheusConfigCRUD().delete_mapping(_id)
    return dict()
```

- [ ] **Step 2: Verify the module imports successfully**

Run: `cd cmdb-api && uv run python -c "from api.views.common_setting.prometheus_config import router; print('OK')"`
Expected: `OK`

---

### Task 5: Create CI alert resolution layer and routes

**Files:**
- Create: `cmdb-api/api/lib/cmdb/prometheus.py`
- Create: `cmdb-api/api/views/cmdb/prometheus.py`

**Interfaces:**
- Consumes: `PrometheusConfigCRUD`, `PrometheusClient`, `CIManager`, `CI` model, `CITypeCache`, `AttributeCache`
- Produces: `check_ci_prometheus(ci_type_id) -> dict`, `resolve_ci_prometheus_alerts(ci_id) -> dict`; routes at `GET /ci_type/{ci_type_id}/prometheus/check` and `GET /ci/{ci_id}/prometheus/alerts`

- [ ] **Step 1: Create `api/lib/cmdb/prometheus.py`**

Create `cmdb-api/api/lib/cmdb/prometheus.py`:

```python
# -*- coding:utf-8 -*-
from api.core.context import current_app
from api.core.errors import abort

from api.lib.cmdb.cache import AttributeCache
from api.lib.cmdb.cache import CITypeCache
from api.lib.cmdb.ci import CIManager
from api.lib.cmdb.resp_format import ErrFormat
from api.lib.common_setting.prometheus import PrometheusConfigCRUD
from api.lib.common_setting.prometheus_client import PrometheusClient
from api.models.cmdb import CI


def check_ci_prometheus(ci_type_id):
    """Check whether a CI type has any Prometheus alert mapping configured.

    Returns ``{"has_prometheus": bool}`` so the frontend can decide whether
    to show the Prometheus alerts tab.
    """
    config = PrometheusConfigCRUD().get_config()
    connections = config.get("connections", [])
    if not connections:
        return {"has_prometheus": False}

    mappings = config.get("mappings", [])
    type_mappings = [
        m for m in mappings
        if m.get("ci_type_id") == ci_type_id and m.get("enable", 1) != 0
    ]
    return {"has_prometheus": len(type_mappings) > 0}


def resolve_ci_prometheus_alerts(ci_id):
    """Return active Prometheus alerts for a CI.

    Returns ``{"configured": bool, "has_prometheus": bool, "alerts": [...]}``.
    """
    ci_obj = CI.get_by_id(ci_id) or abort(404, ErrFormat.ci_not_found.format("id={}".format(ci_id)))
    CIManager.valid_ci_only_read(ci_obj)

    config = PrometheusConfigCRUD().get_config()
    connections = config["connections"]
    mappings = config["mappings"]

    ci = CIManager.get_ci_by_id(ci_id, need_children=False)
    ci_type_id = ci["_type"]

    type_mappings = [m for m in mappings
                     if m.get("ci_type_id") == ci_type_id and m.get("enable", 1) != 0]
    has_prometheus = bool(connections and type_mappings)

    if not connections:
        return dict(configured=False, has_prometheus=False, alerts=[])

    if not type_mappings:
        return dict(configured=True, has_prometheus=False, alerts=[])

    # Collect all alerts across all matching mappings
    all_alerts = []
    seen_fingerprints = set()

    for mapping in type_mappings:
        connection = next((c for c in connections if c.get("id") == mapping["connection_id"]), None)
        if not connection or connection.get("enable", 1) == 0:
            continue

        # Build label matchers from CI attributes
        label_matchers = {}
        for lm in mapping.get("label_mapping") or []:
            prom_label = lm.get("prom_label", "")
            map_type = lm.get("map_type", "field")
            value = lm.get("value", "")
            if map_type == "fixed":
                label_matchers[prom_label] = value
            elif map_type == "field":
                ci_value = ci.get(value)
                if ci_value is not None and ci_value != '':
                    label_matchers[prom_label] = str(ci_value)

        if not label_matchers:
            continue

        try:
            client = PrometheusClient(connection["url"], connection.get("auth_type"), connection.get("auth_data"))
            alerts = client.query_alerts(label_matchers)
        except Exception as e:
            current_app.logger.warning("prometheus query failed for ci {}: {}".format(ci_id, e))
            continue

        for a in alerts:
            fp = a.get("fingerprint", "")
            if fp and fp not in seen_fingerprints:
                seen_fingerprints.add(fp)
                a["connection_id"] = connection["id"]
                # Extract rule name from labels
                a["rule_name"] = a.get("labels", {}).get("alertname", "")
                all_alerts.append(a)

    # Sort: critical > warning > info, then by activeAt descending
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    all_alerts.sort(key=lambda a: (
        severity_order.get(a.get("labels", {}).get("severity", "").lower(), 3),
        a.get("activeAt", ""),
    ))

    return dict(configured=True, has_prometheus=has_prometheus, alerts=all_alerts)
```

- [ ] **Step 2: Create `api/views/cmdb/prometheus.py`**

Create `cmdb-api/api/views/cmdb/prometheus.py`:

```python
# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.lib.cmdb.prometheus import check_ci_prometheus
from api.lib.cmdb.prometheus import resolve_ci_prometheus_alerts
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/ci_type/{ci_type_id:int}/prometheus/check")
def ci_type_prometheus_check(ci_type_id: int):
    """Check whether a CI type has Prometheus alert mapping configured."""
    return check_ci_prometheus(ci_type_id)


@router.get("/ci/{ci_id:int}/prometheus/alerts")
def ci_prometheus_alerts_get(ci_id: int):
    """Return active Prometheus alerts for a CI instance."""
    return resolve_ci_prometheus_alerts(ci_id)
```

- [ ] **Step 3: Verify both modules import correctly**

Run: `cd cmdb-api && uv run python -c "from api.lib.cmdb.prometheus import check_ci_prometheus, resolve_ci_prometheus_alerts; from api.views.cmdb.prometheus import router; print('OK')"`
Expected: `OK`

---

### Task 6: Write backend unit tests

**Files:**
- Create: `cmdb-api/tests/test_prometheus_client.py`

**Interfaces:**
- Consumes: `PrometheusClient`, `PrometheusConfigCRUD`
- Produces: pytest tests (7 test functions)

- [ ] **Step 1: Create test file**

Create `cmdb-api/tests/test_prometheus_client.py`:

```python
# -*- coding:utf-8 -*-
from unittest import mock

import pytest

from api.lib.common_setting.prometheus_client import PrometheusClient


# ---- mocks ----

def _mock_response(status_code=200, json_data=None):
    m = mock.Mock()
    m.raise_for_status.return_value = None
    m.status_code = status_code
    m.json.return_value = json_data or {}
    return m


# ---- PrometheusClient ----

def test_health_check_success():
    client = PrometheusClient("http://prom:9090")
    with mock.patch("api.lib.common_setting.prometheus_client.requests.get") as m:
        m.return_value = _mock_response()
        result = client.health_check()
        assert result is True
        args, kwargs = m.call_args
        assert args[0] == "http://prom:9090/-/healthy"


def test_health_check_raises_on_failure():
    client = PrometheusClient("http://prom:9090")
    with mock.patch("api.lib.common_setting.prometheus_client.requests.get") as m:
        m.return_value.raise_for_status.side_effect = Exception("503")
        with pytest.raises(Exception):
            client.health_check()


def test_auth_headers_bearer():
    client = PrometheusClient("http://prom:9090", auth_type="bearer",
                              auth_data={"token": "my-token"})
    headers = client._headers()
    assert headers["Authorization"] == "Bearer my-token"


def test_auth_headers_basic():
    client = PrometheusClient("http://prom:9090", auth_type="basic",
                              auth_data={"username": "admin", "password": "secret"})
    headers = client._headers()
    assert headers["Authorization"].startswith("Basic ")


def test_auth_headers_none():
    client = PrometheusClient("http://prom:9090", auth_type="none")
    headers = client._headers()
    assert "Authorization" not in headers
    assert headers["Accept"] == "application/json"


def test_query_alerts_firing_only():
    client = PrometheusClient("http://prom:9090")
    resp_data = {
        "status": "success",
        "data": {"alerts": [
            {"fingerprint": "a1", "labels": {"severity": "critical"},
             "annotations": {}, "state": "firing", "activeAt": "", "value": "10"},
            {"fingerprint": "b2", "labels": {}, "annotations": {},
             "state": "inactive", "activeAt": "", "value": ""},
        ]}
    }
    with mock.patch("api.lib.common_setting.prometheus_client.requests.get") as m:
        m.return_value = _mock_response(json_data=resp_data)
        alerts = client.query_alerts({"instance": "x"})
    assert len(alerts) == 1
    assert alerts[0]["state"] == "firing"
    assert alerts[0]["fingerprint"] == "a1"
    # Verify filter arg
    args, kwargs = m.call_args
    assert args[0] == "http://prom:9090/api/v1/alerts"
    assert kwargs["params"]["filter"] == '{instance="x"}'


def test_query_alerts_returns_empty_on_error():
    client = PrometheusClient("http://prom:9090")
    with mock.patch("api.lib.common_setting.prometheus_client.requests.get") as m:
        m.return_value.raise_for_status.side_effect = Exception("timeout")
        alerts = client.query_alerts({"instance": "x"})
    assert alerts == []
```

- [ ] **Step 2: Run tests**

```bash
cd cmdb-api && uv run pytest tests/test_prometheus_client.py -v
```

Expected: 7 passed

- [ ] **Step 3: Verify existing Grafana tests still pass**

```bash
cd cmdb-api && uv run pytest tests/test_grafana_client.py -v
```

Expected: all existing tests pass

---

### Task 7: Create frontend API clients

**Files:**
- Create: `cmdb-ui/src/api/prometheus.js`
- Modify: `cmdb-ui/src/modules/cmdb/api/ci.js`

**Interfaces:**
- Consumes: `axios` from `@/utils/request`
- Produces: `getPrometheusConnections()`, `postPrometheusConnection(data)`, `putPrometheusConnection(id, data)`, `deletePrometheusConnection(id)`, `testPrometheusConnection(data)`, `getPrometheusConnectionsHealth()`, `getPrometheusMappings()`, `postPrometheusMapping(data)`, `putPrometheusMapping(id, data)`, `deletePrometheusMapping(id)`, `getCIPrometheusAlerts(ciId)`, `checkCIPrometheus(ciTypeId)`

- [ ] **Step 1: Create `src/api/prometheus.js`**

Create `cmdb-ui/src/api/prometheus.js`:

```javascript
import { axios } from '@/utils/request'

export function getPrometheusConnections() {
    return axios({
        url: `/common-setting/v1/prometheus/connections`,
        method: 'get',
    })
}

export function postPrometheusConnection(data) {
    return axios({
        url: `/common-setting/v1/prometheus/connections`,
        method: 'post',
        data: { data },
    })
}

export function putPrometheusConnection(id, data) {
    return axios({
        url: `/common-setting/v1/prometheus/connections/${id}`,
        method: 'put',
        data: { data },
    })
}

export function deletePrometheusConnection(id) {
    return axios({
        url: `/common-setting/v1/prometheus/connections/${id}`,
        method: 'delete',
    })
}

export function testPrometheusConnection(data) {
    return axios({
        url: `/common-setting/v1/prometheus/connections/test`,
        method: 'post',
        data: { data },
    })
}

export function getPrometheusConnectionsHealth() {
    return axios({
        url: `/common-setting/v1/prometheus/connections/health`,
        method: 'get',
    })
}

export function getPrometheusMappings() {
    return axios({
        url: `/common-setting/v1/prometheus/mappings`,
        method: 'get',
    })
}

export function postPrometheusMapping(data) {
    return axios({
        url: `/common-setting/v1/prometheus/mappings`,
        method: 'post',
        data: { data },
    })
}

export function putPrometheusMapping(id, data) {
    return axios({
        url: `/common-setting/v1/prometheus/mappings/${id}`,
        method: 'put',
        data: { data },
    })
}

export function deletePrometheusMapping(id) {
    return axios({
        url: `/common-setting/v1/prometheus/mappings/${id}`,
        method: 'delete',
    })
}
```

- [ ] **Step 2: Add Prometheus API functions to `src/modules/cmdb/api/ci.js`**

In `cmdb-ui/src/modules/cmdb/api/ci.js`, after the existing `checkCITypeMonitoring` function (after line 69), add:

```javascript
//  获取CI的Prometheus告警
export function getCIPrometheusAlerts(ciId) {
  return axios({
    url: urlPrefix + `/ci/${ciId}/prometheus/alerts`,
    method: 'GET'
  })
}

//  检查CI类型是否有Prometheus配置
export function checkCIPrometheus(ciTypeId) {
  return axios({
    url: urlPrefix + `/ci_type/${ciTypeId}/prometheus/check`,
    method: 'GET'
  })
}
```

- [ ] **Step 3: Verify frontend builds**

Run: `cd cmdb-ui && yarn build --mode production 2>&1 | tail -5`
Expected: build succeeds (may show warnings about new files not yet imported, that's OK)

---

### Task 8: Create Prometheus settings page

**Files:**
- Create: `cmdb-ui/src/views/setting/prometheus/index.vue`

**Interfaces:**
- Consumes: Prometheus API functions from `@/api/prometheus.js`, `getCITypes` from `@/modules/cmdb/api/CIType`, `getCITypeAttributesById` from `@/modules/cmdb/api/CITypeAttr`
- Route: `/setting/observability/prometheus` (registered in Task 10)

Create `cmdb-ui/src/views/setting/prometheus/index.vue` with the full settings page. This follows the exact same structure as `SettingGrafana` (`cmdb-ui/src/views/setting/grafana/index.vue`) with the following adaptations:

- [ ] **Step 1: Write the complete component**

Create the file with this structure — adaptation from `grafana/index.vue`:
- **Connection card**: table with columns name, url, auth_type, health status (badge), enable (switch), remark, action (edit/delete)
- **Connection modal**: form with name (required), url (required), auth_type select (none/Bearer/Basic), conditional fields for token or username+password, remark, enable
- **Mapping card**: table with columns ci_type (name), connection (name), label_mapping (text), enable (switch), action (edit/delete)
- **Mapping modal**: form with ci_type select, connection select, label_mapping sub-table (prom_label input + map_type select + value input/select + add/remove), enable switch
- **Methods**: `loadAll()`, connection CRUD handlers, mapping CRUD handlers, `loadHealth()`, `handleToggleEnable()`, `handleTest()`

```html
<template>
  <div class="ops-setting-prometheus">
    <a-card :title="$t('cs.prometheus.connection')" :bordered="false" class="prometheus-card">
      <a-button slot="extra" type="primary" @click="openConnectionModal()">
        {{ $t('cs.prometheus.addConnection') }}
      </a-button>
      <a-table
        :columns="connectionColumns"
        :data-source="connections"
        :pagination="false"
        rowKey="id"
        size="small"
      >
        <template slot="statusTitle">
          {{ $t('cs.prometheus.status') }}
          <a-icon type="reload" :style="{ marginLeft: '4px', cursor: 'pointer' }" @click="loadHealth" />
        </template>
        <template slot="status" slot-scope="text, record">
          <a-tooltip v-if="healthMap[record.id] && !healthMap[record.id].ok" :title="healthMap[record.id].error">
            <a-badge status="error" :text="$t('cs.prometheus.unhealthy')" />
          </a-tooltip>
          <a-badge v-else-if="healthMap[record.id] && healthMap[record.id].ok" status="success" :text="$t('cs.prometheus.healthy')" />
          <a-badge v-else status="default" :text="$t('cs.prometheus.checking')" />
        </template>
        <template slot="auth_type" slot-scope="text">
          <a-tag>{{ text || 'none' }}</a-tag>
        </template>
        <template slot="enable" slot-scope="text, record">
          <a-switch :checked="record.enable !== 0" @change="(checked) => handleToggleEnable(record, checked)" />
        </template>
        <template slot="action" slot-scope="text, record">
          <a-space>
            <a @click="openConnectionModal(record)">{{ $t('cs.prometheus.edit') }}</a>
            <a-popconfirm :title="$t('confirmDelete')" @confirm="handleDeleteConnection(record)">
              <a :style="{ color: '#f5222d' }">{{ $t('cs.prometheus.delete') }}</a>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <a-card :title="$t('cs.prometheus.mapping')" :bordered="false" class="prometheus-card">
      <a-button slot="extra" type="primary" @click="openMappingModal()">
        {{ $t('cs.prometheus.addMapping') }}
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
        <template slot="label_mapping" slot-scope="text, record">
          {{ (record.label_mapping || []).map((lm) => `${lm.prom_label}←${lm.value}`).join(', ') || '-' }}
        </template>
        <template slot="enable" slot-scope="text, record">
          <a-switch :checked="record.enable !== 0" @change="(checked) => handleMappingToggleEnable(record, checked)" />
        </template>
        <template slot="action" slot-scope="text, record">
          <a-space>
            <a @click="openMappingModal(record)">{{ $t('cs.prometheus.edit') }}</a>
            <a-popconfirm :title="$t('confirmDelete')" @confirm="handleDeleteMapping(record)">
              <a :style="{ color: '#f5222d' }">{{ $t('cs.prometheus.delete') }}</a>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <!-- Connection Modal -->
    <a-modal
      :title="connectionForm.id ? $t('cs.prometheus.editConnection') : $t('cs.prometheus.addConnection')"
      :visible="connectionModalVisible"
      @cancel="connectionModalVisible = false"
    >
      <a-form-model ref="connectionForm" :model="connectionForm" :rules="connectionRules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-model-item :label="$t('cs.prometheus.name')" prop="name">
          <a-input v-model="connectionForm.name" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.url')" prop="url">
          <a-input v-model="connectionForm.url" placeholder="http://prometheus:9090" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.authType')">
          <a-select v-model="connectionForm.auth_type">
            <a-select-option value="none">None</a-select-option>
            <a-select-option value="bearer">Bearer Token</a-select-option>
            <a-select-option value="basic">Basic Auth</a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item v-if="connectionForm.auth_type === 'bearer'" :label="$t('cs.prometheus.token')">
          <a-input-password v-model="connectionForm.auth_data.token" />
        </a-form-model-item>
        <template v-if="connectionForm.auth_type === 'basic'">
          <a-form-model-item :label="$t('cs.prometheus.username')">
            <a-input v-model="connectionForm.auth_data.username" />
          </a-form-model-item>
          <a-form-model-item :label="$t('cs.prometheus.password')">
            <a-input-password v-model="connectionForm.auth_data.password" />
          </a-form-model-item>
        </template>
        <a-form-model-item :label="$t('cs.prometheus.remark')">
          <a-input v-model="connectionForm.remark" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.enable')">
          <a-switch :checked="connectionForm.enable !== 0" @change="(checked) => { connectionForm.enable = checked ? 1 : 0 }" />
        </a-form-model-item>
      </a-form-model>
      <template slot="footer">
        <a-button :loading="testing" @click="handleTest">{{ $t('cs.prometheus.testConnect') }}</a-button>
        <a-button @click="connectionModalVisible = false">{{ $t('cancel') }}</a-button>
        <a-button type="primary" :loading="saving" @click="handleSaveConnection">{{ $t('save') }}</a-button>
      </template>
    </a-modal>

    <!-- Mapping Modal -->
    <a-modal
      :title="mappingForm.id ? $t('cs.prometheus.editMapping') : $t('cs.prometheus.addMapping')"
      :visible="mappingModalVisible"
      :confirm-loading="saving"
      width="900px"
      @ok="handleSaveMapping"
      @cancel="mappingModalVisible = false"
    >
      <a-form-model ref="mappingForm" :model="mappingForm" :rules="mappingRules" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
        <a-form-model-item :label="$t('cs.prometheus.ciType')" prop="ci_type_id">
          <a-select v-model="mappingForm.ci_type_id" show-search option-filter-prop="children" @change="handleCiTypeChange">
            <a-select-option v-for="t in ciTypes" :key="t.id" :value="t.id">
              {{ t.alias || t.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.connectionInstance')" prop="connection_id">
          <a-select v-model="mappingForm.connection_id">
            <a-select-option v-for="c in connections" :key="c.id" :value="c.id">
              {{ c.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.labelMapping')">
          <a-table
            :columns="labelMappingColumns"
            :data-source="mappingForm.label_mapping"
            :pagination="false"
            size="small"
            rowKey="_key"
            style="margin-bottom: 8px"
          >
            <template slot="prom_label" slot-scope="text, record">
              <a-input v-model="record.prom_label" :placeholder="$t('cs.prometheus.promLabel')" style="width: 100%" />
            </template>
            <template slot="map_type" slot-scope="text, record">
              <a-select v-model="record.map_type" style="width: 100%">
                <a-select-option value="field">{{ $t('cs.prometheus.field') }}</a-select-option>
                <a-select-option value="fixed">{{ $t('cs.prometheus.fixed') }}</a-select-option>
              </a-select>
            </template>
            <template slot="target" slot-scope="text, record">
              <a-select
                v-if="record.map_type === 'field'"
                v-model="record.value"
                show-search
                option-filter-prop="children"
                :placeholder="$t('cs.prometheus.ciAttr')"
                style="width: 100%"
              >
                <a-select-option v-for="a in ciAttrOptions" :key="a.name" :value="a.name">
                  {{ a.alias || a.name }}({{ a.name }})
                </a-select-option>
              </a-select>
              <a-input
                v-else
                v-model="record.value"
                :placeholder="$t('cs.prometheus.fixedValue')"
                style="width: 100%"
              />
            </template>
            <template slot="action" slot-scope="text, record, index">
              <a-icon type="minus-circle" style="cursor: pointer; color: #f5222d; font-size: 16px;" @click="removeLabelMapping(index)" />
            </template>
          </a-table>
          <a-button type="dashed" size="small" icon="plus" @click="addLabelMapping">
            {{ $t('cs.prometheus.addLabelMapping') }}
          </a-button>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.mappingEnable')">
          <a-switch :checked="mappingForm.enable !== 0" @change="(checked) => { mappingForm.enable = checked ? 1 : 0 }" />
        </a-form-model-item>
      </a-form-model>
    </a-modal>
  </div>
</template>

<script>
import {
  getPrometheusConnections,
  postPrometheusConnection,
  putPrometheusConnection,
  deletePrometheusConnection,
  testPrometheusConnection,
  getPrometheusConnectionsHealth,
  getPrometheusMappings,
  postPrometheusMapping,
  putPrometheusMapping,
  deletePrometheusMapping,
} from '@/api/prometheus'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'

export default {
  name: 'SettingPrometheus',
  data() {
    return {
      connections: [],
      mappings: [],
      ciTypes: [],
      saving: false,
      testing: false,
      connectionModalVisible: false,
      mappingModalVisible: false,
      connectionForm: { id: null, name: '', url: '', auth_type: 'none', auth_data: {}, remark: '', enable: 1 },
      mappingForm: { id: null, ci_type_id: undefined, connection_id: undefined, label_mapping: [], enable: 1 },
      labelMappingKeyCounter: 0,
      healthMap: {},
      ciAttrOptions: [],
      connectionColumns: [],
      mappingColumns: [],
      labelMappingColumns: [],
    }
  },
  computed: {
    connectionRules() {
      return {
        name: [{ required: true, message: this.$t('cs.prometheus.nameRequired'), trigger: 'blur' }],
        url: [{ required: true, message: this.$t('cs.prometheus.urlRequired'), trigger: 'blur' }],
      }
    },
    mappingRules() {
      return {
        ci_type_id: [{ required: true, message: this.$t('cs.prometheus.ciTypeRequired'), trigger: 'change' }],
        connection_id: [{ required: true, message: this.$t('cs.prometheus.connectionRequired'), trigger: 'change' }],
      }
    },
  },
  created() {
    // Initialize columns here so $t() works correctly
    this.connectionColumns = [
      { title: this.$t('cs.prometheus.name'), dataIndex: 'name' },
      { title: this.$t('cs.prometheus.url'), dataIndex: 'url' },
      { title: this.$t('cs.prometheus.authType'), scopedSlots: { customRender: 'auth_type' }, width: 90 },
      { slots: { title: 'statusTitle' }, scopedSlots: { customRender: 'status' }, width: 110 },
      { title: this.$t('cs.prometheus.enable'), scopedSlots: { customRender: 'enable' }, width: 80 },
      { title: this.$t('cs.prometheus.remark'), dataIndex: 'remark' },
      { title: this.$t('cs.prometheus.operation'), scopedSlots: { customRender: 'action' }, width: 220 },
    ]
    this.mappingColumns = [
      { title: this.$t('cs.prometheus.ciType'), scopedSlots: { customRender: 'ci_type' } },
      { title: this.$t('cs.prometheus.connectionInstance'), scopedSlots: { customRender: 'connection' } },
      { title: this.$t('cs.prometheus.labelMapping'), scopedSlots: { customRender: 'label_mapping' } },
      { title: this.$t('cs.prometheus.mappingEnable'), scopedSlots: { customRender: 'enable' }, width: 80 },
      { title: this.$t('cs.prometheus.operation'), scopedSlots: { customRender: 'action' }, width: 160 },
    ]
    this.labelMappingColumns = [
      { title: this.$t('cs.prometheus.promLabel'), scopedSlots: { customRender: 'prom_label' } },
      { title: this.$t('cs.prometheus.mapType'), scopedSlots: { customRender: 'map_type' }, width: 100 },
      { title: this.$t('cs.prometheus.target'), scopedSlots: { customRender: 'target' } },
      { title: this.$t('cs.prometheus.operation'), scopedSlots: { customRender: 'action' }, width: 50 },
    ]
  },
  mounted() {
    this.loadAll()
  },
  methods: {
    async loadAll() {
      const [connRes, mapRes, typeRes] = await Promise.all([
        getPrometheusConnections(),
        getPrometheusMappings(),
        getCITypes(),
      ])
      this.connections = connRes.connections || []
      this.mappings = mapRes.mappings || []
      this.ciTypes = typeRes.ci_types || []
      this.loadHealth()
    },
    async loadHealth() {
      this.healthMap = {}
      try {
        const res = await getPrometheusConnectionsHealth()
        const map = {}
        ;(res.health || []).forEach((h) => { map[h.id] = h })
        this.healthMap = map
      } catch (e) {}
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
      if (record) {
        this.connectionForm = {
          id: record.id, name: record.name, url: record.url,
          auth_type: record.auth_type || 'none',
          auth_data: { ...(record.auth_data || {}) },
          remark: record.remark, enable: record.enable === undefined ? 1 : record.enable,
        }
      } else {
        this.connectionForm = { id: null, name: '', url: '', auth_type: 'none', auth_data: {}, remark: '', enable: 1 }
      }
      this.connectionModalVisible = true
      this.$nextTick(() => this.$refs.connectionForm && this.$refs.connectionForm.clearValidate())
    },
    openMappingModal(record = null) {
      if (record) {
        const mapped = (record.label_mapping || []).map((lm, idx) => ({
          _key: idx + 1,
          prom_label: lm.prom_label,
          map_type: lm.map_type || 'field',
          value: lm.value || '',
        }))
        this.labelMappingKeyCounter = mapped.length
        this.mappingForm = {
          id: record.id,
          ci_type_id: record.ci_type_id,
          connection_id: record.connection_id,
          enable: record.enable === undefined ? 1 : record.enable,
          label_mapping: mapped,
        }
      } else {
        this.labelMappingKeyCounter = 0
        this.mappingForm = { id: null, ci_type_id: undefined, connection_id: undefined, label_mapping: [], enable: 1 }
      }
      this.mappingModalVisible = true
      this.$nextTick(() => this.$refs.mappingForm && this.$refs.mappingForm.clearValidate())
      if (this.mappingForm.ci_type_id) this.handleCiTypeChange(this.mappingForm.ci_type_id)
    },
    async handleCiTypeChange(typeId) {
      try {
        const res = await getCITypeAttributesById(typeId)
        this.ciAttrOptions = res.attributes || []
      } catch (e) {
        this.ciAttrOptions = []
      }
    },
    addLabelMapping() {
      this.mappingForm.label_mapping.push({
        _key: ++this.labelMappingKeyCounter,
        prom_label: undefined,
        map_type: 'field',
        value: '',
      })
    },
    removeLabelMapping(index) {
      this.mappingForm.label_mapping.splice(index, 1)
    },
    async handleToggleEnable(record, checked) {
      await putPrometheusConnection(record.id, { enable: checked ? 1 : 0 })
      this.$set(record, 'enable', checked ? 1 : 0)
      this.$message.success(this.$t('saveSuccess'))
    },
    async handleMappingToggleEnable(record, checked) {
      await putPrometheusMapping(record.id, { enable: checked ? 1 : 0 })
      this.$set(record, 'enable', checked ? 1 : 0)
      this.$message.success(this.$t('saveSuccess'))
    },
    handleSaveConnection() {
      this.$refs.connectionForm.validate(async (valid) => {
        if (!valid) return
        this.saving = true
        try {
          const { id, ...data } = this.connectionForm
          if (id) {
            await putPrometheusConnection(id, data)
          } else {
            await postPrometheusConnection(data)
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
        const labelMappings = this.mappingForm.label_mapping || []
        const incomplete = labelMappings.some((lm) => !lm.prom_label || !lm.value)
        if (incomplete) {
          this.$message.error(this.$t('cs.prometheus.labelMappingIncomplete'))
          return
        }
        this.saving = true
        try {
          const { id, ...data } = this.mappingForm
          if (id) {
            await putPrometheusMapping(id, data)
          } else {
            await postPrometheusMapping(data)
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
      await deletePrometheusConnection(record.id)
      this.$message.success(this.$t('deleteSuccess'))
      await this.loadAll()
    },
    async handleDeleteMapping(record) {
      await deletePrometheusMapping(record.id)
      this.$message.success(this.$t('deleteSuccess'))
      await this.loadAll()
    },
    handleTest() {
      this.$refs.connectionForm.validate(async (valid) => {
        if (!valid) return
        this.testing = true
        try {
          await testPrometheusConnection({
            url: this.connectionForm.url,
            auth_type: this.connectionForm.auth_type,
            auth_data: this.connectionForm.auth_data,
          })
          this.$message.success(this.$t('cs.prometheus.testSuccess'))
        } finally {
          this.testing = false
        }
      })
    },
  },
}
</script>

<style lang="less" scoped>
.ops-setting-prometheus {
  padding: 20px;
  background-color: #f5f7fa;
  height: calc(100vh - 64px);
  overflow: auto;
  .prometheus-card {
    margin-bottom: 16px;
  }
}
</style>
```

- [ ] **Step 2: Verify frontend builds with the new file**

Run: `cd cmdb-ui && yarn build --mode production 2>&1 | tail -5`
Expected: build succeeds

---

### Task 9: Create CiDetailPrometheus component

**Files:**
- Create: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailPrometheus.vue`

**Interfaces:**
- Consumes: `getCIPrometheusAlerts` from `@/modules/cmdb/api/ci`
- Prop: `ciId` (Number, required)
- Used by: `ciDetailTab.vue` tab_7

- [ ] **Step 1: Create the CiDetailPrometheus component**

Create `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailPrometheus.vue`:

```html
<template>
  <div class="ci-detail-prometheus">
    <!-- Stats Bar -->
    <div class="prom-alert-stats">
      <div class="prom-stat-card prom-stat-total">
        <div class="stat-icon"><a-icon type="alert" /></div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('cmdb.ci.alertFiring') }}</div>
          <div class="stat-value">{{ alerts.length }}</div>
        </div>
      </div>
      <div class="prom-stat-card prom-stat-critical">
        <div class="stat-icon"><a-icon type="close-circle" /></div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('cmdb.ci.alertCritical') }}</div>
          <div class="stat-value">{{ severityCounts.critical }}</div>
        </div>
      </div>
      <div class="prom-stat-card prom-stat-warning">
        <div class="stat-icon"><a-icon type="exclamation-circle" /></div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('cmdb.ci.alertWarning') }}</div>
          <div class="stat-value">{{ severityCounts.warning }}</div>
        </div>
      </div>
      <div class="prom-stat-card prom-stat-info">
        <div class="stat-icon"><a-icon type="info-circle" /></div>
        <div class="stat-content">
          <div class="stat-label">{{ $t('cmdb.ci.alertInfo') }}</div>
          <div class="stat-value">{{ severityCounts.info }}</div>
        </div>
      </div>
      <div class="prom-refresh-area">
        <span class="last-refresh">{{ $t('cmdb.ci.alertLastRefresh') }}: {{ lastRefreshText }}</span>
        <a-button size="small" @click="loadAlerts" :loading="loading">
          <a-icon type="reload" />{{ $t('cmdb.ci.alertRefresh') }}
        </a-button>
      </div>
    </div>

    <!-- Alert Table -->
    <a-spin :spinning="loading">
      <a-table
        v-if="alerts.length"
        :columns="columns"
        :data-source="alerts"
        :pagination="false"
        rowKey="fingerprint"
        size="small"
        :expandRowByClick="true"
        class="prom-alert-table"
      >
        <template slot="severity" slot-scope="text, record">
          <a-badge
            :status="severityStatus(record.labels.severity)"
            :text="severityStatusText(record.labels.severity)"
          />
        </template>
        <template slot="activeAt" slot-scope="text">
          {{ text | formatTime }}
        </template>
        <template slot="duration" slot-scope="text, record">
          {{ formatDuration(record.activeAt) }}
        </template>
        <template slot="expandedRowRender" slot-scope="record">
          <div class="prom-alert-detail">
            <div class="prom-alert-detail-section">
              <div class="prom-alert-detail-title">{{ $t('cmdb.ci.alertLabels') }}</div>
              <div class="prom-alert-detail-tags">
                <a-tag v-for="(val, key) in record.labels" :key="key" color="blue">
                  {{ key }}={{ val }}
                </a-tag>
              </div>
            </div>
            <div v-if="record.annotations && Object.keys(record.annotations).length" class="prom-alert-detail-section">
              <div class="prom-alert-detail-title">{{ $t('cmdb.ci.alertAnnotations') }}</div>
              <div v-if="record.annotations.summary" class="prom-alert-annotation">
                <strong>Summary:</strong> {{ record.annotations.summary }}
              </div>
              <div v-if="record.annotations.description" class="prom-alert-annotation">
                <strong>Description:</strong> {{ record.annotations.description }}
              </div>
            </div>
            <div class="prom-alert-detail-section">
              <a-row :gutter="16">
                <a-col :span="12">
                  <span class="prom-alert-detail-title">{{ $t('cmdb.ci.alertRuleName') }}:</span>
                  {{ record.rule_name || '-' }}
                </a-col>
                <a-col :span="12">
                  <span class="prom-alert-detail-title">{{ $t('cmdb.ci.alertValue') }}:</span>
                  {{ record.value || '-' }}
                </a-col>
              </a-row>
            </div>
          </div>
        </template>
      </a-table>

      <!-- Empty states -->
      <a-empty
        v-else-if="!loading"
        :image-style="{ height: '100px' }"
        :style="{ paddingTop: '10%' }"
      >
        <img slot="image" :src="require('@/assets/data_empty.png')" />
        <span slot="description">
          {{ errorMsg ? errorMsg : configured ? $t('cmdb.ci.alertNoData') : $t('cmdb.ci.alertNoConfig') }}
        </span>
      </a-empty>
    </a-spin>
  </div>
</template>

<script>
import { getCIPrometheusAlerts } from '@/modules/cmdb/api/ci'

export default {
  name: 'CiDetailPrometheus',
  props: {
    ciId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      configured: true,
      errorMsg: '',
      alerts: [],
      lastRefreshTime: null,
      refreshTimer: null,
    }
  },
  computed: {
    severityCounts() {
      return {
        critical: this.alerts.filter((a) => this._severity(a) === 'critical').length,
        warning: this.alerts.filter((a) => this._severity(a) === 'warning').length,
        info: this.alerts.filter((a) => this._severity(a) === 'info').length,
      }
    },
    lastRefreshText() {
      if (!this.lastRefreshTime) return '-'
      const d = new Date(this.lastRefreshTime)
      return d.toLocaleTimeString()
    },
    columns() {
      return [
        { title: this.$t('cmdb.ci.alertSeverity'), scopedSlots: { customRender: 'severity' }, width: 120 },
        { title: this.$t('cmdb.ci.alertName'), dataIndex: 'rule_name' },
        { title: this.$t('cmdb.ci.alertActiveAt'), scopedSlots: { customRender: 'activeAt' }, width: 180 },
        { title: this.$t('cmdb.ci.alertDuration'), scopedSlots: { customRender: 'duration' }, width: 120 },
      ]
    },
  },
  mounted() {
    this.loadAlerts()
    this.startAutoRefresh()
  },
  beforeDestroy() {
    this.stopAutoRefresh()
  },
  methods: {
    _severity(alert) {
      return (alert.labels || {}).severity || 'info'
    },
    async loadAlerts() {
      this.loading = true
      this.errorMsg = ''
      try {
        const res = await getCIPrometheusAlerts(this.ciId)
        this.configured = res.configured !== false
        this.alerts = res.alerts || []
        this.lastRefreshTime = Date.now()
      } catch (e) {
        this.alerts = []
        this.errorMsg = e.message || 'Connection error'
      } finally {
        this.loading = false
      }
    },
    startAutoRefresh() {
      this.refreshTimer = setInterval(() => {
        this.loadAlerts()
      }, 30000)
    },
    stopAutoRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer)
        this.refreshTimer = null
      }
    },
    severityStatus(severity) {
      const s = (severity || '').toLowerCase()
      if (s === 'critical') return 'error'
      if (s === 'warning') return 'warning'
      return 'processing'
    },
    severityStatusText(severity) {
      const s = (severity || '').toLowerCase()
      if (s === 'critical') return this.$t('cmdb.ci.alertCritical')
      if (s === 'warning') return this.$t('cmdb.ci.alertWarning')
      return this.$t('cmdb.ci.alertInfo')
    },
    formatDuration(activeAt) {
      if (!activeAt) return '-'
      const start = new Date(activeAt).getTime()
      const now = Date.now()
      const diff = Math.floor((now - start) / 1000)
      if (diff < 60) return diff + 's'
      if (diff < 3600) return Math.floor(diff / 60) + 'm'
      if (diff < 86400) return Math.floor(diff / 3600) + 'h'
      return Math.floor(diff / 86400) + 'd'
    },
  },
}
</script>

<style lang="less" scoped>
.ci-detail-prometheus {
  height: 100%;
}
.prom-alert-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
}
.prom-stat-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fb 100%);
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e8eaed;
  min-width: 140px;
  .stat-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    color: #fff;
  }
  .stat-content {
    .stat-label { font-size: 13px; color: #8c8c8c; }
    .stat-value { font-size: 22px; font-weight: 600; color: #262626; line-height: 1; }
  }
  &.prom-stat-total .stat-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
  &.prom-stat-critical .stat-icon { background: linear-gradient(135deg, #f5222d 0%, #cf1322 100%); }
  &.prom-stat-warning .stat-icon { background: linear-gradient(135deg, #fa8c16 0%, #d46b08 100%); }
  &.prom-stat-info .stat-icon { background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%); }
}
.prom-refresh-area {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  .last-refresh { font-size: 12px; color: #8c8c8c; }
}
.prom-alert-table {
  background: #fff;
  border-radius: 8px;
}
.prom-alert-detail {
  padding: 8px 0;
  &-section {
    margin-bottom: 12px;
  }
  &-title {
    font-weight: 600;
    margin-bottom: 6px;
    color: #262626;
  }
  &-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
}
.prom-alert-annotation {
  font-size: 13px;
  color: #595959;
  margin-bottom: 4px;
}
</style>
```

- [ ] **Step 2: Verify the component imports correctly**

Run: `cd cmdb-ui && yarn build --mode production 2>&1 | tail -5`
Expected: build succeeds

---

### Task 10: Integrate tab_7 into ciDetailTab

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailTab.vue`

**Changes:**
- Import `CiDetailPrometheus`
- Import `checkCIPrometheus`
- Add `hasPrometheus` data property
- Add `checkPrometheus()` call in `create()`
- Add `tab_7` template

- [ ] **Step 1: Add import for CiDetailPrometheus**

In `ciDetailTab.vue`, after the existing `CiDetailMonitoring` import (line 238), add:

```javascript
import CiDetailPrometheus from './ciDetailPrometheus.vue'
```

- [ ] **Step 2: Add import for checkCIPrometheus**

In the import from `@/modules/cmdb/api/ci` (line 224), modify the destructuring to include `checkCIPrometheus`:

Change from:
```javascript
import { checkCITypeMonitoring, getCIById, searchCI } from '@/modules/cmdb/api/ci'
```
To:
```javascript
import { checkCITypeMonitoring, checkCIPrometheus, getCIById, searchCI } from '@/modules/cmdb/api/ci'
```

- [ ] **Step 3: Register component**

In the `components` block (after line 254, after `CiDetailMonitoring`), add:
```javascript
CiDetailPrometheus,
```

- [ ] **Step 4: Add `hasPrometheus` data property**

In `data()` return object, after `hasMonitoring: false` (line 280), add:
```javascript
hasPrometheus: false,
```

- [ ] **Step 5: Add `checkPrometheus()` call in `create()` method**

In the `create()` method, after `this.checkMonitoring(effectiveTypeId)` (line 367), add:
```javascript
this.checkPrometheus(effectiveTypeId)
```

- [ ] **Step 6: Add `checkPrometheus` method**

After the `checkMonitoring` method (after line 483), add:
```javascript
async checkPrometheus(typeIdOverride) {
  const typeId = typeIdOverride || this.typeId
  try {
    const res = await checkCIPrometheus(typeId)
    this.hasPrometheus = res.has_prometheus || false
  } catch (e) {
    this.hasPrometheus = false
  }
},
```

- [ ] **Step 7: Add tab_7 in the template**

After the `tab_6` closing `</a-tab-pane>` (after line 204), add:
```html
<a-tab-pane key="tab_7" v-if="hasPrometheus">
  <span slot="tab"><a-icon type="alert" />{{ $t('cmdb.ci.prometheusAlerts') }}</span>
  <div :style="{ padding: '24px', height: '100%' }">
    <CiDetailPrometheus v-if="ciId" :ciId="ciId" />
  </div>
</a-tab-pane>
```

- [ ] **Step 8: Verify frontend builds**

Run: `cd cmdb-ui && yarn build --mode production 2>&1 | tail -5`
Expected: build succeeds

---

### Task 11: Add Prometheus route to router config

**Files:**
- Modify: `cmdb-ui/src/router/config.js`

- [ ] **Step 1: Add Prometheus child route**

In `cmdb-ui/src/router/config.js`, after the Grafana route child (after line 103), add:

```javascript
{
  path: '/setting/observability/prometheus',
  name: 'setting_prometheus',
  meta: { title: 'cs.menu.prometheus' },
  component: () => import(/* webpackChunkName: "setting" */ '@/views/setting/prometheus/index')
}
```

- [ ] **Step 2: Verify build**

Run: `cd cmdb-ui && yarn build --mode production 2>&1 | tail -5`
Expected: build succeeds

---

### Task 12: Add i18n keys

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/lang/zh.js`
- Modify: `cmdb-ui/src/modules/cmdb/lang/en.js`
- Modify: `cmdb-ui/src/views/setting/lang/zh.js`
- Modify: `cmdb-ui/src/views/setting/lang/en.js`

- [ ] **Step 1: Add CMDB i18n keys (Chinese)**

In `cmdb-ui/src/modules/cmdb/lang/zh.js`, find the existing `ci` section near `grafana`, `monitoring` keys and add:

```javascript
prometheusAlerts: 'Prometheus告警',
alerts: '告警',
alertFiring: '活跃告警',
alertCritical: '严重',
alertWarning: '警告',
alertInfo: '信息',
alertSeverity: '级别',
alertName: '告警名称',
alertActiveAt: '触发时间',
alertDuration: '持续时间',
alertNoData: '无活跃告警 — 所有系统正常运行',
alertNoConfig: '未配置Prometheus，请在系统设置中配置',
alertLastRefresh: '最后刷新',
alertRefresh: '刷新',
alertLabels: '标签',
alertAnnotations: '注释',
alertRuleName: '告警规则名称',
alertValue: '当前值',
```

- [ ] **Step 2: Add CMDB i18n keys (English)**

In `cmdb-ui/src/modules/cmdb/lang/en.js`, in the same location, add:

```javascript
prometheusAlerts: 'Prometheus Alerts',
alerts: 'Alerts',
alertFiring: 'Firing',
alertCritical: 'Critical',
alertWarning: 'Warning',
alertInfo: 'Info',
alertSeverity: 'Severity',
alertName: 'Alert Name',
alertActiveAt: 'Active At',
alertDuration: 'Duration',
alertNoData: 'No active alerts — all systems operational',
alertNoConfig: 'Prometheus not configured. Please configure it in System Settings',
alertLastRefresh: 'Last Refresh',
alertRefresh: 'Refresh',
alertLabels: 'Labels',
alertAnnotations: 'Annotations',
alertRuleName: 'Rule Name',
alertValue: 'Current Value',
```

- [ ] **Step 3: Add setting i18n keys (Chinese)**

In `cmdb-ui/src/views/setting/lang/zh.js`, add to the top-level object:

```javascript
'cs.menu.prometheus': 'Prometheus设置',
'cs.prometheus.connection': '连接管理',
'cs.prometheus.addConnection': '新增连接',
'cs.prometheus.editConnection': '编辑连接',
'cs.prometheus.name': '名称',
'cs.prometheus.url': '地址',
'cs.prometheus.authType': '认证方式',
'cs.prometheus.token': 'Token',
'cs.prometheus.username': '用户名',
'cs.prometheus.password': '密码',
'cs.prometheus.remark': '备注',
'cs.prometheus.enable': '启用',
'cs.prometheus.status': '状态',
'cs.prometheus.healthy': '健康',
'cs.prometheus.unhealthy': '异常',
'cs.prometheus.checking': '检测中',
'cs.prometheus.testConnect': '测试连接',
'cs.prometheus.testSuccess': '连接测试成功',
'cs.prometheus.operation': '操作',
'cs.prometheus.edit': '编辑',
'cs.prometheus.delete': '删除',
'cs.prometheus.mapping': '映射管理',
'cs.prometheus.addMapping': '新增映射',
'cs.prometheus.editMapping': '编辑映射',
'cs.prometheus.ciType': 'CI类型',
'cs.prometheus.connectionInstance': '连接实例',
'cs.prometheus.labelMapping': '标签映射',
'cs.prometheus.addLabelMapping': '添加标签',
'cs.prometheus.promLabel': 'Prometheus标签',
'cs.prometheus.ciAttr': 'CI属性',
'cs.prometheus.fixedValue': '固定值',
'cs.prometheus.mapType': '映射类型',
'cs.prometheus.field': '字段',
'cs.prometheus.fixed': '固定',
'cs.prometheus.target': '目标值',
'cs.prometheus.mappingEnable': '启用',
'cs.prometheus.nameRequired': '名称不能为空',
'cs.prometheus.urlRequired': '地址不能为空',
'cs.prometheus.ciTypeRequired': 'CI类型不能为空',
'cs.prometheus.connectionRequired': '连接实例不能为空',
'cs.prometheus.labelMappingIncomplete': '标签映射不完整，请填写所有必填字段',
```

- [ ] **Step 4: Add setting i18n keys (English)**

In `cmdb-ui/src/views/setting/lang/en.js`, add:

```javascript
'cs.menu.prometheus': 'Prometheus Settings',
'cs.prometheus.connection': 'Connections',
'cs.prometheus.addConnection': 'Add Connection',
'cs.prometheus.editConnection': 'Edit Connection',
'cs.prometheus.name': 'Name',
'cs.prometheus.url': 'URL',
'cs.prometheus.authType': 'Auth Type',
'cs.prometheus.token': 'Token',
'cs.prometheus.username': 'Username',
'cs.prometheus.password': 'Password',
'cs.prometheus.remark': 'Remark',
'cs.prometheus.enable': 'Enable',
'cs.prometheus.status': 'Status',
'cs.prometheus.healthy': 'Healthy',
'cs.prometheus.unhealthy': 'Unhealthy',
'cs.prometheus.checking': 'Checking',
'cs.prometheus.testConnect': 'Test Connection',
'cs.prometheus.testSuccess': 'Connection test succeeded',
'cs.prometheus.operation': 'Operation',
'cs.prometheus.edit': 'Edit',
'cs.prometheus.delete': 'Delete',
'cs.prometheus.mapping': 'Mappings',
'cs.prometheus.addMapping': 'Add Mapping',
'cs.prometheus.editMapping': 'Edit Mapping',
'cs.prometheus.ciType': 'CI Type',
'cs.prometheus.connectionInstance': 'Connection',
'cs.prometheus.labelMapping': 'Label Mapping',
'cs.prometheus.addLabelMapping': 'Add Label',
'cs.prometheus.promLabel': 'Prom Label',
'cs.prometheus.ciAttr': 'CI Attribute',
'cs.prometheus.fixedValue': 'Fixed Value',
'cs.prometheus.mapType': 'Map Type',
'cs.prometheus.field': 'Field',
'cs.prometheus.fixed': 'Fixed',
'cs.prometheus.target': 'Target',
'cs.prometheus.mappingEnable': 'Enable',
'cs.prometheus.nameRequired': 'Name is required',
'cs.prometheus.urlRequired': 'URL is required',
'cs.prometheus.ciTypeRequired': 'CI type is required',
'cs.prometheus.connectionRequired': 'Connection is required',
'cs.prometheus.labelMappingIncomplete': 'Label mapping is incomplete, please fill in all required fields',
```

- [ ] **Step 5: Verify frontend builds**

Run: `cd cmdb-ui && yarn build --mode production 2>&1 | tail -5`
Expected: build succeeds

---

### Task 13: Final verification

- [ ] **Step 1: Run backend tests**

```bash
cd cmdb-api && uv run pytest tests/test_prometheus_client.py tests/test_grafana_client.py -v
```

Expected: all tests pass

- [ ] **Step 2: Run backend lint**

```bash
cd cmdb-api && uv run ruff check api/lib/common_setting/prometheus.py api/lib/common_setting/prometheus_client.py api/views/common_setting/prometheus_config.py api/lib/cmdb/prometheus.py api/views/cmdb/prometheus.py api/lib/common_setting/resp_format.py
```

Expected: no errors

- [ ] **Step 3: Verify frontend production build**

```bash
cd cmdb-ui && yarn build --mode production
```

Expected: build succeeds without errors
