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
        return GrafanaClient(connection["url"], connection["api_key"], timeout=2).search_dashboard(str(unique_value))

    try:
        picked = pick_dashboard(connections, config["mappings"], ci_type_id, str(unique_value), search_fn)
    except Exception as e:
        current_app.logger.warning("grafana resolve failed for ci {}: {}".format(ci_id, e))
        return dict(configured=True, result=None)

    if not picked:
        return dict(configured=True, result=None)

    return dict(configured=True, result=dict(
        connection_id=picked["connection"]["id"],
        grafana_url=picked["connection"]["url"],
        uid=picked["uid"],
        slug=picked["slug"],
        var_name=picked["var_name"],
        var_value=picked["var_value"],
    ))
