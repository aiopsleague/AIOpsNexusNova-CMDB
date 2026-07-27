# -*- coding:utf-8 -*-


from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import request

from api.lib.cmdb.relation_type import RelationTypeManager
from api.lib.cmdb.resp_format import ErrFormat
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.decorator import args_required
from api.lib.decorator import args_validate
from api.lib.perm.auth import authenticate

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/relation_types/{rel_id}")
@router.get("/relation_types")
def relation_type_view_get(rel_id: int = None):
    return [i.to_dict() for i in RelationTypeManager.get_all()]


@router.post("/relation_types/{rel_id}")
@router.post("/relation_types")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Relationship_Types,
                     app_cli.op.read, app_cli.admin_name)
@args_required("name")
@args_validate(RelationTypeManager.cls)
def relation_type_view_post(rel_id: int = None):
    name = request.values.get("name") or abort(400, ErrFormat.argument_value_required.format("name"))
    rel = RelationTypeManager.add(name)

    return rel.to_dict()


@router.put("/relation_types/{rel_id}")
@router.put("/relation_types")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Relationship_Types,
                     app_cli.op.read, app_cli.admin_name)
@args_required("name")
@args_validate(RelationTypeManager.cls)
def relation_type_view_put(rel_id: int = None):
    name = request.values.get("name") or abort(400, ErrFormat.argument_value_required.format("name"))
    rel = RelationTypeManager.update(rel_id, name)

    return rel.to_dict()


@router.delete("/relation_types/{rel_id}")
@router.delete("/relation_types")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Relationship_Types,
                     app_cli.op.read, app_cli.admin_name)
def relation_type_view_delete(rel_id: int = None):
    RelationTypeManager.delete(rel_id)

    return dict(rel_id=rel_id)
