# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.lib.cmdb.const import CMDB_QUEUE
from api.lib.cmdb.dcim.const import RackBuiltinAttributes
from api.lib.cmdb.dcim.rack import RackManager
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.decorator import args_required
from api.lib.perm.auth import authenticate
from api.tasks.cmdb import dcim_calc_u_free_count

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


# NOTE(fastapi-port): ``{_id:int}``/``{rack_id:int}``/``{device_id:int}`` use the
# starlette int convertor to mirror flask's ``<int:...>``, so that the static
# path ``/dcim/rack/calc_u_free_count`` and the ``/migrate`` suffix are not
# shadowed by ``/dcim/rack/{_id}`` regardless of registration order.


@router.post("/dcim/rack")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
@args_required("parent_id")
def rack_view_post():
    parent_id = request.values.pop("parent_id")

    return dict(ci_id=RackManager().add(parent_id, **request.values))


@router.put("/dcim/rack/{_id:int}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
def rack_view_put(_id: int = None):
    RackManager().update(_id, **request.values)

    return dict(ci_id=_id)


@router.delete("/dcim/rack/{_id:int}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
def rack_view_delete(_id: int = None):
    RackManager().delete(_id)

    return dict(ci_id=_id)


@router.post("/dcim/rack/{rack_id:int}/device/{device_id:int}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
@args_required(RackBuiltinAttributes.U_START)
def rack_detail_view_post(rack_id: int = None, device_id: int = None):
    u_start = request.values.pop(RackBuiltinAttributes.U_START)
    u_count = request.values.get(RackBuiltinAttributes.U_COUNT)

    RackManager().add_device(rack_id, device_id, u_start, u_count)

    return dict(rack_id=rack_id, device_id=device_id)


@router.put("/dcim/rack/{rack_id:int}/device/{device_id:int}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
@args_required("to_u_start")
def rack_detail_view_put(rack_id: int = None, device_id: int = None):
    to_u_start = request.values.pop("to_u_start")

    RackManager().move_device(rack_id, device_id, to_u_start)

    return dict(rack_id=rack_id, device_id=device_id, to_u_start=to_u_start)


@router.delete("/dcim/rack/{rack_id:int}/device/{device_id:int}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
def rack_detail_view_delete(rack_id: int = None, device_id: int = None):
    RackManager().remove_device(rack_id, device_id)

    return dict(code=200)


@router.put("/dcim/rack/{rack_id:int}/device/{device_id:int}/migrate")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
@args_required("to_rack_id")
@args_required("to_u_start")
def rack_device_migrate_view_put(rack_id: int = None, device_id: int = None):
    to_rack_id = request.values.pop("to_rack_id")
    to_u_start = request.values.pop("to_u_start")

    RackManager().migrate_device(rack_id, device_id, to_rack_id, to_u_start)

    return dict(rack_id=rack_id,
                device_id=device_id,
                to_u_start=to_u_start,
                to_rack_id=to_rack_id)


@router.post("/dcim/rack/calc_u_free_count")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.DCIM,
                     app_cli.op.read, app_cli.admin_name)
def rack_calc_u_free_count_view_post():
    dcim_calc_u_free_count.apply_async(queue=CMDB_QUEUE)

    return dict(code=200)
