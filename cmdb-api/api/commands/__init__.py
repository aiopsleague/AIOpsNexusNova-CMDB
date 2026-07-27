# -*- coding:utf-8 -*-
"""Helpers replacing the ``flask.cli`` bits the legacy CLI commands rely on."""
import functools

from api.core.context import RequestContext
from api.core.context import set_ctx


def with_appcontext(func):
    """Drop-in replacement for ``flask.cli.with_appcontext``.

    In the FastAPI port the app-level facilities (``db``, ``cache``,
    ``current_app``) are import-time singletons, so there is no app context
    to push; this only mirrors flask's app-context teardown by removing the
    scoped DB session once the command finishes.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            from api.extensions import db
            db.session.remove()

    return wrapper


def push_request_context():
    """Drop-in replacement for ``current_app.test_request_context().push()``.

    Establishes a request-scoped context so that ``login_user`` /
    ``session`` / ``request`` work inside a CLI command. As on the flask
    side, the context is intentionally left in place for the remainder of
    the process.
    """
    set_ctx(RequestContext())
