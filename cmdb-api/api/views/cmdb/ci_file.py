# -*- coding:utf-8 -*-
from fastapi import APIRouter
from fastapi import Depends

from api.core.errors import abort
from api.core.context import request
from api.core.responses import send_file
from api.lib.cmdb.ci_file import CIFileManager
from api.lib.perm.auth import authenticate

router = APIRouter(dependencies=[Depends(authenticate)])

_file_manager = CIFileManager()


def _get_mimetype_from_filename(filename):
    if not filename or '.' not in filename:
        return 'application/octet-stream'
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    ext_to_mime = {
        'svg': 'image/svg+xml', 'png': 'image/png', 'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg', 'gif': 'image/gif', 'webp': 'image/webp',
        'bmp': 'image/bmp', 'ico': 'image/vnd.microsoft.icon',
        'tif': 'image/tiff', 'tiff': 'image/tiff',
        'pdf': 'application/pdf', 'txt': 'text/plain', 'csv': 'text/csv',
        'json': 'application/json',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'zip': 'application/zip', '7z': 'application/x-7z-compressed',
        'rar': 'application/vnd.rar',
    }
    return ext_to_mime.get(ext, 'application/octet-stream')


@router.post("/ci/files")
def upload_ci_files_view_post():
    attr_id = request.values.get('attr_id')
    try:
        attr_id = int(attr_id) if attr_id else None
    except (TypeError, ValueError):
        attr_id = None

    if 'files' not in request.files and 'file' not in request.files:
        abort(400, 'No file part in the request')

    # NOTE: request.files is a plain dict (see api.core.context) without
    # werkzeug's .getlist(); accept a single file object or a list per key.
    if 'files' in request.files:
        raw_files = request.files['files']
    else:
        raw_files = request.files['file']
    file_list = raw_files if isinstance(raw_files, list) else [raw_files]

    try:
        results = _file_manager.upload_files(file_list, attr_id=attr_id)
    except ValueError as e:
        abort(400, str(e))

    return {'files': results}


@router.get("/ci/files")
def get_ci_file_view_get(path: str = None, download: int = 0, storage_backend: str = None):
    if not path:
        abort(400, 'path is required')

    try:
        file_stream, filename, mime_type = _file_manager.get_file(path, storage_backend=storage_backend)
    except FileNotFoundError:
        abort(404, 'File not found')

    mimetype = _get_mimetype_from_filename(filename)
    as_attachment = bool(download)
    return send_file(file_stream, as_attachment=as_attachment, download_name=filename, mimetype=mimetype)


@router.delete("/ci/files")
def delete_ci_files_view_delete():
    paths = request.values.get('paths', [])
    if isinstance(paths, str):
        import json
        try:
            paths = json.loads(paths)
        except (json.JSONDecodeError, TypeError):
            paths = [paths]

    if not paths:
        abort(400, 'paths is required')

    deleted = _file_manager.delete_files(paths)
    return {'deleted': deleted}
