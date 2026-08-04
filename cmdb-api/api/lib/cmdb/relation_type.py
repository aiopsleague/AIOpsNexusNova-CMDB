# -*- coding:utf-8 -*-


from api.core.errors import abort

from api.lib.cmdb.resp_format import ErrFormat
from api.models.cmdb import RelationType


class RelationTypeManager(object):
    cls = RelationType

    @staticmethod
    def get_all():
        return RelationType.get_by(to_dict=False)

    @classmethod
    def get_names(cls):
        return [i.name for i in cls.get_all()]

    @classmethod
    def get_pairs(cls):
        return [(i.id, i.name) for i in cls.get_all()]

    @staticmethod
    def add(name, color=None):
        RelationType.get_by(name=name, first=True, to_dict=False) and abort(
            400, ErrFormat.relation_type_exists.format(name))

        kwargs = dict(name=name)
        if color is not None:
            kwargs['color'] = color

        return RelationType.create(**kwargs)

    @staticmethod
    def update(rel_id, name, color=None):
        existed = RelationType.get_by_id(rel_id) or abort(
            404, ErrFormat.relation_type_not_found.format("id={}".format(rel_id)))

        kwargs = dict(name=name)
        if color is not None:
            kwargs['color'] = color

        return existed.update(**kwargs)

    @staticmethod
    def delete(rel_id):
        existed = RelationType.get_by_id(rel_id) or abort(
            404, ErrFormat.relation_type_not_found.format("id={}".format(rel_id)))

        existed.soft_delete()
