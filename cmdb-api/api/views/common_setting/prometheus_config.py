# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.lib.common_setting.prometheus import PrometheusConfigCRUD
from api.lib.perm.acl.acl import role_required
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/prometheus'


# ---- connections ----

@router.get(f'{prefix}/connections')
@role_required("acl_admin")
def prometheus_connections_get():
    return dict(connections=PrometheusConfigCRUD().list_connections())


@router.post(f'{prefix}/connections')
@role_required("acl_admin")
def prometheus_connections_post():
    data = (request.json or {}).get('data', {})
    return PrometheusConfigCRUD().create_connection(data)


@router.post(f'{prefix}/connections/test')
@role_required("acl_admin")
def prometheus_connections_test_post():
    data = (request.json or {}).get('data', {})
    PrometheusConfigCRUD().test_connection(
        data.get('url'), data.get('auth_type'), data.get('auth_data'))
    return dict()


@router.get(f'{prefix}/connections/health')
@role_required("acl_admin")
def prometheus_connections_health_get():
    return dict(health=PrometheusConfigCRUD().check_health())


@router.put(f'{prefix}/connections/{{_id:int}}')
@role_required("acl_admin")
def prometheus_connections_put(_id: int = None):
    data = (request.json or {}).get('data', {})
    return PrometheusConfigCRUD().update_connection(_id, data)


@router.delete(f'{prefix}/connections/{{_id:int}}')
@role_required("acl_admin")
def prometheus_connections_delete(_id: int = None):
    PrometheusConfigCRUD().delete_connection(_id)
    return dict()


# ---- mappings ----

@router.get(f'{prefix}/mappings')
@role_required("acl_admin")
def prometheus_mappings_get():
    return dict(mappings=PrometheusConfigCRUD().list_mappings())


@router.post(f'{prefix}/mappings')
@role_required("acl_admin")
def prometheus_mappings_post():
    data = (request.json or {}).get('data', {})
    return PrometheusConfigCRUD().create_mapping(data)


@router.put(f'{prefix}/mappings/{{_id:int}}')
@role_required("acl_admin")
def prometheus_mappings_put(_id: int = None):
    data = (request.json or {}).get('data', {})
    return PrometheusConfigCRUD().update_mapping(_id, data)


@router.delete(f'{prefix}/mappings/{{_id:int}}')
@role_required("acl_admin")
def prometheus_mappings_delete(_id: int = None):
    PrometheusConfigCRUD().delete_mapping(_id)
    return dict()
