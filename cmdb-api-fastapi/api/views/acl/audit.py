# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.core.errors import abort

from api.lib.perm.acl.audit import AuditCRUD
from api.lib.perm.auth import authenticate
from api.lib.utils import get_page
from api.lib.utils import get_page_size

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/audit_log/{name}")
def audit_log_view_get(name: str = None):
    page = get_page(request.values.get("page", 1))
    page_size = get_page_size(request.values.get("page_size"))
    app_id = request.values.get('app_id')
    q = request.values.get('q')
    start = request.values.get('start')
    end = request.values.get('end')

    func_map = {
        'permission': AuditCRUD.search_permission,
        'role': AuditCRUD.search_role,
        'trigger': AuditCRUD.search_trigger,
        'resource': AuditCRUD.search_resource,
        'login': AuditCRUD.search_login,
    }
    if name not in func_map:
        abort(400, f'wrong {name}, please use {func_map.keys()}')

    _func = func_map[name]

    data = _func(app_id, q, page, page_size, start, end)

    return dict(
        page=page,
        page_size=page_size,
        **data,
    )
