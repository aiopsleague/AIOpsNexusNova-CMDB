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
