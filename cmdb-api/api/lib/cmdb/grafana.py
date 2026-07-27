# -*- coding:utf-8 -*-
from api.core.context import current_app
from api.core.errors import abort

from api.lib.cmdb.cache import AttributeCache
from api.lib.cmdb.cache import CITypeCache
from api.lib.cmdb.ci import CIManager
from api.lib.cmdb.resp_format import ErrFormat
from api.lib.common_setting.grafana import GrafanaConfigCRUD
from api.lib.common_setting.grafana_client import build_vars
from api.lib.common_setting.grafana_client import GrafanaClient
from api.lib.common_setting.grafana_client import pick_dashboard
from api.models.cmdb import CI


def check_ci_type_monitoring(ci_type_id):
    """Check whether a CI type has any monitoring dashboard mapping configured.

    Returns ``{"has_monitoring": bool}`` so the frontend can decide whether
    to show the monitoring tab.  Currently only Grafana mappings are checked;
    Zabbix and other tools will be added here when implemented.
    """
    from api.lib.common_setting.grafana import GrafanaConfigCRUD

    config = GrafanaConfigCRUD().get_config()
    connections = config.get("connections", [])
    if not connections:
        return {"has_monitoring": False}

    mappings = config.get("mappings", [])
    type_mappings = [
        m for m in mappings
        if m.get("ci_type_id") == ci_type_id and m.get("enable", 1) != 0
    ]
    return {"has_monitoring": len(type_mappings) > 0}


def resolve_ci_grafana(ci_id):
    """Return monitoring dashboard info for the CI detail page.

    Returns ``{"configured": bool, "has_monitoring": bool, "tool_type": str|None, "result": {...}|None}``.
    ``has_monitoring`` indicates whether the CI's type has any monitoring mapping;
    ``tool_type`` is the monitoring tool type (currently always ``"grafana"`` when a
    dashboard is resolved).
    """
    ci_obj = CI.get_by_id(ci_id) or abort(404, ErrFormat.ci_not_found.format("id={}".format(ci_id)))
    CIManager.valid_ci_only_read(ci_obj)

    config = GrafanaConfigCRUD().get_config()
    connections = config["connections"]
    mappings = config["mappings"]

    ci = CIManager.get_ci_by_id(ci_id, need_children=False)
    ci_type_id = ci["_type"]

    # Determine whether this CI type has any monitoring mapping at all
    type_mappings = [m for m in mappings
                     if m.get("ci_type_id") == ci_type_id and m.get("enable", 1) != 0]
    has_monitoring = bool(connections and type_mappings)

    if not connections:
        return dict(configured=False, has_monitoring=False, tool_type=None, result=None)

    ci_type = CITypeCache.get(ci_type_id)
    unique_attr = AttributeCache.get(ci_type.unique_id) if ci_type else None
    unique_value = ci.get(unique_attr.name) if unique_attr else None
    if not unique_value:
        current_app.logger.warning("ci {} has no unique value, skip grafana resolve".format(ci_id))
        return dict(configured=True, has_monitoring=has_monitoring, tool_type=None, result=None)

    def search_fn(connection):
        return GrafanaClient(connection["url"], connection["api_key"], timeout=2).search_dashboard(str(unique_value))

    try:
        picked = pick_dashboard(connections, mappings, ci_type_id, ci, str(unique_value), search_fn)
    except Exception as e:
        current_app.logger.warning("grafana resolve failed for ci {}: {}".format(ci_id, e))
        return dict(configured=True, has_monitoring=has_monitoring, tool_type=None, result=None)

    if not picked:
        return dict(configured=True, has_monitoring=has_monitoring, tool_type=None, result=None)

    return dict(configured=True, has_monitoring=has_monitoring, tool_type="grafana", result=dict(
        connection_id=picked["connection"]["id"],
        grafana_url=picked["connection"]["url"],
        uid=picked["uid"],
        slug=picked["slug"],
        vars=build_vars(picked["mapping"], ci, str(unique_value)),
    ))
