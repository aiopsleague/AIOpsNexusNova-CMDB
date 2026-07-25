# -*- coding:utf-8 -*-
import json

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
        except Exception:
            return {"connections": [], "mappings": []}
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
    def _mask(connection):
        masked = dict(connection)
        masked["api_key"] = API_KEY_MASK if connection.get("api_key") else ""
        return masked

    # ---------------- connections ----------------

    def list_connections(self):
        return [self._mask(c) for c in self.get_config()["connections"]]

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
                          remark=(data.get("remark") or "").strip())
        config["connections"].append(connection)
        self._save(config)
        return self._mask(connection)

    def update_connection(self, _id, data):
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

        self._save(config)
        return self._mask(connection)

    def delete_connection(self, _id):
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

    # ---------------- mappings ----------------

    def list_mappings(self):
        return self.get_config()["mappings"]

    def create_mapping(self, data):
        ci_type_id = data.get("ci_type_id")
        connection_id = data.get("connection_id")
        if not ci_type_id or not connection_id:
            abort(400, ErrFormat.value_is_required)

        config = self.get_config()
        if not any(c.get("id") == connection_id for c in config["connections"]):
            abort(404, ErrFormat.grafana_connection_not_found.format(connection_id))

        mapping = dict(id=self._next_id(config["mappings"]),
                       ci_type_id=int(ci_type_id),
                       connection_id=int(connection_id),
                       dashboard_uid=(data.get("dashboard_uid") or "").strip(),
                       var_name=(data.get("var_name") or "").strip() or "ci_name")
        config["mappings"].append(mapping)
        self._save(config)
        return mapping

    def update_mapping(self, _id, data):
        config = self.get_config()
        mapping = next((m for m in config["mappings"] if m.get("id") == _id), None)
        if not mapping:
            abort(404, ErrFormat.grafana_mapping_not_found.format(_id))

        if "ci_type_id" in data and data["ci_type_id"]:
            mapping["ci_type_id"] = int(data["ci_type_id"])
        if "connection_id" in data and data["connection_id"]:
            if not any(c.get("id") == data["connection_id"] for c in config["connections"]):
                abort(404, ErrFormat.grafana_connection_not_found.format(data["connection_id"]))
            mapping["connection_id"] = int(data["connection_id"])
        if "dashboard_uid" in data:
            mapping["dashboard_uid"] = (data["dashboard_uid"] or "").strip()
        if "var_name" in data:
            mapping["var_name"] = (data["var_name"] or "").strip() or "ci_name"

        self._save(config)
        return mapping

    def delete_mapping(self, _id):
        config = self.get_config()
        before = len(config["mappings"])
        config["mappings"] = [m for m in config["mappings"] if m.get("id") != _id]
        if len(config["mappings"]) == before:
            abort(404, ErrFormat.grafana_mapping_not_found.format(_id))
        self._save(config)
