from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.core.errors import abort
from api.core.context import current_app
from api.core.datastructures import MultiDict

from api.lib.perm.auth import auth_abandoned
from api.lib.perm.auth import auth_with_app_token
from api.lib.perm.auth import authenticate
from api.models.common_setting import NoticeConfig
from api.lib.common_setting.notice_config import NoticeConfigForm, NoticeConfigUpdateForm, NoticeConfigCRUD
from api.lib.decorator import args_required
from api.lib.common_setting.resp_format import ErrFormat

router = APIRouter(dependencies=[Depends(authenticate)])

prefix = '/notice_config'

# NOTE(fastapi-port): static routes must be registered before
# "/notice_config/{_id}", otherwise FastAPI matches the parameterized
# route first and returns 422.


@router.get(f'{prefix}')
@args_required('platform')
@auth_with_app_token
def notice_config_view_get():
    platform = request.args.get('platform')
    res = NoticeConfig.get_by(first=True, to_dict=True, platform=platform) or {}
    return res


@router.post(f'{prefix}')
def notice_config_view_post():
    form = NoticeConfigForm(MultiDict(request.json))
    if not form.validate():
        abort(400, ','.join(['{}: {}'.format(filed, ','.join(msg)) for filed, msg in form.errors.items()]))

    data = NoticeConfigCRUD.add_notice_config(**form.data)
    return data.to_dict()


@router.post(f'{prefix}/send_test_email')
def check_email_server_post():
    receive_address = request.args.get('receive_address')
    info = request.values.get('info', {})

    try:

        result = NoticeConfigCRUD.test_send_email(receive_address, **info)
        return dict(result=result)
    except Exception as e:
        current_app.logger.error('test_send_email err:')
        current_app.logger.error(e)
        if 'Timed Out' in str(e):
            abort(400, ErrFormat.email_send_timeout)
        abort(400, f"{str(e)}")


@router.get(f'{prefix}/all')
@auth_abandoned  # origin: method_decorators = [] (no auth_required)
@auth_with_app_token
def notice_config_get_view_get():
    res = NoticeConfigCRUD.get_all()
    return res


@router.get(f'{prefix}/app_bot')
def notice_app_bot_view_get():
    res = NoticeConfigCRUD.get_app_bot()
    return res


@router.put(f'{prefix}/{{_id}}')
def notice_config_update_view_put(_id: int = None):
    form = NoticeConfigUpdateForm(MultiDict(request.json))
    if not form.validate():
        abort(400, ','.join(['{}: {}'.format(filed, ','.join(msg)) for filed, msg in form.errors.items()]))

    data = NoticeConfigCRUD.edit_notice_config(_id, **form.data)
    return data.to_dict()
