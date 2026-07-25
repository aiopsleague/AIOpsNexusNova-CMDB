# -*- coding:utf-8 -*-
import json as _json

import requests
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response

from api.core.context import current_app
from api.core.context import request
from api.core.errors import abort

from api.lib.cmdb.grafana import resolve_ci_grafana
from api.lib.common_setting.grafana import GrafanaConfigCRUD
from api.lib.common_setting.grafana_client import rewrite_dashboard_html
from api.lib.common_setting.resp_format import ErrFormat
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

PROXY_TIMEOUT = 30
# headers that must not be forwarded back to the browser as-is
_HOP_BY_HOP = {"connection", "keep-alive", "transfer-encoding", "content-encoding",
               "content-length", "te", "trailer", "upgrade"}


@router.get("/ci/{ci_id:int}/grafana")
def ci_grafana_view_get(ci_id: int):
    return resolve_ci_grafana(ci_id)


@router.api_route("/grafana/proxy/{connection_id:int}/{path:path}",
                  methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"])
def grafana_proxy_view(connection_id: int, path: str):
    """Reverse-proxy grafana through the backend, injecting the service
    account token so the browser never needs the api key nor grafana
    anonymous access. The grafana index html is rewritten so that relative
    asset urls and frontend api calls are routed back through this proxy."""
    connection = GrafanaConfigCRUD().get_connection(connection_id)
    prefix = "/api/v0.1/grafana/proxy/{}".format(connection_id)

    target = "{}/{}".format(connection["url"], path)
    query = str(request.args)  # QueryParams，保留重复参数（如多值 var-x）
    if query:
        target = "{}?{}".format(target, query)

    headers = {
        "Authorization": "Bearer {}".format(connection["api_key"]),
        "Accept": request.headers.get("accept", "*/*"),
    }
    body = None
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        values = request.values
        if values:
            body = _json.dumps(values)
            headers["Content-Type"] = "application/json"

    try:
        resp = requests.request(request.method, target, headers=headers,
                                data=body, timeout=PROXY_TIMEOUT, allow_redirects=False)
    except Exception as e:
        current_app.logger.warning("grafana proxy to {} failed: {}".format(connection["url"], e))
        abort(502, ErrFormat.grafana_proxy_failed.format(str(e)))

    content = resp.content
    content_type = resp.headers.get("content-type", "")
    if "text/html" in content_type:
        content = rewrite_dashboard_html(content.decode("utf-8", errors="replace"), prefix).encode("utf-8")

    out_headers = {k: v for k, v in resp.headers.items() if k.lower() not in _HOP_BY_HOP}
    # 把指向 grafana 根路径的重定向改写回代理前缀，避免浏览器跳出代理
    location = out_headers.get("location") or out_headers.get("Location")
    if location and location.startswith("/"):
        out_headers["location"] = "{}{}".format(prefix, location)
    return Response(content=content, status_code=resp.status_code, headers=out_headers)
