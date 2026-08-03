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
export default {
  name: 'KkFilePreview',
  props: {
    fileUrl: {
      type: String,
      required: true
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
    previewUrl() {
      if (!this.fileUrl) return ''
      // kkFileView URL format: kkFileServer + ?url= + Base64(UTF-8 bytes of fileUrl)
      // The encodeURIComponent/unescape round-trip is the standard way to make a
      // unicode URL safe for btoa() (which only accepts Latin-1 chars) while
      // keeping the decoded URL byte-for-byte identical to the original.
      const base64Url = window.btoa(unescape(encodeURIComponent(this.fileUrl)))
      return `${this.kkServer}?url=${encodeURIComponent(base64Url)}`
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
