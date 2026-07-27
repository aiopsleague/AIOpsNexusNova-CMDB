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

    def search_dashboard(self, query, limit=5000):
        """Return list of dashboard dicts ({uid, title, url, ...})."""
        resp = requests.get("{}/api/search".format(self.url),
                            params={"query": query, "type": "dash-db", "limit": limit},
                            headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def list_dashboards(self, namespace="default"):
        """Return [{"name", "title"}] via the k8s-style API with pagination;
        fall back to classic /api/search on 404 (older grafana)."""
        base_url = "{}/apis/dashboard.grafana.app/v2alpha1/namespaces/{}/dashboards".format(
            self.url, namespace)
        params = {"limit": 5}
        all_items = []
        while True:
            resp = requests.get(base_url, headers=self._headers(),
                                params=params, timeout=self.timeout)
            
            if resp.status_code == 404:
                if all_items:
                    break
                return [{"name": d.get("uid"), "title": d.get("title")}
                        for d in self.search_dashboard("")]
            resp.raise_for_status()
            body = resp.json()
            items = body.get("items") or []
            all_items.extend(items)
            continue_token = (body.get("metadata") or {}).get("continue")
            if not continue_token or not items:
                break
            params = {"continue": continue_token}

        return [{"name": i.get("metadata", {}).get("name"),
                 "title": i.get("spec", {}).get("title") or i.get("metadata", {}).get("name")}
                for i in all_items]

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


def evaluate_filter_rules(filter_rules, ci_attrs):
    """Evaluate whether a CI instance matches the filter rules.

    :param filter_rules: dict {"logic": "and"|"or", "rules": [...]} or None
    :param ci_attrs: dict of CI attribute name -> value
    :return: True if the CI matches (or no rules defined), False otherwise
    """
    if not filter_rules or not filter_rules.get("rules"):
        return True

    results = []
    for rule in filter_rules["rules"]:
        field_value = str(ci_attrs.get(rule.get("field", ""), "") or "")
        target = rule.get("value")
        op = rule.get("operator", "equal")

        if op == "equal":
            results.append(field_value == str(target))
        elif op == "not_equal":
            results.append(field_value != str(target))
        elif op == "contains":
            results.append(str(target) in field_value)
        elif op == "not_contains":
            results.append(str(target) not in field_value)
        elif op == "in":
            results.append(field_value in (target if isinstance(target, list) else []))
        elif op == "not_in":
            results.append(field_value not in (target if isinstance(target, list) else []))
        else:
            results.append(False)

    if not results:
        return True

    if filter_rules.get("logic") == "or":
        return any(results)
    else:  # "and" (default)
        return all(results)


def pick_dashboard(connections, mappings, ci_type_id, ci_attrs, unique_value, search_fn):
    """Decide which grafana dashboard to show for a CI.

    :param connections: list of {"id", "name", "url", "api_key", "remark", "enable"?}
    :param mappings: list of {"id", "ci_type_id", "connection_id", "dashboard_name", "var_mapping",
                              "filter_rules"?}
    :param ci_type_id: int, the CI's type id
    :param ci_attrs: dict of CI attribute name -> value
    :param unique_value: str, the CI's unique attribute value (search keyword)
    :param search_fn: callable(connection) -> list of dashboard dicts; may raise
    :return: dict(connection=..., uid=..., slug=..., mapping=...|None) or None
    """
    enabled = [c for c in connections if c.get("enable", 1) != 0]
    if not enabled:
        return None

    # Collect enabled mappings for this CI type, split into filtered and fallback groups
    type_mappings = [m for m in mappings
                     if m.get("ci_type_id") == ci_type_id and m.get("enable", 1) != 0]
    filtered = [m for m in type_mappings if m.get("filter_rules") and m["filter_rules"].get("rules")]
    fallback = [m for m in type_mappings if not m.get("filter_rules") or not m["filter_rules"].get("rules")]

    searched_ids = set()

    def _resolve(mapping):
        conn = next((c for c in enabled if c.get("id") == mapping.get("connection_id")), None)
        if not conn:
            return None
        name = (mapping.get("dashboard_name") or "").strip()
        if name:
            return dict(connection=conn, uid=name, slug=None, mapping=mapping)
        searched_ids.add(conn.get("id"))
        dash = _first_hit(search_fn, conn)
        if dash:
            return dict(connection=conn, uid=dash.get("uid"), slug=_slug_from(dash), mapping=mapping)
        return None

    # 1. Priority: filter_rules match
    for mapping in filtered:
        if evaluate_filter_rules(mapping.get("filter_rules"), ci_attrs):
            result = _resolve(mapping)
            if result:
                return result

    # 2. Fallback: no filter_rules (catch-all for this CI type)
    for mapping in fallback:
        result = _resolve(mapping)
        if result:
            return result

    # 3. Global fallback: search all connections
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
