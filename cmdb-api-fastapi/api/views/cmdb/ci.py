# -*- coding:utf-8 -*-

import time

import six
from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import current_app
from api.core.context import request

from api.lib.cmdb.cache import CITypeCache
from api.lib.cmdb.ci import CIManager
from api.lib.cmdb.ci import CIRelationManager
from api.lib.cmdb.const import ExistPolicy
from api.lib.cmdb.const import ResourceTypeEnum, PermEnum
from api.lib.cmdb.const import RetKey
from api.lib.cmdb.perms import has_perm_for_ci
from api.lib.cmdb.search import SearchError
from api.lib.cmdb.search.ci import search as ci_search
from api.lib.decorator import args_required
from api.lib.perm.acl.acl import has_perm_from_args
from api.lib.perm.auth import authenticate
from api.lib.utils import get_page
from api.lib.utils import get_page_size
from api.lib.utils import handle_arg_list
from api.models.cmdb import CI

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/ci/type/{type_id:int}")
def cis_by_type_view_get(type_id: int):
    fields = handle_arg_list(request.values.get("fields", ""))

    ret_key = request.values.get("ret_key", RetKey.NAME)
    if ret_key not in (RetKey.NAME, RetKey.ALIAS, RetKey.ID):
        ret_key = RetKey.NAME

    page = get_page(request.values.get("page", 1))
    count = get_page_size(request.values.get("count"))

    manager = CIManager()
    res = manager.get_cis_by_type(type_id,
                                  ret_key=ret_key,
                                  fields=fields,
                                  page=page,
                                  per_page=count)

    return dict(type_id=type_id,
                numfound=res[0],
                total=len(res[2]),
                page=res[1],
                cis=res[2])


@router.get("/ci/{ci_id:int}")
@router.get("/ci")
def ci_view_get(ci_id: int = None):
    fields = handle_arg_list(request.values.get("fields", ""))

    ret_key = request.values.get("ret_key", RetKey.NAME)
    if ret_key not in (RetKey.NAME, RetKey.ALIAS, RetKey.ID):
        ret_key = RetKey.NAME

    manager = CIManager()
    ci = manager.get_ci_by_id_from_db(ci_id, ret_key=ret_key, fields=fields, valid=True)

    return dict(ci_id=ci_id, ci=ci)


def _wrap_ci_dict():
    ci_dict = {k: v.strip() if isinstance(v, six.string_types) else v for k, v in request.values.items()
               if k != "ci_type" and not k.startswith("_")}

    return ci_dict


@router.post("/ci/{ci_id:int}")
@router.post("/ci")
@has_perm_for_ci("ci_type", ResourceTypeEnum.CI, PermEnum.ADD, lambda x: CITypeCache.get(x))
def ci_view_post():
    ci_type = request.values.get("ci_type")
    ticket_id = request.values.pop("ticket_id", None)
    _no_attribute_policy = request.values.get("no_attribute_policy", ExistPolicy.IGNORE)

    exist_policy = request.values.pop('exist_policy', None)

    ci_dict = _wrap_ci_dict()

    manager = CIManager()
    ci_id = manager.add(ci_type,
                        exist_policy=exist_policy or ExistPolicy.REJECT,
                        _no_attribute_policy=_no_attribute_policy,
                        _is_admin=request.values.pop('__is_admin', None) or False,
                        ticket_id=ticket_id,
                        **ci_dict)

    return dict(ci_id=ci_id)


@router.put("/ci/{ci_id:int}")
@router.put("/ci")
@has_perm_for_ci("ci_id", ResourceTypeEnum.CI, PermEnum.UPDATE, CIManager.get_type)
def ci_view_put(ci_id: int = None):
    args = request.values
    ci_type = args.get("ci_type")
    ticket_id = request.values.pop("ticket_id", None)
    _no_attribute_policy = args.get("no_attribute_policy", ExistPolicy.IGNORE)

    ci_dict = _wrap_ci_dict()
    manager = CIManager()
    if ci_id is not None:
        manager.update(ci_id,
                       _is_admin=request.values.pop('__is_admin', None) or False,
                       ticket_id=ticket_id,
                       **ci_dict)
    else:
        request.values.pop('exist_policy', None)
        ci_id = manager.add(ci_type,
                            exist_policy=ExistPolicy.REPLACE,
                            _no_attribute_policy=_no_attribute_policy,
                            _is_admin=request.values.pop('__is_admin', None) or False,
                            ticket_id=ticket_id,
                            **ci_dict)

    return dict(ci_id=ci_id)


@router.delete("/ci/{ci_id:int}")
@router.delete("/ci")
@has_perm_for_ci("ci_id", ResourceTypeEnum.CI, PermEnum.DELETE, CIManager.get_type)
def ci_view_delete(ci_id: int = None):
    manager = CIManager()
    manager.delete(ci_id)

    return dict(message="ok")


@router.get("/ci/{ci_id:int}/detail")
def ci_detail_view_get(ci_id: int):
    _ci = CI.get_by_id(ci_id).to_dict()

    return dict(**_ci)


@router.get("/ci/s")
@router.get("/ci/search")
def ci_search_view_get():
    """@params: q: query statement
                fl: filter by column
                count/page_size: the number of ci
                ret_key: id, name, alias
                facet: statistic
    """
    page = get_page(request.values.get("page", 1))
    count = get_page_size(request.values.get("count") or request.values.get("page_size"))

    query = request.values.get('q', "")
    fl = handle_arg_list(request.values.get('fl', ""))
    excludes = handle_arg_list(request.values.get('excludes', ""))
    ret_key = request.values.get('ret_key', RetKey.NAME)
    if ret_key not in (RetKey.NAME, RetKey.ALIAS, RetKey.ID):
        ret_key = RetKey.NAME
    facet = handle_arg_list(request.values.get("facet", ""))
    sort = request.values.get("sort")
    use_id_filter = request.values.get("use_id_filter", False) in current_app.config.get('BOOL_TRUE')

    start = time.time()
    s = ci_search(query, fl, facet, page, ret_key, count, sort, excludes, use_id_filter=use_id_filter)
    try:
        response, counter, total, page, numfound, facet = s.search()
    except SearchError as e:
        return abort(400, str(e))

    if request.values.get('need_children') in current_app.config.get('BOOL_TRUE') and len(response) == 1:
        children = CIRelationManager.get_children(response[0]['_id'], ret_key=ret_key)  # one floor
        response[0].update(children)

    current_app.logger.debug("search time is: {0}".format(time.time() - start))

    return dict(numfound=numfound,
                total=total,
                page=page,
                facet=facet,
                counter=counter,
                result=response)


@router.post("/ci/s")
@router.post("/ci/search")
def ci_search_view_post():
    return ci_search_view_get()


@router.put("/ci/{ci_id:int}/unique")
@has_perm_from_args("ci_id", ResourceTypeEnum.CI, PermEnum.UPDATE, CIManager.get_type_name)
def ci_unique_put(ci_id: int = None):
    params = request.values
    unique_name = list(params.keys())[0]
    unique_value = list(params.values())[0]

    CIManager.update_unique_value(ci_id, unique_name, unique_value)

    return dict(ci_id=ci_id)


@router.get("/ci/heartbeat")
@router.get("/ci/heartbeat/{ci_type}/{unique}")
def ci_heartbeat_view_get():
    page = get_page(request.values.get("page", 1))
    ci_type = request.values.get("ci_type", "").strip()
    try:
        type_id = CITypeCache.get(ci_type).type_id
    except AttributeError:
        return dict(numfound=0, result=[])
    agent_status = request.values.get("agent_status")
    if agent_status:
        agent_status = int(agent_status)

    numfound, result = CIManager.get_heartbeat(page, type_id, agent_status=agent_status)

    return dict(numfound=numfound, result=result)


@router.post("/ci/heartbeat")
@router.post("/ci/heartbeat/{ci_type}/{unique}")
def ci_heartbeat_view_post(ci_type: str = None, unique: str = None):
    if not unique or not ci_type:
        return dict(message="error")

    msg, cmd = CIManager().add_heartbeat(ci_type, unique)

    return dict(message=msg, cmd=cmd)


@router.get("/ci/flush")
@router.get("/ci/{ci_id:int}/flush")
def ci_flush_view_get(ci_id: int = None):
    from api.tasks.cmdb import ci_cache
    from api.lib.cmdb.const import CMDB_QUEUE
    if ci_id is not None:
        ci_cache.apply_async(args=(ci_id, None, None), queue=CMDB_QUEUE)
    else:
        cis = CI.get_by(to_dict=False)
        for ci in cis:
            ci_cache.apply_async(args=(ci.id, None, None), queue=CMDB_QUEUE)

    return dict(code=200)


@router.get("/ci/adc/statistics")
def ci_auto_discovery_statistics_view_get():
    return CIManager.get_ad_statistics()


@router.get("/ci/{ci_id:int}/attributes/{attr_id:int}/password")
def ci_password_view_get(ci_id: int, attr_id: int):
    return dict(ci_id=ci_id, attr_id=attr_id, value=CIManager.load_password(ci_id, attr_id))


@router.post("/ci/{ci_id:int}/attributes/{attr_id:int}/password")
def ci_password_view_post(ci_id: int, attr_id: int):
    return ci_password_view_get(ci_id, attr_id)


@router.get("/ci/baseline")
@router.get("/ci/{ci_id:int}/baseline/rollback")
@args_required("before_date")
def ci_baseline_view_get():
    ci_ids = handle_arg_list(request.values.get('ci_ids'))
    before_date = request.values.get('before_date')

    return CIManager().baseline(list(map(int, ci_ids)), before_date)


@router.post("/ci/baseline")
@router.post("/ci/{ci_id:int}/baseline/rollback")
@args_required("before_date")
@has_perm_for_ci("ci_id", ResourceTypeEnum.CI, PermEnum.UPDATE, CIManager.get_type)
def ci_baseline_view_post(ci_id: int = None):
    if 'rollback' in request.url:
        before_date = request.values.get('before_date')

        return dict(**CIManager().rollback(ci_id, before_date))

    return ci_baseline_view_get()


@router.get("/ci/{ci_id:int}/mobile")
def ci_mobile_detail_view_get(ci_id: int):
    ci = CIManager.get_ci_by_id_from_db(ci_id, ret_key=RetKey.NAME, fields=None, valid=True)

    ci_type = CITypeCache.get(ci.get("_type", 0)) if ci.get("_type") else None
    type_info = {"id": ci_type.id, "name": ci_type.name, "alias": ci_type.alias} if ci_type else {}

    attribute_alias_map = {}
    if ci_type:
        from api.lib.cmdb.ci_type import CITypeAttributeManager
        attrs = CITypeAttributeManager.get_attr_names_by_type_id(ci_type.id)
        if attrs:
            from api.lib.cmdb.cache import AttributeCache
            for attr_name in attrs:
                attr_obj = AttributeCache.get(attr_name)
                if attr_obj:
                    attribute_alias_map[attr_obj.name] = attr_obj.alias or attr_obj.name

    relations = {"parents": [], "children": []}
    try:
        children = CIRelationManager.get_children(ci_id, ret_key=RetKey.NAME)
        for type_name, cis in children.items():
            child_type = CITypeCache.get(type_name) if type_name else None
            child_type_name = child_type.alias if child_type else (type_name or "")
            for c in cis:
                c["_type_name"] = child_type_name
                relations["children"].append(c)
    except Exception as e:
        current_app.logger.exception("failed to load child relations for ci_id=%s: %s", ci_id, e)

    try:
        parent_ids = CIRelationManager.get_parent_ids([ci_id]) or {}
        for p_id, p_type_id in parent_ids.get(ci_id, []):
            try:
                parent_ci = CIManager.get_cis_by_ids([str(p_id)], ret_key=RetKey.NAME) or []
            except Exception as e:
                current_app.logger.exception(
                    "failed to load parent ci for ci_id=%s parent_id=%s: %s", ci_id, p_id, e
                )
                continue

            p_type = CITypeCache.get(p_type_id) if p_type_id else None
            parent_type_name = p_type.alias if p_type else ""
            for p in parent_ci:
                p["_type_name"] = parent_type_name
                relations["parents"].append(p)
    except Exception as e:
        current_app.logger.exception("failed to load parent relations for ci_id=%s: %s", ci_id, e)

    from api.lib.cmdb.history import AttributeHistoryManger
    try:
        history = AttributeHistoryManger.get_by_ci_id(ci_id)
        history = history[:10]
    except Exception:
        history = []

    return dict(ci=ci, type=type_info, relations=relations, history=history,
                attribute_alias_map=attribute_alias_map)
