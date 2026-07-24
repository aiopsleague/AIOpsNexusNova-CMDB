# -*- coding:utf-8 -*-
"""gettext based i18n replacing flask-babel.

Keeps the ``lazy_gettext`` (``_l``) semantics used by all ``ErrFormat``
classes: the message is translated lazily, inside the request context, using
the locale negotiated from the ``Accept-Language`` header.
"""
import gettext as _gettext
import os

from api.core.context import get_ctx

HERE = os.path.abspath(os.path.dirname(__file__))
LOCALE_DIR = os.path.join(HERE, os.pardir, "translations")

_translations = {}


def _get_translation(lang):
    if lang not in _translations:
        _translations[lang] = _gettext.translation(
            "messages", localedir=LOCALE_DIR, languages=[lang], fallback=True
        )
    return _translations[lang]


def get_locale():
    ctx = get_ctx()
    if ctx is not None and ctx.locale:
        return ctx.locale
    return "en"


def gettext(message, **kwargs):
    translated = _get_translation(get_locale()).gettext(str(message))
    if kwargs:
        return translated.format(**kwargs)
    return translated


class LazyString(object):
    """Evaluates gettext on ``str()`` — mirrors ``flask_babel.speaklater.LazyString``."""

    def __init__(self, message, **kwargs):
        self._message = message
        self._kwargs = kwargs

    def __str__(self):
        return gettext(self._message, **self._kwargs)

    def __repr__(self):
        return f"LazyString({self._message!r})"

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __add__(self, other):
        return str(self) + str(other)

    def __radd__(self, other):
        return str(other) + str(self)

    def __mod__(self, other):
        return str(self) % other

    def __contains__(self, item):
        return item in str(self)

    def format(self, *args, **kwargs):
        return str(self).format(*args, **kwargs)

    def split(self, *args, **kwargs):
        return str(self).split(*args, **kwargs)

    def strip(self, *args, **kwargs):
        return str(self).strip(*args, **kwargs)

    def lower(self):
        return str(self).lower()

    def upper(self):
        return str(self).upper()

    def encode(self, *args, **kwargs):
        return str(self).encode(*args, **kwargs)


def lazy_gettext(message, **kwargs):
    return LazyString(message, **kwargs)
