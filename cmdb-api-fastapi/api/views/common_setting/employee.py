# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import request
from api.core.datastructures import MultiDict

from api.lib.common_setting.employee import EmployeeCRUD, EmployeeAddForm, EmployeeUpdateByUidForm
from api.lib.common_setting.resp_format import ErrFormat
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/employee'

# NOTE(fastapi-port): static routes must be registered before "/employee/{_id}",
# otherwise FastAPI matches the parameterized route first and returns 422.


@router.get(f'{prefix}')
def employee_view_get():
    department_id = int(request.args.get('department_id', 0))
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    search = request.args.get('search', '')
    order = request.args.get('order', '')
    block_status = int(request.args.get('block_status', -1))

    employee_list = EmployeeCRUD.get_employee_list_by(
        department_id, block_status, search, order, page, page_size)

    return employee_list


@router.post(f'{prefix}')
def employee_view_post():
    form = EmployeeAddForm(MultiDict(request.json))
    if not form.validate():
        abort(400, ','.join(['{}: {}'.format(filed, ','.join(msg))
                             for filed, msg in form.errors.items()]))

    data = EmployeeCRUD.add(**form.data)
    return data.to_dict()


@router.post(f'{prefix}/filter')
def employee_filter_view_post():
    params = request.json
    department_id = int(params.get('department_id', 0))
    page = int(params.get('page', 1))
    page_size = int(params.get('page_size', 10))
    search = params.get('search', '')
    order = params.get('order', '')
    block_status = int(params.get('block_status', -1))
    conditions = list(params.get("conditions", []))
    employee_list = EmployeeCRUD.get_employee_list_by_body(department_id, block_status, search, order, conditions,
                                                           page, page_size)

    return employee_list


@router.get(f'{prefix}/count')
def employee_count_view_get():
    block_status = int(request.args.get('block_status', -1))
    employee_count = EmployeeCRUD.get_employee_count(block_status)
    return dict(employee_count=employee_count)


@router.post(f'{prefix}/import')
def employee_import_view_post():
    employee_list = request.json.get('employee_list', [])
    if not employee_list:
        abort(400, ErrFormat.employee_list_is_empty)
    result = EmployeeCRUD.import_employee(employee_list)
    return result


@router.post(f'{prefix}/batch')
def employee_batch_view_post():
    params = request.json
    column_name = params.get('column_name', None)
    employee_id_list = params.get('employee_id_list', None)
    column_value = params.get('column_value', None)
    if column_name not in ['department_id', 'direct_supervisor_id', 'position_name', 'password', 'block']:
        abort(400, ErrFormat.column_name_not_support)
    result = EmployeeCRUD.batch_employee(
        column_name, column_value, employee_id_list)
    return result


@router.get(f'{prefix}/position')
def employee_position_view_get():
    """"""
    result = EmployeeCRUD.get_all_position()
    return result


@router.post(f'{prefix}/get_notice_by_ids')
def get_employee_notice_by_ids_post():
    employee_ids = request.json.get('employee_ids', [])
    if not employee_ids:
        result = []
    else:
        result = EmployeeCRUD.get_employee_notice_by_ids(employee_ids)
    return result


@router.put(f'{prefix}/by_uid/change_password/{{_uid}}')
def employee_change_password_with_aclid_put(_uid: int = None):
    password = request.json.get('password', None)
    if not password:
        abort(400, ErrFormat.password_is_required)

    EmployeeCRUD.change_password_by_uid(_uid, password)
    return 200


@router.get(f'{prefix}/by_uid/{{_uid}}')
def employee_view_with_aclid_get(_uid: int = None):
    result = EmployeeCRUD.get_employee_by_uid_with_create(_uid)
    return result


@router.put(f'{prefix}/by_uid/{{_uid}}')
def employee_view_with_aclid_put(_uid: int = None):
    form = EmployeeUpdateByUidForm(MultiDict(request.json))
    if not form.validate():
        abort(400, ','.join(['{}: {}'.format(filed, ','.join(msg))
                             for filed, msg in form.errors.items()]))

    data = EmployeeCRUD.edit_employee_by_uid(_uid, **form.data)
    return data.to_dict()


@router.put(f'{prefix}/by_uid/bind_notice/{{platform}}/{{_uid}}')
def employee_bind_notice_with_aclid_put(platform: str = None, _uid: int = None):
    data = EmployeeCRUD.bind_notice_by_uid(platform, _uid)
    return dict(info=data)


@router.delete(f'{prefix}/by_uid/bind_notice/{{platform}}/{{_uid}}')
def employee_bind_notice_with_aclid_delete(platform: str = None, _uid: int = None):
    data = EmployeeCRUD.remove_bind_notice_by_uid(platform, _uid)
    return dict(info=data)


@router.get(f'{prefix}/{{_id}}')
def employee_view_with_id_get(_id: int = None):
    data = EmployeeCRUD.get_employee_by_id(_id)
    return data.to_dict()


@router.put(f'{prefix}/{{_id}}')
def employee_view_with_id_put(_id: int = None):
    params = request.json
    direct_supervisor_id = params.get('direct_supervisor_id', None)
    if direct_supervisor_id and int(_id) == int(direct_supervisor_id):
        abort(400, ErrFormat.direct_supervisor_is_not_self)

    data = EmployeeCRUD.update(_id, **params)
    return data.to_dict()
