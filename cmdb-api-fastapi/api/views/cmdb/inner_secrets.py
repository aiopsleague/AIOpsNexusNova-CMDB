# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request

from api.lib.perm.auth import auth_abandoned
from api.lib.perm.auth import authenticate
from api.lib.secrets.inner import KeyManage
from api.lib.secrets.secrets import InnerKVManger

router = APIRouter(dependencies=[Depends(authenticate)])


@router.post("/secrets/unseal")
@auth_abandoned
def inner_secret_un_seal_view_post():
    unseal_key = request.headers.get("Unseal-Token")
    res = KeyManage(backend=InnerKVManger()).unseal(unseal_key)
    return dict(**res)


@router.post("/secrets/seal")
@auth_abandoned
def inner_secret_seal_view_post():
    unseal_key = request.headers.get("Inner-Token")
    res = KeyManage(backend=InnerKVManger()).seal(unseal_key)
    return dict(**res)


@router.post("/secrets/auto_seal")
@auth_abandoned
def inner_secret_auto_seal_view_post():
    root_key = request.headers.get("Inner-Token")
    res = KeyManage(trigger=root_key,
                    backend=InnerKVManger()).auto_unseal()
    return dict(**res)
