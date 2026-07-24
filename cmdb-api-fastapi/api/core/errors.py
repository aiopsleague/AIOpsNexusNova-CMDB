# -*- coding:utf-8 -*-
"""Exception types and handlers reproducing the Flask error contract:
``{"message": str(error)}`` with the original HTTP status code.
"""
import logging
import traceback

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.core.json_enc import CmdbJSONResponse

logger = logging.getLogger("cmdb")


class AbortException(Exception):
    """Raised by ``abort(code, message)`` — the replacement of ``flask.abort``."""

    def __init__(self, code, message=None):
        super().__init__(message)
        self.code = code if isinstance(code, int) else 400
        self.message = str(message) if message is not None else ""


def abort(code, message=None, **kwargs):
    raise AbortException(code, message)


class HTTPError(Exception):
    """Werkzeug-style HTTP exception (``raise BadRequest("...")`` /
    ``except NotFound``), carrying a numeric ``code`` like werkzeug's."""

    code = 500

    def __init__(self, description=None, **kwargs):
        super().__init__(description)
        self.description = str(description) if description is not None else ""
        self.message = self.description

    def __str__(self):
        return self.description


class BadRequest(HTTPError):
    code = 400


class Unauthorized(HTTPError):
    code = 401


class Forbidden(HTTPError):
    code = 403


class NotFound(HTTPError):
    code = 404


async def abort_exception_handler(request: Request, exc: AbortException):
    return CmdbJSONResponse({"message": str(exc.message)}, status_code=exc.code)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return CmdbJSONResponse({"message": str(exc.detail)}, status_code=exc.status_code)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return CmdbJSONResponse({"message": str(exc.errors())}, status_code=400)


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(traceback.format_exc())
    code = getattr(exc, "code", 500)
    if not str(code).isdigit():
        code = 400
    return CmdbJSONResponse({"message": str(exc)}, status_code=int(code))


def register_exception_handlers(app):
    app.add_exception_handler(AbortException, abort_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
