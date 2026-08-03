<template>
  <div class="kk-preview-container">
    <div v-if="loading" class="preview-loading">
      <a-spin :tip="$t('cmdb.ciType.filePreviewLoading')" />
    </div>
    <iframe
      v-show="!loading"
      :src="previewUrl"
      class="preview-iframe"
      @load="handleIframeLoad"
    />
  </div>
</template>

<script>
// File types for which kkFileView should force re-conversion (bypass its cache),
// so the preview always reflects the latest file content.
// Configurable via VUE_APP_KKFILEVIEW_FORCE_UPDATED_CACHE_TYPES (comma-separated
// extensions); defaults to the simple-text set (matches kkFileView's simText).
const FORCE_UPDATED_CACHE_TYPES = (process.env.VUE_APP_KKFILEVIEW_FORCE_UPDATED_CACHE_TYPES ||
  'txt,html,htm,asp,jsp,xml,json,properties,md,gitignore,log,java,py,c,cpp,sql,sh,bat,m,bas,prg,cmd')
  .split(',')
  .map((type) => type.trim().toLowerCase())
  .filter(Boolean)

export default {
  name: 'KkFilePreview',
  props: {
    fileUrl: {
      type: String,
      required: true
    },
    fileName: {
      // Original file name; used to decide whether to force a cache update.
      type: String,
      default: ''
    }
  },
  data() {
    return {
      loading: true
    }
  },
  computed: {
    kkServer() {
      return process.env.VUE_APP_KKFILEVIEW_SERVER || 'http://127.0.0.1:8012/onlinePreview'
    },
    forceUpdatedCache() {
      if (!this.fileName) return false
      const ext = this.fileName.split('.').pop().toLowerCase()
      return FORCE_UPDATED_CACHE_TYPES.includes(ext)
    },
    previewUrl() {
      if (!this.fileUrl) return ''
      // kkFileView URL format: kkFileServer + ?url= + Base64(UTF-8 bytes of fileUrl)
      // The encodeURIComponent/unescape round-trip is the standard way to make a
      // unicode URL safe for btoa() (which only accepts Latin-1 chars) while
      // keeping the decoded URL byte-for-byte identical to the original.
      const base64Url = window.btoa(unescape(encodeURIComponent(this.fileUrl)))
      // forceUpdatedCache is a top-level kkFileView param (not part of the file
      // URL) that makes it re-convert the file and bypass its cache.
      const forceUpdatedCache = this.forceUpdatedCache ? '&forceUpdatedCache=true' : ''
      return `${this.kkServer}?url=${encodeURIComponent(base64Url)}${forceUpdatedCache}`
    }
  },
  watch: {
    fileUrl() {
      this.loading = true
    }
  },
  methods: {
    handleIframeLoad() {
      this.loading = false
    }
  }
}
</script>

<style lang="less" scoped>
.kk-preview-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 600px;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  min-height: 600px;
}

.preview-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}
</style>
