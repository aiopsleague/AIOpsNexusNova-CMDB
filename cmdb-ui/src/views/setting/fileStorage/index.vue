<template>
  <div class="ops-setting-file-storage">
    <a-card :title="$t('cs.fileStorage.basicConfig')" :bordered="false" class="file-storage-card">
      <a-form-model
        ref="configForm"
        :model="form"
        :rules="rules"
        :label-col="{ span: 4 }"
        :wrapper-col="{ span: 12 }"
      >
        <a-form-model-item :label="$t('cs.fileStorage.storageBackend')" prop="storage_backend">
          <a-select v-model="form.storage_backend" style="width: 100%">
            <a-select-option value="local">{{ $t('cs.fileStorage.local') }}</a-select-option>
            <a-select-option value="s3">S3 (MinIO / Ceph / AWS)</a-select-option>
          </a-select>
        </a-form-model-item>

        <!-- Local storage settings -->
        <template v-if="form.storage_backend === 'local'">
          <a-form-model-item :label="$t('cs.fileStorage.localPath')" prop="local_path">
            <a-input v-model="form.local_path" :placeholder="$t('cs.fileStorage.localPathPlaceholder')" />
          </a-form-model-item>
        </template>

        <!-- S3 settings -->
        <template v-if="form.storage_backend === 's3'">
          <a-form-model-item :label="$t('cs.fileStorage.s3Endpoint')" prop="s3_endpoint_url">
            <a-input v-model="form.s3_endpoint_url" placeholder="http://minio:9000" />
          </a-form-model-item>
          <a-form-model-item :label="$t('cs.fileStorage.s3AccessKey')" prop="s3_access_key">
            <a-input v-model="form.s3_access_key" />
          </a-form-model-item>
          <a-form-model-item :label="$t('cs.fileStorage.s3SecretKey')" prop="s3_secret_key">
            <a-input-password v-model="form.s3_secret_key" :placeholder="form._id ? $t('cs.fileStorage.secretKeyKeepTip') : ''" />
          </a-form-model-item>
          <a-form-model-item :label="$t('cs.fileStorage.s3Bucket')" prop="s3_bucket_name">
            <a-input v-model="form.s3_bucket_name" placeholder="cmdb-files" />
          </a-form-model-item>
          <a-form-model-item :label="$t('cs.fileStorage.s3Region')" prop="s3_region">
            <a-input v-model="form.s3_region" placeholder="us-east-1" />
          </a-form-model-item>
          <a-form-model-item :label="$t('cs.fileStorage.s3UseSSL')" prop="s3_use_ssl">
            <a-switch :checked="form.s3_use_ssl" @change="(checked) => { form.s3_use_ssl = checked }" />
          </a-form-model-item>
          <a-form-model-item :wrapper-col="{ span: 12, offset: 4 }">
            <a-button :loading="testing" @click="handleTestConnection">
              {{ $t('cs.fileStorage.testConnection') }}
            </a-button>
          </a-form-model-item>
        </template>

        <a-divider />

        <a-form-model-item :label="$t('cs.fileStorage.allowedExtensions')" prop="allowed_extensions">
          <a-select
            mode="tags"
            v-model="form.allowed_extensions"
            style="width: 100%"
            :placeholder="$t('cs.fileStorage.allowedExtensionsPlaceholder')"
            :token-separators="[',', '，', ' ']"
          />
        </a-form-model-item>

        <a-form-model-item :label="$t('cs.fileStorage.maxFileSize')" prop="max_file_size_mb">
          <a-input-number v-model="form.max_file_size_mb" :min="1" :max="500" style="width: 100%" />
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
  getFileStorageConfig,
  updateFileStorageConfig,
  testFileStorageConnection,
} from '@/api/fileStorage'

export default {
  name: 'SettingFileStorage',
  data() {
    return {
      form: {
        storage_backend: 'local',
        local_path: './uploaded_files/ci_files',
        s3_endpoint_url: '',
        s3_access_key: '',
        s3_secret_key: '',
        s3_bucket_name: 'cmdb-files',
        s3_region: 'us-east-1',
        s3_use_ssl: true,
        allowed_extensions: [],
        max_file_size_mb: 50,
      },
      saving: false,
      testing: false,
    }
  },
  computed: {
    rules() {
      const req = { required: true, message: this.$t('cs.fileStorage.fieldRequired'), trigger: 'blur' }
      return {
        storage_backend: [req],
        s3_endpoint_url: [
          { required: this.form.storage_backend === 's3', message: this.$t('cs.fileStorage.fieldRequired'), trigger: 'blur' },
        ],
        s3_access_key: [
          { required: this.form.storage_backend === 's3', message: this.$t('cs.fileStorage.fieldRequired'), trigger: 'blur' },
        ],
      }
    },
  },
  mounted() {
    this.loadConfig()
  },
  methods: {
    async loadConfig() {
      try {
        const res = await getFileStorageConfig()
        if (res) {
          this.form = { ...this.form, ...res }
        }
      } catch (e) {
        this.$message.error(this.$t('cs.fileStorage.loadFailed'))
      }
    },
    async handleSave() {
      this.$refs.configForm.validate(async (valid) => {
        if (!valid) return
        this.saving = true
        try {
          await updateFileStorageConfig(this.form)
          this.$message.success(this.$t('saveSuccess'))
        } catch (e) {
          this.$message.error(e.message || this.$t('cs.fileStorage.saveFailed'))
        } finally {
          this.saving = false
        }
      })
    },
    async handleTestConnection() {
      this.testing = true
      try {
        const res = await testFileStorageConnection(this.form)
        if (res.ok) {
          this.$message.success(this.$t('cs.fileStorage.testSuccess'))
        } else {
          this.$message.error(res.error || this.$t('cs.fileStorage.testFailed'))
        }
      } catch (e) {
        this.$message.error(e.message || this.$t('cs.fileStorage.testFailed'))
      } finally {
        this.testing = false
      }
    },
  },
}
</script>

<style lang="less" scoped>
.ops-setting-file-storage {
  padding: 20px;
  background-color: #f5f7fa;
  height: calc(100vh - 64px);
  overflow: auto;
  .file-storage-card {
    max-width: 900px;
  }
}
</style>
