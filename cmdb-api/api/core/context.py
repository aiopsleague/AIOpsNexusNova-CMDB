# -*- coding:utf-8 -*-
"""Request-scoped context emulating the Flask proxies the legacy code relies on.

Legacy modules freely use ``flask.request``, ``flask.session``,
``flask.current_app`` and ``flask_login.current_user``. To keep the business
logic (api/lib) as close to the original as possible, this module provides
drop-in proxies backed by a ``contextvars`` context that is populated by
``RequestContextMiddleware`` for every HTTP request (and manually for Celery
tasks / CLI commands).
"""
import contextvars
import json as _json
import logging

from starlette.middleware.base import BaseHTTPMiddleware

import settings

_ctx = contextvars.ContextVar("cmdb_request_ctx", default=None)


def get_ctx():
    return _ctx.get()


def set_ctx(ctx):
    return _ctx.set(ctx)


def reset_ctx(token):
    _ctx.reset(token)


class UploadedFile(object):
    """Sync wrapper over starlette's ``UploadFile`` emulating
    ``werkzeug.datastructures.FileStorage`` (``.read()``/``.save()``/``.stream``)."""

    def __init__(self, upload_file):
        self._upload = upload_file
        self.filename = upload_file.filename
        self.content_type = upload_file.content_type
        self.stream = upload_file.file

    def read(self, *args, **kwargs):
        return self.stream.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self.stream.seek(*args, **kwargs)

    def save(self, dst):
        from shutil import copyfileobj
        self.stream.seek(0)
        if isinstance(dst, (str, bytes)):
            with open(dst, "wb") as f:
                copyfileobj(self.stream, f)
        else:
            copyfileobj(self.stream, dst)

    def close(self):
        self.stream.close()


class RequestContext(object):
    def __init__(self, raw_request=None, values=None, files=None):
        self.raw = raw_request
        # mirrors flask ``request.values`` after auth_required normalization:
        # a plain mutable dict (JSON body, or form merged with query args)
        self.values = values if values is not None else {}
        self.files = files if files is not None else {}
        self.user = None
        self.locale = None
        self.session = {}


class RequestProxy(object):
    """Emulates the subset of ``flask.request`` used across the code base."""

    def _ctx(self):
        ctx = _ctx.get()
        if ctx is None:
            raise RuntimeError("working outside of request context")
        return ctx

    @property
    def _raw(self):
        return self._ctx().raw

    @property
    def values(self):
        return self._ctx().values

    @values.setter
    def values(self, v):
        self._ctx().values = v

    @property
    def args(self):
        raw = self._raw
        return raw.query_params if raw is not None else {}

    @property
    def headers(self):
        raw = self._raw
        return raw.headers if raw is not None else {}

    @property
    def cookies(self):
        raw = self._raw
        return raw.cookies if raw is not None else {}

    @property
    def method(self):
        raw = self._raw
        return raw.method if raw is not None else "GET"

    @property
    def path(self):
        raw = self._raw
        return raw.url.path if raw is not None else ""

    @property
    def url(self):
        raw = self._raw
        return str(raw.url) if raw is not None else ""

    @property
    def base_url(self):
        raw = self._raw
        return str(raw.base_url) if raw is not None else ""

    @property
    def full_path(self):
        raw = self._raw
        if raw is None:
            return ""
        q = raw.url.query
        return raw.url.path + ("?" + q if q else "")

    @property
    def remote_addr(self):
        raw = self._raw
        return raw.client.host if raw is not None and raw.client else None

    @property
    def files(self):
        return self._ctx().files

    @property
    def session(self):
        return self._ctx().session

    @property
    def json(self):
        return self._ctx().values

    @property
    def endpoint(self):
        raw = self._raw
        if raw is not None and raw.scope.get("endpoint") is not None:
            return getattr(raw.scope["endpoint"], "__name__", None)
        return None

    @property
    def view_args(self):
        # flask: dict of the matched URL rule arguments
        raw = self._raw
        return raw.path_params if raw is not None else {}

    @property
    def referrer(self):
        # flask: the Referer header, None when absent
        raw = self._raw
        return raw.headers.get("referer") if raw is not None else None

    def get_json(self, silent=False, **kwargs):
        values = self._ctx().values
        if values:
            return values
        if silent:
            return None
        raise RuntimeError("no JSON body")

    def __getattr__(self, name):
        raw = self._ctx().raw
        if raw is not None:
            return getattr(raw, name)
        raise AttributeError(name)


class SessionProxy(object):
    """Emulates ``flask.session`` (a signed-cookie backed dict)."""

    def _session(self):
        ctx = _ctx.get()
        if ctx is None:
            raise RuntimeError("working outside of request context")
        return ctx.session

    def __getitem__(self, key):
        return self._session()[key]

    def __setitem__(self, key, value):
        self._session()[key] = value

    def __delitem__(self, key):
        del self._session()[key]

    def __contains__(self, key):
        return key in self._session()

    def __iter__(self):
        return iter(self._session())

    def __len__(self):
        return len(self._session())

    def get(self, key, default=None):
        return self._session().get(key, default)

    def pop(self, key, default=None):
        return self._session().pop(key, default)

    def setdefault(self, key, default=None):
        return self._session().setdefault(key, default)

    def clear(self):
        self._session().clear()

    def keys(self):
        return self._session().keys()

    def items(self):
        return self._session().items()

    def to_dict(self):
        return dict(self._session())


class _ConfigProxy(object):
    """Dict-like view over the uppercase attributes of the settings module."""

    def __init__(self):
        self._store = {k: getattr(settings, k) for k in dir(settings) if k.isupper()}

    def __getitem__(self, key):
        return self._store[key]

    def __setitem__(self, key, value):
        self._store[key] = value
        setattr(settings, key, value)

    def __contains__(self, key):
        return key in self._store

    def get(self, key, default=None):
        return self._store.get(key, default)

    def update(self, *args, **kwargs):
        self._store.update(*args, **kwargs)

    def from_object(self, obj):
        if isinstance(obj, str):
            obj = __import__(obj)
        for k in dir(obj):
            if k.isupper():
                self._store[k] = getattr(obj, k)


class CurrentAppProxy(object):
    """Emulates ``flask.current_app`` (config + logger)."""

    def __init__(self):
        self.__dict__["_config"] = _ConfigProxy()

    @property
    def config(self):
        return self.__dict__["_config"]

    def test_request_context(self, *args, **kwargs):
        """Replacement for ``flask.current_app.test_request_context()`` used by
        Celery tasks: returns a handle whose ``push()`` installs an empty
        request context (so ``request``/``session``/``login_user`` work)."""
        return _PushedRequestContext()

    @property
    def logger(self):
        return logging.getLogger("cmdb")

    @property
    def debug(self):
        return settings.DEBUG

    @property
    def secret_key(self):
        return settings.SECRET_KEY

    def __getattr__(self, name):
        # legacy code occasionally stashes helpers on the app object
        app = self.__dict__["_config"].get("APP_INSTANCE")
        if app is not None and hasattr(app, name):
            return getattr(app, name)
        raise AttributeError(name)


class _PushedRequestContext(object):
    """Handle returned by ``CurrentAppProxy.test_request_context()``."""

    def __init__(self):
        self._token = None

    def push(self):
        self._token = set_ctx(RequestContext())
        return self

    def pop(self):
        if self._token is not None:
            from api.core.database import db_session
            db_session.remove()
            reset_ctx(self._token)
            self._token = None


class _AnonymousUser(object):
    is_authenticated = False
    is_active = False
    is_anonymous = True

    def get_id(self):
        return None

    def __repr__(self):
        return "<AnonymousUser>"


_anonymous = _AnonymousUser()


class CurrentUserProxy(object):
    """Emulates ``flask_login.current_user``."""

    def _get_current_object(self):
        ctx = _ctx.get()
        if ctx is not None and ctx.user is not None:
            return ctx.user
        return _anonymous

    def __getattr__(self, name):
        return getattr(self._get_current_object(), name)

    def __repr__(self):
        return repr(self._get_current_object())

    def __bool__(self):
        return self._get_current_object().is_authenticated


request = RequestProxy()
session = SessionProxy()
current_app = CurrentAppProxy()
current_user = CurrentUserProxy()


def has_request_context():
    return _ctx.get() is not None


def url_for(endpoint, _external=False, **values):
    """Minimal replacement of ``flask.url_for`` (request-bound)."""
    ctx = _ctx.get()
    raw = ctx.raw if ctx is not None else None
    if raw is None:
        raise RuntimeError("working outside of request context")
    path = str(raw.url_for(endpoint, **values))
    return path


def login_user(user):
    ctx = _ctx.get()
    if ctx is not None:
        ctx.user = user


def logout_user():
    ctx = _ctx.get()
    if ctx is not None:
        ctx.user = None


def _best_match_locale(accept_language):
    accepted = settings.ACCEPT_LANGUAGES if hasattr(settings, "ACCEPT_LANGUAGES") else ["en", "zh"]
    if not accept_language:
        return accepted[0]
    for part in accept_language.split(","):
        lang = part.split(";")[0].strip().lower()
        for candidate in accepted:
            if lang == candidate or lang.startswith(candidate + "-"):
                return candidate
    return accepted[0]


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Parse the request once and populate the contextvars context."""

    async def dispatch(self, raw_request, call_next):
        values = {}
        files = {}
        content_type = raw_request.headers.get("content-type", "")
        if raw_request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if "application/json" in content_type:
                try:
                    body = await raw_request.json()
                    if isinstance(body, dict):
                        values = body
                except Exception:
                    try:
                        text = (await raw_request.body()).decode("utf-8")
                        values = _json.loads(text) if text else {}
                    except Exception:
                        values = {}
            elif "form" in content_type or "multipart" in content_type:
                form = await raw_request.form()
                for key, value in form.multi_items():
                    if hasattr(value, "filename"):
                        files[key] = UploadedFile(value)
                    else:
                        values[key] = value
                # flask: request.values = args + form, query args take precedence
                for key, value in raw_request.query_params.items():
                    values[key] = value
        else:
            values = dict(raw_request.query_params)

        ctx = RequestContext(
            raw_request=raw_request,
            values=values,
            files=files,
        )
        ctx.session = raw_request.session  # provided by SessionMiddleware
        ctx.locale = _best_match_locale(raw_request.headers.get("accept-language", ""))

        token = _ctx.set(ctx)
        try:
            response = await call_next(raw_request)
        finally:
            # like Flask-SQLAlchemy's appcontext teardown: return the
            # connection this request's session may still hold to the pool
            from api.core.database import db_session
            db_session.remove()
            _ctx.reset(token)

        return response
