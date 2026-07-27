# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.lib.cmdb.dcim.region import RegionManager
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.perm.auth import authenticate

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


@router.post("/dcim/region")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
def region_view_post():
    return dict(ci_id=RegionManager().add(**request.values))


@router.put("/dcim/region/{_id}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
def region_view_put(_id: int = None):
    RegionManager().update(_id, **request.values)

    return dict(ci_id=_id)


@router.delete("/dcim/region/{_id}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
def region_view_delete(_id: int = None):
    RegionManager().delete(_id)

    return dict(ci_id=_id)
