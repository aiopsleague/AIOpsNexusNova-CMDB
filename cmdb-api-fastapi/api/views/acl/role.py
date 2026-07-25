# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import current_app
from api.core.context import request
from api.core.context import current_user

from api.lib.decorator import args_required
from api.lib.decorator import args_validate
from api.lib.perm.acl import validate_app
from api.lib.perm.acl.acl import is_app_admin
from api.lib.perm.acl.cache import AppCache
from api.lib.perm.acl.cache import RoleCache
from api.lib.perm.acl.resp_format import ErrFormat
from api.lib.perm.acl.role import RoleCRUD
from api.lib.perm.acl.role import RoleRelationCRUD
from api.lib.perm.auth import auth_only_for_acl
from api.lib.perm.auth import auth_with_app_token
from api.lib.perm.auth import authenticate
from api.lib.utils import get_page
from api.lib.utils import get_page_size

router = APIRouter(dependencies=[Depends(authenticate)])


# NOTE(fastapi-port): ``/roles/has_perm`` is registered before ``/roles/{rid}``
# so that it wins the match, mirroring flask's ``<int:rid>`` converter
# semantics.


@router.get("/roles/has_perm")
@args_required('resource_name')
@args_required('resource_type_name')
@args_required('perm')
@validate_app
@auth_with_app_token
def role_has_permission_view_get():
    if not request.values.get('rid'):
        role = RoleCache.get_by_name(None, current_user.username)
        role or abort(404, ErrFormat.role_not_found.format(current_user.username))
    else:
        role = RoleCache.get(int(request.values.get('rid')))

    app_id = request.values.get('app_id')
    if is_app_admin(app_id):
        return dict(result=True)

    resource_name = request.values.get('resource_name')
    resource_type_name = request.values.get('resource_type_name')
    perm = request.values.get('perm')
    result = RoleCRUD.has_permission(role.id, resource_name, resource_type_name, app_id, perm)

    return dict(result=result)


@router.get("/roles")
@router.get("/roles/{rid}")
@validate_app
@auth_with_app_token
def role_view_get(rid: int = None):
    page = get_page(request.values.get("page", 1))
    page_size = get_page_size(request.values.get("page_size"))
    q = request.values.get('q')
    app_id = request.values.get('app_id')
    is_all = request.values.get('is_all', True) in current_app.config.get("BOOL_TRUE")
    user_role = request.values.get('user_role', True) in current_app.config.get("BOOL_TRUE")
    user_only = request.values.get('user_only', False) in current_app.config.get("BOOL_TRUE")

    numfound, roles = RoleCRUD.search(q, app_id, page, page_size, user_role, is_all, user_only)

    id2parents = RoleRelationCRUD.get_parents([i.id for i in roles], app_id=app_id)

    roles = [i.to_dict() for i in roles]
    for i in roles:
        i.pop('password', None)

    return dict(numfound=numfound,
                page=page,
                page_size=page_size,
                id2parents=id2parents,
                roles=roles)


@router.post("/roles")
@router.post("/roles/{rid}")
@args_required('name')
@validate_app
@auth_with_app_token
@args_validate(RoleCRUD.cls, exclude_args=['app_id'])
def role_view_post(rid: int = None):
    name = request.values.get('name')
    app_id = request.values.get('app_id')
    password = request.values.get('password')
    _is_app_admin = request.values.get('is_app_admin', False)

    role = RoleCRUD.add_role(name, app_id, password=password, is_app_admin=_is_app_admin)

    return role.to_dict()


@router.put("/roles")
@router.put("/roles/{rid}")
@auth_only_for_acl
@args_validate(RoleCRUD.cls, exclude_args=['app_id'])
def role_view_put(rid: int = None):
    role = RoleCRUD.update_role(rid, **request.values)

    return role.to_dict()


@router.delete("/roles")
@router.delete("/roles/{rid}")
@auth_only_for_acl
def role_view_delete(rid: int = None):
    RoleCRUD.delete_role(rid)

    return dict(rid=rid)


@router.get("/roles/{rid}/parents")
@router.get("/roles/{rid}/users")
@router.get("/roles/{rid}/children")
@auth_with_app_token
@validate_app
def role_relation_view_get(rid: int = None):
    app_id = request.values.get('app_id')
    app = AppCache.get(app_id)
    if app and app.name == "acl":
        app_id = None  # global

    users = RoleRelationCRUD.get_users_by_rid(rid, app_id)

    return dict(users=users)


@router.post("/roles/{rid}/parents")
@router.post("/roles/{rid}/users")
@router.post("/roles/{rid}/children")
@auth_only_for_acl
@validate_app
@args_validate(RoleRelationCRUD.cls, exclude_args=['app_id'])
def role_relation_view_post(rid: int = None):
    app_id = request.values.get('app_id')
    app = AppCache.get(app_id)
    if app and app.name == "acl":
        app_id = None  # global

    role = RoleCache.get(rid) or abort(400, ErrFormat.role_not_found.format("id={}".format(rid)))

    if request.values.get('parent_id'):
        parent_id = request.values.get('parent_id')

        res = RoleRelationCRUD.add(role, parent_id, [rid], app_id)

        return res
    elif request.values.get("child_ids") and isinstance(request.values['child_ids'], list):
        res = RoleRelationCRUD.add(role, rid, request.values['child_ids'], app_id)

        return res

    else:
        return abort(400, ErrFormat.invalid_request)


@router.delete("/roles/{rid}/parents")
@router.delete("/roles/{rid}/users")
@router.delete("/roles/{rid}/children")
@args_required('parent_id')
@auth_only_for_acl
@validate_app
def role_relation_view_delete(rid: int = None):
    parent_id = request.values.get('parent_id')

    app_id = request.values.get('app_id')
    app = AppCache.get(app_id)
    if app and app.name == "acl":
        app_id = None  # global

    RoleRelationCRUD.delete2(parent_id, rid, app_id)

    return dict(parent_id=parent_id, child_id=rid)


@router.get("/roles/{rid}/resources")
@auth_with_app_token
@validate_app
def role_resources_view_get(rid: int = None):
    resource_type_id = request.values.get('resource_type_id')
    group_flat = request.values.get('group_flat', True)
    res = RoleCRUD.recursive_resources(rid, request.values['app_id'], resource_type_id, group_flat, to_record=True)

    return res
