# 文件管理弹窗优化设计

> 日期：2026-08-03 | 状态：已确认

## 背景

当前 CMDB 文件属性字段（`CiFileField.vue`）在预览和编辑模式下均以内联方式展示文件列表和操作按钮。当文件数量较多时，列表冗长、视觉杂乱、操作不便。

## 目标

将文件管理统一为**单一弹窗**模式，优化交互体验，使界面更简洁、操作更集中、风格更现代化。

## 触发方式

预览模式和编辑模式统一：使用**触发按钮**打开文件管理弹窗。

### 触发按钮状态

| 条件 | 显示 |
|------|------|
| 无文件 | `📎 上传文件` — 点击打开弹窗 |
| 有文件 | `📎 N 个文件` — 显示文件数量徽章，点击打开弹窗 |

## 弹窗布局：列表式

```
┌──────────────────────────────────────────────────────────────┐
│  文件管理                                          [✕]       │
├──────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────┐  │
│  │        📂  将文件拖到此处，或 点击选择文件              │  │
│  │            支持任意类型，单个文件不超过 100 MB           │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ 🖼│ image.png           │ 500 KB │ image/png         │    │
│  │  │ 2026-08-03 14:30    │        │ 👁 预览 ⬇ 下载 🗑 删除 │
│  ├──────────────────────────────────────────────────────┤    │
│  │ 📄│ report.pdf          │ 2.5 MB │ application/pdf   │    │
│  │  │ 2026-08-02 10:15    │        │ 👁 预览 ⬇ 下载 🗑 删除 │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│                                       共 N 个文件            │
│                                                [关闭]       │
└──────────────────────────────────────────────────────────────┘
```

## 文件列表行结构

每行两行结构：

| 区域 | 内容 | 说明 |
|------|------|------|
| 文件图标（左） | 图片缩略图（40×40）或类型图标 | 图片显示缩略图，其他按扩展名显示彩色图标 |
| 文件名 | 粗体，超长省略 | `text-overflow: ellipsis` |
| 文件大小 | 右对齐，灰色 | `formatSize()` 格式化 |
| MIME 类型 | 灰色标签/文字 | 截取显示 |
| 操作按钮 | 预览 / 下载 / 删除 | 图标 + 文字按钮，在行右侧 |

注：当前后端返回字段为 `{original_name, stored_path, size, mime_type, storage_backend}`，不包含上传时间。行设计为单行布局（非两行），操作按钮在右侧。

### 操作行为

| 操作 | 行为 |
|------|------|
| 👁 预览 | 图片：新窗口打开原始文件；其他类型：打开 kkFileView 弹窗（已有 `KkFilePreview` 组件） |
| ⬇ 下载 | `<a>` 标签带 `download` 属性，直接下载 |
| 🗑 删除 | 弹出确认对话框 → 调用 `DELETE /api/v0.1/ci/files` → 成功后从列表移除 |

## 上传区域

- 使用 Ant Design `<a-upload-dragger>` 组件
- 支持拖拽 + 点击选择文件
- 支持多文件同时上传
- 上传中在列表顶部显示带 spinner 的进度行
- 上传失败显示红色错误行，带"重试"和"移除"操作
- 文件大小/类型限制从后端文件存储配置读取

## 状态处理

| 状态 | 显示 |
|------|------|
| 空列表 | 拖拽区域居中放大显示，下方无列表，提示"暂无文件，请上传" |
| 加载中 | 弹窗打开时列表区域显示 skeleton loading |
| 上传中 | 拖拽区域下方出现带 spinner 的临时行 |
| 上传失败 | 红色提示行，带"重试"和"移除"操作 |
| 删除确认 | `Modal.confirm` — "确定要删除 'report.pdf' 吗？删除后不可恢复。" |

## 数据流

```
CiFileField (fileList state)
    │
    ├── handleUpload   → POST /api/v0.1/ci/files    → 追加到 fileList → emit('input')
    ├── handleDelete   → DELETE /api/v0.1/ci/files   → 从 fileList 移除 → emit('input')
    ├── handlePreview  → 打开 kkFileView modal（已有逻辑）
    └── handleDownload → <a> 标签下载（已有逻辑）
```

关键变化：
- **删除操作**：调用后端 `deleteCiFiles` API（目前只做了本地 splice，未调用后端 — 已修复）
- **上传操作**：保持现有 `uploadCiFile` 逻辑，结果即时反映在弹窗列表中
- **值同步**：弹窗关闭时通过 `emit('input')` 同步回父组件

## 组件结构

```
CiFileField.vue
├── 触发按钮 (trigger button — 预览/编辑模式统一)
├── <a-modal> 文件管理弹窗（新增）
│   ├── <a-upload-dragger> 上传区域
│   ├── 文件列表（自定义列表行）
│   └── 底部统计 + 关闭按钮
└── <a-modal> kkFileView 预览弹窗（已存在，保持不变）
```

## 交互细节

- 行 hover 时背景变色（浅灰），操作按钮高亮
- 删除按钮 hover 变红色
- 上传区域 border 使用主题色 `#2f54eb`
- 弹窗宽度 720px，高度自适应（最大 80vh 内容可滚动）
- `destroyOnClose: false` 保持列表状态，关闭后不丢失上传结果

## i18n 新增键值

```js
// zh.js
fileManage: '文件管理',
fileManageTrigger: '个文件',
fileManageUpload: '上传文件',
fileDragTip: '将文件拖到此处，或 点击选择文件',
fileDragHint: '支持任意类型，单个文件不超过',
fileDeleteConfirm: '确认删除',
fileDeleteConfirmTitle: '确定要删除 "{name}" 吗？',
fileDeleteConfirmMsg: '删除后不可恢复。',
fileNoFiles: '暂无文件，请上传',
fileRetry: '重试',
fileRemove: '移除',
fileUploading: '上传中...',
fileTotalCount: '共 {count} 个文件',
```

## 改动范围

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `cmdb-ui/src/modules/cmdb/components/CiFileField.vue` | 主要改造 | 触发按钮 + 管理弹窗 + 列表行 + 删除调用后端 API |
| `cmdb-ui/src/modules/cmdb/components/KkFilePreview.vue` | 不变 | 已有 kkFileView 预览组件 |
| `cmdb-ui/src/modules/cmdb/api/ciFile.js` | 不变 | `uploadCiFile` 和 `deleteCiFiles` 已存在 |
| `cmdb-ui/src/modules/cmdb/lang/zh.js` | 新增 | i18n 键值 |
| `cmdb-ui/src/modules/cmdb/lang/en.js` | 新增 | i18n 键值 |

## 技术约束

- Vue 2.6 Options API（不引入 Composition API）
- Ant Design Vue 1.6.x 组件库
- Less 样式，scoped
- 保持与现有代码风格一致
- 现有 `getFileUrl`、`formatSize`、`isImage` 等辅助方法保留复用
