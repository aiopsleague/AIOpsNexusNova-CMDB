# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.lib.common_setting.file_preview import FilePreviewConfigCRUD
from api.lib.perm.acl.acl import role_required
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/file_preview'


@router.get(f'{prefix}')
def file_preview_config_get():
    """Get file preview configuration.

    Available to any authenticated user — the frontend preview component needs
    the kkFileView server address at runtime, not just admins.
    """
    return FilePreviewConfigCRUD().get_public_config()


@router.put(f'{prefix}')
@role_required("acl_admin")
def file_preview_config_put():
    """Update file preview configuration (partial merge)."""
    data = (request.json or {}).get('data', request.json or {})
    return FilePreviewConfigCRUD().update_config(data)


@router.post(f'{prefix}/test')
@role_required("acl_admin")
def file_preview_test_post():
    """Test kkFileView server reachability."""
    data = (request.json or {}).get('data', request.json or {})
    return FilePreviewConfigCRUD().test_preview_server(data.get("preview_server_url") or "")
