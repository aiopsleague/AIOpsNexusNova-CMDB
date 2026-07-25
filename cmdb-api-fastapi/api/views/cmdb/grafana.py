# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.lib.cmdb.grafana import resolve_ci_grafana
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/ci/{ci_id:int}/grafana")
def ci_grafana_view_get(ci_id: int):
    return resolve_ci_grafana(ci_id)
