<template>
  <div class="ci-file-field">
    <!-- Preview mode: trigger button -->
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

    <!-- Edit mode: trigger button -->
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

    <!-- kkFileView preview modal (shared) -->
    <a-modal
      :visible="previewVisible"
      :title="previewFile ? previewFile.original_name : ''"
      :footer="null"
      width="90%"
      :bodyStyle="{ padding: 0, height: '80vh' }"
      :destroyOnClose="true"
      @cancel="previewVisible = false"
    >
      <KkFilePreview
        v-if="previewVisible"
        :fileUrl="previewFileUrl"
        :fileName="previewFile ? previewFile.original_name : ''"
      />
    </a-modal>

    <!-- File management dialog (shared by both modes) -->
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
        <a-button @click="dialogVisible = false">{{ $t('cancel') }}</a-button>
      </div>
    </a-modal>
  </div>
</template>

<script>
import Vue from 'vue'
import { ACCESS_TOKEN } from '@/store/global/mutation-types'
import { uploadCiFile, deleteCiFiles } from '@/modules/cmdb/api/ciFile'
import { updateCI } from '@/modules/cmdb/api/ci'
import KkFilePreview from '@/modules/cmdb/components/KkFilePreview'

export default {
  name: 'CiFileField',
  components: {
    KkFilePreview
  },
  props: {
    value: {
      // Form bindings (v-decorator/v-model) may pass either a parsed array
      // or a JSON string; the watcher normalizes both.
      type: [Array, String],
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
    },
    ciId: {
      // CI the field belongs to. When provided (and in preview mode),
      // uploads/deletes are persisted to the CI immediately so they survive
      // a page refresh. Edit-mode contexts save via the form on submit.
      type: [Number, String],
      default: null
    },
    attrName: {
      // CI attribute name to save the file list into (used with ciId).
      type: String,
      default: ''
    }
  },
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
  computed: {
    previewFileUrl() {
      if (!this.previewFile) return ''
      // kkFileView fetches the file itself, so hand it the absolute *download*
      // URL (download=1) — the backend serves the raw bytes with an attachment
      // disposition. Also append &fullfilename= so kkFileView can detect the
      // file type: the stored path is percent-encoded and carries no usable
      // extension.
      const relativeUrl = this.getFileUrl(this.previewFile.stored_path, this.previewFile.storage_backend, true)
      // kkFileView requires an absolute URL to fetch the file. Use
      // VUE_APP_FILE_API_BASE_URL so the address is reachable from the
      // kkFileView server (e.g. inside a Docker container, localhost does
      // not resolve to the host machine).
      const baseUrl = process.env.VUE_APP_FILE_API_BASE_URL || window.location.origin
      const fullFilename = encodeURIComponent(this.previewFile.original_name || '')
      return `${baseUrl}${relativeUrl}&fullfilename=${fullFilename}`
    },
    maxFileSizeDisplay() {
      // Default max 100 MB; the backend enforces the real limit.
      // In the future this could be fetched from the file storage config API.
      return '100 MB'
    }
  },
  methods: {
    getFileUrl(storedPath, storageBackend, download = false) {
      let url = `/api/v0.1/ci/files?path=${encodeURIComponent(storedPath)}`
      if (storageBackend) {
        url += `&storage_backend=${encodeURIComponent(storageBackend)}`
      }
      if (download) {
        url += '&download=1'
      }
      // Include the auth token so that direct browser requests (e.g. <a>/<img>
      // tags) are authenticated even when the session cookie is unavailable.
      const token = Vue.ls.get(ACCESS_TOKEN)
      if (token) {
        url += `&_token=${encodeURIComponent(token)}`
      }
      return url
    },
    isImage(mimeType) {
      return mimeType && mimeType.startsWith('image/')
    },
    getStorageLabel(storageBackend) {
      if (storageBackend === 's3') return this.$t('cmdb.ciType.fileStorageS3')
      if (storageBackend === 'local') return this.$t('cmdb.ciType.fileStorageLocal')
      // Files uploaded before the storage_backend field existed carry no value.
      return '--'
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
      const value = JSON.stringify(this.fileList)
      this.$emit('input', value)
      this.$emit('change', value)
    },
    persistFileList() {
      // Preview mode has no form to save the value — persist immediately so
      // uploads survive a refresh. Edit mode saves via the form on submit.
      if (this.isEdit || !this.ciId || !this.attrName) return
      updateCI(this.ciId, { [this.attrName]: JSON.stringify(this.fileList) }, false)
        .catch(() => {
          this.$message.error(this.$t('cmdb.ciType.fileSaveFailed'))
        })
    },
    handleBeforeUpload(file) {
      // validation is done server-side, just allow through
      return true
    },
    async handleCustomRequest({ file, onSuccess, onError }) {
      this.uploading = true
      this.uploadingFileName = file.name
      try {
        const formData = new FormData()
        formData.append('files', file)
        const res = await uploadCiFile(formData, this.attrId)
        const newFiles = res.files || []
        // Always append: accumulating files across multiple uploads
        this.fileList.push(...newFiles)
        this.emitChange()
        this.persistFileList()
        if (onSuccess) onSuccess(res, file)
      } catch (e) {
        this.$message.error(e.message || this.$t('cmdb.ciType.fileUploadFailed'))
        if (onError) onError(e)
      } finally {
        this.uploading = false
        this.uploadingFileName = ''
      }
    },
    handlePreviewImage(file) {
      window.open(this.getFileUrl(file.stored_path, file.storage_backend), '_blank')
    },
    handlePreviewFile(file) {
      this.previewFile = file
      this.previewVisible = true
    },
    handleDeleteFile(idx) {
      const file = this.fileList[idx]
      if (!file) return

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
            this.persistFileList()
            this.$message.success(this.$t('cmdb.ciType.fileDelete') + ' ' + file.original_name)
          } catch (e) {
            this.$message.error(e.message || this.$t('cmdb.ciType.fileDeleteFailed'))
          } finally {
            this.deletePending = false
          }
        }
      })
    },
    getFileIcon(filename) {
      if (!filename) return 'file'
      const ext = filename.split('.').pop().toLowerCase()
      const iconMap = {
        pdf: 'file-pdf',
        doc: 'file-word',
docx: 'file-word',
        xls: 'file-excel',
xlsx: 'file-excel',
        ppt: 'file-ppt',
pptx: 'file-ppt',
        txt: 'file-text',
        zip: 'file-zip',
rar: 'file-zip',
'7z': 'file-zip',
        csv: 'file-excel',
        json: 'file-text',
        jpg: 'file-image',
jpeg: 'file-image',
png: 'file-image',
        gif: 'file-image',
webp: 'file-image',
bmp: 'file-image'
      }
      return iconMap[ext] || 'file'
    },
    openFileDialog() {
      this.dialogVisible = true
    }
  }
}
</script>

<style lang="less" scoped>
.ci-file-field {
  // Trigger button
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
