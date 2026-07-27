# -*- coding:utf-8 -*-


from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import current_app
from api.core.context import request

from api.lib.cmdb.ci_type import CITypeManager
from api.lib.cmdb.const import PermEnum
from api.lib.cmdb.const import ResourceTypeEnum
from api.lib.cmdb.perms import CIFilterPermsCRUD
from api.lib.cmdb.preference import PreferenceManager
from api.lib.cmdb.resp_format import ErrFormat
from api.lib.common_setting.decorator import perms_role_required
from api.lib.common_setting.role_perm_base import CMDBApp
from api.lib.decorator import args_required
from api.lib.decorator import args_validate
from api.lib.perm.acl.acl import ACLManager
from api.lib.perm.acl.acl import has_perm_from_args
from api.lib.perm.acl.acl import is_app_admin
from api.lib.perm.acl.acl import validate_permission
from api.lib.perm.auth import authenticate
from api.lib.utils import handle_arg_list

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/preference/ci_types2")
@router.get("/preference/ci_types")
def preference_show_ci_types_view_get():
    instance = request.values.get("instance")
    tree = request.values.get("tree")

    if "ci_types2" in request.url:
        return PreferenceManager.get_types2(instance, tree)

    return PreferenceManager.get_types(instance, tree)


@router.get("/preference/ci_types/{id_or_name}/attributes")
def preference_show_attributes_view_get(id_or_name: str):
    is_subscribed, attributes = PreferenceManager.get_show_attributes(id_or_name)

    attr_filter = CIFilterPermsCRUD.get_attr_filter(int(id_or_name)) if str(id_or_name).isdigit() else []

    if attr_filter:
        attributes = [i for i in attributes if i['name'] in attr_filter]

    return dict(attributes=attributes, is_subscribed=is_subscribed)


@router.post("/preference/ci_types/{id_or_name}/attributes")
@args_required("attr", value_required=False)
@args_validate(PreferenceManager.pref_attr_cls)
def preference_show_attributes_view_post(id_or_name: str):
    id_or_name = int(id_or_name)
    attr_list = handle_arg_list(request.values.get("attr", ""))  # [[attr, false], ]
    orders = list(range(len(attr_list)))

    if attr_list and not is_app_admin('cmdb'):
        resource_name = CITypeManager.get_name_by_id(id_or_name)
        if not ACLManager('cmdb').has_permission(resource_name, ResourceTypeEnum.CI, PermEnum.READ):
            from api.lib.perm.acl.resp_format import ErrFormat
            return abort(403, ErrFormat.resource_no_permission.format(resource_name, PermEnum.READ))

    PreferenceManager.create_or_update_show_attributes(id_or_name, list(zip(attr_list, orders)))

    return dict(type_id=id_or_name,
                attr_order=list(zip(attr_list, orders)))


@router.put("/preference/ci_types/{id_or_name}/attributes")
@has_perm_from_args("id_or_name", ResourceTypeEnum.CI, PermEnum.READ, CITypeManager.get_name_by_id)
def preference_show_attributes_view_put(id_or_name: str):
    return preference_show_attributes_view_post(id_or_name)


@router.get("/preference/tree/view")
def preference_tree_api_view_get():
    return PreferenceManager.get_tree_view()


@router.post("/preference/tree/view")
@args_required("type_id")
@args_required("levels", value_required=False)
@args_validate(PreferenceManager.pref_tree_cls)
def preference_tree_api_view_post():
    type_id = request.values.get("type_id")
    levels = handle_arg_list(request.values.get("levels"))
    if levels:
        if not is_app_admin("cmdb"):
            validate_permission(CITypeManager.get_name_by_id(type_id), ResourceTypeEnum.CI, PermEnum.READ)

    res = PreferenceManager.create_or_update_tree_view(type_id, levels)

    return res and res.to_dict() or {}


@router.put("/preference/tree/view")
def preference_tree_api_view_put():
    return preference_tree_api_view_post()


@router.get("/preference/relation/view/{_id}")
@router.get("/preference/relation/view")
def preference_relation_api_view_get(_id: int = None):
    views, id2type, name2id = PreferenceManager.get_relation_view()

    return dict(views=views, id2type=id2type, name2id=name2id)


@router.post("/preference/relation/view/{_id}")
@router.post("/preference/relation/view")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Service_Tree_Definition,
                     app_cli.op.read, app_cli.admin_name)
@args_required("name")
@args_required("cr_ids")
@args_validate(PreferenceManager.pref_rel_cls)
def preference_relation_api_view_post(_id: int = None):
    name = request.values.get("name")
    is_public = request.values.get("is_public") in current_app.config.get('BOOL_TRUE')
    cr_ids = request.values.get("cr_ids")
    option = request.values.get("option") or None
    views, id2type, name2id = PreferenceManager.create_or_update_relation_view(name, cr_ids, is_public=is_public,
                                                                               option=option)

    return dict(views=views, id2type=id2type, name2id=name2id)


@router.put("/preference/relation/view/{_id}")
@router.put("/preference/relation/view")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Service_Tree_Definition,
                     app_cli.op.read, app_cli.admin_name)
@args_required("name")
def preference_relation_api_view_put(_id: int = None):
    views, id2type, name2id = PreferenceManager.create_or_update_relation_view(_id=_id, **request.values)

    return dict(views=views, id2type=id2type, name2id=name2id)


@router.delete("/preference/relation/view/{_id}")
@router.delete("/preference/relation/view")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Service_Tree_Definition,
                     app_cli.op.read, app_cli.admin_name)
@args_required("name")
def preference_relation_api_view_delete(_id: int = None):
    name = request.values.get("name")
    PreferenceManager.delete_relation_view(name)

    return dict(name=name)


@router.get("/preference/search/option/{_id}")
@router.get("/preference/search/option")
def preference_search_option_view_get(_id: int = None):
    res = PreferenceManager.get_search_option(**request.values)

    return res


@router.post("/preference/search/option/{_id}")
@router.post("/preference/search/option")
@args_required("name", value_required=True)
@args_required("option", value_required=True)
@args_validate(PreferenceManager.pre_so_cls)
def preference_search_option_view_post(_id: int = None):
    res = PreferenceManager.add_search_option(**request.values)

    return res.to_dict()


@router.put("/preference/search/option/{_id}")
@router.put("/preference/search/option")
@args_validate(PreferenceManager.pre_so_cls)
def preference_search_option_view_put(_id: int = None):
    res = PreferenceManager.update_search_option(_id, **request.values)

    return res.to_dict()


@router.delete("/preference/search/option/{_id}")
@router.delete("/preference/search/option")
def preference_search_option_view_delete(_id: int = None):
    PreferenceManager.delete_search_option(_id)

    return dict(id=_id)


@router.post("/preference/relation/view/roles/{rid}/grant")
def preference_relation_grant_view_post(rid: int):
    name = request.values.get("name")
    perms = request.values.get('perms')

    acl = ACLManager('cmdb')
    if not acl.has_permission(name, ResourceTypeEnum.RELATION_VIEW, PermEnum.GRANT) and \
            not is_app_admin('cmdb'):
        return abort(403, ErrFormat.no_permission.format(name, PermEnum.GRANT))

    acl.grant_resource_to_role_by_rid(name, rid, ResourceTypeEnum.RELATION_VIEW, perms)

    return dict(code=200)


@router.post("/preference/relation/view/roles/{rid}/revoke")
def preference_relation_revoke_view_post(rid: int):
    name = request.values.get("name")
    perms = request.values.get('perms')

    acl = ACLManager('cmdb')
    if not acl.has_permission(name, ResourceTypeEnum.RELATION_VIEW, PermEnum.GRANT) and \
            not is_app_admin('cmdb'):
        return abort(403, ErrFormat.no_permission.format(name, PermEnum.GRANT))

    acl.revoke_resource_from_role_by_rid(name, rid, ResourceTypeEnum.RELATION_VIEW, perms)

    return dict(code=200)


@router.post("/preference/ci_types/order")
def preference_ci_type_order_view_post():
    type_ids = request.values.get("type_ids")
    is_tree = request.values.get("is_tree") in current_app.config.get('BOOL_TRUE')

    PreferenceManager.upsert_ci_type_order(type_ids, is_tree)

    return dict(type_ids=type_ids, is_tree=is_tree)


@router.get("/preference/auto_subscription")
def preference_auto_subscription_view_get():
    config = PreferenceManager.get_auto_subscription_config()
    return config or {}


@router.put("/preference/auto_subscription")
@args_required("base_strategy")
def preference_auto_subscription_view_put():
    base_strategy = request.values.get("base_strategy")
    group_ids = request.values.get("group_ids")
    type_ids = request.values.get("type_ids")
    enabled = request.values.get("enabled", 1) in current_app.config.get('BOOL_TRUE')
    description = request.values.get("description")

    if base_strategy not in ['all', 'none']:
        return abort(400, "base_strategy must be 'all' or 'none'")

    if group_ids:
        try:
            group_ids = [int(x) for x in group_ids.split(',') if x.strip()]
        except ValueError:
            return abort(400, "Invalid group_ids format")

    if type_ids:
        try:
            type_ids = [int(x) for x in type_ids.split(',') if x.strip()]
        except ValueError:
            return abort(400, "Invalid type_ids format")

    result = PreferenceManager.create_or_update_auto_subscription_config(
        base_strategy=base_strategy,
        group_ids=group_ids,
        type_ids=type_ids,
        enabled=enabled,
        description=description
    )

    return result.to_dict()


@router.delete("/preference/auto_subscription")
def preference_auto_subscription_view_delete():
    PreferenceManager.delete_auto_subscription_config()
    return dict(message="Auto subscription config deleted")


@router.patch("/preference/auto_subscription/toggle")
@args_required("enabled")
def preference_auto_subscription_toggle_view_patch():
    enabled = request.values.get("enabled") in current_app.config.get('BOOL_TRUE')

    result = PreferenceManager.toggle_auto_subscription_config(enabled)
    return result.to_dict()
