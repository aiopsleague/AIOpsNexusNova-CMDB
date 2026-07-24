# -*- coding:utf-8 -*-
"""Shared singletons — the FastAPI counterpart of the legacy ``api/extensions.py``.

``db`` mimics the Flask-SQLAlchemy API surface (``db.Model``, ``db.Column``,
``db.session`` ...) so the models layer stays almost unchanged.
"""
import sqlalchemy
from celery import Celery

import settings
from api.core.cache import RedisCache
from api.core.database import Base
from api.core.database import db_session
from api.core.database import engine


class _DBShim(object):
    Model = Base
    session = db_session
    engine = engine

    def __getattr__(self, name):
        if hasattr(sqlalchemy, name):
            return getattr(sqlalchemy, name)
        # Flask-SQLAlchemy also exposes orm-level names (relationship, backref, ...)
        import sqlalchemy.orm as sa_orm
        return getattr(sa_orm, name)


db = _DBShim()

celery = Celery(__name__.split(".")[0])
celery.conf.update(settings.CELERY)
celery.conf.update(ONCE=settings.ONCE)

cache = RedisCache()

from api.lib.utils import ESHandler  # noqa: E402
from api.lib.utils import RedisHandler  # noqa: E402

rd = RedisHandler()
rd.init_app()

es = ESHandler()
if getattr(settings, "USE_ES", False):
    es.init_app()

from api.lib.secrets.inner import KeyManage  # noqa: E402

inner_secrets = KeyManage()
