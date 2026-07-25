# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request

from api.lib.cmdb.ipam.address import IpAddressManager
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.decorator import args_required
from api.lib.perm.auth import authenticate
from api.lib.utils import handle_arg_list

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/ipam/address")
@args_required("parent_id")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def ip_address_view_get():
    parent_id = request.args.get("parent_id")

    numfound, result = IpAddressManager.list_ip_address(parent_id)

    return dict(numfound=numfound, result=result)


@router.post("/ipam/address")
@args_required("ips")
@args_required("assign_status", value_required=False)
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def ip_address_view_post():
    ips = handle_arg_list(request.values.pop("ips"))
    parent_id = request.values.pop("parent_id", None)
    cidr = request.values.pop("cidr", None)

    IpAddressManager().assign_ips(ips, parent_id, cidr, **request.values)

    return dict(code=200)
