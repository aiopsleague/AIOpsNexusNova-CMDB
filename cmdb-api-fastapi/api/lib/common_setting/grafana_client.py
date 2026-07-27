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
        """Return template variables of a dashboard (datasource excluded)
        as [{"name", "description"}]."""
        resp = requests.get("{}/api/dashboards/uid/{}".format(self.url, name),
                            headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        templating = (resp.json().get("dashboard") or {}).get("templating") or {}
        return [{"name": v.get("name"), "description": v.get("description") or ""}
                for v in (templating.get("list") or [])
                if v.get("name") and v.get("type") != "datasource"]


def _slug_from(dash):
    # grafana /api/search returns "url" like "/d/<uid>/<slug>"
    parts = (dash.get("url") or "").strip("/").split("/")
    return parts[-1] if len(parts) >= 3 else None


def rewrite_dashboard_html(html, proxy_prefix):
    """Rewrite the grafana index page so all relative asset URLs (via <base>)
    and frontend API calls (via bootData appSubUrl) go through the proxy.

    :param html: grafana index.html text
    :param proxy_prefix: e.g. "/api/v0.1/grafana/proxy/1" (no trailing slash)
    """
    prefix = proxy_prefix.rstrip("/")
    html = html.replace('<base href="/" />', '<base href="{}/" />'.format(prefix))
    html = html.replace('<base href="/">', '<base href="{}/">'.format(prefix))
    html = html.replace('"appSubUrl":""', '"appSubUrl":"{}"'.format(prefix))
    return html


def _first_hit(search_fn, connection):
    try:
        dashboards = search_fn(connection) or []
    except Exception:
        return None
    return dashboards[0] if dashboards else None


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
    mapping = next((m for m in mappings
                    if m.get("ci_type_id") == ci_type_id and m.get("enable", 1) != 0), None)
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


def build_vars(mapping, ci, unique_value):
    """Build the template-var list for the iframe url.

    var_mapping item: {"grafana_var", "map_type": "field"|"fixed", "value", "remark", "var_type"}
    旧格式 {"grafana_var", "ci_attr"} 按 field + value=ci_attr 兼容读取。

    Returns list of {"name", "value", "var_type"} dicts.
    """
    if not mapping:
        return [dict(name=DEFAULT_VAR_NAME, value=unique_value, var_type="normal")]
    vars_ = []
    for vm in mapping.get("var_mapping") or []:
        name = vm.get("grafana_var")
        value_ref = vm.get("value", vm.get("ci_attr"))
        var_type = vm.get("var_type") or "normal"
        if not name:
            continue
        if (vm.get("map_type") or "field") == "fixed":
            if value_ref is None or value_ref == "":
                continue
            vars_.append(dict(name=name, value=value_ref, var_type=var_type))
        else:
            value = ci.get(value_ref or "")
            if value is None or value == "" or value == []:
                continue
            vars_.append(dict(name=name, value=value, var_type=var_type))
    return vars_
