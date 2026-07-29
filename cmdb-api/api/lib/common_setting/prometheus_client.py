# -*- coding:utf-8 -*-
import base64
import hashlib
import json

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

    @staticmethod
    def _compute_fingerprint(labels):
        """Compute a stable fingerprint from alert labels.

        The standard Prometheus ``/api/v1/alerts`` response does not include a
        ``fingerprint`` field, so we compute one client-side by hashing the
        sorted label key-value pairs.  This produces a consistent identifier
        suitable for deduplication.
        """
        sorted_str = json.dumps(labels, sort_keys=True, separators=(',', ':'))
        return hashlib.md5(sorted_str.encode('utf-8')).hexdigest()

    @staticmethod
    def _labels_match(alert_labels, matchers):
        """Return True if *alert_labels* satisfy all *matchers*.

        Each matcher value is compared for exact string equality against the
        corresponding label in the alert.
        """
        for k, v in matchers.items():
            if alert_labels.get(k) != v:
                return False
        return True

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

        The Prometheus ``/api/v1/alerts`` endpoint does not natively support
        server-side label filtering, so this method fetches **all** active
        alerts and filters them client-side.

        Parameters
        ----------
        labels : dict
            Label matchers, e.g. ``{"instance": "10.0.0.1", "job": "node"}``.
            An alert is included only when its labels contain **all** of the
            specified key-value pairs (exact match).

        Returns
        -------
        list[dict]
            Normalised alert dicts from ``/api/v1/alerts``.
            Returns empty list on any error (never raises).
        """
        if not labels:
            return []

        try:
            resp = requests.get(
                '{}/api/v1/alerts'.format(self.url),
                headers=self._headers(),
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
            alert_labels = a.get('labels', {})
            if not self._labels_match(alert_labels, labels):
                continue
            result.append({
                'fingerprint': a.get('fingerprint') or self._compute_fingerprint(alert_labels),
                'labels': alert_labels,
                'annotations': a.get('annotations', {}),
                'state': a.get('state', 'firing'),
                'activeAt': a.get('activeAt', ''),
                'value': a.get('value', ''),
            })
        return result
