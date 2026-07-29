# -*- coding:utf-8 -*-
import json

from api.core.context import current_app
from api.core.errors import abort
from api.extensions import db
from api.lib.common_setting.prometheus_client import PrometheusClient
from api.lib.common_setting.resp_format import ErrFormat
from api.lib.utils import AESCrypto
from api.models.common_setting import CommonData

DATA_TYPE = "Prometheus"
AUTH_MASK = "******"

VALID_AUTH_TYPES = {"none", "bearer", "basic"}
VALID_MAP_TYPES = {"field", "fixed"}


class PrometheusConfigCRUD(object):
    """All Prometheus config lives in ONE common_data record
    (data_type='Prometheus'), AES-encrypted as a whole, shaped:
    {"connections": [...], "mappings": [...]}.
    """

    @staticmethod
    def _get_record(to_dict=False):
        return CommonData.get_by(first=True, data_type=DATA_TYPE, to_dict=to_dict)

    def get_config(self):
        record = self._get_record(to_dict=True)
        if not record:
            return {"connections": [], "mappings": []}
        try:
            config = json.loads(AESCrypto().decrypt(record.get("data") or ""))
        except Exception as e:
            current_app.logger.error("Failed to decrypt prometheus config: %s", e)
            abort(400, ErrFormat.prometheus_config_broken)
        config.setdefault("connections", [])
        config.setdefault("mappings", [])
        return config

    def _save(self, config):
        encrypted = AESCrypto().encrypt(json.dumps(config))
        record = self._get_record(to_dict=False)
        try:
            if record:
                return record.update(data=encrypted)
            return CommonData.create(data_type=DATA_TYPE, data=encrypted)
        except Exception as e:
            db.session.rollback()
            abort(400, str(e))

    @staticmethod
    def _next_id(items):
        return max([i.get("id", 0) for i in items] or [0]) + 1

    @staticmethod
    def _to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            abort(400, ErrFormat.value_is_required)

    @staticmethod
    def _to_enable(value):
        return 0 if value in (0, "0", False) else 1

    @staticmethod
    def _mask_auth(connection):
        masked = dict(connection)
        if connection.get("auth_type") in ("bearer", "basic"):
            masked.setdefault("auth_data", {})
            masked["auth_data"] = dict(masked["auth_data"] or {})
            if masked["auth_data"]:
                masked["auth_data"]["token"] = AUTH_MASK if masked["auth_data"].get("token") else ""
                masked["auth_data"]["password"] = AUTH_MASK if masked["auth_data"].get("password") else ""
        return masked

    # ---------------- connections ----------------

    def list_connections(self):
        result = []
        for c in self.get_config()["connections"]:
            masked = self._mask_auth(c)
            masked["enable"] = self._to_enable(c.get("enable", 1))
            result.append(masked)
        return result

    def get_connection(self, _id):
        _id = self._to_int(_id)
        connection = next((c for c in self.get_config()["connections"] if c.get("id") == _id), None)
        if not connection:
            abort(404, ErrFormat.prometheus_connection_not_found.format(_id))
        return connection

    def create_connection(self, data):
        if not (data.get("name") or "").strip():
            abort(400, ErrFormat.prometheus_name_required)
        if not (data.get("url") or "").strip():
            abort(400, ErrFormat.prometheus_url_required)

        auth_type = (data.get("auth_type") or "none").strip()
        if auth_type not in VALID_AUTH_TYPES:
            abort(400, "invalid auth_type: {}".format(auth_type))

        connection = dict(
            id=self._next_id(self.get_config()["connections"]),
            name=data["name"].strip(),
            url=data["url"].strip().rstrip("/"),
            auth_type=auth_type,
            auth_data=data.get("auth_data") or {},
            enable=self._to_enable(data.get("enable", 1)),
            remark=(data.get("remark") or "").strip(),
        )
        config = self.get_config()
        config["connections"].append(connection)
        self._save(config)
        return self._mask_auth(connection)

    def update_connection(self, _id, data):
        _id = self._to_int(_id)
        config = self.get_config()
        connection = next((c for c in config["connections"] if c.get("id") == _id), None)
        if not connection:
            abort(404, ErrFormat.prometheus_connection_not_found.format(_id))

        if "name" in data:
            if not (data["name"] or "").strip():
                abort(400, ErrFormat.prometheus_name_required)
            connection["name"] = data["name"].strip()
        if "url" in data:
            if not (data["url"] or "").strip():
                abort(400, ErrFormat.prometheus_url_required)
            connection["url"] = data["url"].strip().rstrip("/")
        if "auth_type" in data:
            auth_type = (data["auth_type"] or "none").strip()
            if auth_type not in VALID_AUTH_TYPES:
                abort(400, "invalid auth_type: {}".format(auth_type))
            connection["auth_type"] = auth_type
        if "auth_data" in data and data["auth_data"]:
            connection.setdefault("auth_data", {})
            if isinstance(data["auth_data"], dict):
                for k, v in data["auth_data"].items():
                    if v:
                        connection["auth_data"][k] = v
        if "remark" in data:
            connection["remark"] = (data["remark"] or "").strip()
        if "enable" in data:
            connection["enable"] = self._to_enable(data["enable"])

        self._save(config)
        return self._mask_auth(connection)

    def delete_connection(self, _id):
        _id = self._to_int(_id)
        config = self.get_config()
        before = len(config["connections"])
        config["connections"] = [c for c in config["connections"] if c.get("id") != _id]
        if len(config["connections"]) == before:
            abort(404, ErrFormat.prometheus_connection_not_found.format(_id))
        config["mappings"] = [m for m in config["mappings"] if m.get("connection_id") != _id]
        self._save(config)

    def test_connection(self, url, auth_type, auth_data):
        if not (url or "").strip():
            abort(400, ErrFormat.prometheus_url_required)
        try:
            PrometheusClient(url.strip(), auth_type or 'none', auth_data or {}).health_check()
        except Exception as e:
            abort(400, ErrFormat.prometheus_test_failed.format(str(e)))

    def check_health(self):
        result = []
        for c in self.get_config()["connections"]:
            try:
                PrometheusClient(c["url"], c.get("auth_type"), c.get("auth_data")).health_check()
                result.append({"id": c["id"], "ok": True, "error": ""})
            except Exception as e:
                result.append({"id": c["id"], "ok": False, "error": str(e)})
        return result

    # ---------------- mappings ----------------

    @staticmethod
    def _valid_label_mapping(label_mapping):
        label_mapping = label_mapping or []
        if not isinstance(label_mapping, list):
            abort(400, ErrFormat.value_is_required)
        result = []
        for lm in label_mapping:
            if not isinstance(lm, dict):
                abort(400, ErrFormat.value_is_required)
            prom_label = str((lm or {}).get("prom_label") or "").strip()
            if not prom_label:
                abort(400, ErrFormat.prometheus_label_mapping_required)
            map_type = lm.get("map_type") or "field"
            if map_type not in VALID_MAP_TYPES:
                abort(400, ErrFormat.value_is_required)
            value = str(lm.get("value") or "").strip()
            if not value:
                abort(400, ErrFormat.value_is_required)
            result.append({"prom_label": prom_label, "map_type": map_type, "value": value})
        return result

    @staticmethod
    def _valid_display_columns(display_columns):
        """Validate and normalise display_columns list.

        Each entry must be a dict with a non-empty ``key``.
        ``title_zh`` and ``title_en`` default to ``key`` when omitted.
        """
        if display_columns is None:
            return []
        if not isinstance(display_columns, list):
            abort(400, ErrFormat.value_is_required)
        result = []
        for dc in display_columns:
            if not isinstance(dc, dict):
                abort(400, ErrFormat.value_is_required)
            key = str((dc or {}).get("key") or "").strip()
            if not key:
                abort(400, ErrFormat.value_is_required)
            result.append({
                "key": key,
                "title_zh": str(dc.get("title_zh") or key).strip(),
                "title_en": str(dc.get("title_en") or key).strip(),
            })
        return result

    def list_mappings(self):
        mappings = self.get_config()["mappings"]
        result = []
        for m in mappings:
            entry = dict(m)
            entry["enable"] = self._to_enable(m.get("enable", 1))
            result.append(entry)
        return result

    def create_mapping(self, data):
        ci_type_id = data.get("ci_type_id")
        connection_id = data.get("connection_id")
        if not ci_type_id or not connection_id:
            abort(400, ErrFormat.value_is_required)
        ci_type_id = self._to_int(ci_type_id)
        connection_id = self._to_int(connection_id)

        config = self.get_config()
        if not any(c.get("id") == connection_id for c in config["connections"]):
            abort(404, ErrFormat.prometheus_connection_not_found.format(connection_id))

        mapping = dict(
            id=self._next_id(config["mappings"]),
            ci_type_id=ci_type_id,
            connection_id=connection_id,
            label_mapping=self._valid_label_mapping(data.get("label_mapping")),
            display_columns=self._valid_display_columns(data.get("display_columns")),
            enable=self._to_enable(data.get("enable", 1)),
        )
        config["mappings"].append(mapping)
        self._save(config)
        return mapping

    def update_mapping(self, _id, data):
        _id = self._to_int(_id)
        config = self.get_config()
        mapping = next((m for m in config["mappings"] if m.get("id") == _id), None)
        if not mapping:
            abort(404, ErrFormat.prometheus_mapping_not_found.format(_id))

        if "ci_type_id" in data and data["ci_type_id"]:
            mapping["ci_type_id"] = self._to_int(data["ci_type_id"])
        if "connection_id" in data and data["connection_id"]:
            connection_id = self._to_int(data["connection_id"])
            if not any(c.get("id") == connection_id for c in config["connections"]):
                abort(404, ErrFormat.prometheus_connection_not_found.format(connection_id))
            mapping["connection_id"] = connection_id
        if "label_mapping" in data:
            mapping["label_mapping"] = self._valid_label_mapping(data["label_mapping"])
        if "display_columns" in data:
            mapping["display_columns"] = self._valid_display_columns(data["display_columns"])
        if "enable" in data:
            mapping["enable"] = self._to_enable(data["enable"])

        self._save(config)
        return mapping

    def delete_mapping(self, _id):
        _id = self._to_int(_id)
        config = self.get_config()
        before = len(config["mappings"])
        config["mappings"] = [m for m in config["mappings"] if m.get("id") != _id]
        if len(config["mappings"]) == before:
            abort(404, ErrFormat.prometheus_mapping_not_found.format(_id))
        self._save(config)
