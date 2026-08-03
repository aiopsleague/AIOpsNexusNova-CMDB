# -*- coding:utf-8 -*-
import json
import logging

from api.core.context import current_app
from api.core.errors import abort
from api.extensions import db
from api.lib.common_setting.resp_format import ErrFormat
from api.lib.utils import AESCrypto
from api.models.common_setting import CommonData

logger = logging.getLogger('cmdb')

DATA_TYPE = "FilePreview"

DEFAULT_CONFIG = {
    "preview_server_url": "http://127.0.0.1:8012/onlinePreview",
    "force_updated_cache_types": [
        "txt", "html", "htm", "asp", "jsp", "xml", "json", "properties",
        "md", "gitignore", "log", "java", "py", "c", "cpp", "sql", "sh",
        "bat", "m", "bas", "prg", "cmd",
    ],
}


class FilePreviewConfigCRUD(object):
    """File preview (kkFileView) config in one CommonData record
    (data_type='FilePreview'), AES-encrypted. Follows the same pattern as
    FileStorageConfigCRUD.
    """

    @staticmethod
    def _get_record(to_dict=False):
        return CommonData.get_by(first=True, data_type=DATA_TYPE, to_dict=to_dict)

    def get_config(self):
        """Return the full config dict with defaults filled in."""
        record = self._get_record(to_dict=True)
        if not record:
            return dict(DEFAULT_CONFIG)
        try:
            config = json.loads(AESCrypto().decrypt(record.get("data") or ""))
        except Exception as e:
            current_app.logger.error("Failed to decrypt file preview config: %s", e)
            abort(400, ErrFormat.file_preview_config_broken)
        result = dict(DEFAULT_CONFIG)
        result.update(config)
        return result

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

    def get_public_config(self):
        """Return the config dict. No secrets stored, so it can be returned
        as-is (available to any authenticated user for the preview component)."""
        return self.get_config()

    def update_config(self, data):
        """Merge partial update into the stored config and validate."""
        if not isinstance(data, dict):
            abort(400, ErrFormat.value_is_required)

        current = self.get_config()
        for key in DEFAULT_CONFIG:
            if key in data:
                current[key] = data[key]

        if not (current.get("preview_server_url") or "").strip():
            abort(400, ErrFormat.file_preview_server_url_required)

        self._save(current)
        return self.get_public_config()

    def test_preview_server(self, preview_server_url):
        """Test kkFileView server reachability.

        Args:
            preview_server_url: e.g. "http://127.0.0.1:8012/onlinePreview"

        Returns:
            dict: {"ok": bool, "error": str}
        """
        import requests

        url = (preview_server_url or "").strip()
        if not url:
            abort(400, ErrFormat.file_preview_server_url_required)

        # Reach the kkFileView server root (strip the /onlinePreview endpoint),
        # since the endpoint itself 4xx's without query params.
        base = url.split("?")[0].rstrip("/")
        for suffix in ("/onlinePreview", "/online"):
            if base.endswith(suffix):
                base = base[: -len(suffix)]
                break
        if not base.startswith(("http://", "https://")):
            base = "http://" + base

        try:
            resp = requests.get(base, timeout=5, allow_redirects=True)
            if resp.status_code < 500:
                return {"ok": True, "error": ""}
            return {"ok": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            logger.warning("File preview server test failed: %s", e)
            return {"ok": False, "error": str(e)}
