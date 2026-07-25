# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.core.context import current_user

from api.lib.decorator import args_required
from api.lib.decorator import args_validate
from api.lib.perm.acl import validate_app
from api.lib.perm.acl.resource import ResourceCRUD
from api.lib.perm.acl.resource import ResourceGroupCRUD
from api.lib.perm.acl.resource import ResourceTypeCRUD
from api.lib.perm.auth import auth_only_for_acl
from api.lib.perm.auth import auth_with_app_token
from api.lib.perm.auth import authenticate
from api.lib.utils import get_page
from api.lib.utils import get_page_size
from api.lib.utils import handle_arg_list

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/resource_types")
@router.get("/resource_types/{type_id}")
@validate_app
@auth_with_app_token
def resource_type_view_get(type_id: int = None):
    page = get_page(request.values.get("page", 1))
    page_size = get_page_size(request.values.get("page_size"))
    q = request.values.get('q')
    app_id = request.values.get('app_id')

    numfound, res, id2perms = ResourceTypeCRUD.search(q, app_id, page, page_size)

    return dict(numfound=numfound,
                page=page,
                page_size=page_size,
                groups=[i.to_dict() for i in res],
                id2perms=id2perms)


@router.post("/resource_types")
@router.post("/resource_types/{type_id}")
@args_required('name')
@args_required('perms')
@validate_app
@auth_only_for_acl
@args_validate(ResourceTypeCRUD.cls, exclude_args=['app_id'])
def resource_type_view_post(type_id: int = None):
    name = request.values.get('name')
    app_id = request.values.get('app_id')
    description = request.values.get('description', '')
    perms = request.values.get('perms')

    rt = ResourceTypeCRUD.add(app_id, name, description, perms)

    return rt.to_dict()


@router.put("/resource_types")
@router.put("/resource_types/{type_id}")
@auth_only_for_acl
@args_validate(ResourceTypeCRUD.cls, exclude_args=['app_id'])
def resource_type_view_put(type_id: int = None):
    rt = ResourceTypeCRUD.update(type_id, **request.values)

    return rt.to_dict()


@router.delete("/resource_types")
@router.delete("/resource_types/{type_id}")
@auth_only_for_acl
def resource_type_view_delete(type_id: int = None):
    ResourceTypeCRUD.delete(type_id)

    return dict(type_id=type_id)


@router.get("/resource_types/{type_id}/perms")
@auth_with_app_token
def resource_type_perms_view_get(type_id: int = None):
    return ResourceTypeCRUD.get_perms(type_id)


@router.get("/resources")
@router.get("/resources/{resource_id}")
@validate_app
@auth_with_app_token
def resource_view_get(resource_id: int = None):
    page = get_page(request.values.get("page", 1))
    page_size = get_page_size(request.values.get("page_size"))
    q = request.values.get('q')
    u = request.values.get('u')
    resource_type_id = request.values.get('resource_type_id')
    app_id = request.values.get('app_id')

    numfound, res = ResourceCRUD.search(q, u, app_id, resource_type_id, page, page_size)

    return dict(numfound=numfound,
                page=page,
                page_size=page_size,
                resources=res)


@router.post("/resources")
@router.post("/resources/{resource_id}")
@args_required('name')
@args_required('type_id')
@validate_app
@auth_only_for_acl
@args_validate(ResourceCRUD.cls, exclude_args=['app_id'])
def resource_view_post(resource_id: int = None):
    name = request.values.get('name')
    type_id = request.values.get('type_id')
    app_id = request.values.get('app_id')
    uid = request.values.get('uid')
    if not uid and hasattr(current_user, "uid"):
        uid = current_user.uid

    resource = ResourceCRUD.add(name, type_id, app_id, uid)

    return resource.to_dict()


@router.put("/resources")
@router.put("/resources/{resource_id}")
@args_required('name')
@auth_only_for_acl
@args_validate(ResourceCRUD.cls, exclude_args=['app_id'])
def resource_view_put(resource_id: int = None):
    name = request.values.get('name')

    resource = ResourceCRUD.update(resource_id, name)

    return resource.to_dict()


@router.delete("/resources")
@router.delete("/resources/{resource_id}")
@auth_only_for_acl
def resource_view_delete(resource_id: int = None):
    ResourceCRUD.delete(resource_id)

    return dict(resource_id=resource_id)


@router.get("/resource_groups")
@router.get("/resource_groups/{group_id}")
@validate_app
@auth_with_app_token
def resource_group_view_get(group_id: int = None):
    page = get_page(request.values.get("page", 1))
    page_size = get_page_size(request.values.get("page_size"))
    q = request.values.get('q')
    app_id = request.values.get('app_id')
    resource_type_id = request.values.get('resource_type_id')

    numfound, res = ResourceGroupCRUD.search(q, app_id, resource_type_id, page, page_size)

    return dict(numfound=numfound,
                page=page,
                page_size=page_size,
                groups=[i.to_dict() for i in res])


@router.post("/resource_groups")
@router.post("/resource_groups/{group_id}")
@args_required('name')
@args_required('type_id')
@validate_app
@auth_only_for_acl
@args_validate(ResourceGroupCRUD.cls, exclude_args=['app_id'])
def resource_group_view_post(group_id: int = None):
    name = request.values.get('name')
    type_id = request.values.get('type_id')
    app_id = request.values.get('app_id')

    group = ResourceGroupCRUD.add(name, type_id, app_id)

    return group.to_dict()


@router.put("/resource_groups")
@router.put("/resource_groups/{group_id}")
@args_required('items')
@auth_only_for_acl
@args_validate(ResourceGroupCRUD.cls, exclude_args=['app_id'])
def resource_group_view_put(group_id: int = None):
    items = handle_arg_list(request.values.get("items"))

    ResourceGroupCRUD.update(group_id, items)

    items = ResourceGroupCRUD.get_items(group_id)

    return items


@router.delete("/resource_groups")
@router.delete("/resource_groups/{group_id}")
@auth_only_for_acl
def resource_group_view_delete(group_id: int = None):
    ResourceGroupCRUD.delete(group_id)

    return dict(group_id=group_id)


@router.get("/resource_groups/{group_id}/items")
@auth_with_app_token
def resource_group_items_view_get(group_id: int = None):
    items = ResourceGroupCRUD.get_items(group_id)

    return items
