<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { ImportOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import CiTypeChoice from './modules/CiTypeChoice.vue'
import CiUploadTable from './modules/CiUploadTable.vue'
import UploadFileForm from './modules/UploadFileForm.vue'
import UploadResult from './modules/UploadResult.vue'
import { filterNull } from '@/modules/cmdb/api/batch'

const { t } = useI18n()

const ciTypeChoiceRef = ref<InstanceType<typeof CiTypeChoice>>()
const uploadFileFormRef = ref<InstanceType<typeof UploadFileForm>>()
const ciUploadTableRef = ref<InstanceType<typeof CiUploadTable>>()
const uploadResultRef = ref<InstanceType<typeof UploadResult>>()

const ciTypeAttrs = ref<Record<string, any>>({})
const uploadData = ref<any[]>([])
const ciType = ref(0)
const uniqueField = ref('')
const uniqueId = ref(0)
const isUploading = ref(false)
const hasError = ref(false)
const currentStep = ref(0)

const windowHeight = computed(() => window.innerHeight)

function showCiType(messageObj: any) {
  ciTypeAttrs.value = messageObj ?? {}
  ciType.value = messageObj?.type_id ?? 0
  uniqueField.value = messageObj?.unique ?? ''
  uniqueId.value = messageObj?.unique_id ?? 0
  if (messageObj) {
    currentStep.value = Math.max(currentStep.value, 1)
  }
}

function handleStepChange(step: number) {
  currentStep.value = Math.max(currentStep.value, step)
}

function uploadDone(dataList: any[][]) {
  const _uploadData = filterNull(dataList).map((item: any[], i: number) => {
    if (i > 0) {
      const _ele: Record<string, any> = {}
      item.forEach((ele: any, j: number) => {
        if (ele !== undefined && ele !== null) {
          const _find = ciTypeAttrs.value.attributes.find(
            (attr: any) => attr.alias === dataList[0][j] || attr.name === dataList[0][j]
          )
          if (_find?.value_type === '4' && typeof ele === 'number') {
            _ele[dataList[0][j]] = dayjs(Math.round((ele - 25569) * 86400 * 1000 - 28800000)).format('YYYY-MM-DD')
          } else if (_find?.value_type === '3' && typeof ele === 'number') {
            _ele[dataList[0][j]] = dayjs(Math.round((ele - 25569) * 86400 * 1000 - 28800000)).format(
              'YYYY-MM-DD HH:mm:ss'
            )
          } else if (_find?.value_type === '5' && typeof ele === 'number') {
            _ele[dataList[0][j]] = dayjs(Math.round(ele * 86400 * 1000 - 28800000)).format('HH:mm:ss')
          } else {
            _ele[dataList[0][j]] = ele
          }
        }
      })
      return _ele
    }
    return item
  })
  uploadData.value = _uploadData.slice(1)
  hasError.value = false
  isUploading.value = false
  if (_uploadData.length > 1) {
    currentStep.value = Math.max(currentStep.value, 2)
  }
}

function handleUpload() {
  if (!ciType.value) {
    message.error(t('cmdb.batch.unselectCIType'))
    return
  }
  if (uploadData.value && uploadData.value.length > 0) {
    isUploading.value = true
    nextTick(() => {
      uploadResultRef.value?.upload2Server()
    })
  } else {
    message.error(t('cmdb.batch.pleaseUploadFile'))
  }
}

function handleCancel() {
  if (!isUploading.value) {
    showCiType(null)
    ciTypeChoiceRef.value?.clearSelectNum()
    hasError.value = false
    currentStep.value = 0
    uploadData.value = []
  } else {
    message.warning(t('cmdb.batch.batchUploadCanceled'))
    isUploading.value = false
  }
}

function uploadResultDone() {
  isUploading.value = false
}

function uploadResultError(index: number) {
  hasError.value = true
  ciUploadTableRef.value?.uploadResultError(index)
}

function downloadError() {
  ciUploadTableRef.value?.downloadError()
}
</script>

<template>
  <div class="cmdb-batch-upload" :style="{ height: `${windowHeight - 64}px` }">
    <div class="cmdb-batch-upload-header">
      <div class="cmdb-batch-upload-header-title">
        <ImportOutlined class="cmdb-batch-upload-header-icon" />
        <span>{{ t('cmdb.menu.batchUpload') }}</span>
      </div>
    </div>

    <a-steps :current="currentStep" class="cmdb-batch-upload-steps">
      <a-step :title="t('cmdb.batch.selectCIType')" :description="t('cmdb.batch.downloadTemplate')" />
      <a-step :title="t('cmdb.batch.uploadFile')" />
      <a-step :title="t('cmdb.batch.dataPreview')" />
    </a-steps>

    <div class="cmdb-batch-upload-content">
      <a-card class="cmdb-batch-upload-card">
        <template #title>
          <span class="cmdb-batch-upload-card-title">1. {{ t('cmdb.batch.selectCIType') }} & {{ t('cmdb.batch.downloadTemplate') }}</span>
        </template>
        <CiTypeChoice ref="ciTypeChoiceRef" @get-ci-type-attr="showCiType" @step-change="handleStepChange" />
      </a-card>

      <a-card class="cmdb-batch-upload-card">
        <template #title>
          <span class="cmdb-batch-upload-card-title">2. {{ t('cmdb.batch.uploadFile') }}</span>
        </template>
        <UploadFileForm
          ref="uploadFileFormRef"
          :is-uploading="isUploading"
          :ci-type="ciType"
          @upload-done="uploadDone"
        ></UploadFileForm>
      </a-card>

      <a-card class="cmdb-batch-upload-card">
        <template #title>
          <span class="cmdb-batch-upload-card-title">3. {{ t('cmdb.batch.dataPreview') }}</span>
        </template>
        <CiUploadTable ref="ciUploadTableRef" :ci-type-attrs="ciTypeAttrs" :upload-data="uploadData"></CiUploadTable>
      </a-card>
    </div>
    <div class="cmdb-batch-upload-action">
      <a-space size="large">
        <a-button :disabled="!(ciType && uploadData.length)" type="primary" @click="handleUpload">
          <template #icon><UploadOutlined /></template>
          {{ t('upload') }}
        </a-button>
        <a-button @click="handleCancel">{{ t('cancel') }}</a-button>
        <a-button v-if="hasError && !isUploading" type="primary" ghost class="ops-button-ghost" @click="downloadError">
          <template #icon><DownloadOutlined /></template>
          {{ t('cmdb.batch.downloadFailed') }}
        </a-button>
      </a-space>
    </div>

    <UploadResult
      v-if="ciType"
      ref="uploadResultRef"
      :up-load-data="uploadData"
      :ci-type="ciType"
      :unique-field="uniqueField"
      :is-uploading="isUploading"
      @upload-result-done="uploadResultDone"
      @upload-result-error="uploadResultError"
    ></UploadResult>
  </div>
</template>

<style lang="less">
.cmdb-batch-upload-label {
  color: @text-color_1;
  font-weight: bold;
  white-space: pre;
  > span {
    color: red;
  }
}
</style>
<style lang="less" scoped>
.cmdb-batch-upload {
  margin-bottom: -24px;
  padding: 24px;
  background-color: #f7f8fa;
  border-radius: @border-radius-box;
  overflow: auto;

  &-header {
    margin-bottom: 24px;

    &-title {
      display: flex;
      align-items: center;
      font-size: 18px;
      font-weight: 600;
      color: @text-color_1;
      gap: 10px;
    }

    &-icon {
      font-size: 24px;
      color: @primary-color;
    }
  }

  &-steps {
    background: #fff;
    padding: 24px 48px;
    border-radius: 8px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);

    :deep(.ant-steps-item-process .ant-steps-item-icon) {
      background-color: @primary-color;
      border-color: @primary-color;

      .ant-steps-icon {
        color: #fff;
      }
    }

    :deep(.ant-steps-item-finish .ant-steps-item-icon) {
      border-color: @primary-color;

      .ant-steps-icon {
        color: @primary-color;
      }
    }

    :deep(.ant-steps-item-wait .ant-steps-item-icon) {
      border-color: #d9d9d9;

      .ant-steps-icon {
        color: rgba(0, 0, 0, 0.25);
      }
    }
  }

  &-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  &-card {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    transition: box-shadow 0.3s ease;

    &:hover {
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }

    :deep(.ant-card-head) {
      border-bottom: 1px solid #e8eaed;
      background: #fafafa;
      border-radius: 8px 8px 0 0;

      .ant-card-head-title {
        font-size: 15px;
        font-weight: 600;
        color: @text-color_1;
      }
    }

    :deep(.ant-card-body) {
      padding: 24px;
    }
  }

  &-action {
    margin-top: 24px;
    padding: 20px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    display: flex;
    justify-content: center;
  }
}
</style>
