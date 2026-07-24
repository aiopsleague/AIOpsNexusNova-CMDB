# -*- coding:utf-8 -*-
"""Response helpers replacing ``flask.jsonify`` / ``send_file`` /
``make_response`` / ``redirect``."""
import os

from starlette.responses import FileResponse
from starlette.responses import RedirectResponse
from starlette.responses import StreamingResponse

from api.core.json_enc import CmdbJSONResponse


def jsonify(*args, **kwargs):
    """Mimics ``flask.jsonify``: returns a CmdbJSONResponse.

    ``jsonify(a=1, b=2)`` -> {"a": 1, "b": 2}
    ``jsonify({"a": 1})``  -> {"a": 1}
    ``jsonify([1, 2])``    -> [1, 2]
    """
    if args and kwargs:
        raise AssertionError("jsonify() behavior undefined when passed both args and kwargs")
    if len(args) == 1:
        content = args[0]
    elif args:
        content = list(args)
    else:
        content = kwargs
    return CmdbJSONResponse(content)


def make_response(content=None, status_code=200, headers=None):
    if isinstance(content, CmdbJSONResponse):
        if status_code and status_code != 200:
            content.status_code = status_code
        return content
    response = CmdbJSONResponse(content, status_code=status_code)
    if headers:
        for k, v in dict(headers).items():
            response.headers[k] = v
    return response


def send_file(path_or_file, download_name=None, as_attachment=False, mimetype=None,
              attachment_filename=None, **kwargs):
    """Mimics ``flask.send_file`` for filesystem paths and file-like objects."""
    filename = download_name or attachment_filename
    if isinstance(path_or_file, (str, os.PathLike)):
        if filename is None:
            filename = os.path.basename(path_or_file)
        return FileResponse(
            path_or_file,
            media_type=mimetype,
            filename=filename if as_attachment or filename else None,
        )

    # file-like object (BytesIO ...)
    headers = {}
    if filename:
        disposition = "attachment" if as_attachment else "inline"
        headers["Content-Disposition"] = f'{disposition}; filename="{filename}"'
    return StreamingResponse(
        path_or_file,
        media_type=mimetype or "application/octet-stream",
        headers=headers,
    )


def send_from_directory(directory, filename, **kwargs):
    return send_file(os.path.join(directory, filename), **kwargs)


def redirect(location, code=302):
    return RedirectResponse(location, status_code=code)
