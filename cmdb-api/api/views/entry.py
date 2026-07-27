# -*- coding:utf-8 -*-
"""Root router aggregating all sub-routers.

Mirrors the legacy blueprint layout (``api/views/entry.py``):
- account:         /api
- cmdb:            /api/v0.1        (every module under api/views/cmdb)
- acl:             /api/v1/acl      (every module under api/views/acl)
- common_setting:  /api/common-setting/v1
"""
import importlib
import pkgutil

from fastapi import APIRouter

from api.views import account

api_router = APIRouter()

api_router.include_router(account.router, prefix="/api")


def _include_tree(package_name, prefix):
    package = importlib.import_module(package_name)
    for module_info in pkgutil.walk_packages(package.__path__, package_name + "."):
        module = importlib.import_module(module_info.name)
        router = getattr(module, "router", None)
        if router is not None:
            api_router.include_router(router, prefix=prefix)


_include_tree("api.views.cmdb", "/api/v0.1")
_include_tree("api.views.acl", "/api/v1/acl")
_include_tree("api.views.common_setting", "/api/common-setting/v1")
