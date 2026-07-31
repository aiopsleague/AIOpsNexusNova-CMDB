# File Attribute Type — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add "File" as a new virtual attribute data type (`value_type=TEXT` + `is_file=True`), with upload/preview/download support backed by a pluggable storage layer (local filesystem or S3-compatible object storage).

**Architecture:** Follow the existing virtual-type pattern (password/link/bool/reference). File type = TEXT(2) + new `is_file` boolean flag. A `StorageBackend` ABC with `LocalStorage` and `S3Storage` implementations handles file persistence, chosen via global config with per-attribute override in `option.file_storage`. File metadata stored as JSON array in `c_value_texts.value`.

**Tech Stack:** Python 3.12, SQLAlchemy 1.4, FastAPI, boto3 (new dep for S3), Vue 2.6 + Ant Design Vue 1.6

## Global Constraints

- Backend code in `cmdb-api/`, frontend in `cmdb-ui/`
- Backend imports: `# -*- coding:utf-8 -*-` header, stdlib → third-party → project grouping
- Backend naming: `snake_case` files/functions, `PascalCase` classes, `UPPER_SNAKE_CASE` constants
- Frontend: Options API (no Composition API), single quotes, no semicolons, 2-space indent
- Views never contain business logic — delegate to `lib/` Manager classes
- New DB column `is_file` on `c_attributes` (Boolean, default False)
- File path format: `{YYYY}/{MM}/{DD}/{uuid}_{secure_filename}.ext` for both local and S3
- Virtual type mapping: UI type `'12'` → `value_type='2'` + `is_file=True`
- `pkgutil.walk_packages` auto-discovers routers in `api/views/cmdb/` — just create `router = APIRouter(...)`

---

### Task 1: Database Migration + ORM Model + Enum

**Files:**
- Modify: `cmdb-api/api/models/cmdb.py` (add `is_file` column to `Attribute`)
- Modify: `cmdb-api/api/lib/cmdb/const.py` (add `FILE = TEXT` to `ValueTypeEnum`)
- Create: `cmdb-api/migrations/versions/0002_add_is_file.py`

**Interfaces:**
- Produces: `Attribute.is_file` (db.Boolean, default False), `ValueTypeEnum.FILE` (= `ValueTypeEnum.TEXT` = `"2"`)

- [ ] **Step 1: Add `is_file` column to `Attribute` model**

In `cmdb-api/api/models/cmdb.py`, inside the `Attribute` class, add after `is_bool` (line ~108):

```python
    is_file = db.Column(db.Boolean, default=False)
```

- [ ] **Step 2: Add `FILE` to `ValueTypeEnum`**

In `cmdb-api/api/lib/cmdb/const.py`, inside `ValueTypeEnum` class, add after `REFERENCE = INT` (line ~20):

```python
    FILE = TEXT
```

Full class should read:

```python
class ValueTypeEnum(BaseEnum):
    INT = "0"
    FLOAT = "1"
    TEXT = "2"
    DATETIME = "3"
    DATE = "4"
    TIME = "5"
    JSON = "6"
    PASSWORD = TEXT
    LINK = TEXT
    BOOL = "7"
    REFERENCE = INT
    FILE = TEXT
```

- [ ] **Step 3: Add `is_file` to `ValueTypeMap.table` so file attributes map to `c_value_texts`**

In `cmdb-api/api/lib/cmdb/utils.py`, in the `TableMap.table` property (line ~145), update the condition that skips index for password/link to also skip for file. Change line 147 from:

```python
        if attr.is_password or attr.is_link:
```

to:

```python
        if attr.is_password or attr.is_link or attr.is_file:
```

And in `TableMap.table_name` property (line ~160), change the same condition:

```python
        if attr.is_password or attr.is_link or attr.is_file:
```

- [ ] **Step 4: Create Alembic migration file**

Create `cmdb-api/migrations/versions/0002_add_is_file.py`:

```python
"""add is_file to c_attributes

Revision ID: 0002
Revises: 6a4df2623057
Create Date: 2026-07-31
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '6a4df2623057'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('c_attributes', sa.Column('is_file', sa.Boolean(), server_default=sa.text('0'), nullable=True))


def downgrade():
    op.drop_column('c_attributes', 'is_file')
```

- [ ] **Step 5: Commit**

```bash
git add cmdb-api/api/models/cmdb.py cmdb-api/api/lib/cmdb/const.py cmdb-api/api/lib/cmdb/utils.py cmdb-api/migrations/versions/0002_add_is_file.py
git commit -m "feat: add is_file column to c_attributes model and migration"
```

---

### Task 2: Storage Backend Abstraction (LocalStorage + S3Storage)

**Files:**
- Create: `cmdb-api/api/lib/cmdb/storage/__init__.py`
- Create: `cmdb-api/api/lib/cmdb/storage/base.py`
- Create: `cmdb-api/api/lib/cmdb/storage/local.py`
- Create: `cmdb-api/api/lib/cmdb/storage/s3_storage.py`
- Modify: `cmdb-api/settings.py`

**Interfaces:**
- Consumes: `settings.FILE_STORAGE_BACKEND`, `settings.FILE_STORAGE_LOCAL_PATH`, `settings.S3_*`
- Produces:
  - `get_storage_backend(backend_name: str) -> StorageBackend` — factory in `__init__.py`
  - `StorageBackend.upload(file_data: bytes, file_path: str, mime_type: str) -> dict`
  - `StorageBackend.download(stored_path: str) -> tuple[BytesIO, str, str]`
  - `StorageBackend.delete(stored_path: str) -> bool`
  - `StorageBackend.get_url(stored_path: str, expires: int = 3600) -> str`

- [ ] **Step 1: Add storage config to settings.py**

Add after the existing `SECRETS_ENGINE` line (end of `cmdb-api/settings.py`):

```python
# # file storage
FILE_STORAGE_BACKEND = env.str('FILE_STORAGE_BACKEND', default='local')
FILE_STORAGE_LOCAL_PATH = env.str('FILE_STORAGE_LOCAL_PATH', default='./uploaded_files/ci_files')
# S3 compatible storage
S3_ENDPOINT_URL = env.str('S3_ENDPOINT_URL', default='')
S3_ACCESS_KEY = env.str('S3_ACCESS_KEY', default='')
S3_SECRET_KEY = env.str('S3_SECRET_KEY', default='')
S3_BUCKET_NAME = env.str('S3_BUCKET_NAME', default='cmdb-files')
S3_REGION = env.str('S3_REGION', default='us-east-1')
S3_USE_SSL = env.bool('S3_USE_SSL', default=True)
```

- [ ] **Step 2: Create `cmdb-api/api/lib/cmdb/storage/__init__.py`**

```python
# -*- coding:utf-8 -*-
from api.core.context import current_app


def get_storage_backend(backend_name=None):
    """Factory: resolve backend name -> StorageBackend instance.
    Falls back to global FILE_STORAGE_BACKEND when backend_name is None/empty.
    """
    if not backend_name:
        backend_name = current_app.config.get('FILE_STORAGE_BACKEND', 'local')

    if backend_name == 's3':
        from api.lib.cmdb.storage.s3_storage import S3Storage
        return S3Storage()
    else:
        from api.lib.cmdb.storage.local import LocalStorage
        return LocalStorage()
```

- [ ] **Step 3: Create `cmdb-api/api/lib/cmdb/storage/base.py`**

```python
# -*- coding:utf-8 -*-
from abc import ABC, abstractmethod
from io import BytesIO


class StorageBackend(ABC):

    @abstractmethod
    def upload(self, file_data: bytes, file_path: str, mime_type: str = 'application/octet-stream') -> dict:
        """Upload a file.

        Returns:
            dict: {"stored_path": str, "size": int}
        """
        ...

    @abstractmethod
    def download(self, stored_path: str) -> tuple:
        """Download a file.

        Returns:
            tuple: (BytesIO_stream, filename, mime_type)
        """
        ...

    @abstractmethod
    def delete(self, stored_path: str) -> bool:
        """Delete a file. Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    def get_url(self, stored_path: str, expires: int = 3600) -> str:
        """Get a direct access URL for the file."""
        ...
```

- [ ] **Step 4: Create `cmdb-api/api/lib/cmdb/storage/local.py`**

```python
# -*- coding:utf-8 -*-
import os
import uuid
from datetime import datetime
from io import BytesIO

from api.core.context import current_app
from api.lib.cmdb.storage.base import StorageBackend


class LocalStorage(StorageBackend):

    def _get_abs_path(self, file_path):
        base = current_app.config.get('FILE_STORAGE_LOCAL_PATH', './uploaded_files/ci_files')
        return os.path.join(base, file_path)

    def upload(self, file_data: bytes, file_path: str = None, mime_type: str = 'application/octet-stream') -> dict:
        # generate dated path: YYYY/MM/DD/uuid_filename
        now = datetime.now()
        date_prefix = now.strftime('%Y/%m/%d')
        uid = str(uuid.uuid4())[:8]
        safe_name = file_path if file_path else f"{uid}.bin"
        if file_path and '.' in file_path:
            name, ext = file_path.rsplit('.', 1)
            safe_name = f"{uid}_{name}.{ext}"
        stored_path = os.path.join(date_prefix, safe_name)

        abs_path = self._get_abs_path(stored_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'wb') as f:
            f.write(file_data)

        return {"stored_path": stored_path, "size": len(file_data)}

    def download(self, stored_path: str) -> tuple:
        abs_path = self._get_abs_path(stored_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {stored_path}")
        filename = os.path.basename(stored_path)
        mime_type = 'application/octet-stream'
        with open(abs_path, 'rb') as f:
            data = f.read()
        return BytesIO(data), filename, mime_type

    def delete(self, stored_path: str) -> bool:
        abs_path = self._get_abs_path(stored_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
            return True
        return False

    def get_url(self, stored_path: str, expires: int = 3600) -> str:
        return f"/api/v0.1/ci/files?path={stored_path}"
```

- [ ] **Step 5: Create `cmdb-api/api/lib/cmdb/storage/s3_storage.py`**

```python
# -*- coding:utf-8 -*-
import uuid
from datetime import datetime
from io import BytesIO

import boto3
from botocore.config import Config as BotoConfig

from api.core.context import current_app
from api.lib.cmdb.storage.base import StorageBackend


class S3Storage(StorageBackend):

    def __init__(self):
        cfg = current_app.config
        self._client = boto3.client(
            's3',
            endpoint_url=cfg.get('S3_ENDPOINT_URL') or None,
            aws_access_key_id=cfg.get('S3_ACCESS_KEY'),
            aws_secret_access_key=cfg.get('S3_SECRET_KEY'),
            region_name=cfg.get('S3_REGION', 'us-east-1'),
            use_ssl=cfg.get('S3_USE_SSL', True),
            config=BotoConfig(signature_version='s3v4'),
        )
        self._bucket = cfg.get('S3_BUCKET_NAME', 'cmdb-files')

    def upload(self, file_data: bytes, file_path: str = None, mime_type: str = 'application/octet-stream') -> dict:
        now = datetime.now()
        date_prefix = now.strftime('%Y/%m/%d')
        uid = str(uuid.uuid4())[:8]
        safe_name = file_path if file_path else f"{uid}.bin"
        if file_path and '.' in file_path:
            name, ext = file_path.rsplit('.', 1)
            safe_name = f"{uid}_{name}.{ext}"
        stored_path = f"{date_prefix}/{safe_name}"

        self._client.put_object(
            Bucket=self._bucket,
            Key=stored_path,
            Body=file_data,
            ContentType=mime_type,
        )
        return {"stored_path": stored_path, "size": len(file_data)}

    def download(self, stored_path: str) -> tuple:
        response = self._client.get_object(Bucket=self._bucket, Key=stored_path)
        data = response['Body'].read()
        filename = stored_path.rsplit('/', 1)[-1]
        mime_type = response.get('ContentType', 'application/octet-stream')
        return BytesIO(data), filename, mime_type

    def delete(self, stored_path: str) -> bool:
        self._client.delete_object(Bucket=self._bucket, Key=stored_path)
        return True

    def get_url(self, stored_path: str, expires: int = 3600) -> str:
        return self._client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self._bucket, 'Key': stored_path},
            ExpiresIn=expires,
        )
```

- [ ] **Step 6: Add boto3 dependency**

```bash
cd cmdb-api && uv add boto3 && cd ..
```

- [ ] **Step 7: Commit**

```bash
git add cmdb-api/settings.py cmdb-api/api/lib/cmdb/storage/ cmdb-api/pyproject.toml cmdb-api/uv.lock
git commit -m "feat: add storage backend abstraction with LocalStorage and S3Storage"
```

---

### Task 3: CIFileManager + API Routes

**Files:**
- Create: `cmdb-api/api/lib/cmdb/ci_file.py`
- Create: `cmdb-api/api/views/cmdb/ci_file.py`

**Interfaces:**
- Consumes: `get_storage_backend()` from Task 2, `AttributeCache` for reading attr `option.file_storage`
- Produces:
  - `CIFileManager.upload_files(files, attr_id=None) -> list[dict]`
  - `CIFileManager.get_file(stored_path: str) -> tuple[BytesIO, str, str]`
  - `CIFileManager.delete_files(paths: list) -> int`
  - `CIFileManager.get_storage_backend_for_attr(attr_id=None) -> StorageBackend`
  - API endpoints auto-discovered via `router = APIRouter(...)`

- [ ] **Step 1: Create `cmdb-api/api/lib/cmdb/ci_file.py`**

```python
# -*- coding:utf-8 -*-
import logging

from api.core.context import current_app
from api.lib.cmdb.cache import AttributeCache
from api.lib.cmdb.storage import get_storage_backend

logger = logging.getLogger('cmdb')

# Default allowed extensions when no config is set
DEFAULT_ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp',
    'xls', 'xlsx', 'doc', 'docx', 'ppt', 'pptx', 'csv', 'json',
    'zip', 'rar', '7z', 'log',
}

DEFAULT_MAX_FILE_SIZE_MB = 50


class CIFileManager(object):

    def get_storage_backend_for_attr(self, attr_id=None):
        """Resolve storage backend: attribute-level -> global -> default."""
        backend_name = None
        if attr_id:
            attr = AttributeCache.get(attr_id)
            if attr and attr.option:
                file_storage = attr.option.get('file_storage', {})
                backend_name = file_storage.get('backend')
        return get_storage_backend(backend_name)

    def _get_allowed_extensions(self, attr_id=None):
        attr_extensions = None
        if attr_id:
            attr = AttributeCache.get(attr_id)
            if attr and attr.option:
                file_storage = attr.option.get('file_storage', {})
                attr_extensions = file_storage.get('allowed_extensions')
        if attr_extensions is not None:
            return set(attr_extensions)
        return current_app.config.get('FILE_ALLOWED_EXTENSIONS', DEFAULT_ALLOWED_EXTENSIONS)

    def _get_max_file_size(self, attr_id=None):
        attr_limit = None
        if attr_id:
            attr = AttributeCache.get(attr_id)
            if attr and attr.option:
                file_storage = attr.option.get('file_storage', {})
                attr_limit = file_storage.get('max_file_size_mb')
        if attr_limit is not None:
            return int(attr_limit) * 1024 * 1024
        return DEFAULT_MAX_FILE_SIZE_MB * 1024 * 1024

    def upload_files(self, files, attr_id=None):
        """Upload one or more files.

        Args:
            files: list of file objects (with .filename, .read())
            attr_id: optional attribute id for config resolution

        Returns:
            list[dict]: [{"original_name": str, "stored_path": str, "size": int, "mime_type": str}, ...]
        """
        backend = self.get_storage_backend_for_attr(attr_id)
        allowed_extensions = self._get_allowed_extensions(attr_id)
        max_size = self._get_max_file_size(attr_id)

        results = []
        for file in files:
            filename = file.filename if hasattr(file, 'filename') else 'unknown'
            extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if extension not in allowed_extensions:
                raise ValueError(f"File type .{extension} is not allowed")

            file_data = file.read()
            if len(file_data) > max_size:
                raise ValueError(f"File {filename} exceeds max size limit")

            mime_type = getattr(file, 'content_type', 'application/octet-stream')
            result = backend.upload(file_data, filename, mime_type)
            result['original_name'] = filename
            result['mime_type'] = mime_type
            results.append(result)

        return results

    def get_file(self, stored_path):
        """Download a file by its stored path.

        Returns:
            tuple: (BytesIO_stream, filename, mime_type)
        """
        backend = get_storage_backend()
        return backend.download(stored_path)

    def delete_files(self, paths):
        """Delete files by their stored paths.

        Args:
            paths: list of stored_path strings

        Returns:
            int: number of successfully deleted files
        """
        backend = get_storage_backend()
        deleted = 0
        for path in paths:
            try:
                if backend.delete(path):
                    deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete file {path}: {e}")
        return deleted
```

- [ ] **Step 2: Create `cmdb-api/api/views/cmdb/ci_file.py`**

```python
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

    file_list = request.files.getlist('files') if 'files' in request.files else [request.files['file']]

    try:
        results = _file_manager.upload_files(file_list, attr_id=attr_id)
    except ValueError as e:
        abort(400, str(e))

    return {'files': results}


@router.get("/ci/files")
def get_ci_file_view_get(path: str = None, download: int = 0):
    if not path:
        abort(400, 'path is required')

    try:
        file_stream, filename, mime_type = _file_manager.get_file(path)
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
```

- [ ] **Step 3: Commit**

```bash
git add cmdb-api/api/lib/cmdb/ci_file.py cmdb-api/api/views/cmdb/ci_file.py
git commit -m "feat: add CIFileManager and file upload/download/delete API routes"
```

---

### Task 4: CI Delete — Clean Up File Resources

**Files:**
- Modify: `cmdb-api/api/lib/cmdb/ci.py`

**Interfaces:**
- Consumes: `CIFileManager` from Task 3, `AttributeCache`
- Produces: Updated `CIManager.delete_ci` that cleans up file storage

- [ ] **Step 1: Find the CI deletion logic and add file cleanup**

Search for the CI delete method in `cmdb-api/api/lib/cmdb/ci.py`. In the method that performs CI deletion (likely a `delete` or `soft_delete` override that also cleans up value tables), add file cleanup code at the end of the deletion flow, AFTER dependent rows are removed but BEFORE the CI record itself is removed:

```python
from api.lib.cmdb.cache import AttributeCache
from api.lib.cmdb.ci_file import CIFileManager

# Inside the CI delete method, after value rows are collected but before deletion:
    # Clean up file storage for file-type attributes
    try:
        file_attr_ids = [
            attr.id for attr in type_attrs
            if getattr(attr, 'is_file', False)
        ]
        if file_attr_ids:
            # Collect stored_paths from all file-type attribute values of this CI
            paths_to_delete = []
            for attr_id in file_attr_ids:
                value_row = (
                    db.session.query(model.CIValueText)
                    .filter_by(ci_id=ci_id, attr_id=attr_id)
                    .first()
                )
                if value_row and value_row.value:
                    import json
                    try:
                        file_list = json.loads(value_row.value)
                        for f in file_list:
                            if f.get('stored_path'):
                                paths_to_delete.append(f['stored_path'])
                    except (json.JSONDecodeError, TypeError):
                        pass
            if paths_to_delete:
                _file_manager = CIFileManager()
                _file_manager.delete_files(paths_to_delete)
    except Exception as e:
        logger.warning(f"File cleanup failed during CI deletion: {e}")
```

Note: The exact location depends on the CI delete method. The key patterns to follow:
- `type_attrs` is typically obtained from `CITypeAttributesCache.get(type_id)` or similar
- `ci_id` is the CI record's `id`
- All value queries go through SQLAlchemy session, NOT raw SQL

If the delete method uses a low-level SQL delete (e.g., `session.execute(delete(CIValueText)...)`), instead collect file paths BEFORE the values table rows are deleted, then clean up.

- [ ] **Step 2: Commit**

```bash
git add cmdb-api/api/lib/cmdb/ci.py
git commit -m "feat: clean up file storage when CI is deleted"
```

---

### Task 5: Frontend — Value Type Map + Helper Functions

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/utils/const.js`
- Modify: `cmdb-ui/src/modules/cmdb/utils/helper.js`
- Modify: `cmdb-ui/src/modules/cmdb/views/ci_types/onetermSync/advancedConfig.vue`
- Modify: `cmdb-ui/src/modules/cmdb/views/ci_types/onetermSync/attributeMappingTable.vue`

**Interfaces:**
- Produces: `valueTypeMap()` includes key `'12'`, `getPropertyType` returns `'12'` when `is_file`, `getPropertyIcon/Style` handle `'12'`

- [ ] **Step 1: Add type `'12'` to `valueTypeMap`**

In `cmdb-ui/src/modules/cmdb/utils/const.js`, inside `valueTypeMap()`, add after `'11'`:

```js
export const valueTypeMap = () => {
  return {
    '0': i18n.t('cmdb.ciType.int'),
    '1': i18n.t('cmdb.ciType.float'),
    '2': i18n.t('cmdb.ciType.shortText'),
    '3': i18n.t('cmdb.ciType.datetime'),
    '4': i18n.t('cmdb.ciType.date'),
    '5': i18n.t('cmdb.ciType.time'),
    '6': 'JSON',
    '7': i18n.t('cmdb.ciType.password'),
    '8': i18n.t('cmdb.ciType.link'),
    '9': i18n.t('cmdb.ciType.longText'),
    '10': i18n.t('cmdb.ciType.bool'),
    '11': i18n.t('cmdb.ciType.reference'),
    '12': i18n.t('cmdb.ciType.file'),
  }
}
```

- [ ] **Step 2: Update `getPropertyType` in `helper.js`**

In `cmdb-ui/src/modules/cmdb/utils/helper.js`, in `getPropertyType` function (line ~217), add after the password/link checks:

```js
export const getPropertyType = (attr) => {
  if (attr.is_password) {
    return '7'
  }
  if (attr.is_link) {
    return '8'
  }
  if (attr.is_file) {
    return '12'
  }

  switch (attr.value_type) {
    case '0':
      if (attr.is_reference) {
        return '11'
      }
      return '0'
    case '2':
      if (!attr.is_index) {
        return '9'
      }
      return '2'
    case '7':
      if (attr.is_bool) {
        return '10'
      }
      return '7'
    default:
      return attr?.value_type ?? ''
  }
}
```

- [ ] **Step 3: Update `getPropertyIcon` in `helper.js`**

Add case for `'12'` before the default return in `getPropertyIcon`:

```js
        case '12':
            return 'duose-file'
```

- [ ] **Step 4: Update `getPropertyStyle` in `helper.js`**

Add case for `'12'` before the closing `}`:

```js
        case '12':
            return { color: '#722ed1', backgroundColor: '#f9f0ff' }
```

- [ ] **Step 5: Update `isLongText` in `helper.js`**

Change the existing `is_attachment` reference to `is_file` (line ~302):

From:
```js
  return attr.value_type === '2' && attr.is_index === false && !attr.is_link && !attr.is_attachment && !attr.is_password
```

To:
```js
  return attr.value_type === '2' && attr.is_index === false && !attr.is_link && !attr.is_file && !attr.is_password
```

- [ ] **Step 6: Update `is_attachment` references in onetermSync files**

In `cmdb-ui/src/modules/cmdb/views/ci_types/onetermSync/advancedConfig.vue` (line ~195), change:

```js
        if (attr.is_attachment) return false
```

to:

```js
        if (attr.is_file) return false
```

In `cmdb-ui/src/modules/cmdb/views/ci_types/onetermSync/attributeMappingTable.vue` (line ~110), change:

```js
        if (attr.is_attachment) return false
```

to:

```js
        if (attr.is_file) return false
```

- [ ] **Step 7: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/utils/const.js cmdb-ui/src/modules/cmdb/utils/helper.js
git commit -m "feat: add file type (12) to valueTypeMap, getPropertyIcon/Type/Style"
```

---

### Task 6: Frontend — Attribute Create/Edit Forms (File Type Option)

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/ci_types/ceateNewAttribute.vue`
- Modify: `cmdb-ui/src/modules/cmdb/views/ci_types/attributeEditForm.vue`
- Modify: `cmdb-ui/src/modules/cmdb/views/ci_types/attributesTable.vue`

- [ ] **Step 1: `ceateNewAttribute.vue` — Add file type to data type dropdown and handleSubmit**

The data type `<a-select>` for `value_type` already renders all entries from `valueTypeMap` — key `'12'` will appear automatically after Task 5.

In `handleSubmit`, inside the `switch (values.value_type)` block, add before the `default:` case:

```js
            case '12':
              values.value_type = '2'
              values.is_file = true
              break
```

- [ ] **Step 2: `attributeEditForm.vue` — Add file type to data type dropdown and handleSubmit**

Same as Step 1 — the dropdown auto-renders from `valueTypeMap`. In `handleSubmit`, add the same `case '12'` block before `default:`:

```js
            case '12':
              values.value_type = '2'
              values.is_file = true
              break
```

- [ ] **Step 3: `attributeEditForm.vue` — Show file storage settings when file type selected**

Add file storage settings section after the "advanced settings" area, conditionally shown when `currentValueType === '12'`:

In the template, after line ~365 (after the `is_dynamic` switch section), add:

```html
        <template v-if="currentValueType === '12'">
          <a-divider style="font-size:14px;margin-top:6px;">{{ $t('cmdb.ciType.fileStorage') }}</a-divider>
          <a-col :span="12">
            <a-form-item
              :label-col="formItemLayout.labelCol"
              :wrapper-col="formItemLayout.wrapperCol"
              :label="$t('cmdb.ciType.fileStorageBackend')"
            >
              <a-select v-model="fileStorageBackend" style="width: 100%">
                <a-select-option value="">{{ $t('cmdb.ciType.followGlobal') }}</a-select-option>
                <a-select-option value="local">{{ $t('cmdb.ciType.local') }}</a-select-option>
                <a-select-option value="s3">S3</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item
              :label-col="formItemLayout.labelCol"
              :wrapper-col="formItemLayout.wrapperCol"
              :label="$t('cmdb.ciType.allowedExtensions')"
            >
              <a-select mode="tags" v-model="fileAllowedExtensions" style="width: 100%" :placeholder="$t('cmdb.ciType.allowedExtensions')">
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item
              :label-col="formItemLayout.labelCol"
              :wrapper-col="formItemLayout.wrapperCol"
              :label="$t('cmdb.ciType.maxFileSize')"
            >
              <a-input-number v-model="fileMaxSizeMb" style="width: 100%" :min="1" :max="500" />
            </a-form-item>
          </a-col>
        </template>
```

In `data()`, add:

```js
      fileStorageBackend: '',
      fileAllowedExtensions: [],
      fileMaxSizeMb: 50,
```

In `handleEdit`, when `_record.value_type === '12'`, populate these from `_record.option?.file_storage`:

```js
        if (_record.value_type === '12') {
          const fs = (_record.option && _record.option.file_storage) || {}
          this.fileStorageBackend = fs.backend || ''
          this.fileAllowedExtensions = fs.allowed_extensions || []
          this.fileMaxSizeMb = fs.max_file_size_mb || 50
        }
```

In `handleSubmit`, when building the file storage option, add to `values` before the switch that remaps types:

```js
          if (this.currentValueType === '12') {
            values.option = values.option || {}
            values.option.file_storage = {
              backend: this.fileStorageBackend || undefined,
              allowed_extensions: this.fileAllowedExtensions.length ? this.fileAllowedExtensions : undefined,
              max_file_size_mb: this.fileMaxSizeMb,
            }
          }
```

- [ ] **Step 4: `attributesTable.vue` — Add `'12'` to type filter keys**

In the computed `valueTypeMap`, the `keys` array already exists. Add `'12'` to the end:

```js
    valueTypeMap() {
      const map = valueTypeMap()
      const keys = ['0', '1', '2', '9', '3', '4', '5', '6', '7', '8', '10', '11', '12']
      return keys.map((key) => ({
        key,
        value: map[key]
      }))
    },
```

- [ ] **Step 4: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/views/ci_types/ceateNewAttribute.vue cmdb-ui/src/modules/cmdb/views/ci_types/attributeEditForm.vue cmdb-ui/src/modules/cmdb/views/ci_types/attributesTable.vue
git commit -m "feat: add file type option to attribute create/edit forms"
```

---

### Task 7: Frontend — CiFileField Component

**Files:**
- Create: `cmdb-ui/src/modules/cmdb/components/CiFileField.vue`

**Interfaces:**
- Consumes: `ciFileApi` from Task 8
- Props: `value` (Array of file objects), `isList` (Boolean), `attrOption` (Object — attribute's option JSON)
- Events: `input` (v-model value change)

- [ ] **Step 1: Create the CiFileField component**

Create `cmdb-ui/src/modules/cmdb/components/CiFileField.vue`:

```vue
<template>
  <div class="ci-file-field">
    <!-- Preview mode -->
    <template v-if="!isEdit">
      <div v-if="!fileList.length" class="ci-file-field-empty">--</div>
      <div v-else class="ci-file-field-preview">
        <div
          v-for="(file, idx) in fileList"
          :key="idx"
          class="ci-file-field-item"
        >
          <!-- Image preview -->
          <a-image
            v-if="isImage(file.mime_type)"
            :src="getFileUrl(file.stored_path)"
            :preview="true"
            :style="{ maxWidth: '100px', maxHeight: '60px' }"
          />
          <ops-icon v-else type="duose-file" style="font-size: 24px; color: #722ed1;" />
          <div class="ci-file-field-info">
            <a :href="getFileUrl(file.stored_path)" :download="file.original_name">
              {{ file.original_name }}
            </a>
            <span class="ci-file-field-size">{{ formatSize(file.size) }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- Edit mode -->
    <template v-else>
      <div v-if="fileList.length" class="ci-file-field-list">
        <div
          v-for="(file, idx) in fileList"
          :key="idx"
          class="ci-file-field-item ci-file-field-item-editable"
        >
          <ops-icon type="duose-file" style="font-size: 18px; color: #722ed1; margin-right: 8px;" />
          <span class="ci-file-field-name">{{ file.original_name }}</span>
          <span class="ci-file-field-size">{{ formatSize(file.size) }}</span>
          <a @click="handleDeleteFile(idx)" style="margin-left: auto; color: #ff4d4f;">
            <a-icon type="delete" />
          </a>
        </div>
      </div>
      <a-upload
        :multiple="isList"
        :showUploadList="false"
        :beforeUpload="handleBeforeUpload"
        :customRequest="handleCustomRequest"
      >
        <a-button>
          <a-icon type="upload" />
          {{ fileList.length ? $t('cmdb.ciType.fileUploadMore') : $t('cmdb.ciType.fileUpload') }}
        </a-button>
      </a-upload>
    </template>
  </div>
</template>

<script>
import { uploadCiFile } from '@/modules/cmdb/api/ciFile'

export default {
  name: 'CiFileField',
  props: {
    value: {
      type: Array,
      default: () => []
    },
    isList: {
      type: Boolean,
      default: false
    },
    isEdit: {
      type: Boolean,
      default: false
    },
    attrId: {
      type: [Number, String],
      default: null
    }
  },
  data() {
    return {
      fileList: [],
      uploading: false
    }
  },
  watch: {
    value: {
      immediate: true,
      handler(val) {
        // Accept value as JSON string or parsed array
        if (typeof val === 'string') {
          try {
            this.fileList = JSON.parse(val)
          } catch (e) {
            this.fileList = []
          }
        } else if (Array.isArray(val)) {
          this.fileList = val
        } else {
          this.fileList = []
        }
      }
    }
  },
  methods: {
    getFileUrl(storedPath) {
      return `/api/v0.1/ci/files?path=${encodeURIComponent(storedPath)}`
    },
    isImage(mimeType) {
      return mimeType && mimeType.startsWith('image/')
    },
    formatSize(bytes) {
      if (!bytes) return '0 B'
      const units = ['B', 'KB', 'MB', 'GB']
      let i = 0
      let size = bytes
      while (size >= 1024 && i < units.length - 1) {
        size /= 1024
        i++
      }
      return size.toFixed(i === 0 ? 0 : 1) + ' ' + units[i]
    },
    emitChange() {
      this.$emit('input', JSON.stringify(this.fileList))
    },
    handleBeforeUpload(file) {
      // validation is done server-side, just allow through
      return true
    },
    async handleCustomRequest({ file, onSuccess, onError }) {
      try {
        const formData = new FormData()
        formData.append('files', file)
        const res = await uploadCiFile(formData, this.attrId)
        const newFiles = res.files || []
        if (this.isList) {
          this.fileList.push(...newFiles)
        } else {
          this.fileList = newFiles
        }
        this.emitChange()
        if (onSuccess) onSuccess(res, file)
      } catch (e) {
        this.$message.error(e.message || this.$t('cmdb.ciType.fileUploadFailed'))
        if (onError) onError(e)
      }
    },
    handleDeleteFile(idx) {
      this.fileList.splice(idx, 1)
      this.emitChange()
    }
  }
}
</script>

<style lang="less" scoped>
.ci-file-field {
  &-empty {
    color: #c3cdd7;
  }
  &-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  &-list {
    margin-bottom: 8px;
  }
  &-item {
    display: flex;
    align-items: center;
    padding: 4px 8px;
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    margin-bottom: 4px;
    &-editable {
      background: #fafafa;
    }
  }
  &-info {
    display: flex;
    flex-direction: column;
    margin-left: 8px;
  }
  &-name {
    flex: 1;
    margin: 0 8px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  &-size {
    color: #a5a9bc;
    font-size: 12px;
    white-space: nowrap;
  }
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/components/CiFileField.vue
git commit -m "feat: add CiFileField component for file upload/preview/download"
```

---

### Task 8: Frontend — API Client for File Operations

**Files:**
- Create: `cmdb-ui/src/modules/cmdb/api/ciFile.js`

**Interfaces:**
- Produces:
  - `uploadCiFile(formData, attrId)` — POST multipart to `/v0.1/ci/files`
  - `deleteCiFiles(paths)` — DELETE `/v0.1/ci/files`

- [ ] **Step 1: Create `cmdb-ui/src/modules/cmdb/api/ciFile.js`**

```js
import { axios } from '@/utils/request'

export function uploadCiFile(formData, attrId) {
  const params = {}
  if (attrId) {
    params.attr_id = attrId
  }
  return axios({
    url: '/v0.1/ci/files',
    method: 'POST',
    data: formData,
    params,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function deleteCiFiles(paths) {
  return axios({
    url: '/v0.1/ci/files',
    method: 'DELETE',
    data: { paths }
  })
}
```

- [ ] **Step 2: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/api/ciFile.js
git commit -m "feat: add ciFile API client for file upload/delete"
```

---

### Task 9: Frontend — CI Detail Page (Preview/Edit File Attributes)

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailAttrContent.vue`
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailTab.vue`

- [ ] **Step 1: `ciDetailAttrContent.vue` — Add file attribute rendering**

In the preview section (the `v-if="!isEdit"` block), add a template for file attributes. After the `is_reference` block (line ~4-13) and before the `is_password` block:

```html
      <CiFileField
        v-else-if="attr.is_file"
        :value="ci[attr.name]"
        :isList="attr.is_list"
        :isEdit="false"
        :attrId="attr.id"
      />
```

In the edit section (the `v-else` block), add after the `CIReferenceAttr` block:

```html
          <CiFileField
            v-else-if="attr.is_file"
            :isEdit="true"
            :isList="attr.is_list"
            :attrId="attr.id"
            v-decorator="[
              attr.name,
              {
                rules: [{ required: attr.is_required, message: $t('placeholder2') + `${attr.alias || attr.name}` }],
              }
            ]"
          />
```

In the `<script>` section, add the import:

```js
import CiFileField from '@/modules/cmdb/components/CiFileField.vue'
```

Add to `components`:

```js
  components: {
    // ... existing components ...
    CiFileField,
  },
```

- [ ] **Step 2: `ciDetailTab.vue` — Ensure CiFileField is available if used there**

Check if `ciDetailTab.vue` renders attributes directly. If it uses `ciDetailAttrContent.vue`, no changes needed. Otherwise, apply the same pattern as Step 1.

- [ ] **Step 3: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailAttrContent.vue cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailTab.vue
git commit -m "feat: integrate CiFileField into CI detail attribute display"
```

---

### Task 10: Frontend — CI Create/Edit Forms (File Upload Integration)

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/CreateInstanceForm.vue`
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/createInstanceFormByGroup.vue`

- [ ] **Step 1: `CreateInstanceForm.vue` — Use CiFileField for file attributes**

In the form field rendering loop, when an attribute has `is_file=true`, render `CiFileField` instead of a text input. Add the import and component registration:

```js
import CiFileField from '@/modules/cmdb/components/CiFileField.vue'

// In components:
  components: {
    // ... existing ...
    CiFileField,
  },
```

In the template where form fields are rendered (look for the `v-for` over attributes that renders different form controls based on type), add a condition for file:

```html
          <CiFileField
            v-else-if="item.is_file"
            :isEdit="true"
            :isList="item.is_list"
            :attrId="item.id"
            v-decorator="[item.name, { rules: getRules(item) }]"
          />
```

- [ ] **Step 2: `createInstanceFormByGroup.vue` — Same pattern as Step 1**

Apply the same `CiFileField` import, component registration, and template condition for file attributes.

- [ ] **Step 3: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/views/ci/modules/CreateInstanceForm.vue cmdb-ui/src/modules/cmdb/views/ci/modules/createInstanceFormByGroup.vue
git commit -m "feat: integrate CiFileField into CI create/edit forms"
```

---

### Task 11: Frontend — CI Table Column for File Attributes

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/utils/helper.js`

- [ ] **Step 1: Update `getCITableColumns` to handle file type**

In `cmdb-ui/src/modules/cmdb/utils/helper.js`, in the `getCITableColumns` function, the `switch (attr.value_type)` block for `editRender` (lines ~59-84) — add file handling. File attributes use JSON display:

```js
            case '2':
                if (attr.is_file) {
                    editRender['props'] = { 'type': 'text' }
                    // display handled via column formatter
                } else {
                    editRender['attrs'] = { 'type': 'text' }
                }
                break
```

And when building the column object (around line ~114), add file-specific properties:

```js
            is_file: attr.is_file,
```

The vxe-table column for file attributes will display file count and total size. In the column definition, add a `formatter` or use the `slots` approach — the simplest is to set additional metadata on the column object that the table component can use. For now, pass `is_file` through so the table template can handle it:

```js
        columns.push({
            // ... existing properties ...
            is_file: attr.is_file,
            // ...
        })
```

- [ ] **Step 2: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/utils/helper.js
git commit -m "feat: add file type handling to CI table column definition"
```

---

### Task 12: Frontend — i18n Strings

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/lang/zh.js`
- Modify: `cmdb-ui/src/modules/cmdb/lang/en.js`

- [ ] **Step 1: Add Chinese i18n strings**

In `cmdb-ui/src/modules/cmdb/lang/zh.js`, find the `cmdb.ciType` section and add:

```js
    file: '文件',
    fileStorage: '文件存储设置',
    fileStorageBackend: '存储方式',
    followGlobal: '跟随全局',
    local: '本地存储',
    allowedExtensions: '允许的文件类型',
    maxFileSize: '单文件最大大小(MB)',
    fileUpload: '上传文件',
    fileUploadMore: '继续上传',
    fileUploadFailed: '文件上传失败',
    filePreview: '预览',
    fileDownload: '下载',
    fileDelete: '删除',
    fileCount: '{count} 个文件',
```

- [ ] **Step 2: Add English i18n strings**

In `cmdb-ui/src/modules/cmdb/lang/en.js`, add:

```js
    file: 'File',
    fileStorage: 'File Storage',
    fileStorageBackend: 'Storage Backend',
    followGlobal: 'Follow Global',
    local: 'Local',
    allowedExtensions: 'Allowed Extensions',
    maxFileSize: 'Max File Size (MB)',
    fileUpload: 'Upload File',
    fileUploadMore: 'Upload More',
    fileUploadFailed: 'File upload failed',
    filePreview: 'Preview',
    fileDownload: 'Download',
    fileDelete: 'Delete',
    fileCount: '{count} file(s)',
```

- [ ] **Step 3: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/lang/zh.js cmdb-ui/src/modules/cmdb/lang/en.js
git commit -m "feat: add i18n strings for file attribute type"
```

---

### Task 13: Integration — Connect and Verify End-to-End

- [ ] **Step 1: Run database migration**

```bash
cd cmdb-api && uv run python cli.py db-setup && cd ..
```

- [ ] **Step 2: Start the API and verify the new routes are discovered**

```bash
cd cmdb-api && timeout 5 uv run uvicorn main:app --port 5001 2>&1 || true
```

Check that `/api/v0.1/ci/files` appears in the route listing.

- [ ] **Step 3: Test file upload via curl**

```bash
echo "test content" > /tmp/test.txt
curl -X POST http://127.0.0.1:5000/api/v0.1/ci/files \
  -H "Access-Token: <valid_token>" \
  -F "files=@/tmp/test.txt"
```

Expected: JSON response with `files` array containing `original_name`, `stored_path`, `size`, `mime_type`.

- [ ] **Step 4: Test file download**

```bash
curl http://127.0.0.1:5000/api/v0.1/ci/files?path=<stored_path_from_step_3>
```

Expected: raw file content "test content".

- [ ] **Step 5: Test creating a file-type attribute via API**

```bash
curl -X POST http://127.0.0.1:5000/api/v0.1/ci_types/attributes \
  -H "Content-Type: application/json" \
  -H "Access-Token: <valid_token>" \
  -d '{"name":"test_file","alias":"Test File","value_type":"2","is_file":true}'
```

- [ ] **Step 6: Build frontend**

```bash
cd cmdb-ui && yarn build && cd ..
```

- [ ] **Step 7: Manual smoke test in browser**

- Create a CI type with a file attribute
- Create a CI instance of that type and upload a file
- View the CI detail — see the file preview/download link
- Edit the CI instance — replace the file
- Delete the CI instance — verify file is cleaned up

- [ ] **Step 8: Commit any fixes**

```bash
git add -A && git commit -m "fix: integration fixes from end-to-end testing"
```
