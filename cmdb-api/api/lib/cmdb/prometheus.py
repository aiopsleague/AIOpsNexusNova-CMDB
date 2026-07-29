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

    # Collect display_columns from all type mappings (dedup by key, first wins)
    merged_display_columns = []
    seen_display_keys = set()
    for mapping in type_mappings:
        for dc in mapping.get("display_columns") or []:
            key = dc.get("key", "")
            if key and key not in seen_display_keys:
                seen_display_keys.add(key)
                merged_display_columns.append({
                    "key": key,
                    "title_zh": dc.get("title_zh", key),
                    "title_en": dc.get("title_en", key),
                })

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
    # Flatten display_columns values into top-level _d_<safe_key> fields on each alert.
    # Keys with a "labels." or "annotations." prefix read from the corresponding
    # source only.  Bare keys first check labels, then fall back to annotations.
    # Dots in the original key are replaced with "__" for safe dataIndex access.
    for a in all_alerts:
        alert_labels = a.get("labels", {})
        alert_annotations = a.get("annotations", {})
        for dc in merged_display_columns:
            raw_key = dc["key"]
            if raw_key.startswith("labels."):
                value = alert_labels.get(raw_key[7:], "")
            elif raw_key.startswith("annotations."):
                value = alert_annotations.get(raw_key[12:], "")
            else:
                value = alert_labels.get(raw_key) or alert_annotations.get(raw_key) or ""
            safe_key = "_d_" + raw_key.replace(".", "__")
            a[safe_key] = value

    # Sort: disaster > emergency > critical > important > warning > info
    severity_order = {"disaster": 0, "emergency": 1, "critical": 2, "important": 3, "warning": 4, "info": 5}
    all_alerts.sort(key=lambda a: (
        severity_order.get(a.get("labels", {}).get("severity", "").lower(), 3),
        a.get("activeAt", ""),
    ))

    return dict(
        configured=True,
        has_prometheus=has_prometheus,
        display_columns=merged_display_columns,
        alerts=all_alerts,
    )
