# -*- coding: utf-8 -*-
"""FastAPI application factory — the counterpart of the legacy ``api/app.py``."""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

import settings
from api.core.context import RequestContextMiddleware
from api.core.errors import register_exception_handlers
from api.core.json_enc import CmdbJSONResponse

HERE = os.path.abspath(os.path.dirname(__file__))

logger = logging.getLogger("cmdb")


class RootPathMiddleware(object):
    """Pure ASGI middleware honoring X-Script-Name / X-Scheme,
    replacing the legacy WSGI ``ReverseProxy`` wrapper."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
            script_name = headers.get("x-script-name", "")
            if script_name and scope["path"].startswith(script_name):
                scope["root_path"] = script_name
            scheme = headers.get("x-scheme", "")
            if scheme:
                scope["scheme"] = scheme
        await self.app(scope, receive, send)


def configure_logger():
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(pathname)s %(lineno)d - %(message)s")

    if settings.DEBUG:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    log_file = settings.LOG_PATH
    if log_file and log_file != "/dev/stdout":
        file_handler = RotatingFileHandler(log_file, maxBytes=2 ** 30, backupCount=7)
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))


def configure_upload_dir():
    upload_dir = getattr(settings, "UPLOAD_DIRECTORY", "uploaded_files")
    full_path = os.path.join(os.path.join(HERE, "api"), upload_dir)
    if not os.path.exists(full_path):
        logger.warning(f"{full_path}, not exist, create...")
        os.makedirs(full_path)
    settings.UPLOAD_DIRECTORY_FULL = full_path


def register_routers(app):
    from api.views.entry import api_router
    app.include_router(api_router)


def register_sso(app):
    """Mount the CAS / OAuth2 SSO routers — the counterpart of the legacy
    ``CAS(app)`` / ``OAuth2(app)`` calls in ``api/app.py``.

    The legacy ``init_app`` also supplied config defaults; here they are
    applied to the settings-backed ``current_app.config`` instead, as the
    FastAPI app object has no ``config`` mapping."""
    from api.core.context import current_app
    from api.lib.perm.authentication.cas.routing import router as cas_router
    from api.lib.perm.authentication.oauth2.routing import router as oauth2_router

    config = current_app.config
    for key, default in (
            ('CAS_TOKEN_SESSION_KEY', '_CAS_TOKEN'),
            ('CAS_USERNAME_SESSION_KEY', 'CAS_USERNAME'),
            ('CAS_LOGIN_ROUTE', '/login'),
            ('CAS_LOGOUT_ROUTE', '/logout'),
            ('CAS_VALIDATE_ROUTE', '/serviceValidate'),
            ('OAUTH2_GRANT_TYPE', 'authorization_code'),
            ('OAUTH2_RESPONSE_TYPE', 'code'),
            ('OAUTH2_AFTER_LOGIN', '/'),
            ('OIDC_GRANT_TYPE', 'authorization_code'),
            ('OIDC_RESPONSE_TYPE', 'code'),
            ('OIDC_AFTER_LOGIN', '/')):
        if key not in config:
            config[key] = default

    app.include_router(cas_router)
    app.include_router(oauth2_router)


def create_app():
    app = FastAPI(
        title="CMDB API",
        default_response_class=CmdbJSONResponse,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        openapi_url=settings.OPENAPI_URL,
    )

    configure_logger()
    configure_upload_dir()

    # middleware order: the last one added runs first (outermost).
    # CORS -> Session -> RequestContext -> route
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY,
                       session_cookie="session", https_only=False, same_site="lax")
    app.add_middleware(CORSMiddleware,
                       allow_origins=["*"],
                       allow_credentials=True,
                       allow_methods=["*"],
                       allow_headers=["*"])

    register_exception_handlers(app)
    register_routers(app)
    register_sso(app)

    @app.get("/api/health", include_in_schema=False)
    def health():
        return {"status": "ok"}

    return RootPathMiddleware(app)


app = create_app()
