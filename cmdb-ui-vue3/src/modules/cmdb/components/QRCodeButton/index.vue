<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { QrcodeOutlined, DownloadOutlined, CopyOutlined } from '@ant-design/icons-vue'
import QRCode from 'qrcode'

/**
 * Button that renders a scannable QR code pointing at the CI's mobile detail
 * page, with download / copy actions.
 */
const props = withDefaults(
  defineProps<{
    typeId?: number | string | null
    ciId?: number | string | null
  }>(),
  {
    typeId: null,
    ciId: null,
  }
)

const { t } = useI18n()

const visible = ref(false)
const qrcodeCanvas = ref<HTMLCanvasElement>()

const hasValidId = computed(
  () =>
    props.typeId !== null &&
    props.typeId !== undefined &&
    props.ciId !== null &&
    props.ciId !== undefined
)

const mobileUrl = computed(() => {
  if (!hasValidId.value) {
    return ''
  }
  const origin = window.location.origin
  return `${origin}/cmdb/mobile/${props.typeId}/${props.ciId}`
})

async function showQRCode() {
  if (!hasValidId.value) {
    return
  }
  visible.value = true
  await nextTick()
  generateQRCode()
}

async function generateQRCode() {
  const canvas = qrcodeCanvas.value
  if (!canvas) return
  try {
    await QRCode.toCanvas(canvas, mobileUrl.value, {
      width: 220,
      margin: 1,
      color: {
        dark: '#000000',
        light: '#ffffff',
      },
    })
  } catch (e) {
    console.error('QRCode generate failed:', e)
  }
}

function downloadQRCode() {
  const canvas = qrcodeCanvas.value
  if (!canvas || !hasValidId.value) return
  const link = document.createElement('a')
  link.download = `cmdb-ci-${props.ciId}-qrcode.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}

function copyMobileUrl() {
  if (!hasValidId.value) {
    return
  }
  navigator.clipboard
    .writeText(mobileUrl.value)
    .then(() => {
      message.success(t('copySuccess'))
    })
    .catch(() => {
      message.error(t('cmdb.ci.copyFailed'))
    })
}
</script>

<template>
  <span>
    <a class="qrcode-btn" :style="{ marginRight: '12px' }" @click="showQRCode">
      <QrcodeOutlined />
      {{ t('cmdb.ci.qrcode') }}
    </a>

    <a-modal
      v-model:open="visible"
      :title="t('cmdb.ci.qrcodeTitle')"
      :footer="null"
      width="360px"
      :mask-closable="true"
      centered
    >
      <div class="qrcode-modal-content">
        <p class="qrcode-modal-tip">{{ t('cmdb.ci.qrcodeTip') }}</p>
        <div class="qrcode-canvas-wrapper">
          <canvas ref="qrcodeCanvas"></canvas>
        </div>
        <p class="qrcode-modal-url">{{ mobileUrl }}</p>
        <a-space class="qrcode-modal-actions">
          <a-button type="primary" size="small" @click="downloadQRCode">
            <DownloadOutlined /> {{ t('cmdb.ci.qrcodeDownload') }}
          </a-button>
          <a-button size="small" @click="copyMobileUrl">
            <CopyOutlined /> {{ t('copy') }}
          </a-button>
        </a-space>
      </div>
    </a-modal>
  </span>
</template>

<style lang="less" scoped>
.qrcode-btn {
  color: rgba(0, 0, 0, 0.65);
  &:hover {
    color: @primary-color;
  }
}

.qrcode-modal-content {
  text-align: center;
}

.qrcode-modal-tip {
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
  margin-bottom: 16px;
}

.qrcode-canvas-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}

.qrcode-modal-url {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  word-break: break-all;
  margin-bottom: 16px;
  padding: 0 12px;
}

.qrcode-modal-actions {
  display: flex;
  justify-content: center;
}
</style>
