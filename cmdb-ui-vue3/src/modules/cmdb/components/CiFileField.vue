<script setup lang="ts">
import { computed, ref, watch, type Component } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import {
  DeleteOutlined,
  DownloadOutlined,
  EyeOutlined,
  FileExcelOutlined,
  FileImageOutlined,
  FileOutlined,
  FilePdfOutlined,
  FilePptOutlined,
  FileTextOutlined,
  FileWordOutlined,
  FileZipOutlined,
  InboxOutlined,
  PaperClipOutlined,
} from '@ant-design/icons-vue'
import { uploadCiFile, deleteCiFiles } from '@/modules/cmdb/api/ciFile'
import { updateCI } from '@/modules/cmdb/api/ci'
import { getAccessToken } from '@/utils/request'
import KkFilePreview from '@/modules/cmdb/components/KkFilePreview.vue'

/**
 * CI file attachment field. In preview mode it renders a trigger that opens a
 * file management dialog; in edit mode the same dialog is used but uploads are
 * only persisted via the form submit (or immediately when a ciId is provided).
 */

interface CiFile {
  original_name?: string
  stored_path?: string
  storage_backend?: string
  mime_type?: string
  size?: number
}

const props = withDefaults(
  defineProps<{
    value?: Array<CiFile> | string | null
    isList?: boolean
    isEdit?: boolean
    attrId?: number | string | null
    // CI the field belongs to. When provided (and in preview mode), uploads and
    // deletes are persisted to the CI immediately so they survive a refresh.
    ciId?: number | string | null
    // CI attribute name to save the file list into (used with ciId).
    attrName?: string
  }>(),
  {
    value: () => [],
    isList: false,
    isEdit: false,
    attrId: null,
    ciId: null,
    attrName: '',
  }
)

const emit = defineEmits<{
  (e: 'input', value: string): void
  (e: 'change', value: string): void
}>()

const { t } = useI18n()

const fileList = ref<CiFile[]>([])
const uploading = ref(false)
const uploadingFileName = ref('')
const previewVisible = ref(false)
const previewFile = ref<CiFile | null>(null)
const dialogVisible = ref(false)
const deletePending = ref(false)

watch(
  () => props.value,
  (val) => {
    if (typeof val === 'string') {
      try {
        fileList.value = JSON.parse(val)
      } catch {
        fileList.value = []
      }
    } else if (Array.isArray(val)) {
      fileList.value = val
    } else {
      fileList.value = []
    }
  },
  { immediate: true }
)

const previewFileUrl = computed(() => {
  if (!previewFile.value) return ''
  // kkFileView fetches the file itself, so hand it the absolute download URL
  // (download=1). Also append &fullfilename= so kkFileView can detect the type.
  const relativeUrl = getFileUrl(
    previewFile.value.stored_path,
    previewFile.value.storage_backend,
    true
  )
  // kkFileView requires an absolute URL to fetch the file.
  const baseUrl = import.meta.env.VITE_FILE_API_BASE_URL || window.location.origin
  const fullFilename = encodeURIComponent(previewFile.value.original_name || '')
  return `${baseUrl}${relativeUrl}&fullfilename=${fullFilename}`
})

const maxFileSizeDisplay = '100 MB'

function getFileUrl(storedPath?: string, storageBackend?: string, download = false): string {
  let url = `/api/v0.1/ci/files?path=${encodeURIComponent(storedPath || '')}`
  if (storageBackend) {
    url += `&storage_backend=${encodeURIComponent(storageBackend)}`
  }
  if (download) {
    url += '&download=1'
  }
  // Include the auth token so direct browser requests (e.g. <a>/<img> tags)
  // are authenticated even when the session cookie is unavailable.
  const token = getAccessToken()
  if (token) {
    url += `&_token=${encodeURIComponent(token)}`
  }
  return url
}

function isImage(mimeType?: string): boolean {
  return !!mimeType && mimeType.startsWith('image/')
}

function getStorageLabel(storageBackend?: string): string {
  if (storageBackend === 's3') return t('cmdb.ciType.fileStorageS3')
  if (storageBackend === 'local') return t('cmdb.ciType.fileStorageLocal')
  // Files uploaded before the storage_backend field existed carry no value.
  return '--'
}

function formatSize(bytes?: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return size.toFixed(i === 0 ? 0 : 1) + ' ' + units[i]
}

function emitChange() {
  const value = JSON.stringify(fileList.value)
  emit('input', value)
  emit('change', value)
}

function persistFileList() {
  // Preview mode has no form to save the value — persist immediately so uploads
  // survive a refresh. Edit mode saves via the form on submit.
  if (props.isEdit || !props.ciId || !props.attrName) return
  updateCI(props.ciId, { [props.attrName]: JSON.stringify(fileList.value) }, false).catch(() => {
    message.error(t('cmdb.ciType.fileSaveFailed'))
  })
}

function handleBeforeUpload(): boolean {
  // Validation is done server-side, just allow through.
  return true
}

async function handleCustomRequest({ file, onSuccess, onError }: {
  file: File
  onSuccess?: (body: any, file: File) => void
  onError?: (event: Error) => void
}) {
  uploading.value = true
  uploadingFileName.value = file.name
  try {
    const formData = new FormData()
    formData.append('files', file)
    const res = await uploadCiFile(formData, props.attrId as string | number | undefined)
    const newFiles = res.files || []
    // Always append: accumulating files across multiple uploads.
    fileList.value.push(...newFiles)
    emitChange()
    persistFileList()
    if (onSuccess) onSuccess(res, file)
  } catch (e) {
    message.error((e as Error).message || t('cmdb.ciType.fileUploadFailed'))
    if (onError) onError(e as Error)
  } finally {
    uploading.value = false
    uploadingFileName.value = ''
  }
}

function handlePreviewFile(file: CiFile) {
  previewFile.value = file
  previewVisible.value = true
}

function handleDeleteFile(idx: number) {
  const file = fileList.value[idx]
  if (!file) return

  Modal.confirm({
    title: t('cmdb.ciType.fileDeleteConfirm'),
    content: `"${file.original_name}" — ${t('cmdb.ciType.fileDeleteConfirmMsg')}`,
    okText: t('cmdb.ciType.fileDeleteOk'),
    okType: 'danger',
    cancelText: t('cancel'),
    onOk: async () => {
      deletePending.value = true
      try {
        await deleteCiFiles([{ path: file.stored_path, storage_backend: file.storage_backend }])
        fileList.value.splice(idx, 1)
        emitChange()
        persistFileList()
        message.success(t('cmdb.ciType.fileDelete') + ' ' + file.original_name)
      } catch (e) {
        message.error((e as Error).message || t('cmdb.ciType.fileDeleteFailed'))
      } finally {
        deletePending.value = false
      }
    },
  })
}

function getFileIcon(filename?: string): Component {
  if (!filename) return FileOutlined
  const ext = filename.split('.').pop()?.toLowerCase()
  const iconMap: Record<string, Component> = {
    pdf: FilePdfOutlined,
    doc: FileWordOutlined,
    docx: FileWordOutlined,
    xls: FileExcelOutlined,
    xlsx: FileExcelOutlined,
    ppt: FilePptOutlined,
    pptx: FilePptOutlined,
    txt: FileTextOutlined,
    zip: FileZipOutlined,
    rar: FileZipOutlined,
    '7z': FileZipOutlined,
    csv: FileExcelOutlined,
    json: FileTextOutlined,
    jpg: FileImageOutlined,
    jpeg: FileImageOutlined,
    png: FileImageOutlined,
    gif: FileImageOutlined,
    webp: FileImageOutlined,
    bmp: FileImageOutlined,
  }
  return (ext && iconMap[ext]) || FileOutlined
}

function openFileDialog() {
  dialogVisible.value = true
}
</script>

<template>
  <div class="ci-file-field">
    <template v-if="!isEdit">
      <div class="ci-file-field-trigger" @click="openFileDialog">
        <PaperClipOutlined style="margin-right: 4px" />
        <template v-if="fileList.length">
          {{ t('cmdb.ciType.fileCount', { count: fileList.length }) }}
        </template>
        <template v-else>
          {{ t('cmdb.ciType.fileManageUpload') }}
        </template>
      </div>
    </template>

    <template v-else>
      <div class="ci-file-field-trigger ci-file-field-trigger-editable" @click="openFileDialog">
        <PaperClipOutlined style="margin-right: 4px" />
        <template v-if="fileList.length">
          {{ t('cmdb.ciType.fileCount', { count: fileList.length }) }}
        </template>
        <template v-else>
          {{ t('cmdb.ciType.fileManageUpload') }}
        </template>
      </div>
    </template>

    <!-- kkFileView preview modal -->
    <a-modal
      :open="previewVisible"
      :title="previewFile ? previewFile.original_name : ''"
      :footer="null"
      width="90%"
      :body-style="{ padding: 0, height: '80vh' }"
      :destroy-on-close="true"
      @cancel="previewVisible = false"
    >
      <KkFilePreview
        v-if="previewVisible"
        :file-url="previewFileUrl"
        :file-name="previewFile ? previewFile.original_name : ''"
      />
    </a-modal>

    <!-- File management dialog -->
    <a-modal
      :open="dialogVisible"
      :title="t('cmdb.ciType.fileManage')"
      :footer="null"
      width="720px"
      :body-style="{ padding: '16px 24px', maxHeight: '70vh', overflowY: 'auto' }"
      :destroy-on-close="false"
      @cancel="dialogVisible = false"
    >
      <a-upload-dragger
        :multiple="true"
        :show-upload-list="false"
        :before-upload="handleBeforeUpload"
        :custom-request="handleCustomRequest"
        class="file-dialog-uploader"
      >
        <p class="upload-drag-icon">
          <InboxOutlined style="font-size: 36px; color: #2f54eb" />
        </p>
        <p class="upload-drag-text">{{ t('cmdb.ciType.fileDragTip') }}</p>
        <p class="upload-drag-hint">
          {{ t('cmdb.ciType.fileDragHint') }} {{ maxFileSizeDisplay }}
        </p>
      </a-upload-dragger>

      <div v-if="uploading" class="file-dialog-uploading">
        <a-spin size="small" />
        <span style="margin-left: 8px">{{ t('cmdb.ciType.fileUploading') }} {{ uploadingFileName }}</span>
      </div>

      <div v-if="fileList.length" class="file-dialog-list">
        <div v-for="(file, idx) in fileList" :key="idx" class="file-dialog-item">
          <div class="file-dialog-item-icon">
            <img
              v-if="isImage(file.mime_type)"
              :src="getFileUrl(file.stored_path, file.storage_backend)"
              class="file-dialog-thumb"
            />
            <component :is="getFileIcon(file.original_name)" v-else class="file-dialog-icon" />
          </div>
          <div class="file-dialog-item-info">
            <div class="file-dialog-item-name-row">
              <span class="file-dialog-item-name" :title="file.original_name">
                {{ file.original_name }}
              </span>
              <span
                class="file-dialog-item-storage"
                :class="'storage-' + (file.storage_backend || 'unknown')"
              >
                {{ getStorageLabel(file.storage_backend) }}
              </span>
            </div>
            <span class="file-dialog-item-meta">
              {{ formatSize(file.size) }} · {{ file.mime_type || '--' }}
            </span>
          </div>
          <div class="file-dialog-item-actions">
            <a class="file-action-btn" @click="handlePreviewFile(file)">
              <EyeOutlined />
              {{ t('cmdb.ciType.filePreview') }}
            </a>
            <a
              :href="getFileUrl(file.stored_path, file.storage_backend, true)"
              :download="file.original_name"
              class="file-action-btn"
            >
              <DownloadOutlined />
              {{ t('cmdb.ciType.fileDownload') }}
            </a>
            <a class="file-action-btn file-action-delete" @click="handleDeleteFile(idx)">
              <DeleteOutlined />
              {{ t('cmdb.ciType.fileDelete') }}
            </a>
          </div>
        </div>
      </div>

      <div v-if="!fileList.length && !uploading" class="file-dialog-empty">
        <a-empty :description="t('cmdb.ciType.fileNoFiles')" />
      </div>

      <div class="file-dialog-footer">
        <span v-if="fileList.length" class="file-dialog-count">
          {{ t('cmdb.ciType.fileTotalCount', { count: fileList.length }) }}
        </span>
        <a-button @click="dialogVisible = false">{{ t('cancel') }}</a-button>
      </div>
    </a-modal>
  </div>
</template>

<style lang="less" scoped>
.ci-file-field {
  &-trigger {
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
}

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

.file-dialog-item-name-row {
  display: flex;
  align-items: center;
  min-width: 0;
}

.file-dialog-item-name {
  font-weight: 500;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-dialog-item-storage {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 6px;
  margin-left: 8px;
  border-radius: 3px;
  font-size: 11px;
  line-height: 18px;

  &.storage-local {
    color: #2f54eb;
    background: rgba(47, 84, 235, 0.08);
    border: 1px solid rgba(47, 84, 235, 0.2);
  }

  &.storage-s3 {
    color: #d46b08;
    background: rgba(250, 140, 22, 0.1);
    border: 1px solid rgba(250, 140, 22, 0.25);
  }

  &.storage-unknown {
    color: rgba(0, 0, 0, 0.45);
    background: #fafafa;
    border: 1px solid #f0f0f0;
  }
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
</style>
