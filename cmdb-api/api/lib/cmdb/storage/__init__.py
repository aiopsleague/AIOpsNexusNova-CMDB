# -*- coding:utf-8 -*-
from api.core.context import current_app


def get_storage_backend(backend_name=None):
    """Factory: resolve backend name -> StorageBackend instance.

    Resolution order: explicit arg -> common settings (DB) -> settings.py -> local.
    """
    if not backend_name:
        # Try DB common settings first (user-configurable via UI)
        try:
            from api.lib.common_setting.file_storage import FileStorageConfigCRUD
            common_backend = FileStorageConfigCRUD().get_storage_backend_name()
            if common_backend:
                backend_name = common_backend
        except Exception:
            pass
    if not backend_name:
        backend_name = current_app.config.get('FILE_STORAGE_BACKEND', 'local')

    if backend_name == 's3':
        from api.lib.cmdb.storage.s3_storage import S3Storage
        return S3Storage()
    else:
        from api.lib.cmdb.storage.local import LocalStorage
        return LocalStorage()
