# -*- coding:utf-8 -*-

from api.core.context import current_app

from . import routing


class OAuth2(object):
    def __init__(self, app=None, url_prefix=None):
        self._app = app
        if app is not None:
            self.init_app(app, url_prefix)

    @staticmethod
    def init_app(app, url_prefix=None):
        # Configuration defaults
        app.config.setdefault('OAUTH2_GRANT_TYPE', 'authorization_code')
        app.config.setdefault('OAUTH2_RESPONSE_TYPE', 'code')
        app.config.setdefault('OAUTH2_AFTER_LOGIN', '/')

        app.config.setdefault('OIDC_GRANT_TYPE', 'authorization_code')
        app.config.setdefault('OIDC_RESPONSE_TYPE', 'code')
        app.config.setdefault('OIDC_AFTER_LOGIN', '/')

        # Register router (flask: register_blueprint)
        app.include_router(routing.router, prefix=url_prefix or "")

    @property
    def app(self):
        return self._app or current_app
