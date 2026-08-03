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
      // kkFileView URL format: kkFileServer + ?url= + Base64(encodeURIComponent(fileUrl))
      const encodedFileUrl = encodeURIComponent(this.fileUrl)
      const base64Url = window.btoa(encodedFileUrl)
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
