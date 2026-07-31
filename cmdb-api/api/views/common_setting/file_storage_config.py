# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.lib.common_setting.file_storage import FileStorageConfigCRUD
from api.lib.perm.acl.acl import role_required
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/file_storage'


@router.get(f'{prefix}')
@role_required("acl_admin")
def file_storage_config_get():
    """Get file storage configuration (secrets masked)."""
    return FileStorageConfigCRUD().get_public_config()


@router.put(f'{prefix}')
@role_required("acl_admin")
def file_storage_config_put():
    """Update file storage configuration (partial merge)."""
    data = (request.json or {}).get('data', request.json or {})
    return FileStorageConfigCRUD().update_config(data)


@router.post(f'{prefix}/test')
@role_required("acl_admin")
def file_storage_test_post():
    """Test S3 connectivity with provided credentials."""
    data = (request.json or {}).get('data', request.json or {})
    return FileStorageConfigCRUD().test_s3_connection(data)
