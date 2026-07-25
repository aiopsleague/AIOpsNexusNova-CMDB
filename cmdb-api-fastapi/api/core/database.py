# -*- coding:utf-8 -*-
"""Plain SQLAlchemy engine/session, replacing Flask-SQLAlchemy."""
import math

from sqlalchemy import create_engine
from sqlalchemy.orm import Query
from sqlalchemy.orm import Session as _Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

import settings


class Pagination(object):
    """Minimal stand-in for Flask-SQLAlchemy's ``Pagination``."""

    def __init__(self, query, page, per_page, total, items):
        self.query = query
        self.page = page
        self.per_page = per_page
        self.total = total
        self.items = items

    @property
    def pages(self):
        if self.per_page == 0 or self.total is None:
            return 0
        return int(math.ceil(self.total / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def next_num(self):
        return self.page + 1


class CmdbQuery(Query):
    def paginate(self, page=None, per_page=None, error_out=True, max_per_page=None, count=True):
        page = page or 1
        per_page = per_page or 20
        if count:
            total = self.order_by(None).count()
        else:
            total = None
        items = self.limit(per_page).offset((page - 1) * per_page).all()
        if not items and page != 1 and error_out:
            from api.core.errors import abort
            abort(404, "page not found")
        return Pagination(self, page, per_page, total, items)

    def get_or_404(self, ident, description=None):
        rv = self.get(ident)
        if rv is None:
            from api.core.errors import abort
            abort(404, description)
        return rv

    def first_or_404(self, description=None):
        rv = self.first()
        if rv is None:
            from api.core.errors import abort
            abort(404, description)
        return rv


class CmdbSession(_Session):
    """Session with Flask-SQLAlchemy compat helpers.

    The legacy code base uses ``db.session().using_bind("master")``; with a
    single engine there is nothing to rebind, so this is a no-op.
    """

    def using_bind(self, bind):  # noqa
        return self


engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_recycle=settings.SQLALCHEMY_ENGINE_OPTIONS.get("pool_recycle", 300),
    # uvicorn serves concurrent requests from a 40-thread pool (vs. a handful
    # of single-threaded gunicorn workers on the Flask side), so the SQLAlchemy
    # defaults (5 + 10) saturate under parallel dashboard traffic.
    pool_size=settings.SQLALCHEMY_ENGINE_OPTIONS.get("pool_size", 20),
    max_overflow=settings.SQLALCHEMY_ENGINE_OPTIONS.get("max_overflow", 40),
    echo=settings.SQLALCHEMY_ECHO,
)

# autoflush=False matches the legacy Flask-SQLAlchemy session options.
# scopefunc: key the session registry on the request context (contextvars),
# NOT the thread — endpoints run in anyio's threadpool while middleware runs
# on the event-loop thread, so a thread-scoped session could never be
# remove()d by the request teardown and leaked its connection (#pool exhaustion).
from api.core.context import get_ctx  # noqa: E402  (context.py only imports this module lazily)

db_session = scoped_session(
    sessionmaker(bind=engine, class_=CmdbSession, query_cls=CmdbQuery, autoflush=False, autocommit=False),
    scopefunc=get_ctx,
)

Base = declarative_base()


class _QueryProperty(object):
    """Replicates Flask-SQLAlchemy's ``Model.query``, honoring a
    model-level ``query_class`` attribute (e.g. ``UserQuery``)."""

    def __get__(self, obj, cls):
        query_cls = getattr(cls, "query_class", CmdbQuery)
        return query_cls(cls, session=db_session())


Base.query = _QueryProperty()
