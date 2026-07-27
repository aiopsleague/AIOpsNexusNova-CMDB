# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import current_app
from api.core.context import request

from api.lib.decorator import args_required
from api.lib.perm.acl.acl import ACLManager
from api.lib.perm.acl.cache import AppCache
from api.lib.perm.acl.permission import PermissionCRUD
from api.lib.perm.acl.resp_format import ErrFormat
from api.lib.perm.auth import auth_only_for_acl
from api.lib.perm.auth import auth_with_app_token
from api.lib.perm.auth import authenticate
from api.lib.utils import handle_arg_list

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/resources/{resource_id}/permissions")
@router.get("/resource_groups/{group_id}/permissions")
@auth_with_app_token
def resource_permission_view_get(resource_id: int = None, group_id: int = None):
    need_users = request.values.get('need_users', 1) in current_app.config.get('BOOL_TRUE')
    return PermissionCRUD.get_all(resource_id, group_id, need_users=need_users)


@router.get("/resource/permissions")
@args_required('resource_name')
@args_required('resource_type_name')
@auth_with_app_token
def resource_permission2_view_get():
    resource_name = request.values.get('resource_name')
    resource_type_name = request.values.get('resource_type_name')
    app_id = request.values.get('app_id')

    return PermissionCRUD.get_all2(resource_name, resource_type_name, app_id)


# NOTE(fastapi-port): the batch routes (literal "batch" segment) are registered
# before the ``{resource_id}``/``{group_id}`` routes so that they win the match,
# mirroring flask's ``<int:>`` converter semantics.


@router.post('/roles/{rid}/resources/batch/grant')
@router.post('/roles/{rid}/resource_groups/batch/grant')
@auth_only_for_acl
def role_permission_batch_grant_view_post(rid: int = None):
    resource_ids = request.values.get('resource_ids')
    group_ids = request.values.get('group_ids')

    perms = handle_arg_list(request.values.get("perms"))

    if resource_ids and isinstance(resource_ids, list):
        for resource_id in resource_ids[:-1]:
            PermissionCRUD.grant(rid, perms, resource_id=resource_id, group_id=None, rebuild=False)
        PermissionCRUD.grant(rid, perms, resource_id=resource_ids[-1], group_id=None, rebuild=True)

    if group_ids and isinstance(group_ids, list):
        for group_id in group_ids[:-1]:
            PermissionCRUD.grant(rid, perms, resource_id=None, group_id=group_id, rebuild=False)
        PermissionCRUD.grant(rid, perms, resource_id=None, group_id=group_ids[-1], rebuild=True)

    return dict(rid=rid, resource_ids=resource_ids, group_ids=group_ids, perms=perms)


@router.post('/roles/{rid}/resources/batch/revoke')
@router.post('/roles/{rid}/resource_groups/batch/revoke')
@auth_only_for_acl
def role_permission_batch_revoke_view_post(rid: int = None):
    resource_ids = request.values.get('resource_ids')
    group_ids = request.values.get('group_ids')

    perms = handle_arg_list(request.values.get("perms"))

    if resource_ids and isinstance(resource_ids, list):
        for resource_id in resource_ids[:-1]:
            PermissionCRUD.revoke(rid, perms, resource_id=resource_id, group_id=None, rebuild=False)
        PermissionCRUD.revoke(rid, perms, resource_id=resource_ids[-1], group_id=None, rebuild=True)

    if group_ids and isinstance(group_ids, list):
        for group_id in group_ids[:-1]:
            PermissionCRUD.revoke(rid, perms, resource_id=None, group_id=group_id, rebuild=False)
        PermissionCRUD.revoke(rid, perms, resource_id=None, group_id=group_ids[-1], rebuild=True)

    return dict(rid=rid, resource_ids=resource_ids, group_ids=group_ids, perms=perms)


@router.post('/roles/{rid}/resources/batch/grant2')
@router.post('/roles/{rid}/resources/{resource_id}/grant')
@router.post('/roles/{rid}/resource_groups/{group_id}/grant')
@auth_only_for_acl
def role_permission_grant_view_post(rid: int = None, resource_id: int = None, group_id: int = None):
    perms = handle_arg_list(request.values.get("perms"))

    if "batch" in request.url:
        resource_ids = request.values.get('resource_ids')
        perm_map = request.values.get('perm_map')
        resource_names = request.values.get('resource_names')
        resource_type_id = request.values.get('resource_type_id')
        app = AppCache.get(request.values.get('app_id'))
        PermissionCRUD.batch_grant_by_resource_names(rid, perms, resource_type_id, resource_names,
                                                     resource_ids, perm_map, app_id=app and app.id)

        return dict(rid=rid, resource_names=resource_names, resource_type_id=resource_type_id, perms=perms)

    PermissionCRUD.grant(rid, perms, resource_id=resource_id, group_id=group_id)

    return dict(rid=rid, resource_id=resource_id, group_id=group_id, perms=perms)


@router.post('/roles/{rid}/resources/{resource_id}/grant2')
def role_permission_grant2_view_post(rid: int = None, resource_id: int = None):
    if not ACLManager(request.values.get('app_id')).has_permission(None, None, 'grant', resource_id):
        return abort(403, ErrFormat.no_permission2)

    perms = handle_arg_list(request.values.get("perms"))

    PermissionCRUD.grant(rid, perms, resource_id=resource_id)

    return dict(rid=rid, resource_id=resource_id, perms=perms)


@router.post('/roles/{rid}/resources/batch/revoke2')
@router.post('/roles/{rid}/resources/{resource_id}/revoke')
@router.post('/roles/{rid}/resource_groups/{group_id}/revoke')
@auth_only_for_acl
def role_permission_revoke_view_post(rid: int = None, resource_id: int = None, group_id: int = None):
    perms = handle_arg_list(request.values.get("perms"))
    if "batch" in request.url:
        resource_names = request.values.get('resource_names')
        resource_type_id = request.values.get('resource_type_id')
        resource_ids = request.values.get('resource_ids')
        perm_map = request.values.get('perm_map')
        app = AppCache.get(request.values.get('app_id'))
        PermissionCRUD.batch_revoke_by_resource_names(rid, perms, resource_type_id, resource_names,
                                                      resource_ids, perm_map, app_id=app and app.id)

        return dict(rid=rid, resource_names=resource_names, resource_type_id=resource_type_id, perms=perms)

    PermissionCRUD.revoke(rid, perms, resource_id=resource_id, group_id=group_id)

    return dict(rid=rid, resource_id=resource_id, group_id=group_id, perms=perms)


@router.post('/roles/{rid}/resources/{resource_id}/revoke2')
@router.post('/roles/{rid}/resource_groups/{group_id}/revoke2')
def role_permission_revoke2_view_post(rid: int = None, resource_id: int = None, group_id: int = None):
    if not ACLManager(request.values.get('app_id')).has_permission(None, None, 'grant', resource_id):
        return abort(403, ErrFormat.no_permission2)

    perms = handle_arg_list(request.values.get("perms"))

    PermissionCRUD.revoke(rid, perms, resource_id=resource_id, group_id=group_id)

    return dict(rid=rid, resource_id=resource_id, perms=perms)
