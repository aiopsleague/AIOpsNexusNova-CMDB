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
