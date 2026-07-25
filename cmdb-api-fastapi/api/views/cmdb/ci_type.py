# -*- coding:utf-8 -*-


import json
from io import BytesIO

from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import current_app
from api.core.context import request
from api.core.responses import send_file

from api.lib.cmdb.cache import AttributeCache
from api.lib.cmdb.cache import CITypeCache
from api.lib.cmdb.ci import CITriggerManager
from api.lib.cmdb.ci_type import CITypeAttributeGroupManager
from api.lib.cmdb.ci_type import CITypeAttributeManager
from api.lib.cmdb.ci_type import CITypeGroupManager
from api.lib.cmdb.ci_type import CITypeInheritanceManager
from api.lib.cmdb.ci_type import CITypeManager
from api.lib.cmdb.ci_type import CITypeTemplateManager
from api.lib.cmdb.ci_type import CITypeTriggerManager
from api.lib.cmdb.ci_type import CITypeUniqueConstraintManager
from api.lib.cmdb.const import PermEnum, ResourceTypeEnum
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
from api.lib.perm.acl.acl import role_required
from api.lib.perm.acl.cache import AppCache
from api.lib.perm.acl.role import RoleCRUD
from api.lib.perm.acl.role import RoleRelationCRUD
from api.lib.perm.auth import auth_with_app_token
from api.lib.perm.auth import authenticate
from api.lib.utils import handle_arg_list

app_cli = CMDBApp()

router = APIRouter(dependencies=[Depends(authenticate)])


# NOTE(fastapi-port): starlette matches routes in registration order, so all
# static single-segment paths under ``/ci_types`` (``groups``, ``query``,
# ``attributes``, ``common_attributes``, ``can_define_computed``, ``icons``,
# ...) are registered before the ``/ci_types/{type_name}`` catch-all of
# ``ci_type_view_get`` at the bottom of this module. ``{type_id:int}`` uses
# the starlette int convertor to mirror flask's ``<int:type_id>`` (non-numeric
# names fall through to ``{type_name}``).


@router.post("/ci_types/inheritance")
@args_required("parent_ids")
@args_required("child_id")
@has_perm_from_args("child_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
def ci_type_inheritance_view_post():
    CITypeInheritanceManager.add(request.values['parent_ids'], request.values['child_id'])

    return dict(**request.values)


@router.delete("/ci_types/inheritance")
@args_required("parent_id")
@args_required("child_id")
@has_perm_from_args("child_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
def ci_type_inheritance_view_delete():
    CITypeInheritanceManager.delete(request.values['parent_id'], request.values['child_id'])

    return dict(**request.values)


@router.get("/ci_types/groups/config")
@router.get("/ci_types/groups")
def ci_type_group_view_get():
    config_required = True if "/config" in request.url else False
    need_other = request.values.get("need_other")

    return CITypeGroupManager.get(need_other, config_required)


@router.post("/ci_types/groups/config")
@router.post("/ci_types/groups")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Model_Configuration,
                     app_cli.op.create_CIType_group, app_cli.admin_name)
@args_required("name")
@args_validate(CITypeGroupManager.cls)
def ci_type_group_view_post():
    name = request.values.get("name")
    group = CITypeGroupManager.add(name)

    return group.to_dict()


@router.put("/ci_types/groups/{gid:int}")
@router.put("/ci_types/groups/config")
@router.put("/ci_types/groups")
@args_validate(CITypeGroupManager.cls)
def ci_type_group_view_put(gid: int = None):
    name = request.values.get('name') or abort(400, ErrFormat.argument_value_required.format("name"))
    type_ids = request.values.get('type_ids')

    CITypeGroupManager.update(gid, name, type_ids)

    return dict(gid=gid)


@router.delete("/ci_types/groups/{gid:int}")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Model_Configuration,
                     app_cli.op.delete_CIType_group, app_cli.admin_name)
def ci_type_group_view_delete(gid: int = None):
    type_ids = request.values.get("type_ids")
    CITypeGroupManager.delete(gid, type_ids)

    return dict(gid=gid)


@router.put("/ci_types/groups/order")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Model_Configuration,
                     app_cli.op.update_CIType_group, app_cli.admin_name)
def ci_type_group_order_view_put():
    group_ids = request.values.get('group_ids')
    CITypeGroupManager.order(group_ids)

    return dict(group_ids=group_ids)


@router.get("/ci_types/query")
@args_required("q")
def ci_type_query_view_get():
    q = request.args.get("q")
    res = CITypeManager.query(q)

    return dict(ci_type=res)


@router.get("/ci_types/attributes")
@args_required("type_ids", value_required=True)
def ci_types_attribute_view_get():
    type_ids = handle_arg_list(request.values.get('type_ids'))

    attr_names = set()
    attributes = list()
    for type_id in type_ids:
        _attributes = CITypeAttributeManager.get_attributes_by_type_id(type_id)
        for _attr in _attributes:
            if _attr['name'] not in attr_names:
                attr_names.add(_attr['name'])
                attributes.append(_attr)

    return dict(attributes=attributes)


@router.get("/ci_types/{type_name}/attributes")
@router.get("/ci_types/{type_id:int}/attributes")
@router.get("/ci_types/common_attributes")
def ci_type_attribute_view_get(type_id: int = None, type_name: str = None):
    if request.path.endswith("/common_attributes"):
        type_ids = handle_arg_list(request.values.get('type_ids'))

        return dict(attributes=CITypeAttributeManager.get_common_attributes(type_ids))

    t = CITypeCache.get(type_id) or CITypeCache.get(type_name) or abort(404, ErrFormat.ci_type_not_found)
    type_id = t.id
    unique_id = t.unique_id
    unique = AttributeCache.get(unique_id)
    unique = unique and unique.name

    attr_filter = CIFilterPermsCRUD.get_attr_filter(type_id)
    attributes = CITypeAttributeManager.get_attributes_by_type_id(type_id)
    if attr_filter:
        attributes = [i for i in attributes if i['name'] in attr_filter]

    return dict(attributes=attributes,
                type_id=type_id,
                unique_id=unique_id,
                unique=unique)


@router.post("/ci_types/{type_id:int}/attributes")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
@args_required("attr_id")
def ci_type_attribute_view_post(type_id: int = None):
    attr_id_list = handle_arg_list(request.values.get("attr_id"))
    params = request.values
    params.pop("attr_id", "")

    CITypeAttributeManager.add(type_id, attr_id_list, **params)

    return dict(attributes=attr_id_list)


@router.put("/ci_types/{type_id:int}/attributes")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
@args_required("attributes")
def ci_type_attribute_view_put(type_id: int = None):
    """
    attributes is list, only support raw data request
    :param type_id:
    :return:
    """
    attributes = request.values.get("attributes")
    current_app.logger.debug(attributes)
    if not isinstance(attributes, list):
        return abort(400, ErrFormat.argument_attributes_must_be_list)

    CITypeAttributeManager.update(type_id, attributes)

    return dict(attributes=attributes)


@router.delete("/ci_types/{type_id:int}/attributes")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
@args_required("attr_id")
def ci_type_attribute_view_delete(type_id: int = None):
    """
    Form request: attr_id is a string, separated by commas
    Raw data request: attr_id is a list
    :param type_id:
    :return:
    """
    attr_id_list = handle_arg_list(request.values.get("attr_id", ""))

    CITypeAttributeManager.delete(type_id, attr_id_list)

    return dict(attributes=attr_id_list)


@router.get("/ci_types/can_define_computed")
@router.head("/ci_types/can_define_computed", include_in_schema=False)
@role_required(PermEnum.CONFIG)
def ci_type_can_define_computed_get():
    return dict(code=200)


@router.get("/ci_types/template/export")
@router.get("/ci_types/template/import")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Model_Configuration,
                     app_cli.op.download_CIType, app_cli.admin_name)
def ci_type_template_view_get():  # export
    type_ids = list(map(int, handle_arg_list(request.values.get('type_ids')))) or None
    return dict(ci_type_template=CITypeTemplateManager.export_template(type_ids=type_ids))


@router.post("/ci_types/template/export")
@router.post("/ci_types/template/import")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Model_Configuration,
                     app_cli.op.download_CIType, app_cli.admin_name)
def ci_type_template_view_post():  # import
    tpt = request.values.get('ci_type_template') or {}

    CITypeTemplateManager().import_template(tpt)

    return dict(code=200)


@router.get("/ci_types/template/export/file")
@router.get("/ci_types/template/import/file")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Model_Configuration,
                     app_cli.op.download_CIType, app_cli.admin_name)
def ci_type_template_file_view_get():  # export
    tpt_json = CITypeTemplateManager.export_template()
    tpt_json = dict(ci_type_template=tpt_json)

    bf = BytesIO()
    bf.write(bytes(json.dumps(tpt_json).encode('utf-8')))
    bf.seek(0)

    return send_file(bf,
                     as_attachment=True,
                     download_name="cmdb_template.json",
                     mimetype='application/json',
                     max_age=0)


@router.post("/ci_types/template/export/file")
@router.post("/ci_types/template/import/file")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Model_Configuration,
                     app_cli.op.download_CIType, app_cli.admin_name)
def ci_type_template_file_view_post():  # import
    f = request.files.get('file')

    if f is None:
        return abort(400, ErrFormat.argument_file_not_found)

    content = f.read()
    try:
        content = json.loads(content)
    except:
        return abort(400, ErrFormat.invalid_json)
    tpt = content.get('ci_type_template')

    CITypeTemplateManager().import_template(tpt)

    return dict(code=200)


@router.post("/ci_types/{type_id:int}/enable")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
def enable_ci_type_view_post(type_id: int = None):
    enable = request.values.get("enable", True)
    CITypeManager.set_enabled(type_id, enabled=enable)

    return dict(type_id=type_id, enable=enable)


@router.post("/ci_types/{type_id:int}/attributes/transfer")
@args_required('from')
@args_required('to')
def ci_type_attribute_transfer_view_post(type_id: int = None):
    _from = request.values.get('from')  # {'attr_id': xx, 'group_id': xx, 'group_name': xx}
    _to = request.values.get('to')  # {'group_id': xx, 'group_name': xx, 'order': xxx}

    CITypeAttributeManager.transfer(type_id, _from, _to)

    return dict(code=200)


@router.post("/ci_types/{type_id:int}/attribute_groups/transfer")
@args_required('from')
@args_required('to')
def ci_type_attribute_group_transfer_view_post(type_id: int = None):
    _from = request.values.get('from')  # group_id or group_name
    _to = request.values.get('to')  # group_id or group_name

    CITypeAttributeGroupManager.transfer(type_id, _from, _to)

    return dict(code=200)


@router.get("/ci_types/{type_id:int}/attribute_groups")
def ci_type_attribute_group_view_get(type_id: int = None):
    need_other = request.values.get("need_other")
    groups = CITypeAttributeGroupManager.get_by_type_id(type_id, need_other)

    attr_filter = CIFilterPermsCRUD.get_attr_filter(type_id)
    if attr_filter:
        for group in groups:
            group['attributes'] = [attr for attr in (group.get('attributes') or []) if attr['name'] in attr_filter]

    return groups


@router.post("/ci_types/{type_id:int}/attribute_groups")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
@args_required("name")
@args_validate(CITypeAttributeGroupManager.cls)
def ci_type_attribute_group_view_post(type_id: int = None):
    name = request.values.get("name").strip()
    order = request.values.get("order") or 0
    attrs = handle_arg_list(request.values.get("attributes", ""))
    orders = list(range(len(attrs)))

    attr_order = list(zip(attrs, orders))
    group = CITypeAttributeGroupManager.create_or_update(type_id, name, attr_order, order)

    return dict(group_id=group.id)


@router.put("/ci_types/attribute_groups/{group_id:int}")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
@args_required("name")
@args_validate(CITypeAttributeGroupManager.cls)
def ci_type_attribute_group_view_put(group_id: int = None):
    name = request.values.get("name")
    order = request.values.get("order") or 0
    attrs = handle_arg_list(request.values.get("attributes", ""))
    orders = list(range(len(attrs)))

    attr_order = list(zip(attrs, orders))
    CITypeAttributeGroupManager.update(group_id, name, attr_order, order)

    return dict(group_id=group_id)


@router.delete("/ci_types/attribute_groups/{group_id:int}")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
def ci_type_attribute_group_view_delete(group_id: int = None):
    CITypeAttributeGroupManager.delete(group_id)

    return dict(group_id=group_id)


@router.get("/ci_types/{type_id:int}/unique_constraint")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
def ci_type_unique_constraint_view_get(type_id: int = None):
    return CITypeUniqueConstraintManager.get_detail(type_id)


@router.post("/ci_types/{type_id:int}/unique_constraint")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
@args_required("attr_ids")
def ci_type_unique_constraint_view_post(type_id: int = None):
    attr_ids = request.values.get('attr_ids')

    return CITypeUniqueConstraintManager().add(type_id, attr_ids)


@router.put("/ci_types/{type_id:int}/unique_constraint/{_id:int}")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
@args_required("attr_ids")
def ci_type_unique_constraint_view_put(type_id: int = None, _id: int = None):
    assert type_id is not None

    attr_ids = request.values.get('attr_ids')

    return CITypeUniqueConstraintManager().update(_id, attr_ids)


@router.delete("/ci_types/{type_id:int}/unique_constraint/{_id:int}")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
def ci_type_unique_constraint_view_delete(type_id: int = None, _id: int = None):
    assert type_id is not None

    CITypeUniqueConstraintManager().delete(_id)

    return dict(code=200)


@router.get("/ci_types/{type_id:int}/triggers")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
def ci_type_trigger_view_get(type_id: int = None):
    return CITypeTriggerManager.get(type_id)


@router.post("/ci_types/{type_id:int}/triggers")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
@args_required("option")
def ci_type_trigger_view_post(type_id: int = None):
    attr_id = request.values.get('attr_id') or None
    option = request.values.get('option')

    return CITypeTriggerManager().add(type_id, attr_id, option)


@router.put("/ci_types/{type_id:int}/triggers/{_id:int}")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
@args_required("option")
def ci_type_trigger_view_put(type_id: int = None, _id: int = None):
    assert type_id is not None

    option = request.values.get('option')
    attr_id = request.values.get('attr_id')

    return CITypeTriggerManager().update(_id, attr_id, option)


@router.delete("/ci_types/{type_id:int}/triggers/{_id:int}")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
def ci_type_trigger_view_delete(type_id: int = None, _id: int = None):
    assert type_id is not None

    CITypeTriggerManager().delete(_id)

    return dict(code=200)


@router.post("/ci_types/{type_id:int}/triggers/{_id:int}/test_notify")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
def ci_type_trigger_test_view_post(type_id: int = None, _id: int = None):
    CITriggerManager().trigger_notify_test(type_id, _id)

    return dict(code=200)


@router.post("/ci_types/{type_id:int}/roles/{rid:int}/grant")
def ci_type_grant_view_post(type_id: int = None, rid: int = None):
    perms = request.values.pop('perms', None)

    if request.values.get('attr_filter'):
        request.values['attr_filter'] = handle_arg_list(request.values.get('attr_filter', ''))

    _type = CITypeCache.get(type_id)
    type_name = _type and _type.name or abort(404, ErrFormat.ci_type_not_found)
    acl = ACLManager('cmdb')
    if not acl.has_permission(type_name, ResourceTypeEnum.CI_TYPE, PermEnum.GRANT) and not is_app_admin('cmdb'):
        return abort(403, ErrFormat.no_permission.format(type_name, PermEnum.GRANT))

    if perms and not request.values.get('id_filter'):
        acl.grant_resource_to_role_by_rid(type_name, rid, ResourceTypeEnum.CI_TYPE, perms, rebuild=False)

    new_resource = None
    if 'ci_filter' in request.values or 'attr_filter' in request.values or 'id_filter' in request.values:
        new_resource = CIFilterPermsCRUD().add(type_id=type_id, rid=rid, **request.values)

    if not new_resource:
        from api.tasks.acl import role_rebuild
        from api.lib.perm.acl.const import ACL_QUEUE

        app_id = AppCache.get('cmdb').id
        role_rebuild.apply_async(args=(rid, app_id), queue=ACL_QUEUE)

    return dict(code=200)


@router.post("/ci_types/{type_id:int}/roles/{rid:int}/revoke")
@args_required('perms')
def ci_type_revoke_view_post(type_id: int = None, rid: int = None):
    perms = request.values.pop('perms', None)

    if request.values.get('attr_filter'):
        request.values['attr_filter'] = handle_arg_list(request.values.get('attr_filter', ''))

    _type = CITypeCache.get(type_id)
    type_name = _type and _type.name or abort(404, ErrFormat.ci_type_not_found)
    acl = ACLManager('cmdb')
    if not acl.has_permission(type_name, ResourceTypeEnum.CI_TYPE, PermEnum.GRANT) and not is_app_admin('cmdb'):
        return abort(403, ErrFormat.no_permission.format(type_name, PermEnum.GRANT))

    app_id = AppCache.get('cmdb').id
    resource = None

    if request.values.get('id_filter'):
        CIFilterPermsCRUD().delete2(
            type_id=type_id, rid=rid, id_filter=request.values['id_filter'],
            parent_path=request.values.get('parent_path'))

        return dict(type_id=type_id, rid=rid)

    acl.revoke_resource_from_role_by_rid(type_name, rid, ResourceTypeEnum.CI_TYPE, perms, rebuild=False)

    if PermEnum.READ in perms or not perms:
        resource = CIFilterPermsCRUD().delete(type_id=type_id, rid=rid)

    if not resource:
        from api.tasks.acl import role_rebuild
        from api.lib.perm.acl.const import ACL_QUEUE

        role_rebuild.apply_async(args=(rid, app_id), queue=ACL_QUEUE)

    users = RoleRelationCRUD.get_users_by_rid(rid, app_id)
    for i in (users or []):
        if i.get('role', {}).get('id') and not RoleCRUD.has_permission(
                i.get('role').get('id'), type_name, ResourceTypeEnum.CI_TYPE, app_id, PermEnum.READ):
            PreferenceManager.delete_by_type_id(type_id, i.get('uid'))

    return dict(type_id=type_id, rid=rid)


@router.get("/ci_types/{type_id:int}/filters/permissions")
@auth_with_app_token
def ci_type_filter_permission_view_get(type_id: int = None):
    return CIFilterPermsCRUD().get(type_id)


@router.get("/ci_types/{type_name}")
@router.get("/ci_types/{type_id:int}")
@router.get("/ci_types")
@router.get("/ci_types/icons")
def ci_type_view_get(type_id: int = None, type_name: str = None):
    if request.url.endswith("icons"):
        return CITypeManager().get_icons()

    q = request.values.get("type_name")
    type_ids = handle_arg_list(request.values.get("type_ids"))
    type_ids = type_ids or (type_id and [type_id])
    if type_ids:
        ci_types = []
        for _type_id in type_ids:
            ci_type = CITypeCache.get(_type_id)
            if ci_type is None:
                return abort(404, ErrFormat.ci_type_not_found)

            ci_type = ci_type.to_dict()
            ci_type['parent_ids'] = CITypeInheritanceManager.get_parents(_type_id)
            ci_type['show_name'] = ci_type.get('show_id') and AttributeCache.get(ci_type['show_id']).name
            ci_type['unique_name'] = ci_type['unique_id'] and AttributeCache.get(ci_type['unique_id']).name
            ci_types.append(ci_type)
    elif type_name is not None:
        ci_type = CITypeCache.get(type_name)
        if ci_type is not None:
            ci_type = ci_type.to_dict()
            ci_type['parent_ids'] = CITypeInheritanceManager.get_parents(ci_type['id'])
            ci_types = [ci_type]
        else:
            ci_types = []
    else:
        ci_types = CITypeManager().get_ci_types(q)
    count = len(ci_types)

    return dict(numfound=count, ci_types=ci_types)


@router.post("/ci_types")
@args_required("name")
@args_validate(CITypeManager.cls, exclude_args=['parent_ids'])
def ci_type_view_post():
    params = request.values

    type_name = params.get("name")
    type_alias = params.get("alias")
    type_alias = type_name if not type_alias else type_alias
    params['alias'] = type_alias

    manager = CITypeManager()
    type_id = manager.add(**params)

    return dict(type_id=type_id)


@router.put("/ci_types/{type_id:int}")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
@args_validate(CITypeManager.cls)
def ci_type_view_put(type_id: int = None):
    params = request.values

    manager = CITypeManager()
    manager.update(type_id, **params)

    return dict(type_id=type_id)


@router.delete("/ci_types/{type_id:int}")
@has_perm_from_args("type_id", ResourceTypeEnum.CI, PermEnum.CONFIG, CITypeManager.get_name_by_id)
def ci_type_view_delete(type_id: int = None):
    CITypeManager.delete(type_id)

    return dict(type_id=type_id)
