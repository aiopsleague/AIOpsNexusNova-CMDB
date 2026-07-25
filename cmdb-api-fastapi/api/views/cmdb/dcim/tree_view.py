# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.lib.cmdb.dcim.tree_view import TreeViewManager
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.perm.auth import authenticate

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/dcim/tree_view")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
def dcim_tree_view_get():
    result, type2name = TreeViewManager.get()

    return dict(result=result, type2name=type2name)
