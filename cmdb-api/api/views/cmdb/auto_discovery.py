# -*- coding:utf-8 -*-
import copy
import json
import uuid
from io import BytesIO

from fastapi import APIRouter
from fastapi import Depends

from api.core.context import current_app
from api.core.context import current_user
from api.core.context import request
from api.core.errors import abort
from api.core.responses import send_file
from api.lib.cmdb.auto_discovery.auto_discovery import AutoDiscoveryAccountCRUD
from api.lib.cmdb.auto_discovery.auto_discovery import AutoDiscoveryCICRUD
from api.lib.cmdb.auto_discovery.auto_discovery import AutoDiscoveryCITypeCRUD
from api.lib.cmdb.auto_discovery.auto_discovery import AutoDiscoveryCITypeRelationCRUD
from api.lib.cmdb.auto_discovery.auto_discovery import AutoDiscoveryComponentsManager
from api.lib.cmdb.auto_discovery.auto_discovery import AutoDiscoveryCounterCRUD
from api.lib.cmdb.auto_discovery.auto_discovery import AutoDiscoveryExecHistoryCRUD
from api.lib.cmdb.auto_discovery.auto_discovery import AutoDiscoveryHTTPManager
from api.lib.cmdb.auto_discovery.auto_discovery import AutoDiscoveryRuleCRUD
from api.lib.cmdb.auto_discovery.auto_discovery import AutoDiscoveryRuleSyncHistoryCRUD
from api.lib.cmdb.auto_discovery.auto_discovery import AutoDiscoverySNMPManager
from api.lib.cmdb.auto_discovery.const import DEFAULT_INNER
from api.lib.cmdb.auto_discovery.const import PRIVILEGED_USERS
from api.lib.cmdb.cache import AttributeCache
from api.lib.cmdb.const import PermEnum
from api.lib.cmdb.const import ResourceTypeEnum
from api.lib.cmdb.ipam.subnet import SubnetManager
from api.lib.cmdb.resp_format import ErrFormat
from api.lib.cmdb.search import SearchError
from api.lib.cmdb.search.ci import search as ci_search
from api.lib.decorator import args_required
from api.lib.decorator import args_validate
from api.lib.exception import AbortException
from api.lib.perm.acl.acl import has_perm_from_args
from api.lib.perm.auth import authenticate
from api.lib.utils import AESCrypto
from api.lib.utils import get_page
from api.lib.utils import get_page_size
from api.lib.utils import handle_arg_list

router = APIRouter(dependencies=[Depends(authenticate)])


@router.get("/adr/{adr_id:int}")
@router.get("/adr")
def auto_discovery_rule_view_get(adr_id: int = None):
    _, res = AutoDiscoveryRuleCRUD.search(page=1, page_size=100000, **request.values)

    rebuild = False
    exists = {i['name'] for i in res}
    for i in copy.deepcopy(DEFAULT_INNER):
        if i['name'] not in exists:
            i.pop('en', None)
            AutoDiscoveryRuleCRUD().add(**i)
            rebuild = True

    if rebuild:
        _, res = AutoDiscoveryRuleCRUD.search(page=1, page_size=100000, **request.values)

    for i in res:
        if i['type'] == 'http':
            i['resources'] = AutoDiscoveryHTTPManager().get_resources(i['name'])

    return res


@router.post("/adr/{adr_id:int}")
@router.post("/adr")
@args_required("name", value_required=True)
@args_validate(AutoDiscoveryRuleCRUD.cls)
def auto_discovery_rule_view_post(adr_id: int = None):
    return AutoDiscoveryRuleCRUD().add(**request.values).to_dict()


@router.put("/adr/{adr_id:int}")
@router.put("/adr")
@args_validate(AutoDiscoveryRuleCRUD.cls)
def auto_discovery_rule_view_put(adr_id: int = None):
    return AutoDiscoveryRuleCRUD().update(adr_id, **request.values).to_dict()


@router.delete("/adr/{adr_id:int}")
@router.delete("/adr")
def auto_discovery_rule_view_delete(adr_id: int = None):
    AutoDiscoveryRuleCRUD().delete(adr_id)

    return dict(adr_id=adr_id)


@router.get("/adr/template/import/file")
@router.get("/adr/template/export/file")
def auto_discovery_rule_template_file_view_get():  # export
    adr_tpt = AutoDiscoveryRuleCRUD().get_by_inner()
    adr_tpt = dict(auto_discovery_rules=adr_tpt)

    bf = BytesIO()
    bf.write(bytes(json.dumps(adr_tpt).encode('utf-8')))
    bf.seek(0)

    return send_file(bf,
                     as_attachment=True,
                     download_name="cmdb_auto_discovery.json",
                     mimetype='application/json',
                     max_age=0)


@router.post("/adr/template/import/file")
@router.post("/adr/template/export/file")
def auto_discovery_rule_template_file_view_post():
    f = request.files.get('file')

    if f is None:
        return abort(400, ErrFormat.argument_file_not_found)

    content = f.read()
    try:
        content = json.loads(content)
    except:
        return abort(400, ErrFormat.invalid_json)
    tpt = content.get('auto_discovery_rules')

    AutoDiscoveryRuleCRUD().import_template(tpt)

    return dict(code=200)


@router.get("/adr/http/{name}/categories")
@router.get("/adr/http/{name}/attributes")
@router.get("/adr/http/{name}/mapping")
@router.get("/adr/snmp/{name}/attributes")
@router.get("/adr/components/{name}/attributes")
def auto_discovery_rule_http_view_get(name: str = None):
    if "snmp" in request.url:
        return AutoDiscoverySNMPManager.get_attributes()

    if "components" in request.url:
        return AutoDiscoveryComponentsManager.get_attributes(name)

    if "attributes" in request.url:
        resource = request.values.get('resource')
        return AutoDiscoveryHTTPManager.get_attributes(name, resource)

    if "mapping" in request.url:
        resource = request.values.get('resource')
        return AutoDiscoveryHTTPManager.get_mapping(name, resource)

    return AutoDiscoveryHTTPManager.get_categories(name)


@router.get("/adt/ci_types/{type_id:int}")
@router.get("/adt/ci_types/{type_id:int}/attributes")
@router.get("/adt/{adt_id:int}")
def auto_discovery_ci_type_view_get(type_id: int = None, adt_id: int = None):
    if "attributes" in request.url:
        return AutoDiscoveryCITypeCRUD.get_ad_attributes(type_id)

    _, res = AutoDiscoveryCITypeCRUD.search(page=1, page_size=100000, type_id=type_id, **request.values)
    for i in res:
        if isinstance(i.get("extra_option"), dict) and i['extra_option'].get('secret'):
            if not (current_user.username == "cmdb_agent" or current_user.uid == i['uid']):
                i['extra_option'].pop('secret', None)
            else:
                i['extra_option']['secret'] = AESCrypto.decrypt(i['extra_option']['secret'])
        if isinstance(i.get("extra_option"), dict) and i['extra_option'].get('password'):
            if not (current_user.username == "cmdb_agent" or current_user.uid == i['uid']):
                i['extra_option'].pop('password', None)
            else:
                i['extra_option']['password'] = AESCrypto.decrypt(i['extra_option']['password'])

    return res


@router.post("/adt/ci_types/{type_id:int}")
@router.post("/adt/ci_types/{type_id:int}/attributes")
@router.post("/adt/{adt_id:int}")
@args_validate(AutoDiscoveryCITypeCRUD.cls)
def auto_discovery_ci_type_view_post(type_id: int = None, adt_id: int = None):
    if not request.values.get('interval'):
        request.values.pop('interval', None)

    return AutoDiscoveryCITypeCRUD().add(type_id=type_id, **request.values).to_dict()


@router.put("/adt/ci_types/{type_id:int}")
@router.put("/adt/ci_types/{type_id:int}/attributes")
@router.put("/adt/{adt_id:int}")
@args_validate(AutoDiscoveryCITypeCRUD.cls)
def auto_discovery_ci_type_view_put(type_id: int = None, adt_id: int = None):
    if not request.values.get('interval'):
        request.values.pop('interval', None)

    return AutoDiscoveryCITypeCRUD().update(adt_id, **request.values).to_dict()


@router.delete("/adt/ci_types/{type_id:int}")
@router.delete("/adt/ci_types/{type_id:int}/attributes")
@router.delete("/adt/{adt_id:int}")
def auto_discovery_ci_type_view_delete(type_id: int = None, adt_id: int = None):
    AutoDiscoveryCITypeCRUD().delete(adt_id)

    return dict(adt_id=adt_id)


@router.get("/adt/ci_types/{type_id:int}/relations")
@router.get("/adt/relations/{_id:int}")
def auto_discovery_ci_type_relation_view_get(type_id: int = None, _id: int = None):
    _, res = AutoDiscoveryCITypeRelationCRUD.search(page=1, page_size=100000, ad_type_id=type_id, **request.values)

    return res


@router.post("/adt/ci_types/{type_id:int}/relations")
@router.post("/adt/relations/{_id:int}")
@args_required("relations")
def auto_discovery_ci_type_relation_view_post(type_id: int = None, _id: int = None):
    return AutoDiscoveryCITypeRelationCRUD().upsert(type_id, request.values['relations'])


@router.put("/adt/ci_types/{type_id:int}/relations")
@router.put("/adt/relations/{_id:int}")
def auto_discovery_ci_type_relation_view_put(type_id: int = None, _id: int = None):
    return auto_discovery_ci_type_relation_view_post(type_id)


@router.delete("/adt/ci_types/{type_id:int}/relations")
@router.delete("/adt/relations/{_id:int}")
def auto_discovery_ci_type_relation_view_delete(type_id: int = None, _id: int = None):
    AutoDiscoveryCITypeRelationCRUD().delete(_id)

    return dict(id=_id)


@router.get("/adc")
@router.get("/adc/{adc_id:int}")
@router.get("/adc/ci_types/{type_id:int}/attributes")
@router.get("/adc/ci_types")
def auto_discovery_ci_view_get(type_id: int = None, adc_id: int = None):
    if "attributes" in request.url:
        return AutoDiscoveryCICRUD.get_attributes_by_type_id(type_id)
    if "ci_types" in request.url:
        need_other = request.values.get("need_other")
        return AutoDiscoveryCICRUD.get_ci_types(need_other)
    if adc_id is not None:
        return AutoDiscoveryCICRUD.get_instance_by_id(adc_id)

    page = get_page(request.values.pop('page', 1))
    page_size = get_page_size(request.values.pop('page_size', None))
    fl = handle_arg_list(request.values.get('fl'))
    numfound, res = AutoDiscoveryCICRUD.search(page=page, page_size=page_size, fl=fl, **request.values)

    return dict(page=page,
                page_size=page_size,
                numfound=numfound,
                total=len(res),
                result=res)


@router.post("/adc")
@router.post("/adc/{adc_id:int}")
@router.post("/adc/ci_types/{type_id:int}/attributes")
@router.post("/adc/ci_types")
@args_validate(AutoDiscoveryCICRUD.cls)
@args_required("type_id")
@args_required("adt_id")
@args_required("instance")
@args_required("unique_value")
def auto_discovery_ci_view_post(type_id: int = None, adc_id: int = None):
    request.values.pop("_key", None)
    request.values.pop("_secret", None)

    return AutoDiscoveryCICRUD().upsert(**request.values).to_dict()


@router.put("/adc")
@router.put("/adc/{adc_id:int}")
@router.put("/adc/ci_types/{type_id:int}/attributes")
@router.put("/adc/ci_types")
def auto_discovery_ci_view_put(type_id: int = None, adc_id: int = None):
    return auto_discovery_ci_view_post()


@router.delete("/adc/{adc_id:int}")
@has_perm_from_args("adc_id", ResourceTypeEnum.CI, PermEnum.DELETE, AutoDiscoveryCICRUD.get_type_name)
def auto_discovery_ci_view_delete(adc_id: int = None):
    AutoDiscoveryCICRUD().delete(adc_id)

    return dict(adc_id=adc_id)


@router.delete("/adc")
def auto_discovery_ci_delete2_view_delete():
    type_id = request.values.get('type_id')
    unique_value = request.values.get('unique_value')

    AutoDiscoveryCICRUD.delete2(type_id, unique_value)

    return dict(type_id=type_id, unique_value=unique_value)


@router.put("/adc/{adc_id:int}/accept")
@has_perm_from_args("adc_id", ResourceTypeEnum.CI, PermEnum.ADD, AutoDiscoveryCICRUD.get_type_name)
def auto_discovery_ci_accept_view_put(adc_id: int = None):
    AutoDiscoveryCICRUD.accept(None, adc_id=adc_id)

    return dict(adc_id=adc_id)


@router.get("/adt/sync")
def auto_discovery_rule_sync_view_get():
    if current_user.username not in PRIVILEGED_USERS:
        return abort(403)

    oneagent_name = request.values.get('oneagent_name')
    oneagent_id = request.values.get('oneagent_id')
    last_update_at = request.values.get('last_update_at')

    response = []
    if AttributeCache.get('oneagent_id'):
        query = "oneagent_id:{}".format(oneagent_id)
        s = ci_search(query)
        try:
            response, _, _, _, _, _ = s.search()
        except SearchError as e:
            import traceback
            current_app.logger.error(traceback.format_exc())
            return abort(400, str(e))

    for res in response:
        if res.get('{}_name'.format(res['ci_type'])) == oneagent_name or oneagent_name == res.get('oneagent_name'):
            ci_id = res["_id"]
            rules, last_update_at = AutoDiscoveryCITypeCRUD.get(ci_id, oneagent_id, oneagent_name, last_update_at)

            return dict(rules=rules, last_update_at=last_update_at)

    rules, last_update_at1 = AutoDiscoveryCITypeCRUD.get(None, oneagent_id, oneagent_name, last_update_at)

    try:
        subnet_scan_rules, last_update_at2 = SubnetManager().scan_rules(oneagent_id, last_update_at)
    except AbortException:
        subnet_scan_rules, last_update_at2 = [], ""

    return dict(rules=rules,
                subnet_scan_rules=subnet_scan_rules,
                last_update_at=max(last_update_at1 or "", last_update_at2 or ""))


@router.get("/adt/{adt_id:int}/sync/histories")
def auto_discovery_rule_sync_history_view_get(adt_id: int = None):
    page = get_page(request.values.pop('page', 1))
    page_size = get_page_size(request.values.pop('page_size', None))
    numfound, res = AutoDiscoveryRuleSyncHistoryCRUD.search(page=page,
                                                            page_size=page_size,
                                                            adt_id=adt_id,
                                                            **request.values)

    return dict(page=page,
                page_size=page_size,
                numfound=numfound,
                total=len(res),
                result=res)


@router.get("/adt/{adt_id:int}/test")
@router.get("/adt/test/{exec_id}/result")
def auto_discovery_test_view_get(adt_id: int = None, exec_id: str = None):
    return dict(stdout="1\n2\n3", exec_id=exec_id)


@router.post("/adt/{adt_id:int}/test")
@router.post("/adt/test/{exec_id}/result")
def auto_discovery_test_view_post(adt_id: int = None, exec_id: str = None):
    return dict(exec_id=uuid.uuid4().hex)


@router.get("/adc/exec/histories")
@args_required('type_id')
def auto_discovery_exec_history_view_get():
    page = get_page(request.values.pop('page', 1))
    page_size = get_page_size(request.values.pop('page_size', None))
    last_size = request.values.pop('last_size', None)
    if last_size and last_size.isdigit():
        last_size = int(last_size)
    numfound, res = AutoDiscoveryExecHistoryCRUD.search(page=page,
                                                        page_size=page_size,
                                                        last_size=last_size,
                                                        **request.values)

    return dict(page=page,
                page_size=page_size,
                numfound=numfound,
                total=len(res),
                result=res)


@router.post("/adc/exec/histories")
@args_required('type_id')
@args_required('stdout')
def auto_discovery_exec_history_view_post():
    AutoDiscoveryExecHistoryCRUD().add(type_id=request.values.get('type_id'),
                                       stdout=request.values.get('stdout'))

    return dict(code=200)


@router.delete("/adc/exec/histories/{type_id:int}")
def auto_discovery_exec_history_view_delete(type_id: int):
    from api.extensions import db
    from api.models.cmdb import AutoDiscoveryExecHistory

    db.session.query(AutoDiscoveryExecHistory).filter(
        AutoDiscoveryExecHistory.type_id == type_id
    ).delete()
    db.session.commit()

    return dict(code=200)


@router.get("/adc/counter")
@args_required('type_id')
def auto_discovery_counter_view_get():
    type_id = request.values.get('type_id')

    return AutoDiscoveryCounterCRUD().get(type_id)


@router.get("/adr/accounts")
@router.get("/adr/accounts/{account_id:int}")
@args_required('adr_id')
def auto_discovery_account_view_get(account_id: int = None):
    adr_id = request.values.get('adr_id')

    return AutoDiscoveryAccountCRUD().get(adr_id)


@router.post("/adr/accounts")
@router.post("/adr/accounts/{account_id:int}")
@args_required('adr_id')
@args_required('accounts', value_required=False)
def auto_discovery_account_view_post(account_id: int = None):
    AutoDiscoveryAccountCRUD().upsert(**request.values)

    return dict(code=200)


@router.put("/adr/accounts")
@router.put("/adr/accounts/{account_id:int}")
@args_required('config')
def auto_discovery_account_view_put(account_id: int = None):
    res = AutoDiscoveryAccountCRUD().update(account_id, **request.values)

    return res.to_dict()


@router.delete("/adr/accounts")
@router.delete("/adr/accounts/{account_id:int}")
def auto_discovery_account_view_delete(account_id: int = None):
    AutoDiscoveryAccountCRUD().delete(account_id)

    return dict(account_id=account_id)
