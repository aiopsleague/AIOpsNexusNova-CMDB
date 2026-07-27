# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import request

from api.lib.decorator import args_required
from api.lib.decorator import args_validate
from api.lib.perm.acl.acl import is_app_admin
from api.lib.perm.acl.app import AppCRUD
from api.lib.perm.acl.resp_format import ErrFormat
from api.lib.perm.auth import auth_abandoned
from api.lib.perm.auth import authenticate
from api.lib.utils import get_page
from api.lib.utils import get_page_size

router = APIRouter(dependencies=[Depends(authenticate)])


# NOTE(fastapi-port): ``/apps/token`` is registered before ``/apps/{_id}`` so
# that it wins the match, mirroring flask's ``<int:_id>`` converter semantics.


@router.post('/apps/token')
@args_required('app_id')
@args_required('secret_key')
@auth_abandoned
def app_access_token_view_post():
    token = AppCRUD.gen_token(request.values.get('app_id'), request.values.get('secret_key'))

    return dict(token=token)


@router.get('/apps')
@router.get('/apps/{_id}')
def app_view_get(_id: int = None):
    if _id is not None:
        if not is_app_admin('acl'):
            return abort(403, ErrFormat.no_permission)

        app = AppCRUD.get(_id)
        app = app and app.to_dict() or {}

        return dict(**app)

    page = get_page(request.values.get('page', 1))
    page_size = get_page_size(request.values.get('page_size'))
    q = request.values.get('q')

    numfound, res = AppCRUD.search(q, page, page_size)

    res = [i.to_dict() for i in res]
    for i in res:
        i.pop('app_id', None)
        i.pop('secret_key', None)

    return dict(page=page,
                page_size=page_size,
                numfound=numfound,
                total=len(res),
                apps=res)


@router.post('/apps')
@router.post('/apps/{_id}')
@args_required('name')
@args_validate(AppCRUD.cls)
def app_view_post(_id: int = None):
    name = request.values.get('name')
    description = request.values.get('description')

    app = AppCRUD.add(name, description)

    return app.to_dict()


@router.put('/apps')
@router.put('/apps/{_id}')
@args_validate(AppCRUD.cls)
def app_view_put(_id: int = None):
    app = AppCRUD.update(_id, **request.values)

    return app.to_dict()


@router.delete('/apps')
@router.delete('/apps/{_id}')
def app_view_delete(_id: int = None):
    AppCRUD.delete(_id)

    return dict(id=_id)
