# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.lib.cmdb.prometheus import check_ci_prometheus
from api.lib.cmdb.prometheus import resolve_ci_prometheus_alerts
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/ci_type/{ci_type_id:int}/prometheus/check")
def ci_type_prometheus_check(ci_type_id: int):
    """Check whether a CI type has Prometheus alert mapping configured."""
    return check_ci_prometheus(ci_type_id)


@router.get("/ci/{ci_id:int}/prometheus/alerts")
def ci_prometheus_alerts_get(ci_id: int):
    """Return active Prometheus alerts for a CI instance."""
    return resolve_ci_prometheus_alerts(ci_id)
