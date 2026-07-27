# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request

from api.lib.decorator import args_required
from api.lib.decorator import args_validate
from api.lib.perm.acl import validate_app
from api.lib.perm.acl.trigger import TriggerCRUD
from api.lib.perm.auth import auth_only_for_acl
from api.lib.perm.auth import auth_with_app_token
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])


# NOTE(fastapi-port): ``/triggers/resources`` is registered before
# ``/triggers/{_id}`` so that it wins the match, mirroring flask's
# ``<int:_id>`` converter semantics.


@router.post("/triggers/resources")
@validate_app
@auth_with_app_token
@args_required("resource_type_id")
def trigger_resource_view_post():
    app_id = request.values.get('app_id')
    resource_type_id = request.values.get('resource_type_id')
    wildcard = request.values.get('pattern')
    uid = request.values.get('owner')

    resources = TriggerCRUD.get_resources(app_id, resource_type_id, wildcard, uid)
    resources = [i.to_dict() for i in resources]

    return resources


@router.get("/triggers")
@router.get("/triggers/{_id}")
@validate_app
@auth_with_app_token
def trigger_view_get(_id: int = None):
    return TriggerCRUD.get(request.values.get('app_id'))


@router.post("/triggers")
@router.post("/triggers/{_id}")
@args_required('name')
@args_required('resource_type_id')
@args_required('roles')
@args_required('permissions')
@validate_app
@auth_only_for_acl
@args_validate(TriggerCRUD.cls, exclude_args=['app_id'])
def trigger_view_post(_id: int = None):
    request.values.pop('_key', None)
    request.values.pop('_secret', None)
    trigger = TriggerCRUD.add(request.values.pop('app_id', None), **request.values)

    return trigger.to_dict()


@router.put("/triggers")
@router.put("/triggers/{_id}")
@args_required('resource_type_id')
@args_required('roles')
@args_required('permissions')
@validate_app
@auth_only_for_acl
@args_validate(TriggerCRUD.cls, exclude_args=['app_id'])
def trigger_view_put(_id: int = None):
    request.values.pop('_key', None)
    request.values.pop('_secret', None)

    trigger = TriggerCRUD.update(_id, **request.values)

    return trigger.to_dict()


@router.delete("/triggers")
@router.delete("/triggers/{_id}")
@auth_only_for_acl
def trigger_view_delete(_id: int = None):
    TriggerCRUD.delete(_id)

    return dict(id=_id)


@router.post("/triggers/{_id}/apply")
@auth_only_for_acl
def trigger_apply_view_post(_id: int = None):
    TriggerCRUD.apply(_id)

    return dict(id=_id)


@router.post("/triggers/{_id}/cancel")
@auth_only_for_acl
def trigger_cancel_view_post(_id: int = None):
    TriggerCRUD.cancel(_id)

    return dict(id=_id)
