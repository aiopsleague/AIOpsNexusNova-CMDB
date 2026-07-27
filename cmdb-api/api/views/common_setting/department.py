# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import request
from api.core.datastructures import MultiDict

from api.lib.common_setting.department import DepartmentCRUD
from api.lib.common_setting.department import DepartmentTree, DepartmentForm
from api.lib.common_setting.employee import EmployeeCRUD
from api.lib.common_setting.resp_format import ErrFormat
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/department'

# NOTE(fastapi-port): static routes must be registered before "/department/{_id}",
# otherwise FastAPI matches the parameterized route first and returns 422.


@router.get(f'{prefix}/all')
def department_all_view_get():
    is_tree = int(request.args.get('is_tree', 1))

    res = DepartmentTree().get_all_departments(is_tree)
    return res


@router.get(f'{prefix}/all_with_employee')
def department_all_view_with_employee_get():
    block = int(request.args.get('block', -1))
    try:
        res = DepartmentCRUD.get_all_departments_with_employee(block)
        return res
    except Exception as e:
        abort(500, str(e))


@router.get(f'{prefix}/allow_parent')
def department_parent_view_get():
    department_id = request.args.get('department_id', None)
    if department_id is None:
        abort(400, ErrFormat.department_id_is_required)

    p_department_list = DepartmentCRUD.get_allow_parent_d_id_by(
        int(department_id))
    return p_department_list


@router.put(f'{prefix}/update_sort')
def department_sort_view_put():
    """
    only can sort in the same parent
    """
    department_list = request.json.get('department_list', None)
    if department_list is None:
        abort(400, ErrFormat.department_list_is_required)

    result = DepartmentCRUD.update_department_sort(department_list)

    return result


@router.get(f'{prefix}')
def department_view_get():
    department_parent_id = request.args.get('department_parent_id', 0)
    block = int(request.args.get('block', 0))

    departments, department_id_list = DepartmentCRUD.get_departments_and_ids(
        department_parent_id, block)
    employees = EmployeeCRUD.get_employees_by_department_id(
        department_parent_id, block)

    return dict(departments=departments, employees=employees)


@router.post(f'{prefix}')
def department_view_post():
    form = DepartmentForm(MultiDict(request.json))
    if not form.validate():
        abort(400, ','.join(['{}: {}'.format(filed, ','.join(msg))
                             for filed, msg in form.errors.items()]))

    data = DepartmentCRUD.add(**form.data)

    return data.to_dict()


@router.put(f'{prefix}/{{_id}}')
def department_id_view_put(_id: int = None):
    form = DepartmentForm(MultiDict(request.json))
    if not form.validate():
        abort(400, ','.join(['{}: {}'.format(filed, ','.join(msg))
                             for filed, msg in form.errors.items()]))

    department_parent_id = form.data.get('department_parent_id')
    if int(_id) == int(department_parent_id):
        abort(400, ErrFormat.parent_department_is_not_self)

    data = DepartmentCRUD.edit(_id, **form.data)
    return data.to_dict()


@router.delete(f'{prefix}/{{_id}}')
def department_id_view_delete(_id: int = None):
    if _id in [-1, 0]:
        abort(400, ErrFormat.delete_reserved_department_name)
    DepartmentCRUD.delete(_id)
    return dict(status='success')
