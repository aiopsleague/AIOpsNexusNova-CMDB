# -*- coding:utf-8 -*-
import json

from api.core.context import current_app
from api.core.errors import abort
from api.extensions import db
from api.lib.common_setting.grafana_client import GrafanaClient
from api.lib.common_setting.resp_format import ErrFormat
from api.lib.utils import AESCrypto
from api.models.common_setting import CommonData

DATA_TYPE = "Grafana"
API_KEY_MASK = "******"


class GrafanaConfigCRUD(object):
    """All grafana config lives in ONE common_data record (data_type='Grafana'),
    AES-encrypted as a whole, shaped: {"connections": [...], "mappings": [...]}.
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
            # 解密/解析失败（例如 SECRET_KEY 变更）时不能返回空配置，
            # 否则后续写操作会用空配置覆盖已有记录，导致配置被清空
            current_app.logger.error("Failed to decrypt grafana config: %s", e)
            abort(400, ErrFormat.grafana_config_broken)
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
    def _mask(connection):
        masked = dict(connection)
        masked["api_key"] = API_KEY_MASK if connection.get("api_key") else ""
        return masked

    @staticmethod
    def _to_enable(value):
        return 0 if value in (0, "0", False) else 1

    # ---------------- connections ----------------

    def list_connections(self):
        result = []
        for c in self.get_config()["connections"]:
            masked = self._mask(c)
            masked["enable"] = self._to_enable(c.get("enable", 1))
            result.append(masked)
        return result

    def get_connection(self, _id):
        """Return the connection dict with PLAINTEXT api_key — backend internal use only."""
        _id = self._to_int(_id)
        connection = next((c for c in self.get_config()["connections"] if c.get("id") == _id), None)
        if not connection:
            abort(404, ErrFormat.grafana_connection_not_found.format(_id))
        return connection

    def create_connection(self, data):
        if not (data.get("name") or "").strip():
            abort(400, ErrFormat.grafana_name_required)
        if not (data.get("url") or "").strip():
            abort(400, ErrFormat.grafana_url_required)
        if not (data.get("api_key") or "").strip():
            abort(400, ErrFormat.grafana_api_key_required)

        config = self.get_config()
        connection = dict(id=self._next_id(config["connections"]),
                          name=data["name"].strip(),
                          url=data["url"].strip().rstrip("/"),
                          api_key=data["api_key"].strip(),
                          enable=self._to_enable(data.get("enable", 1)),
                          remark=(data.get("remark") or "").strip())
        config["connections"].append(connection)
        self._save(config)
        return self._mask(connection)

    def update_connection(self, _id, data):
        _id = self._to_int(_id)
        config = self.get_config()
        connection = next((c for c in config["connections"] if c.get("id") == _id), None)
        if not connection:
            abort(404, ErrFormat.grafana_connection_not_found.format(_id))

        if "name" in data:
            if not (data["name"] or "").strip():
                abort(400, ErrFormat.grafana_name_required)
            connection["name"] = data["name"].strip()
        if "url" in data:
            if not (data["url"] or "").strip():
                abort(400, ErrFormat.grafana_url_required)
            connection["url"] = data["url"].strip().rstrip("/")
        if (data.get("api_key") or "").strip():
            connection["api_key"] = data["api_key"].strip()
        if "remark" in data:
            connection["remark"] = (data["remark"] or "").strip()
        if "enable" in data:
            connection["enable"] = self._to_enable(data["enable"])

        self._save(config)
        return self._mask(connection)

    def delete_connection(self, _id):
        _id = self._to_int(_id)
        config = self.get_config()
        before = len(config["connections"])
        config["connections"] = [c for c in config["connections"] if c.get("id") != _id]
        if len(config["connections"]) == before:
            abort(404, ErrFormat.grafana_connection_not_found.format(_id))
        # 级联删除引用该实例的映射
        config["mappings"] = [m for m in config["mappings"] if m.get("connection_id") != _id]
        self._save(config)

    def test_connection(self, url, api_key):
        if not (url or "").strip():
            abort(400, ErrFormat.grafana_url_required)
        if not (api_key or "").strip():
            abort(400, ErrFormat.grafana_api_key_required)
        try:
            return GrafanaClient(url.strip(), api_key.strip()).test_connection()
        except Exception as e:
            abort(400, ErrFormat.grafana_test_failed.format(str(e)))

    def check_health(self):
        """Per-connection liveness: [{"id", "ok", "error"}]. Never raises."""
        result = []
        for c in self.get_config()["connections"]:
            try:
                GrafanaClient(c["url"], c["api_key"]).test_connection()
                result.append({"id": c["id"], "ok": True, "error": ""})
            except Exception as e:
                result.append({"id": c["id"], "ok": False, "error": str(e)})
        return result

    # ---------------- mappings ----------------

    def list_mappings(self):
        """Return mappings with normalized var_mapping items and enable field.

        Legacy stored data may still have ``{grafana_var, ci_attr}`` items;
        this normalizes every item to the extended shape so the frontend
        always receives a consistent format.
        """
        mappings = self.get_config()["mappings"]
        result = []
        for m in mappings:
            entry = dict(m)
            entry["enable"] = self._to_enable(m.get("enable", 1))
            normalized = []
            for vm in m.get("var_mapping") or []:
                normalized.append({
                    "grafana_var": vm.get("grafana_var", ""),
                    "map_type": vm.get("map_type") or "field",
                    "value": vm.get("value") or vm.get("ci_attr") or "",
                    "remark": vm.get("remark") or "",
                    "enable": 0 if vm.get("enable") in (0, "0", False) else 1,
                    "no_var_prefix": True if vm.get("no_var_prefix") in (True, 1, "1") else False,
                })
            entry["var_mapping"] = normalized
            result.append(entry)
        return result

    @staticmethod
    def _valid_var_mapping(var_mapping):
        """Validate and normalize var_mapping items.

        Supports both legacy ``{grafana_var, ci_attr}`` and extended
        ``{grafana_var, map_type, value, remark, enable}`` format.
        Always returns the extended (normalized) shape.
        """
        var_mapping = var_mapping or []
        if not isinstance(var_mapping, list):
            abort(400, ErrFormat.value_is_required)
        result = []
        for vm in var_mapping:
            if not isinstance(vm, dict):
                abort(400, ErrFormat.value_is_required)
            grafana_var = str((vm or {}).get("grafana_var") or "").strip()
            if not grafana_var:
                abort(400, ErrFormat.value_is_required)

            map_type = vm.get("map_type") or "field"
            if map_type not in ("field", "fixed"):
                abort(400, ErrFormat.value_is_required)

            # Backward compat: new "value" field takes precedence over legacy "ci_attr"
            value = str(vm.get("value") or vm.get("ci_attr") or "").strip()
            if not value:
                abort(400, ErrFormat.value_is_required)

            remark = str(vm.get("remark") or "").strip()
            enable = 0 if vm.get("enable") in (0, "0", False) else 1
            no_var_prefix = True if vm.get("no_var_prefix") in (True, 1, "1") else False

            result.append({
                "grafana_var": grafana_var,
                "map_type": map_type,
                "value": value,
                "remark": remark,
                "enable": enable,
                "no_var_prefix": no_var_prefix,
            })
        return result

    def create_mapping(self, data):
        ci_type_id = data.get("ci_type_id")
        connection_id = data.get("connection_id")
        dashboard_name = (data.get("dashboard_name") or "").strip()
        if not ci_type_id or not connection_id or not dashboard_name:
            abort(400, ErrFormat.value_is_required)
        ci_type_id = self._to_int(ci_type_id)
        connection_id = self._to_int(connection_id)

        config = self.get_config()
        if not any(c.get("id") == connection_id for c in config["connections"]):
            abort(404, ErrFormat.grafana_connection_not_found.format(connection_id))

        mapping = dict(id=self._next_id(config["mappings"]),
                       ci_type_id=ci_type_id,
                       connection_id=connection_id,
                       namespace=(data.get("namespace") or "").strip() or "default",
                       dashboard_name=dashboard_name,
                       dashboard_title=(data.get("dashboard_title") or "").strip(),
                       enable=self._to_enable(data.get("enable", 1)),
                       var_mapping=self._valid_var_mapping(data.get("var_mapping")))
        config["mappings"].append(mapping)
        self._save(config)
        return mapping

    def update_mapping(self, _id, data):
        _id = self._to_int(_id)
        config = self.get_config()
        mapping = next((m for m in config["mappings"] if m.get("id") == _id), None)
        if not mapping:
            abort(404, ErrFormat.grafana_mapping_not_found.format(_id))

        if "ci_type_id" in data and data["ci_type_id"]:
            mapping["ci_type_id"] = self._to_int(data["ci_type_id"])
        if "connection_id" in data and data["connection_id"]:
            connection_id = self._to_int(data["connection_id"])
            if not any(c.get("id") == connection_id for c in config["connections"]):
                abort(404, ErrFormat.grafana_connection_not_found.format(connection_id))
            mapping["connection_id"] = connection_id
        if "namespace" in data:
            mapping["namespace"] = (data["namespace"] or "").strip() or "default"
        if "dashboard_name" in data:
            if not (data["dashboard_name"] or "").strip():
                abort(400, ErrFormat.value_is_required)
            mapping["dashboard_name"] = data["dashboard_name"].strip()
        if "dashboard_title" in data:
            mapping["dashboard_title"] = (data["dashboard_title"] or "").strip()
        if "var_mapping" in data:
            mapping["var_mapping"] = self._valid_var_mapping(data["var_mapping"])
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
            abort(404, ErrFormat.grafana_mapping_not_found.format(_id))
        self._save(config)
