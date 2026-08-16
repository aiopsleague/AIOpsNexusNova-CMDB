<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getFilePreviewConfig } from '@/api/filePreview'

/**
 * kkFileView-powered file preview iframe. The file URL is Base64-encoded and
 * passed to the kkFileView server, which converts and renders the document.
 */

// File types for which kkFileView should force re-conversion (bypass its
// cache), so the preview always reflects the latest file content. Configurable
// via VITE_KKFILEVIEW_FORCE_UPDATED_CACHE_TYPES (comma-separated extensions);
// defaults to the simple-text set (matches kkFileView's simText). The
// admin-configured value from the backend takes precedence at runtime.
const ENV_FORCE_UPDATED_CACHE_TYPES = (
  import.meta.env.VITE_KKFILEVIEW_FORCE_UPDATED_CACHE_TYPES ||
  'txt,html,htm,asp,jsp,xml,json,properties,md,gitignore,log,java,py,c,cpp,sql,sh,bat,m,bas,prg,cmd'
)
  .split(',')
  .map((type: string) => type.trim().toLowerCase())
  .filter(Boolean)

// Fetch the backend preview config once per page load and cache it. On error
// (e.g. non-admin without access) fall back to {} — the env-based defaults
// below keep the component working as before.
let cachedPreviewConfig: Record<string, any> | null = null
let previewConfigPromise: Promise<Record<string, any>> | null = null
function loadPreviewConfig(): Promise<Record<string, any>> {
  if (cachedPreviewConfig) return Promise.resolve(cachedPreviewConfig)
  if (previewConfigPromise) return previewConfigPromise
  previewConfigPromise = getFilePreviewConfig()
    .then((config: Record<string, any>) => {
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

const props = withDefaults(
  defineProps<{
    fileUrl: string
    // Original file name; used to decide whether to force a cache update.
    fileName?: string
  }>(),
  {
    fileName: '',
  }
)

const { t } = useI18n()

const loading = ref(true)
// null until the backend config resolves; previewUrl stays '' until then so
// the iframe never briefly loads with the env fallback URL.
const previewConfig = ref<Record<string, any> | null>(null)

const kkServer = computed(() =>
  previewConfig.value && previewConfig.value.preview_server_url
    ? previewConfig.value.preview_server_url
    : import.meta.env.VITE_KKFILEVIEW_SERVER || 'http://127.0.0.1:8012/onlinePreview'
)

const forceUpdatedCacheTypes = computed<string[]>(() => {
  const configured = previewConfig.value && previewConfig.value.force_updated_cache_types
  if (configured && Array.isArray(configured) && configured.length) {
    return configured.map((type: unknown) => String(type).trim().toLowerCase()).filter(Boolean)
  }
  return ENV_FORCE_UPDATED_CACHE_TYPES
})

const forceUpdatedCache = computed(() => {
  if (!props.fileName) return false
  const ext = props.fileName.split('.').pop()?.toLowerCase()
  return ext ? forceUpdatedCacheTypes.value.includes(ext) : false
})

const previewUrl = computed(() => {
  if (!props.fileUrl || !previewConfig.value) return ''
  // kkFileView URL format: kkFileServer + ?url= + Base64(UTF-8 bytes of fileUrl).
  const base64Url = window.btoa(unescape(encodeURIComponent(props.fileUrl)))
  // forceUpdatedCache is a top-level kkFileView param (not part of the file URL).
  const forceUpdatedCacheParam = forceUpdatedCache.value ? '&forceUpdatedCache=true' : ''
  return `${kkServer.value}?url=${encodeURIComponent(base64Url)}${forceUpdatedCacheParam}`
})

watch(
  () => props.fileUrl,
  () => {
    loading.value = true
  }
)

onMounted(() => {
  loadPreviewConfig().then((config) => {
    previewConfig.value = config
  })
})

function handleIframeLoad() {
  loading.value = false
}
</script>

<template>
  <div class="kk-preview-container">
    <div v-if="loading" class="preview-loading">
      <a-spin :tip="t('cmdb.ciType.filePreviewLoading')" />
    </div>
    <iframe v-show="!loading" :src="previewUrl" class="preview-iframe" @load="handleIframeLoad" />
  </div>
</template>

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
