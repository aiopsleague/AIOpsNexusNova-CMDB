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
import { getFilePreviewConfig } from '@/api/filePreview'

// File types for which kkFileView should force re-conversion (bypass its cache),
// so the preview always reflects the latest file content.
// Configurable via VUE_APP_KKFILEVIEW_FORCE_UPDATED_CACHE_TYPES (comma-separated
// extensions); defaults to the simple-text set (matches kkFileView's simText).
// At runtime, the admin-configured value from the backend file preview settings
// takes precedence (see loadPreviewConfig below).
const ENV_FORCE_UPDATED_CACHE_TYPES = (process.env.VUE_APP_KKFILEVIEW_FORCE_UPDATED_CACHE_TYPES ||
  'txt,html,htm,asp,jsp,xml,json,properties,md,gitignore,log,java,py,c,cpp,sql,sh,bat,m,bas,prg,cmd')
  .split(',')
  .map((type) => type.trim().toLowerCase())
  .filter(Boolean)

// Fetch the backend file preview config once per page load and cache it, so
// every preview open reuses it instead of hitting the API each time. On error
// (e.g. non-admin without access) we fall back to {} — the env-based defaults
// below then keep the component working as before.
let cachedPreviewConfig = null
let previewConfigPromise = null
function loadPreviewConfig() {
  if (cachedPreviewConfig) return Promise.resolve(cachedPreviewConfig)
  if (previewConfigPromise) return previewConfigPromise
  previewConfigPromise = getFilePreviewConfig()
    .then((config) => {
      cachedPreviewConfig = config || {}
      return cachedPreviewConfig
    })
    .catch(() => {
      cachedPreviewConfig = {}
      return cachedPreviewConfig
    })
    .finally(() => {
      previewConfigPromise = null
    })
  return previewConfigPromise
}

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
      loading: true,
      // null until the backend config resolves; previewUrl stays '' until then
      // so the iframe never briefly loads with the env fallback URL.
      previewConfig: null
    }
  },
  computed: {
    kkServer() {
      return this.previewConfig && this.previewConfig.preview_server_url
        ? this.previewConfig.preview_server_url
        : (process.env.VUE_APP_KKFILEVIEW_SERVER || 'http://127.0.0.1:8012/onlinePreview')
    },
    forceUpdatedCacheTypes() {
      const configured = this.previewConfig && this.previewConfig.force_updated_cache_types
      if (configured && Array.isArray(configured) && configured.length) {
        return configured.map((type) => String(type).trim().toLowerCase()).filter(Boolean)
      }
      return ENV_FORCE_UPDATED_CACHE_TYPES
    },
    forceUpdatedCache() {
      if (!this.fileName) return false
      const ext = this.fileName.split('.').pop().toLowerCase()
      return this.forceUpdatedCacheTypes.includes(ext)
    },
    previewUrl() {
      if (!this.fileUrl || !this.previewConfig) return ''
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
  created() {
    loadPreviewConfig().then((config) => {
      this.previewConfig = config
    })
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
