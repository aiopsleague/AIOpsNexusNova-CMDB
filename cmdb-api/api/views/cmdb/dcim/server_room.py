# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.lib.cmdb.dcim.server_room import ServerRoomManager
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.decorator import args_required
from api.lib.perm.auth import authenticate

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/dcim/server_room")
@router.get("/dcim/server_room/{_id}")
@router.get("/dcim/server_room/{_id}/racks")
def server_room_view_get(_id: int = None):
    q = request.values.get('q')
    counter, result = ServerRoomManager.get_racks(_id, q)

    return dict(counter=counter, result=result)


@router.post("/dcim/server_room")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
@args_required("parent_id")
def server_room_view_post():
    parent_id = request.values.pop("parent_id")

    return dict(ci_id=ServerRoomManager().add(parent_id, **request.values))


@router.put("/dcim/server_room/{_id}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
def server_room_view_put(_id: int = None):
    ServerRoomManager().update(_id, **request.values)

    return dict(ci_id=_id)


@router.delete("/dcim/server_room/{_id}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
def server_room_view_delete(_id: int = None):
    ServerRoomManager().delete(_id)

    return dict(ci_id=_id)
