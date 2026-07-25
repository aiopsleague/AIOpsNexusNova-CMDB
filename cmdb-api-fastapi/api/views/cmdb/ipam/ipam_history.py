# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request

from api.lib.cmdb.ipam.history import OperateHistoryManager
from api.lib.cmdb.ipam.history import ScanHistoryManager
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.decorator import args_required
from api.lib.perm.auth import authenticate
from api.lib.utils import get_page
from api.lib.utils import get_page_size
from api.lib.utils import handle_arg_list

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/ipam/history/operate")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def ipam_operate_history_view_get():
    page = get_page(request.values.pop("page", 1))
    page_size = get_page_size(request.values.pop("page_size", None))
    operate_type = handle_arg_list(request.values.pop('operate_type', []))
    if operate_type:
        request.values["operate_type"] = operate_type

    numfound, result = OperateHistoryManager.search(page, page_size, **request.values)

    return dict(numfound=numfound, result=result)


@router.get("/ipam/history/scan")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def ipam_scan_history_view_get():
    page = get_page(request.values.pop("page", 1))
    page_size = get_page_size(request.values.pop("page_size", None))

    numfound, result = ScanHistoryManager.search(page, page_size, **request.values)

    return dict(numfound=numfound, result=result)


@router.post("/ipam/history/scan")
@args_required("exec_id")
def ipam_scan_history_view_post():
    ScanHistoryManager().add(**request.values)

    return dict(code=200)
