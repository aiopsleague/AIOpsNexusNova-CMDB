# -*- coding:utf-8 -*-

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import request
from api.lib.cmdb.custom_dashboard import CustomDashboardManager
from api.lib.cmdb.custom_dashboard import SystemConfigManager
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.decorator import args_required
from api.lib.decorator import args_validate
from api.lib.perm.auth import authenticate

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/custom_dashboard")
@router.get("/custom_dashboard/{_id:int}")
@router.get("/custom_dashboard/batch")
@router.get("/custom_dashboard/preview")
def custom_dashboard_api_view_get(_id: int = None):
    return CustomDashboardManager.get()


@router.post("/custom_dashboard")
@router.post("/custom_dashboard/{_id:int}")
@router.post("/custom_dashboard/batch")
@router.post("/custom_dashboard/preview")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Customized_Dashboard,
                     app_cli.op.read, app_cli.admin_name)
@args_validate(CustomDashboardManager.cls)
def custom_dashboard_api_view_post(_id: int = None):
    if request.url.endswith("/preview"):
        return dict(counter=CustomDashboardManager.preview(**request.values))

    cm, counter = CustomDashboardManager.add(**request.values)

    res = cm.to_dict()
    res.update(counter=counter)

    return res


@router.put("/custom_dashboard")
@router.put("/custom_dashboard/{_id:int}")
@router.put("/custom_dashboard/batch")
@router.put("/custom_dashboard/preview")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Customized_Dashboard,
                     app_cli.op.read, app_cli.admin_name)
@args_validate(CustomDashboardManager.cls)
def custom_dashboard_api_view_put(_id: int = None):
    if _id is not None:
        cm, counter = CustomDashboardManager.update(_id, **request.values)

        res = cm.to_dict()
        res.update(counter=counter)

        return res

    CustomDashboardManager.batch_update(request.values.get("id2options"))

    return dict(id2options=request.values.get('id2options'))


@router.delete("/custom_dashboard")
@router.delete("/custom_dashboard/{_id:int}")
@router.delete("/custom_dashboard/batch")
@router.delete("/custom_dashboard/preview")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Customized_Dashboard,
                     app_cli.op.read, app_cli.admin_name)
def custom_dashboard_api_view_delete(_id: int = None):
    CustomDashboardManager.delete(_id)

    return dict(code=200)


@router.get("/system_config")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Service_Tree_Definition,
                     app_cli.op.read, app_cli.admin_name)
@args_required("name", value_required=True)
def system_config_api_view_get():
    return SystemConfigManager.get(request.values['name'])


@router.post("/system_config")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Service_Tree_Definition,
                     app_cli.op.read, app_cli.admin_name)
@args_validate(SystemConfigManager.cls)
@args_required("name", value_required=True)
@args_required("option", value_required=True)
def system_config_api_view_post():
    cm = SystemConfigManager.create_or_update(**request.values)

    return cm.to_dict()


@router.put("/system_config")
def system_config_api_view_put(_id: int = None):
    return system_config_api_view_post()


@router.delete("/system_config")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Service_Tree_Definition,
                     app_cli.op.read, app_cli.admin_name)
@args_required("name")
def system_config_api_view_delete():
    CustomDashboardManager.delete(request.values['name'])

    return dict(code=200)
