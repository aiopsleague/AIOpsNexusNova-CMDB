# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.core.errors import abort
from api.lib.common_setting.grafana import GrafanaConfigCRUD
from api.lib.common_setting.grafana_client import GrafanaClient
from api.lib.common_setting.resp_format import ErrFormat
from api.lib.perm.acl.acl import role_required
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/grafana'

# NOTE(fastapi-port): static routes must be registered before parameterized
# ones ("/grafana/connections/{_id}" etc.), otherwise FastAPI matches them
# first and returns 422.


@router.get(f'{prefix}/connections')
@role_required("acl_admin")
def grafana_connections_get():
    return dict(connections=GrafanaConfigCRUD().list_connections())


@router.post(f'{prefix}/connections')
@role_required("acl_admin")
def grafana_connections_post():
    data = (request.json or {}).get('data', {})
    return GrafanaConfigCRUD().create_connection(data)


@router.post(f'{prefix}/connections/test')
@role_required("acl_admin")
def grafana_connections_test_post():
    data = (request.json or {}).get('data', {})
    GrafanaConfigCRUD().test_connection(data.get('url'), data.get('api_key'))
    return dict()


@router.get(f'{prefix}/connections/health')
@role_required("acl_admin")
def grafana_connections_health_get():
    return dict(health=GrafanaConfigCRUD().check_health())


@router.put(f'{prefix}/connections/{{_id:int}}')
@role_required("acl_admin")
def grafana_connections_put(_id: int = None):
    data = (request.json or {}).get('data', {})
    return GrafanaConfigCRUD().update_connection(_id, data)


@router.delete(f'{prefix}/connections/{{_id:int}}')
@role_required("acl_admin")
def grafana_connections_delete(_id: int = None):
    GrafanaConfigCRUD().delete_connection(_id)
    return dict()


@router.get(f'{prefix}/connections/{{_id:int}}/dashboards')
@role_required("acl_admin")
def grafana_connection_dashboards_get(_id: int = None):
    namespace = request.values.get('namespace') or 'default'
    connection = GrafanaConfigCRUD().get_connection(_id)
    try:
        dashboards = GrafanaClient(connection["url"], connection["api_key"]).list_dashboards(namespace)
    except Exception as e:
        abort(400, ErrFormat.grafana_test_failed.format(str(e)))
    return dict(dashboards=dashboards)


@router.get(f'{prefix}/connections/{{_id:int}}/dashboards/{{name}}/variables')
@role_required("acl_admin")
def grafana_connection_dashboard_variables_get(_id: int = None, name: str = None):
    connection = GrafanaConfigCRUD().get_connection(_id)
    try:
        variables = GrafanaClient(connection["url"], connection["api_key"]).get_dashboard_variables(name)
    except Exception as e:
        abort(400, ErrFormat.grafana_test_failed.format(str(e)))
    return dict(variables=variables)


@router.get(f'{prefix}/mappings')
@role_required("acl_admin")
def grafana_mappings_get():
    return dict(mappings=GrafanaConfigCRUD().list_mappings())


@router.post(f'{prefix}/mappings')
@role_required("acl_admin")
def grafana_mappings_post():
    data = (request.json or {}).get('data', {})
    return GrafanaConfigCRUD().create_mapping(data)


@router.put(f'{prefix}/mappings/{{_id:int}}')
@role_required("acl_admin")
def grafana_mappings_put(_id: int = None):
    data = (request.json or {}).get('data', {})
    return GrafanaConfigCRUD().update_mapping(_id, data)


@router.delete(f'{prefix}/mappings/{{_id:int}}')
@role_required("acl_admin")
def grafana_mappings_delete(_id: int = None):
    GrafanaConfigCRUD().delete_mapping(_id)
    return dict()
