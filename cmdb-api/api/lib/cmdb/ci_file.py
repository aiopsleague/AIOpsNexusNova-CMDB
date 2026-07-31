# -*- coding:utf-8 -*-
import logging

from api.core.context import current_app
from api.lib.cmdb.cache import AttributeCache
from api.lib.cmdb.storage import get_storage_backend

logger = logging.getLogger('cmdb')

# Default allowed extensions when no config is set
DEFAULT_ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp',
    'xls', 'xlsx', 'doc', 'docx', 'ppt', 'pptx', 'csv', 'json',
    'zip', 'rar', '7z', 'log',
}

DEFAULT_MAX_FILE_SIZE_MB = 50


class CIFileManager(object):

    def get_storage_backend_for_attr(self, attr_id=None):
        """Resolve storage backend: attribute-level -> global -> default."""
        backend_name = None
        if attr_id:
            attr = AttributeCache.get(attr_id)
            if attr and attr.option:
                file_storage = attr.option.get('file_storage', {})
                backend_name = file_storage.get('backend')
        return get_storage_backend(backend_name)

    def _get_allowed_extensions(self, attr_id=None):
        attr_extensions = None
        if attr_id:
            attr = AttributeCache.get(attr_id)
            if attr and attr.option:
                file_storage = attr.option.get('file_storage', {})
                attr_extensions = file_storage.get('allowed_extensions')
        if attr_extensions is not None:
            return set(attr_extensions)
        return current_app.config.get('FILE_ALLOWED_EXTENSIONS', DEFAULT_ALLOWED_EXTENSIONS)

    def _get_max_file_size(self, attr_id=None):
        attr_limit = None
        if attr_id:
            attr = AttributeCache.get(attr_id)
            if attr and attr.option:
                file_storage = attr.option.get('file_storage', {})
                attr_limit = file_storage.get('max_file_size_mb')
        if attr_limit is not None:
            return int(attr_limit) * 1024 * 1024
        return DEFAULT_MAX_FILE_SIZE_MB * 1024 * 1024

    def upload_files(self, files, attr_id=None):
        """Upload one or more files.

        Args:
            files: list of file objects (with .filename, .read())
            attr_id: optional attribute id for config resolution

        Returns:
            list[dict]: [{"original_name": str, "stored_path": str, "size": int, "mime_type": str}, ...]
        """
        backend = self.get_storage_backend_for_attr(attr_id)
        allowed_extensions = self._get_allowed_extensions(attr_id)
        max_size = self._get_max_file_size(attr_id)

        results = []
        for file in files:
            filename = file.filename if hasattr(file, 'filename') else 'unknown'
            extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if extension not in allowed_extensions:
                raise ValueError(f"File type .{extension} is not allowed")

            file_data = file.read()
            if len(file_data) > max_size:
                raise ValueError(f"File {filename} exceeds max size limit")

            mime_type = getattr(file, 'content_type', 'application/octet-stream')
            result = backend.upload(file_data, filename, mime_type)
            result['original_name'] = filename
            result['mime_type'] = mime_type
            results.append(result)

        return results

    def get_file(self, stored_path):
        """Download a file by its stored path.

        Returns:
            tuple: (BytesIO_stream, filename, mime_type)
        """
        backend = get_storage_backend()
        return backend.download(stored_path)

    def delete_files(self, paths):
        """Delete files by their stored paths.

        Args:
            paths: list of stored_path strings

        Returns:
            int: number of successfully deleted files
        """
        backend = get_storage_backend()
        deleted = 0
        for path in paths:
            try:
                if backend.delete(path):
                    deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete file {path}: {e}")
        return deleted
