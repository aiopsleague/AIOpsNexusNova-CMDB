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
          <img
            v-if="isImage(file.mime_type)"
            :src="getFileUrl(file.stored_path, file.storage_backend)"
            :style="{ maxWidth: '100px', maxHeight: '60px', objectFit: 'cover', cursor: 'pointer' }"
            :title="file.original_name"
            @click="handlePreviewImage(file)"
          />
          <ops-icon v-else type="file" style="font-size: 24px; color: #722ed1;" />
          <div class="ci-file-field-info">
            <span class="ci-file-field-filename">{{ file.original_name }}</span>
            <span class="ci-file-field-size">{{ formatSize(file.size) }}</span>
          </div>
          <div class="ci-file-field-actions">
            <a @click="handlePreviewFile(file)">{{ $t('cmdb.ciType.filePreview') }}</a>
            <a-divider type="vertical" />
            <a
              :href="getFileUrl(file.stored_path, file.storage_backend, true)"
              :download="file.original_name"
            >
              {{ $t('cmdb.ciType.fileDownload') }}
            </a>
          </div>
        </div>
      </div>
      <!-- kkFileView preview modal -->
      <a-modal
        :visible="previewVisible"
        :title="previewFile ? previewFile.original_name : ''"
        :footer="null"
        width="90%"
        :bodyStyle="{ padding: 0, height: '80vh' }"
        :destroyOnClose="true"
        @cancel="previewVisible = false"
      >
        <KkFilePreview v-if="previewVisible" :fileUrl="previewFileUrl" />
      </a-modal>
    </template>

    <!-- Edit mode -->
    <template v-else>
      <div v-if="fileList.length" class="ci-file-field-list">
        <div
          v-for="(file, idx) in fileList"
          :key="idx"
          class="ci-file-field-item ci-file-field-item-editable"
        >
          <ops-icon type="file" style="font-size: 18px; color: #722ed1; margin-right: 8px;" />
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
import Vue from 'vue'
import { ACCESS_TOKEN } from '@/store/global/mutation-types'
import { uploadCiFile } from '@/modules/cmdb/api/ciFile'
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
    }
  },
  data() {
    return {
      fileList: [],
      uploading: false,
      previewVisible: false,
      previewFile: null
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
      const relativeUrl = this.getFileUrl(this.previewFile.stored_path, this.previewFile.storage_backend)
      // kkFileView requires an absolute URL to fetch the file. Use
      // VUE_APP_FILE_API_BASE_URL so the address is reachable from the
      // kkFileView server (e.g. inside a Docker container, localhost does
      // not resolve to the host machine).
      const baseUrl = process.env.VUE_APP_FILE_API_BASE_URL || window.location.origin
      return baseUrl + relativeUrl
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
        // Always append: "继续上传" accumulates files so already-uploaded
        // files are kept (the value is a JSON array regardless of is_list).
        this.fileList.push(...newFiles)
        this.emitChange()
        if (onSuccess) onSuccess(res, file)
      } catch (e) {
        this.$message.error(e.message || this.$t('cmdb.ciType.fileUploadFailed'))
        if (onError) onError(e)
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
    min-width: 0;
    flex: 1;
  }
  &-filename {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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
  &-actions {
    display: flex;
    align-items: center;
    margin-left: 12px;
    white-space: nowrap;
    flex-shrink: 0;
  }
}
</style>
