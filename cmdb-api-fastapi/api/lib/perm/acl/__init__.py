# -*- coding:utf-8 -*-


from functools import wraps

from api.core.errors import abort
from api.core.context import request


def __getattr__(name):
    # NOTE(fastapi-port): lazy re-exports to break the circular import chain
    # models.acl -> lib.perm.acl -> cache -> models.acl
    if name == "AppCache":
        from api.lib.perm.acl.cache import AppCache
        return AppCache
    if name == "ErrFormat":
        from api.lib.perm.acl.resp_format import ErrFormat
        return ErrFormat
    raise AttributeError(name)


def validate_app(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        from api.lib.perm.acl.cache import AppCache
        from api.lib.perm.acl.resp_format import ErrFormat

        if not request.headers.get('App-Access-Token', '').strip():
            app_id = request.values.get('app_id')
            app = AppCache.get(app_id)
            if app is None:
                return abort(400, ErrFormat.app_not_found.format("id={}".format(app_id)))
            request.values['app_id'] = app.id

        return func(*args, **kwargs)

    return wrapper
