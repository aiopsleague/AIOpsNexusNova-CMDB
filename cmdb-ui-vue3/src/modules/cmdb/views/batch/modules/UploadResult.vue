<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { CloseCircleOutlined } from '@ant-design/icons-vue'
import { uploadData } from '@/modules/cmdb/api/batch'

const props = withDefaults(
  defineProps<{
    upLoadData: any[]
    ciType: number
    uniqueField: string
    isUploading?: boolean
  }>(),
  { isUploading: false }
)

const emit = defineEmits<{
  (e: 'uploadResultDone'): void
  (e: 'uploadResultError', index: number): void
}>()

const { t } = useI18n()

const visible = ref(false)
const errorNum = ref(0)
const success = ref(0)
const errorItems = ref<string[]>([])

const total = computed(() => props.upLoadData.length || 0)

watch(
  () => props.ciType,
  () => {
    visible.value = false
  }
)

async function upload2Server() {
  success.value = 0
  errorNum.value = 0
  errorItems.value = []
  const floor = Math.ceil(total.value / 6)
  for (let i = 0; i < floor; i++) {
    if (props.isUploading) {
      const itemList = props.upLoadData.slice(6 * i, 6 * i + 6)
      const promises = itemList.map((x) => uploadData(props.ciType, x))
      await Promise.allSettled(promises)
        .then((res) => {
          res.forEach((r, j) => {
            if (r.status === 'fulfilled') {
              success.value += 1
            } else {
              errorItems.value.push(r.reason?.response?.data?.message ?? t('cmdb.batch.requestFailedTips'))
              errorNum.value += 1
              emit('uploadResultError', 6 * i + j)
            }
          })
        })
        .finally(() => {
          // Upload progress is tracked per batch of 6.
        })
    } else {
      break
    }
  }
  if (props.isUploading) {
    visible.value = true
    emit('uploadResultDone')
  }
}

function handleOk() {
  visible.value = false
}

defineExpose({ upload2Server })
</script>

<template>
  <a-modal
    v-model:open="visible"
    :title="t('cmdb.batch.uploadResult')"
    :footer="null"
    :width="700"
    :mask-closable="false"
  >
    <div class="cmdb-batch-upload-result">
      <a-result
        :status="errorNum > 0 ? 'warning' : 'success'"
        :title="errorNum > 0 ? t('cmdb.batch.uploadPartialSuccess') : t('cmdb.batch.uploadAllSuccess')"
      >
        <template #subTitle>
          <div class="upload-result-summary">
            <span>{{ t('cmdb.batch.total') }}: <strong>{{ total }}</strong></span>
            <a-divider type="vertical" />
            <span class="success-text">{{ t('cmdb.batch.successItems') }}: <strong>{{ success }}</strong></span>
            <a-divider type="vertical" />
            <span class="error-text">{{ t('cmdb.batch.failedItems') }}: <strong>{{ errorNum }}</strong></span>
          </div>
        </template>
        <template #extra>
          <a-button type="primary" @click="handleOk">{{ t('confirm') }}</a-button>
        </template>
      </a-result>

      <div v-if="errorItems.length > 0" class="error-details">
        <a-divider orientation="left">{{ t('cmdb.batch.errorTips') }}</a-divider>
        <div class="error-list">
          <div v-for="(item, index) in errorItems" :key="index" class="error-item">
            <CloseCircleOutlined class="error-icon" />
            <span>{{ item }}</span>
          </div>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<style lang="less" scoped>
.cmdb-batch-upload-result {
  .upload-result-summary {
    font-size: 14px;
    margin-top: 16px;

    strong {
      font-size: 18px;
      margin-left: 4px;
    }

    .success-text {
      color: #52c41a;

      strong {
        color: #52c41a;
      }
    }

    .error-text {
      color: #ff4d4f;

      strong {
        color: #ff4d4f;
      }
    }
  }

  .error-details {
    margin-top: 24px;

    .error-list {
      max-height: 300px;
      overflow-y: auto;
      padding: 12px;
      background: #fff1f0;
      border: 1px solid #ffccc7;
      border-radius: 6px;

      .error-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 8px 0;
        color: @text-color_2;

        &:not(:last-child) {
          border-bottom: 1px solid #ffe7e5;
        }

        .error-icon {
          color: #ff4d4f;
          font-size: 16px;
          margin-top: 2px;
          flex-shrink: 0;
        }

        span {
          flex: 1;
          word-break: break-all;
        }
      }
    }
  }
}
</style>
