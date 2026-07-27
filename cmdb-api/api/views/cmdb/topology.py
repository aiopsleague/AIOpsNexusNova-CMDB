# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import request

from api.lib.cmdb.const import PermEnum, ResourceTypeEnum
from api.lib.cmdb.resp_format import ErrFormat
from api.lib.cmdb.topology import TopologyViewManager
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.decorator import args_required
from api.lib.decorator import args_validate
from api.lib.perm.acl.acl import ACLManager
from api.lib.perm.acl.acl import has_perm_from_args
from api.lib.perm.acl.acl import is_app_admin
from api.lib.perm.auth import authenticate

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


# NOTE(fastapi-port): views with static paths are defined before
# ``/topology_views/{_id}`` so that starlette's registration-order matching
# does not shadow them (werkzeug ranked static rules above dynamic ones).


@router.post("/topology_views/groups/order")
@args_required('group_ids')
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.TopologyView,
                     app_cli.op.update_topology_group, app_cli.admin_name)
def topology_group_order_view_post():
    group_ids = request.values.get('group_ids')

    TopologyViewManager.group_order(group_ids)

    return dict(group_ids=group_ids)


@router.put("/topology_views/groups/order")
def topology_group_order_view_put():
    return topology_group_order_view_post()


@router.post("/topology_views/groups/{group_id}")
@router.post("/topology_views/groups")
@args_required('name')
@args_validate(TopologyViewManager.group_cls)
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.TopologyView,
                     app_cli.op.create_topology_group, app_cli.admin_name)
def topology_group_view_post(group_id: int = None):
    name = request.values.get('name')
    order = request.values.get('order')

    group = TopologyViewManager.add_group(name, order)

    return group.to_dict()


@router.put("/topology_views/groups/{group_id}")
@router.put("/topology_views/groups")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.TopologyView,
                     app_cli.op.update_topology_group, app_cli.admin_name)
def topology_group_view_put(group_id: int = None):
    name = request.values.get('name')
    view_ids = request.values.get('view_ids')
    group = TopologyViewManager().update_group(group_id, name, view_ids)

    return dict(**group)


@router.delete("/topology_views/groups/{group_id}")
@router.delete("/topology_views/groups")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.TopologyView,
                     app_cli.op.delete_topology_group, app_cli.admin_name)
def topology_group_view_delete(group_id: int = None):
    TopologyViewManager.delete_group(group_id)

    return dict(group_id=group_id)


@router.post("/topology_views/order")
@args_required('view_ids')
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.TopologyView,
                     app_cli.op.create_topology_view, app_cli.admin_name)
def topology_order_view_post():
    view_ids = request.values.get('view_ids')

    TopologyViewManager.group_inner_order(view_ids)

    return dict(view_ids=view_ids)


@router.put("/topology_views/order")
def topology_order_view_put():
    return topology_order_view_post()


@router.get("/topology_views/{_id}/view")
@router.get("/topology_views/preview")
def topology_view_preview_get(_id: int = None):
    if _id is not None:
        acl = ACLManager('cmdb')
        resource_name = TopologyViewManager.get_name_by_id(_id)
        if (not acl.has_permission(resource_name, ResourceTypeEnum.TOPOLOGY_VIEW, PermEnum.READ) and
                not is_app_admin('cmdb')):
            return abort(403, ErrFormat.no_permission.format(resource_name, PermEnum.READ))

        return TopologyViewManager().topology_view(view_id=_id)
    else:
        return TopologyViewManager().topology_view(preview=request.values)


@router.post("/topology_views/{_id}/view")
@router.post("/topology_views/preview")
def topology_view_preview_post(_id: int = None):
    return topology_view_preview_get(_id)


@router.get("/topology_views/{_id}")
@router.get("/topology_views/relations/ci_types/{type_id}")
@router.get("/topology_views")
def topology_view_get(type_id: int = None, _id: int = None):
    if type_id is not None:
        return TopologyViewManager.relation_from_ci_type(type_id)

    if _id is not None:
        return TopologyViewManager().get_view_by_id(_id)

    return TopologyViewManager.get_all()


@router.post("/topology_views/{_id}")
@router.post("/topology_views/relations/ci_types/{type_id}")
@router.post("/topology_views")
@args_required('name', 'central_node_type', 'central_node_instances', 'path', 'group_id')
@args_validate(TopologyViewManager.cls)
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.TopologyView,
                     app_cli.op.create_topology_view, app_cli.admin_name)
def topology_view_post(type_id: int = None, _id: int = None):
    name = request.values.pop('name')
    group_id = request.values.pop('group_id', None)
    option = request.values.pop('option', None)
    order = request.values.pop('order', None)

    topo_view = TopologyViewManager.add(name, group_id, option, order, **request.values)

    return topo_view


@router.put("/topology_views/{_id}")
@router.put("/topology_views/relations/ci_types/{type_id}")
@router.put("/topology_views")
@args_validate(TopologyViewManager.cls)
@has_perm_from_args("_id", ResourceTypeEnum.TOPOLOGY_VIEW, PermEnum.UPDATE, TopologyViewManager.get_name_by_id)
def topology_view_put(type_id: int = None, _id: int = None):
    topo_view = TopologyViewManager.update(_id, **request.values)

    return topo_view


@router.delete("/topology_views/{_id}")
@router.delete("/topology_views/relations/ci_types/{type_id}")
@router.delete("/topology_views")
@has_perm_from_args("_id", ResourceTypeEnum.TOPOLOGY_VIEW, PermEnum.DELETE, TopologyViewManager.get_name_by_id)
def topology_view_delete(type_id: int = None, _id: int = None):
    TopologyViewManager.delete(_id)

    return dict(code=200)


@router.post("/topology_views/{view_id}/roles/{rid}/grant")
def topology_view_grant_view_post(view_id: int, rid: int):
    perms = request.values.pop('perms', None)

    view_name = TopologyViewManager.get_name_by_id(view_id) or abort(404, ErrFormat.not_found)
    acl = ACLManager('cmdb')
    if not acl.has_permission(view_name, ResourceTypeEnum.TOPOLOGY_VIEW,
                              PermEnum.GRANT) and not is_app_admin('cmdb'):
        return abort(403, ErrFormat.no_permission.format(view_name, PermEnum.GRANT))

    acl.grant_resource_to_role_by_rid(view_name, rid, ResourceTypeEnum.TOPOLOGY_VIEW, perms, rebuild=True)

    return dict(code=200)


@router.post("/topology_views/{view_id}/roles/{rid}/revoke")
@args_required('perms')
def topology_view_revoke_view_post(view_id: int, rid: int):
    perms = request.values.pop('perms', None)

    view_name = TopologyViewManager.get_name_by_id(view_id) or abort(404, ErrFormat.not_found)
    acl = ACLManager('cmdb')
    if not acl.has_permission(view_name, ResourceTypeEnum.TOPOLOGY_VIEW,
                              PermEnum.GRANT) and not is_app_admin('cmdb'):
        return abort(403, ErrFormat.no_permission.format(view_name, PermEnum.GRANT))

    acl.revoke_resource_from_role_by_rid(view_name, rid, ResourceTypeEnum.TOPOLOGY_VIEW, perms, rebuild=True)

    return dict(code=200)
