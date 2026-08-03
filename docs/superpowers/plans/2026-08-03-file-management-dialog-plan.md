# 文件管理弹窗优化 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 将 CiFileField.vue 中的文件列表展示从内联模式重构为弹窗管理模式，统一预览和编辑两种状态，提升交互体验。

**架构：** 在 CiFileField 组件中新增一个 a-modal 管理弹窗，内部包含 a-upload-dragger 上传区域和自定义文件列表（列表式行，含预览/下载/删除操作），替代原有的内联文件展示。触发按钮在预览和编辑模式下统一显示。删除操作接入后端 deleteCiFiles API。

**技术栈：** Vue 2.6 Options API / Ant Design Vue 1.6.x / Less scoped

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `cmdb-ui/src/modules/cmdb/components/CiFileField.vue` | 主要改造：触发按钮、管理弹窗、文件列表行、上传和删除逻辑 |
| `cmdb-ui/src/modules/cmdb/components/KkFilePreview.vue` | 不变 — 已有 kkFileView 预览组件 |
| `cmdb-ui/src/modules/cmdb/api/ciFile.js` | 不变 — `uploadCiFile` 和 `deleteCiFiles` 已存在 |
| `cmdb-ui/src/modules/cmdb/lang/zh.js` | 新增 i18n 键值 |
| `cmdb-ui/src/modules/cmdb/lang/en.js` | 新增 i18n 键值 |

---

### Task 1: 添加 i18n 键值

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/lang/zh.js`
- Modify: `cmdb-ui/src/modules/cmdb/lang/en.js`

- [ ] **Step 1: 在 zh.js 中添加中文键值**

在 `file` 区块（约第 233 行 `file: '文件'` 附近）新增以下内容：

```js
// 替换现有的 fileCount 行并新增以下键值：
fileCount: '{count} 个文件',
fileManage: '文件管理',
fileManageUpload: '上传文件',
fileDragTip: '将文件拖到此处，或 点击选择文件',
fileDragHint: '支持任意类型，单个文件不超过',
fileDeleteConfirm: '确认删除',
fileDeleteConfirmTitle: '确定要删除 "{name}" 吗？',
fileDeleteConfirmMsg: '删除后不可恢复。',
fileDeleteOk: '确认删除',
fileRetry: '重试',
fileRemove: '移除',
fileUploading: '上传中...',
fileTotalCount: '共 {count} 个文件',
```

具体操作：找到 `zh.js` 中 `file` 相关键值位置（行 233-241），在 `fileCount` 或 `fileDownload` 之后插入以上新增键值。

- [ ] **Step 2: 在 en.js 中添加英文键值**

在对应位置新增：

```js
fileCount: '{count} file(s)',
fileManage: 'File Management',
fileManageUpload: 'Upload File',
fileDragTip: 'Drop files here, or click to select',
fileDragHint: 'Any file type, max {size} per file',
fileDeleteConfirm: 'Confirm Delete',
fileDeleteConfirmTitle: 'Are you sure you want to delete "{name}"?',
fileDeleteConfirmMsg: 'This action cannot be undone.',
fileDeleteOk: 'Delete',
fileRetry: 'Retry',
fileRemove: 'Remove',
fileUploading: 'Uploading...',
fileTotalCount: '{count} file(s) total',
```

- [ ] **Step 3: 验证 i18n 文件无语法错误**

```bash
cd cmdb-ui && node -e "
const zh = require('./src/modules/cmdb/lang/zh.js')
const en = require('./src/modules/cmdb/lang/en.js')
console.log('zh keys:', Object.keys(zh).length)
console.log('en keys:', Object.keys(en).length)
"
```

- [ ] **Step 4: 提交**

```bash
git add cmdb-ui/src/modules/cmdb/lang/zh.js cmdb-ui/src/modules/cmdb/lang/en.js
git commit -m "feat: add i18n keys for file management dialog

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: 重构 CiFileField 模板 — 触发按钮

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/components/CiFileField.vue`

- [ ] **Step 1: 将预览模式内联文件列表替换为触发按钮**

将 `<template v-if="!isEdit">` 块（第 4-49 行）中的内联文件列表部分替换为触发按钮。

**删除** 第 5-36 行的预览文件列表代码（从 `<div v-if="!fileList.length"` 到 `</div>` 整个 `ci-file-field-preview` 块）。

**替换为** 触发按钮：

```html
<template v-if="!isEdit">
  <div class="ci-file-field-trigger" @click="openFileDialog">
    <a-icon type="paper-clip" style="margin-right: 4px;" />
    <template v-if="fileList.length">
      {{ $t('cmdb.ciType.fileCount', { count: fileList.length }) }}
    </template>
    <template v-else>
      {{ $t('cmdb.ciType.fileManageUpload') }}
    </template>
  </div>
</template>
```

- [ ] **Step 2: 将编辑模式内联文件列表替换为触发按钮**

将 `<template v-else>` 块（第 52-77 行）中的内联文件列表和上传按钮替换为同样的触发按钮。

**删除** 第 53-77 行（从 `<div v-if="fileList.length"` 的 `ci-file-field-list` 到整个 `</a-upload>` 结束）。

**替换为**：

```html
<template v-else>
  <div class="ci-file-field-trigger ci-file-field-trigger-editable" @click="openFileDialog">
    <a-icon type="paper-clip" style="margin-right: 4px;" />
    <template v-if="fileList.length">
      {{ $t('cmdb.ciType.fileCount', { count: fileList.length }) }}
    </template>
    <template v-else>
      {{ $t('cmdb.ciType.fileManageUpload') }}
    </template>
  </div>
</template>
```

- [ ] **Step 3: 保留 kkFileView 预览弹窗**

保留第 38-48 行的 `<a-modal>`（kkFileView 预览弹窗），保持不变。

- [ ] **Step 4: 提交**

```bash
git add cmdb-ui/src/modules/cmdb/components/CiFileField.vue
git commit -m "feat: replace inline file list with trigger button in CiFileField

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: 添加文件管理弹窗 — 模板

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/components/CiFileField.vue`

- [ ] **Step 1: 在 kkFileView 预览弹窗之后添加文件管理弹窗**

在第 48 行 `</a-modal>`（kkFileView 预览弹窗）之后，`</template>`（`v-if="!isEdit"` 的结束标签）之前，新增：

```html
<!-- File management dialog -->
<a-modal
  :visible="dialogVisible"
  :title="$t('cmdb.ciType.fileManage')"
  :footer="null"
  width="720px"
  :bodyStyle="{ padding: '16px 24px', maxHeight: '70vh', overflowY: 'auto' }"
  :destroyOnClose="false"
  @cancel="dialogVisible = false"
>
  <!-- Upload area -->
  <a-upload-dragger
    :multiple="true"
    :showUploadList="false"
    :beforeUpload="handleBeforeUpload"
    :customRequest="handleCustomRequest"
    class="file-dialog-uploader"
  >
    <p class="upload-drag-icon">
      <a-icon type="inbox" style="font-size: 36px; color: #2f54eb;" />
    </p>
    <p class="upload-drag-text">{{ $t('cmdb.ciType.fileDragTip') }}</p>
    <p class="upload-drag-hint">
      {{ $t('cmdb.ciType.fileDragHint') }} {{ maxFileSizeDisplay }}
    </p>
  </a-upload-dragger>

  <!-- Uploading indicator -->
  <div v-if="uploading" class="file-dialog-uploading">
    <a-spin size="small" />
    <span style="margin-left: 8px;">{{ $t('cmdb.ciType.fileUploading') }} {{ uploadingFileName }}</span>
  </div>

  <!-- File list -->
  <div v-if="fileList.length" class="file-dialog-list">
    <div
      v-for="(file, idx) in fileList"
      :key="idx"
      class="file-dialog-item"
    >
      <!-- File icon -->
      <div class="file-dialog-item-icon">
        <img
          v-if="isImage(file.mime_type)"
          :src="getFileUrl(file.stored_path, file.storage_backend)"
          class="file-dialog-thumb"
        />
        <a-icon v-else :type="getFileIcon(file.original_name)" class="file-dialog-icon" />
      </div>
      <!-- File info -->
      <div class="file-dialog-item-info">
        <span class="file-dialog-item-name" :title="file.original_name">
          {{ file.original_name }}
        </span>
        <span class="file-dialog-item-meta">
          {{ formatSize(file.size) }} · {{ file.mime_type || '--' }}
        </span>
      </div>
      <!-- Actions -->
      <div class="file-dialog-item-actions">
        <a @click="handlePreviewFile(file)" class="file-action-btn">
          <a-icon type="eye" />
          {{ $t('cmdb.ciType.filePreview') }}
        </a>
        <a
          :href="getFileUrl(file.stored_path, file.storage_backend, true)"
          :download="file.original_name"
          class="file-action-btn"
        >
          <a-icon type="download" />
          {{ $t('cmdb.ciType.fileDownload') }}
        </a>
        <a @click="handleDeleteFile(idx)" class="file-action-btn file-action-delete">
          <a-icon type="delete" />
          {{ $t('cmdb.ciType.fileDelete') }}
        </a>
      </div>
    </div>
  </div>

  <!-- Empty state -->
  <div v-if="!fileList.length && !uploading" class="file-dialog-empty">
    <a-empty :description="$t('cmdb.ciType.fileNoFiles')" />
  </div>

  <!-- Footer stats -->
  <div class="file-dialog-footer">
    <span v-if="fileList.length" class="file-dialog-count">
      {{ $t('cmdb.ciType.fileTotalCount', { count: fileList.length }) }}
    </span>
    <a-button @click="dialogVisible = false">{{ $t('close') }}</a-button>
  </div>
</a-modal>
```

- [ ] **Step 2: 提交**

```bash
git add cmdb-ui/src/modules/cmdb/components/CiFileField.vue
git commit -m "feat: add file management dialog template to CiFileField

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: 添加文件管理弹窗 — 数据和方法

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/components/CiFileField.vue`

- [ ] **Step 1: 更新 data() 添加新状态**

找到 `data()` 方法（第 113-119 行），在返回对象中添加新字段：

```js
data() {
  return {
    fileList: [],
    uploading: false,
    uploadingFileName: '',
    previewVisible: false,
    previewFile: null,
    dialogVisible: false,
    deletePending: false
  }
}
```

新增字段：`dialogVisible`（管理弹窗开关）、`deletePending`（删除中状态）、`uploadingFileName`（上传中文件名）。

- [ ] **Step 2: 添加 maxFileSizeDisplay 计算属性**

在 `computed` 块中添加（在 `previewFileUrl` 之后）：

```js
computed: {
  // ... existing previewFileUrl computed ...

  maxFileSizeDisplay() {
    // Default max 50 MB as fallback; the backend enforces the real limit.
    // In the future this could be fetched from the file storage config API.
    return '100 MB'
  }
}
```

- [ ] **Step 3: 添加 openFileDialog 方法**

在 `methods` 块中添加：

```js
openFileDialog() {
  this.dialogVisible = true
}
```

- [ ] **Step 4: 更新 handleCustomRequest 显示上传状态**

修改现有的 `handleCustomRequest` 方法，添加上传文件名追踪：

```js
async handleCustomRequest({ file, onSuccess, onError }) {
  this.uploading = true
  this.uploadingFileName = file.name
  try {
    const formData = new FormData()
    formData.append('files', file)
    const res = await uploadCiFile(formData, this.attrId)
    const newFiles = res.files || []
    this.fileList.push(...newFiles)
    this.emitChange()
    if (onSuccess) onSuccess(res, file)
  } catch (e) {
    this.$message.error(e.message || this.$t('cmdb.ciType.fileUploadFailed'))
    if (onError) onError(e)
  } finally {
    this.uploading = false
    this.uploadingFileName = ''
  }
}
```

- [ ] **Step 5: 添加 getFileIcon 方法**

在 `methods` 块中添加辅助方法，根据文件扩展名返回合适的图标：

```js
getFileIcon(filename) {
  if (!filename) return 'file'
  const ext = filename.split('.').pop().toLowerCase()
  const iconMap = {
    pdf: 'file-pdf',
    doc: 'file-word', docx: 'file-word',
    xls: 'file-excel', xlsx: 'file-excel',
    ppt: 'file-ppt', pptx: 'file-ppt',
    txt: 'file-text',
    zip: 'file-zip', rar: 'file-zip', '7z': 'file-zip',
    csv: 'file-excel',
    json: 'file-text',
    jpg: 'file-image', jpeg: 'file-image', png: 'file-image',
    gif: 'file-image', webp: 'file-image', bmp: 'file-image'
  }
  return iconMap[ext] || 'file'
}
```

- [ ] **Step 6: 提交**

```bash
git add cmdb-ui/src/modules/cmdb/components/CiFileField.vue
git commit -m "feat: add data, computed, and helper methods for file dialog

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: 接入后端删除 API

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/components/CiFileField.vue`

- [ ] **Step 1: 重写 handleDeleteFile 方法，接入后端 API**

替换现有的 `handleDeleteFile` 方法（第 221-223 行）：

```js
handleDeleteFile(idx) {
  const file = this.fileList[idx]
  if (!file) return

  const title = this.$t('cmdb.ciType.fileDeleteConfirmTitle', { name: file.original_name })
  this.$confirm({
    title: this.$t('cmdb.ciType.fileDeleteConfirm'),
    content: `"${file.original_name}" — ${this.$t('cmdb.ciType.fileDeleteConfirmMsg')}`,
    okText: this.$t('cmdb.ciType.fileDeleteOk'),
    okType: 'danger',
    cancelText: this.$t('cancel'),
    onOk: async () => {
      this.deletePending = true
      try {
        await deleteCiFiles([{ path: file.stored_path, storage_backend: file.storage_backend }])
        this.fileList.splice(idx, 1)
        this.emitChange()
        this.$message.success(this.$t('cmdb.ciType.fileDelete') + ' ' + file.original_name)
      } catch (e) {
        this.$message.error(e.message || this.$t('cmdb.ciType.fileDeleteFailed'))
      } finally {
        this.deletePending = false
      }
    }
  })
}
```

- [ ] **Step 2: 在 script 顶部导入 deleteCiFiles**

第 85 行的 import 语句修改为：

```js
import { uploadCiFile, deleteCiFiles } from '@/modules/cmdb/api/ciFile'
```

- [ ] **Step 3: 提交**

```bash
git add cmdb-ui/src/modules/cmdb/components/CiFileField.vue
git commit -m "feat: wire up backend deleteCiFiles API in file management dialog

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: 添加弹窗样式

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/components/CiFileField.vue`

- [ ] **Step 1: 在 `<style lang="less" scoped>` 块中添加新样式**

在现有样式下方（第 229-285 行的 `ci-file-field` 样式块之后）新增：

```less
// Trigger button
.ci-file-field-trigger {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  color: #2f54eb;
  font-size: 13px;
  transition: all 0.2s;

  &:hover {
    border-color: #2f54eb;
    background: rgba(47, 84, 235, 0.04);
  }

  &-editable {
    border-style: solid;
    background: #fafafa;
  }
}

// File dialog
.file-dialog-uploader {
  margin-bottom: 16px;

  .upload-drag-icon {
    margin-bottom: 4px;
  }
  .upload-drag-text {
    font-size: 14px;
    color: rgba(0, 0, 0, 0.65);
  }
  .upload-drag-hint {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    margin-top: 4px;
  }
}

.file-dialog-uploading {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 8px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  font-size: 13px;
}

.file-dialog-list {
  margin: 12px 0;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  overflow: hidden;
}

.file-dialog-item {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  transition: background 0.15s;
  border-bottom: 1px solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: #fafafa;

    .file-dialog-item-actions {
      opacity: 1;
    }
  }
}

.file-dialog-item-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;

  .file-dialog-thumb {
    width: 40px;
    height: 40px;
    object-fit: cover;
    border-radius: 4px;
    cursor: pointer;
  }

  .file-dialog-icon {
    font-size: 28px;
    color: #8c8c8c;
  }
}

.file-dialog-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.file-dialog-item-name {
  font-weight: 500;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-dialog-item-meta {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 2px;
}

.file-dialog-item-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 16px;
  opacity: 0.7;
  transition: opacity 0.15s;

  .file-action-btn {
    padding: 2px 8px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.65);
    white-space: nowrap;
    border-radius: 4px;
    transition: all 0.15s;

    &:hover {
      color: #2f54eb;
      background: rgba(47, 84, 235, 0.06);
    }

    &.file-action-delete:hover {
      color: #ff4d4f;
      background: rgba(255, 77, 79, 0.06);
    }
  }
}

.file-dialog-empty {
  padding: 40px 0;
}

.file-dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.file-dialog-count {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.45);
}
```

- [ ] **Step 2: 删除旧的预览模式样式（不再需要）**

删除以下旧样式块（第 230-285 行）中不再使用的部分：
- `.ci-file-field-preview` 及其子样式（`flex-wrap`, `gap` 等，行 234-237）
- `.ci-file-field-info` 样式（行 253-258，不再使用两行布局）
- `.ci-file-field-filename` 样式（行 260-264）
- `.ci-file-field-actions` 样式（行 277-284）

保留 `.ci-file-field-empty`（行 231-233）和 `.ci-file-field-item` / `.ci-file-field-item-editable` 基础样式（行 242-251）以备将来使用。

- [ ] **Step 3: 提交**

```bash
git add cmdb-ui/src/modules/cmdb/components/CiFileField.vue
git commit -m "feat: add dialog and trigger button styles for file management

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: 删除冗余的旧样式和验证完整性

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/components/CiFileField.vue`

- [ ] **Step 1: 清理不再使用的样式**

删除以下样式块（因为旧的预览和编辑内联布局已被弹窗替代）：
- `.ci-file-field-empty`（行 231-233）
- `.ci-file-field-preview`（行 234-237）
- `.ci-file-field-list`（行 239-241）
- `.ci-file-field-item`、`&-editable`（行 242-251）
- `.ci-file-field-info`（行 253-258）
- `.ci-file-field-filename`（行 260-264）
- `.ci-file-field-name`（行 265-271）
- `.ci-file-field-size`（行 272-276）
- `.ci-file-field-actions`（行 277-284）

保留样式块的开头 `& {` 和结尾 `}`，只删除以上具体规则。现在 `.ci-file-field` 块的旧样式全部移除，仅保留在 Task 6 中添加的新样式。

- [ ] **Step 2: 运行 lint 检查**

```bash
cd cmdb-ui && npx eslint src/modules/cmdb/components/CiFileField.vue --fix 2>&1 || true
```

- [ ] **Step 3: 完整验证 CiFileField.vue 文件**

确认组件核心功能完整：
- `props`: `value` (Array/String), `isList` (Boolean), `isEdit` (Boolean), `attrId` (Number/String)
- `data`: `fileList`, `uploading`, `uploadingFileName`, `previewVisible`, `previewFile`, `dialogVisible`, `deletePending`
- `computed`: `previewFileUrl`, `maxFileSizeDisplay`
- `methods`: `getFileUrl`, `isImage`, `formatSize`, `emitChange`, `handleBeforeUpload`, `handleCustomRequest`, `handlePreviewImage`, `handlePreviewFile`, `handleDeleteFile`, `openFileDialog`, `getFileIcon`
- `watch`: `value` (immediate) — normalizes JSON string/array to `fileList`
- 模板：触发按钮 + 预览弹窗（KkFilePreview） + 管理弹窗

- [ ] **Step 4: 提交**

```bash
git add cmdb-ui/src/modules/cmdb/components/CiFileField.vue
git commit -m "feat: remove obsolete inline-file-list styles from CiFileField

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: 启动开发服务器进行功能验证

- [ ] **Step 1: 启动前端开发服务器**

```bash
cd cmdb-ui && yarn serve
```

- [ ] **Step 2: 手动验证以下场景**

1. **预览模式 — 无文件**：触发按钮显示 "📎 上传文件"，点击打开弹窗，弹窗显示空状态（拖拽区域 + empty 提示）
2. **预览模式 — 有文件**：触发按钮显示 "📎 N 个文件"，点击打开弹窗，弹窗显示文件列表
3. **编辑模式 — 无文件**：触发按钮显示 "📎 上传文件"，点击打开弹窗
4. **编辑模式 — 有文件**：触发按钮显示 "📎 N 个文件"，点击打开弹窗
5. **上传文件**：在弹窗中拖拽/选择文件，文件出现在列表中
6. **预览文件**：点击预览 → 打开 kkFileView 弹窗
7. **下载文件**：点击下载 → 浏览器下载文件
8. **删除文件**：点击删除 → 确认对话框 → 文件从列表移除
9. **关闭弹窗**：数据通过 emit 同步到父组件

- [ ] **Step 3: 提交最终确认**

```bash
git add cmdb-ui/src/modules/cmdb/components/CiFileField.vue
git commit -m "feat: complete file management dialog redesign in CiFileField

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
