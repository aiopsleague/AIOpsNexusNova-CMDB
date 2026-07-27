# -*- coding:utf-8 -*- 


import datetime

from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import request

from api.lib.cmdb.ci import CIManager
from api.lib.cmdb.const import PermEnum
from api.lib.cmdb.const import ResourceTypeEnum
from api.lib.cmdb.history import AttributeHistoryManger
from api.lib.cmdb.history import CITriggerHistoryManager
from api.lib.cmdb.history import CITypeHistoryManager
from api.lib.cmdb.resp_format import ErrFormat
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.perm.acl.acl import has_perm_from_args
from api.lib.perm.auth import authenticate
from api.lib.utils import get_page
from api.lib.utils import get_page_size

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/history/records/relation")
@router.get("/history/records/attribute")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Operation_Audit,
                     app_cli.op.read, app_cli.admin_name)
def record_view_get():
    page = get_page(request.values.get("page", 1))
    page_size = get_page_size(request.values.get("page_size"))
    _start = request.values.get("start")
    _end = request.values.get("end")
    username = request.values.get("username", "")
    operate_type = request.values.get("operate_type", "")
    type_id = request.values.get("type_id")
    start, end = None, None
    if _start:
        try:
            start = datetime.datetime.strptime(_start, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return abort(400, ErrFormat.datetime_argument_invalid.format('start'))
    if _end:
        try:
            end = datetime.datetime.strptime(_end, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return abort(400, ErrFormat.datetime_argument_invalid.format('start'))

    if "attribute" in request.url:
        total, res = AttributeHistoryManger.get_records_for_attributes(start, end, username, page, page_size,
                                                                       operate_type,
                                                                       type_id,
                                                                       request.values.get('ci_id'),
                                                                       request.values.get('attr_id'))
        return dict(records=res,
                    total=total,
                    **request.values)
    else:
        total, res, cis = AttributeHistoryManger.get_records_for_relation(start, end, username, page, page_size,
                                                                          operate_type,
                                                                          type_id,
                                                                          request.values.get('first_ci_id'),
                                                                          request.values.get('second_ci_id'))

        return dict(records=res,
                    total=total,
                    cis=cis,
                    **request.values)


@router.get("/history/ci/{ci_id}")
@has_perm_from_args("ci_id", ResourceTypeEnum.CI, PermEnum.READ, CIManager.get_type_name)
def ci_history_view_get(ci_id: int):
    result = AttributeHistoryManger.get_by_ci_id(ci_id)

    return result


@router.get("/history/ci_triggers/{ci_id}")
@has_perm_from_args("ci_id", ResourceTypeEnum.CI, PermEnum.READ, CIManager.get_type_name)
def ci_trigger_history_view_get(ci_id: int):
    result = CITriggerHistoryManager.get_by_ci_id(ci_id)

    return result


@router.get("/history/ci_triggers")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Operation_Audit,
                     app_cli.op.read, app_cli.admin_name)
def cis_trigger_history_view_get():
    type_id = request.values.get("type_id")
    trigger_id = request.values.get("trigger_id")
    operate_type = request.values.get("operate_type")

    page = get_page(request.values.get('page', 1))
    page_size = get_page_size(request.values.get('page_size', 1))

    numfound, result = CITriggerHistoryManager.get(page,
                                                   page_size,
                                                   type_id=type_id,
                                                   trigger_id=trigger_id,
                                                   operate_type=operate_type)

    return dict(page=page,
                page_size=page_size,
                numfound=numfound,
                total=len(result),
                result=result)


@router.get("/history/ci_types")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Operation_Audit,
                     app_cli.op.read, app_cli.admin_name)
def ci_type_history_view_get():
    type_id = request.values.get("type_id")
    username = request.values.get("username")
    operate_type = request.values.get("operate_type")

    page = get_page(request.values.get('page', 1))
    page_size = get_page_size(request.values.get('page_size', 1))

    numfound, result = CITypeHistoryManager.get(page, page_size, username,
                                                type_id=type_id, operate_type=operate_type)

    return dict(page=page,
                page_size=page_size,
                numfound=numfound,
                total=len(result),
                result=result)
