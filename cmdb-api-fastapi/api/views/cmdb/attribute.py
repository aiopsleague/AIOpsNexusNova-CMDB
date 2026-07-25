# -*- coding:utf-8 -*- 


from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import current_app
from api.core.context import request

from api.lib.cmdb.attribute import AttributeManager
from api.lib.cmdb.resp_format import ErrFormat
from api.lib.decorator import args_required
from api.lib.decorator import args_validate
from api.lib.perm.auth import authenticate
from api.lib.utils import get_page
from api.lib.utils import get_page_size
from api.lib.utils import handle_arg_list

router = APIRouter(dependencies=[Depends(authenticate)])


# NOTE(fastapi-port): the static search paths are registered before
# ``/attributes/{attr_name}`` so that starlette's registration-order matching
# does not shadow them. ``{attr_id:int}`` uses the starlette int convertor to
# mirror flask's ``<int:attr_id>`` (non-numeric names fall through to
# ``{attr_name}``).


@router.get("/attributes/search")
@router.get("/attributes/s")
def attribute_search_view_get():
    name = request.values.get("name")
    alias = request.values.get("alias")
    page = get_page(request.values.get("page", 1))
    page_size = get_page_size(request.values.get("page_size"))
    numfound, res = AttributeManager.search_attributes(name=name, alias=alias, page=page, page_size=page_size)

    return dict(page=page,
                page_size=page_size,
                numfound=numfound,
                total=len(res),
                attributes=res)


@router.get("/attributes/{attr_id:int}/calc_computed_attribute")
@router.get("/attributes/{attr_name}")
@router.get("/attributes/{attr_id:int}")
@router.get("/attributes")
def attribute_view_get(attr_name: str = None, attr_id: int = None):
    attr_manager = AttributeManager()
    attr_dict = None
    if attr_name is not None:
        attr_dict = attr_manager.get_attribute_by_name(attr_name)
        if attr_dict is None:
            attr_dict = attr_manager.get_attribute_by_alias(attr_name)

        if not attr_dict:
            return abort(404, ErrFormat.attribute_not_found.format("name={}".format(attr_name)))
    elif attr_id is not None:
        attr_dict = attr_manager.get_attribute_by_id(attr_id)

        if not attr_dict:
            return abort(404, ErrFormat.attribute_not_found.format("name={}".format(attr_name)))

    return dict(attribute=attr_dict)


@router.post("/attributes")
@args_required("name")
@args_validate(AttributeManager.cls)
def attribute_view_post():
    choice_value = handle_arg_list(request.values.get("choice_value"))
    params = request.values
    params["choice_value"] = choice_value

    current_app.logger.debug(params)

    attr_id = AttributeManager.add(**params)

    return dict(attr_id=attr_id)


@router.put("/attributes/{attr_id:int}/calc_computed_attribute")
@router.put("/attributes/{attr_id:int}")
@args_validate(AttributeManager.cls)
def attribute_view_put(attr_id: int = None):
    if request.url.endswith("/calc_computed_attribute"):
        AttributeManager.calc_computed_attribute(attr_id)

        return dict(attr_id=attr_id)

    choice_value = handle_arg_list(request.values.get("choice_value"))
    params = request.values
    params["choice_value"] = choice_value
    current_app.logger.debug(params)
    AttributeManager().update(attr_id, **params)

    return dict(attr_id=attr_id)


@router.delete("/attributes/{attr_id:int}")
def attribute_view_delete(attr_id: int = None):
    attr_name = AttributeManager.delete(attr_id)

    return dict(message="attribute {0} deleted".format(attr_name))
