# -*- coding:utf-8 -*-


from api.core.errors import BadRequest, Forbidden, NotFound  # noqa


class CommitException(Exception):
    pass


AbortException = (NotFound, Forbidden, BadRequest)
