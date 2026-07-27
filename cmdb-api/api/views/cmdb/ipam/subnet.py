# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request

from api.lib.cmdb.ipam.subnet import SubnetManager
from api.lib.cmdb.ipam.subnet import SubnetScopeManager
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.decorator import args_required
from api.lib.perm.auth import authenticate

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


# NOTE(fastapi-port): ``/ipam/subnet/hosts`` is registered before
# ``/ipam/subnet/{_id:int}`` to mirror flask's routing; the int convertor
# mirrors flask's ``<int:_id>``.


@router.get("/ipam/subnet/hosts")
@router.get("/ipam/subnet/{_id:int}")
@router.get("/ipam/subnet")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def subnet_view_get(_id: int = None):
    if "hosts" in request.url:
        return SubnetManager.get_hosts(request.values.get('cidr'))

    if _id is not None:
        return SubnetManager().get_by_id(_id)

    result, type2name = SubnetManager().tree_view()

    return dict(result=result, type2name=type2name)


@router.post("/ipam/subnet")
@args_required("cidr")
@args_required("parent_id", value_required=False)
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def subnet_view_post():
    cidr = request.values.pop("cidr")
    parent_id = request.values.pop("parent_id")
    agent_id = request.values.pop("agent_id", None)
    cron = request.values.pop("cron", None)

    return SubnetManager().add(cidr, parent_id, agent_id, cron, **request.values)


@router.put("/ipam/subnet/{_id:int}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def subnet_view_put(_id: int = None):
    return dict(id=SubnetManager().update(_id, **request.values))


@router.delete("/ipam/subnet/{_id:int}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def subnet_view_delete(_id: int = None):
    return dict(id=SubnetManager().delete(_id))


@router.put("/ipam/subnet/{_id:int}/move")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def subnet_move_view_put(_id: int = None):
    return dict(id=SubnetManager().move(_id, request.values.get('target_parent_id')))


@router.post("/ipam/scope")
@args_required("parent_id", value_required=False)
@args_required("name")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def subnet_scope_view_post():
    parent_id = request.values.pop("parent_id")
    name = request.values.pop("name")

    return SubnetScopeManager().add(parent_id, name)


@router.put("/ipam/scope/{_id:int}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def subnet_scope_view_put(_id: int = None):
    return dict(id=SubnetScopeManager().update(_id, **request.values))


@router.delete("/ipam/scope/{_id:int}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.IPAM,
                     app_cli.op.read, app_cli.admin_name)
def subnet_scope_view_delete(_id: int = None):
    return dict(id=SubnetScopeManager.delete(_id))
