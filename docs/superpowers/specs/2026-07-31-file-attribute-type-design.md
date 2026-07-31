# 文件属性类型 — 设计方案

> 状态：待审批 | 分支：[feature/file-attribute-type](../../../.git) | 日期：2026-07-31

## 1. 背景与目标

在 CMDB 模型配置中新增"文件"数据类型，使 CI 实例的属性支持文件上传、预览和下载。文件存储支持**本地文件系统**和 **S3 兼容对象存储**（MinIO、Ceph RGW、AWS S3 等），通过全局配置 + 属性级覆盖来切换。

## 2. 设计决策

| 决策 | 选项 | 理由 |
|------|------|------|
| 实现模式 | 虚拟类型（`value_type=TEXT` + `is_file=true`） | 与 password/link/bool/reference 保持一致，改动范围最小 |
| 文件数量 | 复用 `is_list` 标志支持多文件 | 现有 flag 语义清晰，无需新建列 |
| 存储配置 | 全局默认 + 属性级覆盖 | 兼顾运维统一性和业务灵活性 |
| 交互场景 | 创建/编辑/详情预览/下载/替换/批量导入 | 覆盖完整 CI 生命周期 |
| 预览范围 | 全类型预览（含 Office 文档） | 用户体验优先 |
| 文件类型限制 | 全局默认 + 属性级覆盖 | 安全管控与灵活性兼顾 |

## 3. 存储架构

### 3.1 全局配置（settings.py / .env）

```
FILE_STORAGE_BACKEND = 'local'          # 'local' | 's3'
FILE_STORAGE_LOCAL_PATH = './uploaded_files/ci_files'

# S3 兼容存储
S3_ENDPOINT_URL = ''                    # 空=标准 S3；MinIO/Ceph 填自定义地址
S3_ACCESS_KEY = ''
S3_SECRET_KEY = ''
S3_BUCKET_NAME = 'cmdb-files'
S3_REGION = 'us-east-1'
S3_USE_SSL = True
```

### 3.2 存储后端抽象层

```
api/lib/cmdb/storage/
├── __init__.py           # get_storage_backend(backend_name) 工厂函数
├── base.py               # StorageBackend 抽象基类
├── local.py              # LocalStorage — 服务器本地磁盘
└── s3_storage.py         # S3Storage — boto3 → S3 兼容对象存储
```

**StorageBackend 接口定义：**

```python
class StorageBackend(ABC):
    @abstractmethod
    def upload(self, file_data: bytes, file_path: str, mime_type: str) -> dict:
        """返回 {"stored_path": str, "size": int}"""
        ...

    @abstractmethod
    def download(self, stored_path: str) -> tuple[BytesIO, str, str]:
        """返回 (file_stream, filename, mime_type)"""
        ...

    @abstractmethod
    def delete(self, stored_path: str) -> bool:
        ...

    @abstractmethod
    def get_url(self, stored_path: str, expires: int = 3600) -> str:
        """获取可访问 URL：S3 用 presigned URL，本地返回 API 路由"""
        ...
```

**LocalStorage 实现要点：**

- 文件存到 `FILE_STORAGE_LOCAL_PATH / YYYY / MM / DD / {uuid}_{secure_filename}`
- `get_url()` 返回内部 API 路由 `/api/v0.1/ci/files?path=xxx`
- 创建日期子目录，便于按日清理

**S3Storage 实现要点：**

- 依赖 `boto3` 库
- `upload()` → `s3_client.put_object(Bucket=..., Key=..., Body=..., ContentType=...)`
- `get_url()` → `s3_client.generate_presigned_url('get_object', ...)`
- `download()` → `s3_client.get_object(...)['Body'].read()`

### 3.3 属性级覆盖（option JSON）

```json
{
  "file_storage": {
    "backend": "s3",
    "allowed_extensions": ["pdf", "docx", "xlsx", "jpg", "png"],
    "max_file_size_mb": 100
  }
}
```

- `backend`: 可选，为空时使用全局默认
- `allowed_extensions`: 可选，为空时使用全局默认
- `max_file_size_mb`: 可选，为空时使用全局默认（默认 50MB）

文件上传验证时，后端的解析顺序：**属性级配置 > 全局配置 > 硬编码兜底**。

### 3.4 文件路径规范

```
本地: {YYYY}/{MM}/{DD}/{uuid}_{secure_filename}.ext
S3:   {YYYY}/{MM}/{DD}/{uuid}_{secure_filename}.ext
```

路径不包含属性 ID 或 CI ID，保证文件可以在 CI 实例间引用移动。

## 4. 数据库改动

### 4.1 c_attributes 表

```sql
ALTER TABLE c_attributes ADD COLUMN is_file BOOLEAN DEFAULT FALSE;
```

### 4.2 ORM 模型

```python
# api/models/cmdb.py — Attribute 类
is_file = db.Column(db.Boolean, default=False)
```

### 4.3 ValueTypeEnum

```python
class ValueTypeEnum(BaseEnum):
    # ... existing types (0-7) ...
    FILE = TEXT    # 文件类型：value_type='2' + is_file=True
```

### 4.4 ValueTypeMap

文件类型映射到 `c_value_texts` 表，与其他 TEXT 衍生类型一致。在 map 中 `"2"` 条目增加 `file` 相关标记。

### 4.5 文件值存储格式（c_value_texts.value）

CI 实例的文件属性值以 JSON 数组存储在 `c_value_texts.value`：

```json
[
  {
    "original_name": "拓扑架构图-v2.png",
    "stored_path": "2026/07/31/a1b2c3d4_拓扑架构图-v2.png",
    "size": 2048000,
    "mime_type": "image/png",
    "uploaded_at": "2026-07-31T10:30:00",
    "uploaded_by": "zhangsan"
  }
]
```

## 5. 后端 API 改动

### 5.1 新增文件操作 API

路由前缀 `/api/v0.1/ci/files`，放在 `views/cmdb/ci_file.py`：

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/ci/files` | multipart 上传文件（`?attr_id=123` 可选用于读取属性存储配置） |
| `GET` | `/ci/files` | 根据 `?path=xxx` 下载/预览文件；`?download=1` 强制 attachment |
| `DELETE` | `/ci/files` | body: `{"paths": ["path1", "path2"]}` 批量删除 |

**上传请求：**
```
POST /api/v0.1/ci/files?attr_id=123
Content-Type: multipart/form-data
files: [file1, file2, ...]
```

**上传响应：**
```json
{
  "files": [
    {
      "original_name": "doc.pdf",
      "stored_path": "2026/07/31/xxx_doc.pdf",
      "size": 1048576,
      "mime_type": "application/pdf"
    }
  ]
}
```

**下载响应：**
```
GET /api/v0.1/ci/files?path=2026/07/31/xxx_doc.pdf
→ 二进制文件流 (Content-Type 根据文件 extension 推断)
```

**下载（强制下载）：**
```
GET /api/v0.1/ci/files?path=2026/07/31/xxx_doc.pdf&download=1
→ Content-Disposition: attachment; filename="doc.pdf"
```

### 5.2 业务逻辑层

`api/lib/cmdb/ci_file.py` — `CIFileManager` 类：

- `upload_files(files, attr_id=None) -> list[dict]`
  - 确定存储后端（属性配置 → 全局配置）
  - 校验文件扩展名和大小（属性配置 → 全局配置 → 默认允许列表）
  - 生成安全存储路径
  - 逐个上传并收集元数据

- `get_file(stored_path) -> tuple[BytesIO, str, str]`
  - 解析路径判断后端类型 → 调用对应后端 download

- `delete_files(paths: list) -> int`
  - 解析每个路径 → 调用后端 delete → 返回成功删除数

- `get_storage_backend(attr_id=None) -> StorageBackend`
  - 属性存在 → 读 `option.file_storage.backend` → 回退到全局 `FILE_STORAGE_BACKEND`

### 5.3 CI 增删改中的文件处理

- **CI 创建/更新**：CI 实例保存时文件值已是 JSON 字符串，直接写入 `c_value_texts`，无需特殊处理
- **CI 删除**：CI 删除时遍历文件属性值，调用 `CIFileManager.delete_files()` 清理存储文件
- **CI 详情**：文件值返回时保持 JSON 格式，前端根据结构化数据渲染

## 6. 前端改动

### 6.1 模型配置层

#### const.js — 新增显示类型

```js
export const valueTypeMap = () => {
  return {
    // ... existing '0'-'11' ...
    '12': i18n.t('cmdb.ciType.file'),  // 新增
  }
}
```

#### helper.js — 三个函数扩展

- `getPropertyIcon`: case `'12'` → 文件图标
- `getPropertyType`: `attr.is_file` → return `'12'`
- `getPropertyStyle`: case `'12'` → 新背景色

#### attributesTable.vue

`valueTypeMap` computed 的 keys 列表加入 `'12'`。

### 6.2 属性编辑表单

**ceateNewAttribute.vue / attributeEditForm.vue:**

- 数据类型下拉框新增「文件」选项（value=`'12'`）
- 选中文件类型时，展示"文件存储设置"区域：
  - 存储方式下拉：跟随全局 / S3 / 本地
  - 允许的文件扩展名：tags 输入（如 `pdf, docx, jpg`）
  - 单文件最大大小：数字输入（单位 MB）
- `handleSubmit` switch 新增：
  ```js
  case '12':
    values.value_type = '2'
    values.is_file = true
    break
  ```

### 6.3 文件字段组件（新增）

**`components/CiFileField.vue`** — 通用文件上传/预览/下载组件：

| 场景 | 展示 |
|------|------|
| 无文件 + 编辑 | 虚线框上传区 + 点击/拖拽上传 |
| 已有文件 + 编辑 | 文件列表（名称、大小、时间、删除按钮）+ 继续上传按钮 |
| 预览模式 | 图片/PDF 内嵌预览；其他文件显示名称 + 下载链接 |

Props:
- `value` — 文件值 JSON 数组
- `isList` — 是否允许多文件
- `attrOption` — 属性 option（含文件存储配置）

Events:
- `input` — 值变更
- `upload` / `delete` — 单文件操作

### 6.4 CI 实例表单

**CreateInstanceForm.vue / createInstanceFormByGroup.vue:**

对于 `is_file=true` 的属性字段，使用 `CiFileField` 替代普通输入框。

上传流程：
1. 用户在 `CiFileField` 内选择文件
2. 组件调用 `POST /api/v0.1/ci/files` 上传到服务器
3. 服务器返回文件元数据列表
4. 组件将元数据写入表单 v-model
5. 提交表单时，文件值（JSON 字符串）随 CI 实例一起保存

### 6.5 CI 详情页

**ciDetailAttrContent.vue:**

- 对 `is_file=true` 属性，使用 `CiFileField`（预览模式）
- 支持点击文件直接预览（图片/PDF/Office）
- Office 文档预览：新窗口打开 Office 在线预览服务

### 6.6 CI 表格

**helper.js `getCITableColumns`:**

文件类型列显示：`{N} 个文件`（总大小），hover 展开文件列表，可直接下载。

### 6.7 批量导入

batch 导入 Excel 时，文件字段的值留空或填写已有的文件路径；导入后 CI 实例的文件属性值为空，用户通过编辑页面手动上传文件。导出 Excel 时文件列显示文件名列表。

### 6.8 国际化

新增 i18n key（zh/en）：

```
cmdb.ciType.file           # 文件 / File
cmdb.ciType.fileStorage    # 文件存储设置 / File Storage
cmdb.ciType.fileStorageBackend  # 存储方式 / Storage Backend
cmdb.ciType.allowedExtensions    # 允许的文件类型 / Allowed Extensions
cmdb.ciType.maxFileSize    # 单文件最大大小(MB) / Max File Size (MB)
cmdb.ciType.fileUpload     # 上传文件 / Upload File
cmdb.ciType.filePreview    # 预览 / Preview
cmdb.ciType.fileDownload   # 下载 / Download
cmdb.ciType.fileDelete     # 删除 / Delete
cmdb.ciType.fileCount      # {count} 个文件 / {count} file(s)
```

## 7. 改动文件清单

### 7.1 后端（cmdb-api/）

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `settings.py` | 修改 | 新增 `FILE_STORAGE_*` + `S3_*` 配置项 |
| `api/lib/cmdb/const.py` | 修改 | `ValueTypeEnum` 加 `FILE = TEXT` |
| `api/lib/cmdb/utils.py` | 修改 | `ValueTypeMap` 加文件类型映射 |
| `api/models/cmdb.py` | 修改 | `Attribute` 模型加 `is_file` 列 |
| `api/lib/cmdb/storage/__init__.py` | **新增** | 存储后端工厂函数 |
| `api/lib/cmdb/storage/base.py` | **新增** | `StorageBackend` 抽象基类 |
| `api/lib/cmdb/storage/local.py` | **新增** | `LocalStorage` 实现 |
| `api/lib/cmdb/storage/s3_storage.py` | **新增** | `S3Storage` 实现 |
| `api/lib/cmdb/ci_file.py` | **新增** | `CIFileManager` 业务逻辑 |
| `api/views/cmdb/ci_file.py` | **新增** | 文件上传/下载/删除 API |
| `api/lib/cmdb/ci.py` | 修改 | CI 删除时清理文件资源 |
| `migrations/versions/` | **新增** | Alembic 迁移文件 |

### 7.2 前端（cmdb-ui/）

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `src/modules/cmdb/utils/const.js` | 修改 | `valueTypeMap` 加 `'12'` |
| `src/modules/cmdb/utils/helper.js` | 修改 | `getPropertyIcon/Type/Style` + 文件列渲染 |
| `src/modules/cmdb/views/ci_types/ceateNewAttribute.vue` | 修改 | 新建属性支持文件类型 |
| `src/modules/cmdb/views/ci_types/attributeEditForm.vue` | 修改 | 编辑属性支持文件类型 |
| `src/modules/cmdb/views/ci_types/attributesTable.vue` | 修改 | 类型筛选 keys 加 `'12'` |
| `src/modules/cmdb/components/CiFileField.vue` | **新增** | 文件字段通用组件 |
| `src/modules/cmdb/views/ci/modules/ciDetailAttrContent.vue` | 修改 | 文件属性预览/编辑 |
| `src/modules/cmdb/views/ci/modules/CreateInstanceForm.vue` | 修改 | 创建表单集成文件上传 |
| `src/modules/cmdb/views/ci/modules/createInstanceFormByGroup.vue` | 修改 | 分组创建集成文件上传 |
| `src/modules/cmdb/api/ciFile.js` | **新增** | 文件操作 API 客户端 |
| `src/modules/cmdb/lang/zh.js` | 修改 | 中文 i18n |
| `src/modules/cmdb/lang/en.js` | 修改 | 英文 i18n |

## 8. 约束与边界

1. **单文件大小上限**：默认 50MB（可配置），最大 500MB（受限于 FastAPI/nginx 上传限制）
2. **文件扩展名默认允许列表**：`txt, pdf, png, jpg, jpeg, gif, svg, webp, bmp, xls, xlsx, doc, docx, ppt, pptx, csv, json, zip, rar, 7z, log`
3. **Office 预览**：依赖外部 Office 在线预览服务（如 Microsoft Office Online 或 OnlyOffice），本方案不实现 Office 渲染引擎
4. **孤儿文件清理**：CI 实例保存失败或取消编辑时，已上传的文件通过客户端对比清理（上传时已持久化，需显式删除）
5. **事务一致性与最终一致**：文件实际上传在事务之外完成（存储操作不可回滚），CI 实例删除时确保文件清理

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| S3 服务不可用 | 文件上传/下载失败 | 上传前检测 S3 连通性；提供本地降级开关 |
| 大量文件存储成本 | 磁盘/S3 成本上升 | 配置属性级文件大小和数量限制 |
| Office 预览依赖外部服务 | Office 文件无法预览 | 降级为直接下载，不影响功能核心 |
| boto3 稳定 API 变动 | S3Storage 行为不合预期 | 锁定 boto3 API 调用到稳定版本 |
| 文件孤儿 | 磁盘/S3 空间浪费 | 提供 `CleanupFilesTask` Celery 定时任务对比数据库与存储 |
