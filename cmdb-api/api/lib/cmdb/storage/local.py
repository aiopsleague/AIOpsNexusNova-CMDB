# -*- coding:utf-8 -*-
import os
import uuid
from datetime import datetime
from io import BytesIO
from urllib.parse import quote

from api.core.context import current_app
from api.lib.cmdb.storage.base import StorageBackend


class LocalStorage(StorageBackend):

    def _get_abs_path(self, file_path):
        base = current_app.config.get('FILE_STORAGE_LOCAL_PATH', './uploaded_files/ci_files')
        return os.path.join(base, file_path)

    def _validate_path(self, stored_path):
        """Ensure stored_path resolves inside the base directory."""
        base = os.path.realpath(current_app.config.get('FILE_STORAGE_LOCAL_PATH', './uploaded_files/ci_files'))
        abs_path = os.path.realpath(self._get_abs_path(stored_path))
        if not abs_path.startswith(base + os.sep):
            raise ValueError(f"Invalid path: {stored_path}")
        return abs_path

    def upload(self, file_data: bytes, file_path: str = None, mime_type: str = 'application/octet-stream') -> dict:
        # generate dated path: YYYY/MM/DD/uuid_filename
        now = datetime.now()
        date_prefix = now.strftime('%Y/%m/%d')
        uid = str(uuid.uuid4())[:8]
        safe_name = file_path if file_path else f"{uid}.bin"
        if file_path and '.' in file_path:
            name, ext = file_path.rsplit('.', 1)
            safe_name = f"{uid}_{name}.{ext}"
        stored_path = os.path.join(date_prefix, safe_name)

        abs_path = self._validate_path(stored_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'wb') as f:
            f.write(file_data)

        return {"stored_path": stored_path, "size": len(file_data)}

    def download(self, stored_path: str) -> tuple:
        abs_path = self._validate_path(stored_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {stored_path}")
        filename = os.path.basename(stored_path)
        mime_type = 'application/octet-stream'
        with open(abs_path, 'rb') as f:
            data = f.read()
        return BytesIO(data), filename, mime_type

    def delete(self, stored_path: str) -> bool:
        abs_path = self._validate_path(stored_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
            return True
        return False

    def get_url(self, stored_path: str, expires: int = 3600) -> str:
        return f"/api/v0.1/ci/files?path={quote(stored_path, safe='')}"
