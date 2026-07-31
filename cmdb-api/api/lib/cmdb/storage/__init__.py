# -*- coding:utf-8 -*-
from api.core.context import current_app


def get_storage_backend(backend_name=None):
    """Factory: resolve backend name -> StorageBackend instance.
    Falls back to global FILE_STORAGE_BACKEND when backend_name is None/empty.
    """
    if not backend_name:
        backend_name = current_app.config.get('FILE_STORAGE_BACKEND', 'local')

    if backend_name == 's3':
        from api.lib.cmdb.storage.s3_storage import S3Storage
        return S3Storage()
    else:
        from api.lib.cmdb.storage.local import LocalStorage
        return LocalStorage()
