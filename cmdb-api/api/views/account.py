# -*- coding:utf-8 -*-

import datetime

import jwt
import six
from fastapi import APIRouter
from fastapi import Depends

from api.core.context import current_app
from api.core.context import login_user
from api.core.context import logout_user
from api.core.context import request
from api.core.errors import abort
from api.lib.decorator import args_required
from api.lib.perm.acl.cache import User
from api.lib.perm.auth import auth_abandoned
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])


@router.post("/login")
@args_required("username")
@args_required("password")
@auth_abandoned
def login():
    username = request.values.get("username") or request.values.get("email")
    password = request.values.get("password")
    user, authenticated = User.query.authenticate(username, password)
    if not authenticated:
        return abort(401, "invalid username or password")

    login_user(user)

    token = jwt.encode({
        'sub': user.email,
        'iat': datetime.datetime.now(),
        'exp': datetime.datetime.now() + datetime.timedelta(minutes=24 * 60 * 7)},
        current_app.config['SECRET_KEY'])

    return dict(token=token.decode() if six.PY2 else token, username=username)


@router.post("/auth_with_key")
@args_required("key")
@args_required("secret")
@args_required("path")
@auth_abandoned
def auth_with_key():
    key = request.values.get('key')
    secret = request.values.get('secret')
    path = six.moves.urllib.parse.urlparse(request.values.get('path')).path
    payload = request.values.get('payload') or {}

    payload.pop('_key', None)
    payload.pop('_secret', None)

    req_args = [str(payload[k]) for k in sorted(payload.keys())]
    user, authenticated = User.query.authenticate_with_key(key, secret, req_args, path)

    return dict(user=user.to_dict() if user else {},
                authenticated=authenticated)


@router.post("/logout")
@auth_abandoned
def logout():
    logout_user()
    return dict(code=200)
