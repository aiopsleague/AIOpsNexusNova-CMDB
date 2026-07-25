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


def test_pick_dashboard_skips_disabled_mapping():
    mappings = [{"id": 1, "ci_type_id": 3, "connection_id": 2, "dashboard_name": "xyz",
                 "var_mapping": [], "enable": 0}]
    picked = pick_dashboard([CONN1, CONN2], mappings, 3, "host-01", _ok_search([DASH]))
    # 映射停用 → 视同无映射 → 全局搜索（CONN1 先命中）
    assert picked["connection"] is CONN1
    assert picked["mapping"] is None


def test_pick_dashboard_all_disabled():
    assert pick_dashboard([CONN3_DISABLED], [], 3, "host-01", _ok_search([DASH])) is None


# ---------------- build_vars ----------------

def test_build_vars_fallback_without_mapping():
    assert build_vars(None, {}, "host-01") == [{"name": "ci_name", "value": "host-01"}]


def test_build_vars_field_and_fixed():
    mapping = {"var_mapping": [
        {"grafana_var": "instance", "map_type": "field", "value": "ip", "remark": ""},
        {"grafana_var": "env", "map_type": "fixed", "value": "prod", "remark": ""},
    ]}
    ci = {"ip": "10.0.0.1"}
    assert build_vars(mapping, ci, "x") == [{"name": "instance", "value": "10.0.0.1"},
                                            {"name": "env", "value": "prod"}]


def test_build_vars_legacy_ci_attr_compat():
    mapping = {"var_mapping": [{"grafana_var": "instance", "ci_attr": "ip"}]}
    ci = {"ip": "10.0.0.1"}
    assert build_vars(mapping, ci, "x") == [{"name": "instance", "value": "10.0.0.1"}]


def test_build_vars_skips_empty_values():
    mapping = {"var_mapping": [
        {"grafana_var": "a", "map_type": "field", "value": "x"},
        {"grafana_var": "b", "map_type": "field", "value": "y"},
        {"grafana_var": "c", "map_type": "field", "value": "z"},
        {"grafana_var": "d", "map_type": "field", "value": "w"},
        {"grafana_var": "e", "map_type": "fixed", "value": ""},
        {"grafana_var": "f", "map_type": "fixed", "value": "keep"},
    ]}
    ci = {"x": "", "y": None, "z": [], "w": "keep"}
    assert build_vars(mapping, ci, "v") == [{"name": "d", "value": "keep"},
                                            {"name": "f", "value": "keep"}]


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


def test_get_dashboard_variables_with_description():
    client = GrafanaClient("http://g:3000/", "key")
    payload = {"dashboard": {"templating": {"list": [
        {"name": "instance", "type": "query", "description": "实例IP"},
        {"name": "datasource", "type": "datasource"},
        {"name": "maintype", "type": "query"},
        {"type": "query"},
    ]}}}
    with mock.patch("api.lib.common_setting.grafana_client.requests.get") as m:
        m.return_value.json.return_value = payload
        m.return_value.raise_for_status.return_value = None
        result = client.get_dashboard_variables("rYdddlPWo")
    assert result == [{"name": "instance", "description": "实例IP"},
                      {"name": "maintype", "description": ""}]
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
