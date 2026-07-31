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

DATA_TYPE = "FileStorage"
MASKED_SECRET = "******"

DEFAULT_CONFIG = {
    "storage_backend": "local",
    "local_path": "./uploaded_files/ci_files",
    "s3_endpoint_url": "",
    "s3_access_key": "",
    "s3_secret_key": "",
    "s3_bucket_name": "cmdb-files",
    "s3_region": "us-east-1",
    "s3_use_ssl": True,
    "allowed_extensions": [
        "txt", "pdf", "png", "jpg", "jpeg", "gif", "webp", "bmp",
        "xls", "xlsx", "doc", "docx", "ppt", "pptx", "csv", "json",
        "zip", "rar", "7z", "log",
    ],
    "max_file_size_mb": 50,
}


class FileStorageConfigCRUD(object):
    """File storage config in one CommonData record (data_type='FileStorage'),
    AES-encrypted. Follows the same pattern as GrafanaConfigCRUD.
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
            current_app.logger.error("Failed to decrypt file storage config: %s", e)
            abort(400, ErrFormat.file_storage_config_broken)
        # Merge with defaults for any missing keys
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
        """Return config with masked secret_key for API responses."""
        config = self.get_config()
        return self._mask_secrets(config)

    @staticmethod
    def _mask_secrets(config):
        """Mask sensitive fields for API responses."""
        masked = dict(config)
        if masked.get("s3_secret_key"):
            masked["s3_secret_key"] = MASKED_SECRET
        return masked

    def update_config(self, data):
        """Merge partial update into the stored config.

        When storage_backend is 's3', validates required S3 fields.
        """
        if not isinstance(data, dict):
            abort(400, ErrFormat.value_is_required)

        current = self.get_config()

        # Merge top-level fields
        for key in DEFAULT_CONFIG:
            if key in data:
                current[key] = data[key]

        # Validate S3 fields when backend is 's3'
        if current.get("storage_backend") == "s3":
            if not (current.get("s3_endpoint_url") or "").strip():
                abort(400, ErrFormat.file_storage_s3_endpoint_required)

        # Preserve existing secret key if masked value was sent back
        if data.get("s3_secret_key") == MASKED_SECRET:
            # Keep the existing secret key from stored config
            pass

        self._save(current)
        return self._mask_secrets(current)

    def test_s3_connection(self, data):
        """Test S3 connectivity with the provided credentials.

        Args:
            data: dict with s3 fields (endpoint_url, access_key, secret_key,
                  bucket_name, region, use_ssl)

        Returns:
            dict: {"ok": bool, "error": str}
        """
        import boto3
        from botocore.config import Config as BotoConfig

        endpoint_url = (data.get("s3_endpoint_url") or "").strip()
        access_key = (data.get("s3_access_key") or "").strip()
        secret_key = data.get("s3_secret_key") or ""

        if not endpoint_url:
            abort(400, ErrFormat.file_storage_s3_endpoint_required)
        if not access_key:
            abort(400, ErrFormat.value_is_required)

        # If the masked secret was passed, use the stored one
        if secret_key == MASKED_SECRET:
            secret_key = self.get_config().get("s3_secret_key") or ""

        try:
            client = boto3.client(
                's3',
                endpoint_url=endpoint_url or None,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=(data.get("s3_region") or "us-east-1").strip(),
                use_ssl=data.get("s3_use_ssl", True),
                config=BotoConfig(
                    signature_version='s3v4',
                    connect_timeout=5,
                    read_timeout=5,
                    retries={'max_attempts': 1},
                ),
            )
            bucket = (data.get("s3_bucket_name") or "cmdb-files").strip()
            client.head_bucket(Bucket=bucket)
            return {"ok": True, "error": ""}
        except Exception as e:
            logger.warning("S3 connection test failed: %s", e)
            return {"ok": False, "error": str(e)}

    def get_allowed_extensions(self):
        """Get allowed extensions from common settings.

        Used by CIFileManager as a global fallback.
        Returns a set of extension strings, or None if not configured.
        """
        try:
            config = self.get_config()
            exts = config.get("allowed_extensions")
            if exts and isinstance(exts, list) and len(exts) > 0:
                return set(exts)
        except Exception:
            pass
        return None

    def get_storage_backend_name(self):
        """Get storage backend name from common settings.

        Used by CIFileManager as a global fallback.
        Returns backend name string, or None if not configured.
        """
        try:
            config = self.get_config()
            backend = config.get("storage_backend")
            if backend:
                return backend
        except Exception:
            pass
        return None

    def get_max_file_size_mb(self):
        """Get max file size from common settings.

        Returns size in MB, or None if not configured.
        """
        try:
            config = self.get_config()
            size = config.get("max_file_size_mb")
            if size is not None:
                return int(size)
        except Exception:
            pass
        return None
