# -*- coding:utf-8 -*-
"""JSON encoding aligned with the legacy Flask ``MyJSONEncoder``:
- datetime  -> '%Y-%m-%d %H:%M:%S'
- date/time/Decimal/LazyString -> str
"""
import datetime
import decimal
import json

from starlette.responses import JSONResponse


def cmdb_json_default(o):
    from api.core.i18n import LazyString

    if isinstance(o, datetime.datetime):
        return o.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(o, (datetime.date, datetime.time)):
        return str(o)
    if isinstance(o, decimal.Decimal):
        return str(o)
    if isinstance(o, LazyString):
        return str(o)
    if isinstance(o, bytes):
        return o.decode("utf-8", errors="ignore")
    if hasattr(o, "to_dict"):
        return o.to_dict()
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


class CmdbJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            default=cmdb_json_default,
        ).encode("utf-8")
