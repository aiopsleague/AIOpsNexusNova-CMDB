# -*- coding:utf-8 -*-


from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request

from api.lib.cmdb.ipam.stats import Stats
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.decorator import args_required
from api.lib.perm.auth import authenticate

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/ipam/stats")
@args_required("parent_id")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def ipam_stats_view_get():
    parent_id = request.values.get("parent_id")

    return dict(Stats().summary(parent_id))
