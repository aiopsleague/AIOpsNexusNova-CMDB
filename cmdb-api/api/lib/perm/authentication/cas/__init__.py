# -*- coding:utf-8 -*-

"""
flask_cas.__init__  (ported to FastAPI)

The flask ``_app_ctx_stack`` / ``_request_ctx_stack`` storage is replaced by
the request-scoped context provided by ``api.core.context`` (``get_ctx()``).
"""

from api.core.context import current_app
from api.core.context import get_ctx
from api.core.context import session

from . import routing


class CAS(object):
    """
    Required Configs:

    |Key             |
    |----------------|
    |CAS_SERVER      |
    |CAS_AFTER_LOGIN |

    Optional Configs:

    |Key                      | Default        |
    |-------------------------|----------------|
    |CAS_TOKEN_SESSION_KEY    | _CAS_TOKEN     |
    |CAS_USERNAME_SESSION_KEY | CAS_USERNAME   |
    |CAS_LOGIN_ROUTE          | '/cas'         |
    |CAS_LOGOUT_ROUTE         | '/cas/logout'  |
    |CAS_VALIDATE_ROUTE       | '/cas/validate'|
    """

    def __init__(self, app=None, url_prefix=None):
        self._app = app
        if app is not None:
            self.init_app(app, url_prefix)

    def init_app(self, app, url_prefix=None):
        # Configuration defaults
        app.config.setdefault('CAS_TOKEN_SESSION_KEY', '_CAS_TOKEN')
        app.config.setdefault('CAS_USERNAME_SESSION_KEY', 'CAS_USERNAME')
        app.config.setdefault('CAS_LOGIN_ROUTE', '/login')
        app.config.setdefault('CAS_LOGOUT_ROUTE', '/logout')
        app.config.setdefault('CAS_VALIDATE_ROUTE', '/serviceValidate')
        # Register router (flask: register_blueprint)
        app.include_router(routing.router, prefix=url_prefix or "")

    def teardown(self, exception):
        ctx = get_ctx()

    @property
    def app(self):
        return self._app or current_app

    @property
    def username(self):
        return session.get(
            self.app.config['CAS_USERNAME_SESSION_KEY'], None)

    @property
    def token(self):
        return session.get(
            self.app.config['CAS_TOKEN_SESSION_KEY'], None)
