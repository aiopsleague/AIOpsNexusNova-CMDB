# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request

from api.lib.common_setting.company_info import CompanyInfoCRUD
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/company'


@router.get(f'{prefix}/info')
def company_info_view_get():
    return CompanyInfoCRUD.get()


@router.post(f'{prefix}/info')
def company_info_view_post():
    data = {
        'info': {
            **request.values
        }
    }
    info = CompanyInfoCRUD.get()
    if info:
        d = CompanyInfoCRUD.update(info.get('id'), **data)
    else:
        d = CompanyInfoCRUD.create(**data)
    res = d.to_dict()
    return res


@router.put(f'{prefix}/info/{{_id}}')
def company_info_view_with_id_put(_id: int = None):
    data = {
        'info': {
            **request.values
        }
    }
    d = CompanyInfoCRUD.update(_id, **data)
    res = d.to_dict()
    return res
