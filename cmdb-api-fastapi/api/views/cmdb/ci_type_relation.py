# -*- coding:utf-8 -*- 


from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import request

from api.lib.cmdb.ci_type import CITypeManager
from api.lib.cmdb.ci_type import CITypeRelationManager
from api.lib.cmdb.const import PermEnum
from api.lib.cmdb.const import ResourceTypeEnum
from api.lib.cmdb.preference import PreferenceManager
from api.lib.cmdb.resp_format import ErrFormat
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.decorator import args_required
from api.lib.perm.acl.acl import ACLManager
from api.lib.perm.acl.acl import has_perm_from_args
from api.lib.perm.acl.acl import is_app_admin
from api.lib.perm.auth import authenticate
from api.lib.utils import handle_arg_list

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/ci_type_relations/{parent_id:int}/recursive_level2children")
@router.get("/ci_type_relations/{parent_id:int}/children")
def get_children_view_get(parent_id: int = None):
    if request.url.endswith("recursive_level2children"):
        return CITypeRelationManager.recursive_level2children(parent_id)

    return dict(children=CITypeRelationManager.get_children(parent_id))


@router.get("/ci_type_relations/{child_id:int}/parents")
def get_parents_view_get(child_id: int = None):
    return dict(parents=CITypeRelationManager.get_parents(child_id))


@router.get("/ci_type_relations/path")
@args_required("source_type_id", "target_type_ids")
def ci_type_relation_path_view_get():
    source_type_id = request.values.get("source_type_id")
    target_type_ids = handle_arg_list(request.values.get("target_type_ids"))

    paths = CITypeRelationManager.find_path(source_type_id, target_type_ids)

    return dict(paths=paths)


@router.get("/ci_type_relations")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Service_Tree_Definition,
                     app_cli.op.read, app_cli.admin_name)
def ci_type_relation_view_get():
    res, type2attributes = CITypeRelationManager.get()

    return dict(relations=res, type2attributes=type2attributes)


@router.post("/ci_type_relations/{parent_id:int}/{child_id:int}")
@has_perm_from_args("parent_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
@args_required("relation_type_id")
def ci_type_relation_view_post(parent_id: int = None, child_id: int = None):
    relation_type_id = request.values.get("relation_type_id")
    constraint = request.values.get("constraint")
    parent_attr_ids = request.values.get("parent_attr_ids")
    child_attr_ids = request.values.get("child_attr_ids")
    ctr_id = CITypeRelationManager.add(parent_id, child_id, relation_type_id, constraint,
                                       parent_attr_ids, child_attr_ids)

    return dict(ctr_id=ctr_id)


@router.delete("/ci_type_relations/{parent_id:int}/{child_id:int}")
@has_perm_from_args("parent_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
def ci_type_relation_view_delete(parent_id: int = None, child_id: int = None):
    CITypeRelationManager.delete_2(parent_id, child_id)

    return dict(code=200, parent_id=parent_id, child_id=child_id)


@router.delete("/ci_type_relations/{ctr_id:int}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Model_Relationships,
                     app_cli.op.read, app_cli.admin_name)
def ci_type_relation_delete2_view_delete(ctr_id: int = None):
    CITypeRelationManager.delete(ctr_id)

    return dict(code=200, ctr_id=ctr_id)


@router.post("/ci_type_relations/{parent_id:int}/{child_id:int}/roles/{rid:int}/grant")
def ci_type_relation_grant_view_post(parent_id: int = None, child_id: int = None, rid: int = None):
    p = CITypeManager.check_is_existed(parent_id)
    c = CITypeManager.check_is_existed(child_id)
    resource_name = CITypeRelationManager.acl_resource_name(p.name, c.name)

    perms = request.values.get('perms')

    acl = ACLManager('cmdb')
    if not acl.has_permission(resource_name, ResourceTypeEnum.CI_TYPE_RELATION, PermEnum.GRANT) and \
            not is_app_admin('cmdb'):
        return abort(403, ErrFormat.no_permission.format(resource_name, PermEnum.GRANT))

    acl.grant_resource_to_role_by_rid(resource_name, rid, ResourceTypeEnum.CI_TYPE_RELATION, perms)

    return dict(code=200)


@router.post("/ci_type_relations/{parent_id:int}/{child_id:int}/roles/{rid:int}/revoke")
def ci_type_relation_revoke_view_post(parent_id: int = None, child_id: int = None, rid: int = None):
    p = CITypeManager.check_is_existed(parent_id)
    c = CITypeManager.check_is_existed(child_id)
    resource_name = CITypeRelationManager.acl_resource_name(p.name, c.name)

    perms = request.values.get('perms')
    acl = ACLManager('cmdb')
    if not acl.has_permission(resource_name, ResourceTypeEnum.CI_TYPE_RELATION, PermEnum.GRANT) and \
            not is_app_admin('cmdb'):
        return abort(403, ErrFormat.no_permission.format(resource_name, PermEnum.GRANT))

    acl.revoke_resource_from_role_by_rid(resource_name, rid, ResourceTypeEnum.CI_TYPE_RELATION, perms)

    return dict(code=200)


@router.get("/ci_type_relations/{parent_id:int}/{child_id:int}/can_edit")
def ci_type_relation_can_edit_view_get(parent_id: int = None, child_id: int = None):
    return dict(result=PreferenceManager.can_edit_relation(parent_id, child_id))
