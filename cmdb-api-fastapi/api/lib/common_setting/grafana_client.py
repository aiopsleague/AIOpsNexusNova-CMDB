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

    searched_ids = set()
    mapping = next((m for m in mappings if m.get("ci_type_id") == ci_type_id), None)
    if mapping:
        conn = next((c for c in connections if c.get("id") == mapping.get("connection_id")), None)
        if conn:
            uid = (mapping.get("dashboard_uid") or "").strip()
            if uid:
                return _result(conn, uid, None, mapping.get("var_name"), unique_value)
            searched_ids.add(conn.get("id"))
            dash = _first_hit(search_fn, conn)
            if dash:
                return _result(conn, dash.get("uid"), _slug_from(dash),
                               mapping.get("var_name"), unique_value)
            # 映射实例搜不到 → 继续全局兜底

    for conn in connections:
        if conn.get("id") in searched_ids:
            continue
        dash = _first_hit(search_fn, conn)
        if dash:
            return _result(conn, dash.get("uid"), _slug_from(dash), None, unique_value)

    return None
