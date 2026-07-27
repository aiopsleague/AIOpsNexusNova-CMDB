from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import request

from api.lib.common_setting.common_data import AuthenticateDataCRUD
from api.lib.common_setting.const import TestType
from api.lib.common_setting.resp_format import ErrFormat
from api.lib.perm.acl.acl import role_required
from api.lib.perm.auth import auth_abandoned
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/auth_config'

# NOTE(fastapi-port): static routes must be registered before parameterized
# ones ("/auth_config/{auth_type}" etc.), and "{auth_type}/test" before
# "{auth_type}/{_id}", otherwise FastAPI matches them first and returns 422.


@router.get(f'{prefix}/enable_list')
@auth_abandoned  # origin: method_decorators = [] (no auth_required)
def auth_enable_list_view_get():
    return AuthenticateDataCRUD.get_enable_list()


@router.post(f'{prefix}/{{auth_type}}/test')
def auth_config_test_view_post(auth_type: str = None):
    test_type = request.values.get('test_type', TestType.Connect)
    params = request.json
    return AuthenticateDataCRUD(auth_type).test(test_type, params.get('data'))


@router.get(f'{prefix}/{{auth_type}}')
@role_required("acl_admin")
def auth_config_view_get(auth_type: str = None):
    cli = AuthenticateDataCRUD(auth_type)

    if auth_type not in cli.get_support_type_list():
        abort(400, ErrFormat.not_support_auth_type.format(auth_type))

    if auth_type in cli.common_type_list:
        data = cli.get_record(True)
    else:
        data = cli.get_record_with_decrypt()
    return data


@router.post(f'{prefix}/{{auth_type}}')
@role_required("acl_admin")
def auth_config_view_post(auth_type: str = None):
    cli = AuthenticateDataCRUD(auth_type)

    if auth_type not in cli.get_support_type_list():
        abort(400, ErrFormat.not_support_auth_type.format(auth_type))

    params = request.json
    data = params.get('data', {})
    if auth_type in cli.common_type_list:
        data['encrypt'] = False
    cli.create(data)

    return params


@router.put(f'{prefix}/{{auth_type}}/{{_id}}')
@role_required("acl_admin")
def auth_config_view_with_id_put(auth_type: str = None, _id: int = None):
    cli = AuthenticateDataCRUD(auth_type)

    if auth_type not in cli.get_support_type_list():
        abort(400, ErrFormat.not_support_auth_type.format(auth_type))

    params = request.json
    data = params.get('data', {})
    if auth_type in cli.common_type_list:
        data['encrypt'] = False

    res = cli.update(_id, data)

    return res.to_dict()


@router.delete(f'{prefix}/{{auth_type}}/{{_id}}')
@role_required("acl_admin")
def auth_config_view_with_id_delete(auth_type: str = None, _id: int = None):
    cli = AuthenticateDataCRUD(auth_type)

    if auth_type not in cli.get_support_type_list():
        abort(400, ErrFormat.not_support_auth_type.format(auth_type))
    cli.delete(_id)
    return dict()
