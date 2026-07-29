# -*- coding:utf-8 -*-
import base64

import requests


class PrometheusClient(object):
    """Lightweight HTTP client for the Prometheus HTTP API.

    Parameters
    ----------
    url : str
        Prometheus base URL, e.g. ``http://localhost:9090``.
    auth_type : str
        ``none`` (default), ``bearer``, or ``basic``.
    auth_data : dict | None
        Required keys depend on auth_type:
        - bearer: ``{"token": "..."}``
        - basic: ``{"username": "...", "password": "..."}``
    timeout : int
        Request timeout in seconds (default 5).
    """

    def __init__(self, url, auth_type='none', auth_data=None, timeout=5):
        self.url = url.rstrip('/')
        self.auth_type = auth_type or 'none'
        self.auth_data = auth_data or {}
        self.timeout = timeout

    def _headers(self):
        """Build request headers with auth."""
        headers = {'Accept': 'application/json'}
        if self.auth_type == 'bearer':
            token = self.auth_data.get('token', '')
            headers['Authorization'] = 'Bearer {}'.format(token)
        elif self.auth_type == 'basic':
            username = self.auth_data.get('username', '')
            password = self.auth_data.get('password', '')
            if username or password:
                creds = base64.b64encode('{}:{}'.format(username, password).encode('utf-8')).decode('utf-8')
                headers['Authorization'] = 'Basic {}'.format(creds)
        return headers

    def health_check(self):
        """Return True if Prometheus is reachable and healthy.

        Calls ``GET /-/healthy``.
        """
        resp = requests.get(
            '{}/-/healthy'.format(self.url),
            headers=self._headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return True

    def query_alerts(self, labels):
        """Query firing alerts matching the given label matchers.

        Parameters
        ----------
        labels : dict
            Label matchers, e.g. ``{"instance": "10.0.0.1", "job": "node"}``.

        Returns
        -------
        list[dict]
            Normalised alert dicts from ``/api/v1/alerts``.
            Returns empty list on any error (never raises).
        """
        if not labels:
            return []

        matchers = []
        for k, v in labels.items():
            matchers.append('{}="{}"'.format(k, v))
        filter_expr = '{' + ','.join(matchers) + '}'

        try:
            resp = requests.get(
                '{}/api/v1/alerts'.format(self.url),
                headers=self._headers(),
                params={'filter': filter_expr},
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except Exception:
            return []

        data = resp.json()
        if data.get('status') != 'success':
            return []

        alerts = data.get('data', {}).get('alerts', [])
        result = []
        for a in alerts:
            if a.get('state') != 'firing':
                continue
            result.append({
                'fingerprint': a.get('fingerprint', ''),
                'labels': a.get('labels', {}),
                'annotations': a.get('annotations', {}),
                'state': a.get('state', 'firing'),
                'activeAt': a.get('activeAt', ''),
                'value': a.get('value', ''),
            })
        return result
