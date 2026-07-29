# Prometheus Alert Integration — Design Spec

**Date**: 2026-07-29
**Status**: Approved
**Scope**: Integrate Prometheus alert information into the CI detail page, with a configurable settings page under Observability Settings.

---

## Overview

Add Prometheus alert integration to the CMDB, following the same architectural pattern established by the existing Grafana integration. This includes:

1. A **settings page** under `/setting/observability/prometheus` where admins configure Prometheus connections and CI-type-to-label mappings.
2. A new **alert tab (tab_7)** in `ciDetailTab.vue` that displays active/firing Prometheus alerts for the current CI, matching via label mappings.
3. Backend APIs for config CRUD, health checks, and alert resolution per CI.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Frontend                                           │
│  ┌──────────────────┐  ┌──────────────────────────┐ │
│  │ SettingPrometheus │  │ CiDetailPrometheus       │ │
│  │ /setting/...      │  │ (tab_7 in ciDetailTab)   │ │
│  └──────┬───────────┘  └───────────┬──────────────┘ │
│         │                          │                 │
└─────────┼──────────────────────────┼─────────────────┘
          │                          │
   ┌──────▼──────────┐     ┌────────▼─────────────┐
   │ /common-setting │     │ /v0.1                 │
   │ /v1/prometheus/*│     │ /ci/{id}/prometheus/* │
   │ (admin CRUD)    │     │ /ci_type/{id}/        │
   │                 │     │   prometheus/check    │
   └──────┬──────────┘     └────────┬─────────────┘
          │                          │
   ┌──────▼──────────────────────────▼─────────────┐
   │  Backend Lib Layer                             │
   │  ┌───────────────────┐  ┌────────────────────┐ │
   │  │ PrometheusConfig  │  │ PrometheusClient   │ │
   │  │ CRUD (AES加密)    │  │ (HTTP client)      │ │
   │  └───────────────────┘  └────────────────────┘ │
   └────────────────────────────────────────────────┘
          │
   ┌──────▼──────────────────────────────────────────┐
   │  Storage: CommonData table                      │
   │  data_type = 'Prometheus' (AES encrypted JSON)  │
   │  shape: {connections: [...], mappings: [...]}    │
   └─────────────────────────────────────────────────┘
          │
   ┌──────▼──────────┐
   │  External:       │
   │  Prometheus API  │
   │  /api/v1/alerts  │
   └─────────────────┘
```

---

## Backend Design

### Config Storage

All Prometheus config is stored in a **single `CommonData` record** with `data_type='Prometheus'`, AES-encrypted via `AESCrypto`. The JSON shape:

```json
{
  "connections": [{
    "id": 1,
    "name": "prod-prometheus",
    "url": "http://prometheus.example.com:9090",
    "auth_type": "bearer",
    "auth_data": {"token": "<encrypted>"},
    "enable": 1,
    "remark": ""
  }],
  "mappings": [{
    "id": 1,
    "ci_type_id": 3,
    "connection_id": 1,
    "label_mapping": [
      {"prom_label": "instance", "map_type": "field", "value": "hostname"},
      {"prom_label": "job", "map_type": "fixed", "value": "node_exporter"}
    ],
    "enable": 1
  }]
}
```

### New Files

| File | Purpose |
|------|---------|
| `api/lib/common_setting/prometheus.py` | `PrometheusConfigCRUD` — CRUD + validation + encryption |
| `api/lib/common_setting/prometheus_client.py` | `PrometheusClient` — HTTP client for Prometheus API |
| `api/views/common_setting/prometheus_config.py` | Admin config CRUD routes (under `/prometheus`) |
| `api/views/cmdb/prometheus.py` | CI alert resolution routes |
| `api/lib/cmdb/prometheus.py` | `check_ci_prometheus()`, `resolve_ci_prometheus_alerts()` |

### New API Endpoints

**Settings (admin-only, `@role_required("acl_admin")`)**:
- `GET    /common-setting/v1/prometheus/connections` — list connections (auth masked)
- `POST   /common-setting/v1/prometheus/connections` — create connection
- `PUT    /common-setting/v1/prometheus/connections/{id}` — update connection
- `DELETE /common-setting/v1/prometheus/connections/{id}` — delete connection (cascade mappings)
- `POST   /common-setting/v1/prometheus/connections/test` — test connection
- `GET    /common-setting/v1/prometheus/connections/health` — per-connection health check
- `GET    /common-setting/v1/prometheus/mappings` — list mappings
- `POST   /common-setting/v1/prometheus/mappings` — create mapping
- `PUT    /common-setting/v1/prometheus/mappings/{id}` — update mapping
- `DELETE /common-setting/v1/prometheus/mappings/{id}` — delete mapping

**CI-level (authenticated, used by detail page)**:
- `GET /v0.1/ci_type/{ci_type_id}/prometheus/check` — check if CI type has Prometheus configured
- `GET /v0.1/ci/{ci_id}/prometheus/alerts` — resolve and return active alerts for this CI

### PrometheusConfigCRUD (`api/lib/common_setting/prometheus.py`)

Mirrors `GrafanaConfigCRUD` exactly:

- `get_config()` — read from `CommonData`, AES decrypt, parse JSON, default to `{connections:[], mappings:[]}`
- `_save(config)` — AES encrypt, write to `CommonData`
- Connection CRUD with validation (name/url required, auth_data required if auth_type is not 'none')
- Mapping CRUD: validates `ci_type_id`, `connection_id`, and `label_mapping` structure
- `test_connection(url, auth_type, auth_data)` — calls Prometheus `/-/healthy`
- `check_health()` — per-connection liveness, never raises
- API key/token masking for list responses

### PrometheusClient (`api/lib/common_setting/prometheus_client.py`)

```python
class PrometheusClient:
    def __init__(self, url, auth_type=None, auth_data=None, timeout=5)
    def health_check() -> bool                # GET /-/healthy
    def query_alerts(labels: dict) -> list    # GET /api/v1/alerts with label matchers
    def _build_request_kwargs() -> dict       # headers with Bearer/Basic auth
```

Auth support:
- `none` — no auth header
- `bearer` — `Authorization: Bearer <token>`
- `basic` — `Authorization: Basic <base64(user:pass)>`

Alert query: builds label matchers from the mapping's `label_mapping`, e.g. `{instance="10.0.0.1",job="node_exporter"}`.

### Alert Resolution (`api/lib/cmdb/prometheus.py`)

```python
def check_ci_prometheus(ci_type_id: int) -> dict:
    """Check if ci_type has any enabled Prometheus mapping.
    Returns {"has_prometheus": bool}."""
    # 1. Get config, check connections exist
    # 2. Find enabled mappings for ci_type_id
    # 3. Return {"has_prometheus": len(type_mappings) > 0}

def resolve_ci_prometheus_alerts(ci_id: int) -> dict:
    """Resolve active Prometheus alerts for a CI.
    Returns {"configured": bool, "alerts": [...]}."""
    # 1. Get CI by id, check permission
    # 2. Get CI data via CIManager
    # 3. Find matching enabled mappings for ci_type_id
    # 4. For each mapping: build label filters, call PrometheusClient.query_alerts()
    # 5. Merge and deduplicate alerts (by fingerprint)
    # 6. Return standardized alert list
```

### Alert Response Format

```json
{
  "configured": true,
  "has_prometheus": true,
  "alerts": [{
    "fingerprint": "abc123def456",
    "labels": {
      "alertname": "HighCPUUsage",
      "instance": "10.0.0.1:9100",
      "severity": "critical",
      "job": "node_exporter"
    },
    "annotations": {
      "summary": "CPU usage above 90%",
      "description": "CPU usage on instance 10.0.0.1 has been above 90% for 5 minutes."
    },
    "state": "firing",
    "activeAt": "2026-07-29T12:00:00Z",
    "value": "95.2",
    "rule_name": "HighCPUUsage",
    "connection_id": 1
  }]
}
```

### Error Handling

New error keys in `api/lib/common_setting/resp_format.py`:
- `prometheus_name_required`
- `prometheus_url_required`
- `prometheus_test_failed`
- `prometheus_connection_not_found`
- `prometheus_mapping_not_found`
- `prometheus_config_broken`

---

## Frontend Design

### New Files

| File | Purpose |
|------|---------|
| `src/views/setting/prometheus/index.vue` | Prometheus settings page (connections + mappings) |
| `src/modules/cmdb/views/ci/modules/ciDetailPrometheus.vue` | CI detail alert tab component |
| `src/api/prometheus.js` | Prometheus settings API client |

### Modified Files

| File | Change |
|------|--------|
| `src/modules/cmdb/views/ci/modules/ciDetailTab.vue` | Add `tab_7` + imports + `checkPrometheus()` in create() |
| `src/modules/cmdb/api/ci.js` | Add `getCIPrometheusAlerts()`, `checkCIPrometheus()` |
| `src/router/config.js` | Add `/setting/observability/prometheus` child route |
| `src/modules/cmdb/lang/zh.js` | Add alert i18n keys |
| `src/modules/cmdb/lang/en.js` | Add alert i18n keys |
| `src/views/setting/lang/zh.js` | Add Prometheus settings i18n keys |
| `src/views/setting/lang/en.js` | Add Prometheus settings i18n keys |
| `src/views/setting/grafana/index.vue` | Change redirect to Prometheus as second observability child |

### Settings Page (`SettingPrometheus`)

Follows the **exact same layout** as `SettingGrafana`:

**Connection Card:**
- Table: name, URL, auth_type, health status, enable switch, remark, actions
- Modal form: name, URL, auth_type select (none/Bearer/Basic), token/username+password fields, remark, enable
- Actions: create, edit, delete, test connection, health check

**Mapping Card:**
- Table: CI type, connection, label mappings, enable switch, actions
- Modal form: CI type select, connection select, label mapping sub-table
- Label mapping sub-table: Prometheus label name (input), map type (field/fixed), map value (CI attr select or fixed input), action (add/remove row)
- Actions: create, edit, delete

### CI Detail Alert Tab (tab_7)

**`ciDetailTab.vue` changes:**
```html
<a-tab-pane key="tab_7" v-if="hasPrometheus">
  <span slot="tab"><a-icon type="alert" />Prometheus {{ $t('cmdb.ci.alerts') }}</span>
  <div :style="{ padding: '24px', height: '100%' }">
    <CiDetailPrometheus v-if="ciId" :ciId="ciId" />
  </div>
</a-tab-pane>
```

Data properties added:
- `hasPrometheus: false` — controlled by `checkCIPrometheus()` API
- Called in `create()` alongside existing `checkMonitoring()`

**`CiDetailPrometheus.vue` component:**

Layout (top to bottom):

1. **Alert Stats Bar** — 4 stat cards in a row:
   - Total firing alerts (red gradient)
   - Critical count (red)
   - Warning count (orange)
   - Info count (blue)
   - Right side: last refresh timestamp + manual refresh button

2. **Expandable Alert Table** (vxe-table or a-table):
   - Columns: severity badge, alert name (from labels.alertname), active since (activeAt), duration
   - Default sort: severity (critical > warning > info), then by activeAt descending
   - Expand row content:
     - All labels (key: value pairs, styled as tags)
     - Annotations (summary + description)
     - Rule name
     - Current value

3. **Empty States**:
   - Not configured: empty state with "Prometheus not configured" message
   - No active alerts: green success state "No active alerts — all systems operational"
   - Connection error: error state with retry button

4. **Auto-refresh**:
   - 30-second polling interval when tab is active
   - Stop polling when user switches away from the tab
   - Manual refresh button always accessible in the stats bar
   - Last refresh timestamp displayed

### Route

Add to `/setting/observability` children in `router/config.js`:
```javascript
{
  path: '/setting/observability/prometheus',
  name: 'setting_prometheus',
  meta: { title: 'cs.menu.prometheus' },
  component: () => import(/* webpackChunkName: "setting" */ '@/views/setting/prometheus/index')
}
```

---

## Data Flow

```
ciDetailTab.create(ciId)
  ├── getCI()
  ├── getAttributes(typeId)
  ├── checkMonitoring(typeId)      # existing Grafana check
  ├── checkPrometheus(typeId)      # NEW: GET /v0.1/ci_type/{typeId}/prometheus/check
  │     → sets hasPrometheus
  └── ...

User clicks tab_7
  → CiDetailPrometheus mounted
    → loadAlerts()
      → GET /v0.1/ci/{ciId}/prometheus/alerts
      → renders alert stats + table
    → startAutoRefresh()  # 30s interval
      → clearInterval on tab switch / unmount

Admin configures settings
  → SettingPrometheus
    → loadAll() → GET connections + GET mappings + GET ciTypes
    → CRUD operations via prometheus API client
```

---

## i18n Keys to Add

**CMDB module** (`cmdb-ui/src/modules/cmdb/lang/`):
- `cmdb.ci.prometheusAlerts` / `cmdb.ci.alerts`
- `cmdb.ci.alertNoData` / `cmdb.ci.alertNoConfig`
- `cmdb.ci.alertFiring` / `cmdb.ci.alertCritical` / `cmdb.ci.alertWarning` / `cmdb.ci.alertInfo`
- `cmdb.ci.alertLastRefresh` / `cmdb.ci.alertRefresh`
- `cmdb.ci.alertLabels` / `cmdb.ci.alertAnnotations` / `cmdb.ci.alertRuleName` / `cmdb.ci.alertValue`

**Setting module** (`cmdb-ui/src/views/setting/lang/`):
- `cs.menu.prometheus` — "Prometheus 设置" / "Prometheus Settings"
- `cs.prometheus.connection` / `.addConnection` / `.editConnection`
- `cs.prometheus.name` / `.url` / `.authType` / `.token` / `.username` / `.password` / `.remark`
- `cs.prometheus.status` / `.healthy` / `.unhealthy` / `.checking`
- `cs.prometheus.testConnect` / `.testSuccess`
- `cs.prometheus.mapping` / `.addMapping` / `.editMapping`
- `cs.prometheus.ciType` / `.connectionInstance` / `.labelMapping`
- `cs.prometheus.promLabel` / `.ciAttr` / `.fixedValue` / `.mapType`
- `cs.prometheus.nameRequired` / `.urlRequired` / `.ciTypeRequired` / `.connectionRequired`

---

## Testing

**Backend** (new file `cmdb-api/tests/test_prometheus_client.py`):
- Unit tests for `PrometheusClient` (mocked HTTP requests)
- Unit tests for `PrometheusConfigCRUD` (mocked `CommonData`)
- Test auth header generation for none/bearer/basic
- Test alert label filter construction

**Frontend** (manual verification):
- CI detail page: tab_7 shows/Hides based on config
- Alert list rendering with mock data
- Auto-refresh behavior
- Settings page CRUD operations

---

## Implementation Order

1. **Backend config layer** — `PrometheusConfigCRUD` + `PrometheusClient` + models
2. **Backend API routes** — settings CRUD + CI alert routes
3. **Frontend settings page** — `SettingPrometheus` + API client
4. **Frontend CI alert tab** — `CiDetailPrometheus` + `ciDetailTab` integration
5. **i18n** — all language keys
6. **Testing & verification**
