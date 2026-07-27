from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request

from api.lib.common_setting.common_data import CommonDataCRUD
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/data'


@router.get(f'{prefix}/{{data_type}}')
def data_view_get(data_type: str = None):
    data_list = CommonDataCRUD.get_data_by_type(data_type)

    return data_list


@router.post(f'{prefix}/{{data_type}}')
def data_view_post(data_type: str = None):
    params = request.json
    CommonDataCRUD.create_new_data(data_type, **params)

    return params


@router.put(f'{prefix}/{{data_type}}/{{_id}}')
def data_view_with_id_put(data_type: str = None, _id: int = None):
    params = request.json
    res = CommonDataCRUD.update_data(_id, **params)

    return res.to_dict()


@router.delete(f'{prefix}/{{data_type}}/{{_id}}')
def data_view_with_id_delete(data_type: str = None, _id: int = None):
    CommonDataCRUD.delete(_id)
    return dict()
