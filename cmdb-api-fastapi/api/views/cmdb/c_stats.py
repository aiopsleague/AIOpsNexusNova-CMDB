# -*- coding:utf-8 -*-


from fastapi import APIRouter
from fastapi import Depends

from api.lib.cmdb.cache import CMDBCounterCache
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/statistics")
def cmdb_statistics_view_get():
    return CMDBCounterCache.get()
