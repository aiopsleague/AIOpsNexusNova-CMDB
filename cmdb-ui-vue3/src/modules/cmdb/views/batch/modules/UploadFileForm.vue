<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { InboxOutlined, FileOutlined } from '@ant-design/icons-vue'
import { processFile } from '@/modules/cmdb/api/batch'

const props = withDefaults(
  defineProps<{
    ciType?: number
    isUploading?: boolean
  }>(),
  {
    ciType: 0,
    isUploading: false,
  }
)

const emit = defineEmits<{
  (e: 'uploadDone', data: any[][]): void
}>()

const { t } = useI18n()

const fileList = ref<any[]>([])
const dataList = ref<any[][]>([])
const progressStatus = ref<'active' | 'success' | 'exception' | 'normal'>('active')
const percent = ref(0)

watch(
  () => props.ciType,
  () => {
    fileList.value = []
    dataList.value = []
    progressStatus.value = 'active'
    percent.value = 0
    emit('uploadDone', dataList.value)
  }
)

function customRequest(data: any) {
  fileList.value = [data.file]
  processFile(data.file)
    .then((res) => {
      progressStatus.value = 'success'
      percent.value = 100
      dataList.value = res
      emit('uploadDone', dataList.value)
    })
    .catch(() => {
      progressStatus.value = 'exception'
      percent.value = 0
      message.error(t('cmdb.batch.requestFailedTips'))
    })
}
</script>

<template>
  <!-- eslint-disable vue/no-v-html -->
  <div class="cmdb-batch-upload-dragger">
    <a-upload-dragger
      :multiple="false"
      :custom-request="customRequest"
      accept=".xls,.xlsx"
      :show-upload-list="false"
      :file-list="fileList"
      :disabled="!ciType || isUploading"
    >
      <InboxOutlined />
      <p class="ant-upload-hint">{{ t('cmdb.batch.supportFileTypes') }}</p>
      <p v-html="t('cmdb.batch.drawTips1')"></p>
      <p v-html="t('cmdb.batch.drawTips2')"></p>
      <div v-for="item in fileList" :key="item.name" class="cmdb-batch-upload-dragger-file">
        <span><FileOutlined class="cmdb-batch-upload-dragger-file-icon" />{{ item.name }}</span>
        <a-progress :status="progressStatus" :percent="percent" />
      </div>
    </a-upload-dragger>
    <div class="cmdb-batch-upload-tips">
      <p>{{ t('cmdb.batch.tips1') }}</p>
      <div>{{ t('cmdb.batch.tips2') }}</div>
      <div>{{ t('cmdb.batch.tips3') }}</div>
      <div>{{ t('cmdb.batch.tips4') }}</div>
      <div>{{ t('cmdb.batch.tips5') }}</div>
    </div>
  </div>
</template>

<style lang="less">
.cmdb-batch-upload-dragger {
  height: auto;
  margin: 16px 0;
  .ant-upload p {
    margin-bottom: 5px;
  }
  .ant-upload.ant-upload-drag {
    border: none;
    background: ~'linear-gradient(90deg, @{text-color_5} 50%, transparent 0) repeat-x 0 0 / 15px 1px, linear-gradient(90deg, @{text-color_5} 50%, transparent 0) repeat-x 0 100% / 15px 1px, linear-gradient(0deg, @{text-color_5} 50%, transparent 0) repeat-y 0 0 / 1px 15px, linear-gradient(0deg, @{text-color_5} 50%, transparent 0) repeat-y 100% 0 / 1px 15px';
    .ant-upload-drag-container > i {
      font-size: 60px;
    }
    .cmdb-batch-upload-tips {
      color: @primary-color;
    }

    &:hover {
      background: ~'linear-gradient(90deg, @{primary-color_2} 50%, transparent 0) repeat-x 0 0 / 15px 1px, linear-gradient(90deg, @{primary-color_2} 50%, transparent 0) repeat-x 0 100% / 15px 1px, linear-gradient(0deg, @{primary-color_2} 50%, transparent 0) repeat-y 0 0 / 1px 15px, linear-gradient(0deg, @{primary-color_2} 50%, transparent 0) repeat-y 100% 0 / 1px 15px, @{primary-color_7}';
    }
  }
  .ant-upload.ant-upload-drag .ant-upload-drag-container {
    vertical-align: baseline;
  }
}
</style>
<style lang="less" scoped>
.cmdb-batch-upload-dragger {
  position: relative;
  display: flex;
  > span {
    display: inline-block;
    width: 50%;
  }
  .cmdb-batch-upload-dragger-file {
    background-color: @primary-color_7;
    border-radius: 2px;
    width: 80%;
    padding: 2px 8px;
    display: inline-flex;
    > span {
      white-space: nowrap;
      margin-right: 10px;
    }

    &-icon {
      color: @primary-color;
      margin-right: 5px;
    }
  }
  .cmdb-batch-upload-tips {
    width: 50%;
    padding-left: 20px;
    color: @text-color_3;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    p:first-child {
      color: @text-color_1;
    }
  }
}
</style>
