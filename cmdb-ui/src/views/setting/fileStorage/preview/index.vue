<template>
  <div class="ops-setting-file-preview">
    <a-card :title="$t('cs.filePreview.basicConfig')" :bordered="false" class="file-preview-card">
      <a-form-model
        ref="configForm"
        :model="form"
        :rules="rules"
        :label-col="{ span: 4 }"
        :wrapper-col="{ span: 12 }"
      >
        <a-form-model-item :label="$t('cs.filePreview.previewServerUrl')" prop="preview_server_url">
          <a-input v-model="form.preview_server_url" :placeholder="$t('cs.filePreview.previewServerUrlPlaceholder')" />
        </a-form-model-item>

        <a-form-model-item :label="$t('cs.filePreview.forceUpdatedCacheTypes')" prop="force_updated_cache_types">
          <a-select
            mode="tags"
            v-model="form.force_updated_cache_types"
            style="width: 100%"
            :placeholder="$t('cs.filePreview.forceUpdatedCacheTypesPlaceholder')"
            :token-separators="[',', '，', ' ']"
          />
        </a-form-model-item>

        <a-form-model-item :wrapper-col="{ span: 12, offset: 4 }">
          <a-button :loading="testing" @click="handleTestConnection">
            {{ $t('cs.filePreview.testConnection') }}
          </a-button>
        </a-form-model-item>

        <a-form-model-item :wrapper-col="{ span: 12, offset: 4 }">
          <a-button type="primary" :loading="saving" @click="handleSave">
            {{ $t('save') }}
          </a-button>
        </a-form-model-item>
      </a-form-model>
    </a-card>
  </div>
</template>

<script>
import {
  getFilePreviewConfig,
  updateFilePreviewConfig,
  testFilePreviewConnection,
} from '@/api/filePreview'

export default {
  name: 'SettingFilePreview',
  data() {
    return {
      form: {
        preview_server_url: 'http://127.0.0.1:8012/onlinePreview',
        force_updated_cache_types: [],
      },
      saving: false,
      testing: false,
    }
  },
  computed: {
    rules() {
      return {
        preview_server_url: [{ required: true, message: this.$t('cs.filePreview.fieldRequired'), trigger: 'blur' }],
      }
    },
  },
  mounted() {
    this.loadConfig()
  },
  methods: {
    async loadConfig() {
      try {
        const res = await getFilePreviewConfig()
        if (res) {
          this.form = { ...this.form, ...res }
        }
      } catch (e) {
        this.$message.error(this.$t('cs.filePreview.loadFailed'))
      }
    },
    async handleSave() {
      this.$refs.configForm.validate(async (valid) => {
        if (!valid) return
        this.saving = true
        try {
          await updateFilePreviewConfig(this.form)
          this.$message.success(this.$t('saveSuccess'))
        } catch (e) {
          this.$message.error(e.message || this.$t('cs.filePreview.saveFailed'))
        } finally {
          this.saving = false
        }
      })
    },
    async handleTestConnection() {
      this.testing = true
      try {
        const res = await testFilePreviewConnection({ preview_server_url: this.form.preview_server_url })
        if (res.ok) {
          this.$message.success(this.$t('cs.filePreview.testSuccess'))
        } else {
          this.$message.error(res.error || this.$t('cs.filePreview.testFailed'))
        }
      } catch (e) {
        this.$message.error(e.message || this.$t('cs.filePreview.testFailed'))
      } finally {
        this.testing = false
      }
    },
  },
}
</script>

<style lang="less" scoped>
.ops-setting-file-preview {
  padding: 20px;
  background-color: #f5f7fa;
  height: calc(100vh - 64px);
  overflow: auto;
  .file-preview-card {
    max-width: 900px;
  }
}
</style>
