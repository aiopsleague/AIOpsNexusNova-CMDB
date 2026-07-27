# -*- coding:utf-8 -*-

import requests
from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import current_app
from api.core.context import request
from api.core.context import session
from api.core.context import current_user

from api.lib.decorator import args_required
from api.lib.decorator import args_validate
from api.lib.perm.acl.acl import ACLManager
from api.lib.perm.acl.acl import AuditCRUD
from api.lib.perm.acl.acl import role_required
from api.lib.perm.acl.cache import AppCache
from api.lib.perm.acl.cache import UserCache
from api.lib.perm.acl.resp_format import ErrFormat
from api.lib.perm.acl.role import RoleRelationCRUD
from api.lib.perm.acl.user import UserCRUD
from api.lib.perm.auth import auth_with_app_token
from api.lib.perm.auth import authenticate
from api.lib.utils import get_page
from api.lib.utils import get_page_size

router = APIRouter(dependencies=[Depends(authenticate)])


# NOTE(fastapi-port): routes with a literal suffix (``/users/info`` etc.) are
# registered before ``/users/{uid}`` so that they win the match, mirroring
# flask's ``<int:uid>`` converter semantics.


@router.get("/users/info")
@auth_with_app_token
def get_user_info_view_get():
    app_id = request.values.get('app_id')
    if not app_id:
        name = session.get("acl", {}).get("userName") or session.get("CAS_USERNAME") or \
               current_user.username or request.values.get('username')
    else:

        name = request.values.get('username')

    current_app.logger.info("get user info for1: app_id: {0}, name: {1}".format(request.values.get('app_id'), name))
    user_info = ACLManager().get_user_info(name, request.values.get('app_id'))
    current_app.logger.info("get user info for2: {}".format(user_info))

    result = dict(name=user_info.get('nickname') or name,
                  username=user_info.get('username') or name,
                  email=user_info.get('email'),
                  uid=user_info.get('uid'),
                  rid=user_info.get('rid'),
                  role=dict(permissions=user_info.get('parents')),
                  avatar=user_info.get('avatar'))

    if request.values.get('channel'):
        _id = AuditCRUD.add_login_log(name, True, ErrFormat.login_succeed,
                                      ip=request.values.get('ip'),
                                      browser=request.values.get('browser'))
        session['LOGIN_ID'] = _id
        result['LOGIN_ID'] = _id

    current_app.logger.info("get user info for3: {}".format(result))
    return dict(result=result)


@router.get("/users/secret")
@auth_with_app_token
def get_user_key_secret_view_get():
    if not request.values.get('app_id'):
        name = session.get("acl", {}).get("userName") or session.get("CAS_USERNAME") or current_user.username
    else:
        name = request.values.get('username')

    user = UserCache.get(name) or abort(404, ErrFormat.user_not_found.format(name))

    return dict(key=user.key, secret=user.secret)


@router.get("/users/employee")
@auth_with_app_token
def user_on_the_job_view_get():
    if current_app.config.get('HR_URI'):
        try:
            return requests.get(current_app.config["HR_URI"]).json()
        except:
            return abort(400, ErrFormat.invalid_request)
    else:
        return UserCRUD.get_employees()


@router.post("/users/reset_key_secret")
def user_reset_key_secret_view_post():
    key, secret = UserCRUD.reset_key_secret()

    return dict(key=key, secret=secret)


@router.put("/users/reset_key_secret")
def user_reset_key_secret_view_put():
    return user_reset_key_secret_view_post()


@router.post("/users/reset_password")
@auth_with_app_token
@args_required('username')
@args_required('password')
@args_validate(UserCRUD.cls, exclude_args=['app_id'])
def user_reset_password_view_post():
    if request.values.get('app_id'):
        app = AppCache.get(request.values['app_id'])
        if app.name not in ('cas-server', 'acl'):
            return abort(403, ErrFormat.invalid_request)

    elif hasattr(current_user, 'username'):
        if current_user.username != request.values['username']:
            return abort(403, ErrFormat.invalid_request)

    else:
        return abort(400, ErrFormat.invalid_operation)

    user = UserCache.get(request.values['username'])
    user or abort(404, ErrFormat.user_not_found.format(request.values['username']))

    UserCRUD.update(user.uid, password=request.values['password'])

    return dict(code=200)


@router.get("/users")
@router.get("/users/{uid}")
@auth_with_app_token
def user_view_get(uid: int = None):
    page = get_page(request.values.get('page', 1))
    page_size = get_page_size(request.values.get('page_size'))
    q = request.values.get("q")
    numfound, users = UserCRUD.search(q, page, page_size)
    id2parents = RoleRelationCRUD.get_parents(uids=[i.uid for i in users], all_app=True)

    users = [i.to_dict() for i in users]
    for u in users:
        u.pop('password', None)
        u.pop('key', None)
        u.pop('secret', None)

    return dict(numfound=numfound,
                page=page,
                page_size=page_size,
                id2parents=id2parents,
                users=users)


@router.post("/users")
@router.post("/users/{uid}")
@args_required('username')
@args_required('email')
@role_required("acl_admin")
@args_validate(UserCRUD.cls)
def user_view_post(uid: int = None):
    request.values.pop('_key', None)
    request.values.pop('_secret', None)

    user = UserCRUD.add(**request.values)

    return user.to_dict()


@router.put("/users")
@router.put("/users/{uid}")
@role_required("acl_admin")
@args_validate(UserCRUD.cls)
def user_view_put(uid: int = None):
    request.values.pop('_key', None)
    request.values.pop('_secret', None)

    user = UserCRUD.update(uid, **request.values)

    return user.to_dict()


@router.delete("/users")
@router.delete("/users/{uid}")
@role_required("acl_admin")
def user_view_delete(uid: int = None):
    if current_user.uid == uid:
        return abort(400, ErrFormat.invalid_operation)
    UserCRUD.delete(uid)

    return dict(uid=uid)
