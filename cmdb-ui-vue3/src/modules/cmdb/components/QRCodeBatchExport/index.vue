<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { QuestionCircleOutlined, DownloadOutlined, PrinterOutlined } from '@ant-design/icons-vue'
import QRCode from 'qrcode'

/**
 * Batch QR-code export modal. `open(ciList)` is exposed so the parent can pass
 * the selected CIs to render.
 */
interface QRCodeItem {
  ciId: string | number
  typeId: string | number
  label: string
  url: string
}

const { t } = useI18n()

const visible = ref(false)
const ciList = ref<Array<Record<string, any>>>([])
const qrcodeList = ref<QRCodeItem[]>([])
const generating = ref(false)
const generatedCount = ref(0)
const totalCount = ref(0)

const qrcodeGrid = ref<HTMLElement>()

function open(nextCiList: Array<Record<string, any>>) {
  if (!nextCiList || !nextCiList.length) {
    message.warning(t('cmdb.ci.qrcodeBatchEmpty'))
    return
  }
  ciList.value = nextCiList
  qrcodeList.value = []
  visible.value = true
  nextTick(() => {
    generateAll()
  })
}

async function generateAll() {
  generating.value = true
  generatedCount.value = 0
  totalCount.value = ciList.value.length

  const list: QRCodeItem[] = ciList.value.map((ci) => {
    const mobileUrl = `${window.location.origin}/cmdb/mobile/${ci.typeId}/${ci.ciId}`
    return {
      ciId: ci.ciId,
      typeId: ci.typeId,
      label: ci.label || ci.name || `CI ${ci.ciId}`,
      url: mobileUrl,
    }
  })

  qrcodeList.value = list
  await nextTick()

  const canvases = qrcodeGrid.value?.querySelectorAll('canvas')
  for (let i = 0; i < qrcodeList.value.length; i++) {
    const item = qrcodeList.value[i]
    const canvas = canvases?.[i]
    if (canvas) {
      try {
        await QRCode.toCanvas(canvas, item.url, {
          width: 140,
          margin: 1,
          color: { dark: '#000000', light: '#ffffff' },
        })
      } catch (e) {
        console.error('QRCode generate failed for CI', item.ciId, e)
      }
    }
    generatedCount.value++
  }

  generating.value = false
}

async function downloadAll() {
  const grid = qrcodeGrid.value
  if (!grid) return

  const link = document.createElement('a')
  link.download = 'cmdb-qrcodes-batch.png'

  try {
    const { default: html2canvas } = await import('html2canvas')
    const canvas = await html2canvas(grid, {
      backgroundColor: '#ffffff',
      scale: 2,
    })
    link.href = canvas.toDataURL('image/png')
    link.click()
  } catch {
    message.warning(t('cmdb.ci.copyFailed'))
  }
}

function printAll() {
  const grid = qrcodeGrid.value
  if (!grid) return

  const printWindow = window.open('', '_blank', 'width=800,height=600')
  if (!printWindow) {
    message.warning(t('cmdb.ci.copyFailed'))
    return
  }

  const printGrid = grid.cloneNode(true) as HTMLElement
  const sourceCanvases = grid.querySelectorAll('canvas')
  const printCanvases = printGrid.querySelectorAll('canvas')
  printCanvases.forEach((canvas, index) => {
    const sourceCanvas = sourceCanvases[index]
    if (!sourceCanvas) return
    const img = printWindow.document.createElement('img')
    img.src = sourceCanvas.toDataURL('image/png')
    img.width = sourceCanvas.width || 140
    img.height = sourceCanvas.height || 140
    canvas.replaceWith(img)
  })

  const content = printGrid.innerHTML
  printWindow.document.write(`
    <html>
      <head>
        <title>CMDB QR Codes</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          .qrcode-batch-grid { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }
          .qrcode-batch-item { text-align: center; width: 170px; }
          .qrcode-batch-item-label { font-size: 12px; margin: 4px 0 2px; word-break: break-all; }
          .qrcode-batch-item-id { font-size: 11px; color: #999; margin: 0; }
          .qrcode-batch-item img { display: block; margin: 0 auto; }
          @media print {
            .qrcode-batch-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
            .qrcode-batch-item { page-break-inside: avoid; }
          }
        </style>
      </head>
      <body>
        <div class="qrcode-batch-grid">${content}</div>
      </body>
    </html>
  `)
  printWindow.document.close()
  setTimeout(() => {
    printWindow.print()
    printWindow.close()
  }, 500)
}

defineExpose({ open })
</script>

<template>
  <a-modal v-model:open="visible" width="800px" :footer="null" :mask-closable="true">
    <template #title>
      {{ t('cmdb.ci.qrcodeBatchTitle') }}
      <a-tooltip :title="t('cmdb.ci.qrcodeBatchTip')">
        <QuestionCircleOutlined style="color: #999; cursor: pointer" />
      </a-tooltip>
    </template>

    <div v-if="qrcodeList.length === 0 && !generating" class="qrcode-batch-empty">
      <a-empty :description="t('cmdb.ci.qrcodeBatchEmpty')" />
    </div>

    <div v-if="generating" class="qrcode-batch-generating">
      <a-spin />
      <span>{{ t('cmdb.ci.qrcodeBatchGenerating', { generatedCount, totalCount }) }}</span>
    </div>

    <div v-if="qrcodeList.length" ref="qrcodeGrid" class="qrcode-batch-grid">
      <div v-for="item in qrcodeList" :key="item.ciId" class="qrcode-batch-item">
        <canvas></canvas>
        <p class="qrcode-batch-item-label">{{ item.label }}</p>
        <p class="qrcode-batch-item-id">CI ID: {{ item.ciId }}</p>
      </div>
    </div>

    <div v-if="qrcodeList.length" class="qrcode-batch-actions">
      <a-button type="primary" @click="downloadAll">
        <DownloadOutlined /> {{ t('cmdb.ci.qrcodeDownload') }}
      </a-button>
      <a-button @click="printAll">
        <PrinterOutlined /> {{ t('cmdb.ci.printQRCode') }}
      </a-button>
    </div>
  </a-modal>
</template>

<style lang="less" scoped>
.qrcode-batch-tip {
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
  margin-bottom: 16px;
}

.qrcode-batch-empty {
  padding: 20px 0;
}

.qrcode-batch-generating {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 0;
  color: #999;
}

.qrcode-batch-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
  max-height: 50vh;
  overflow-y: auto;
}

.qrcode-batch-item {
  text-align: center;
  width: 160px;
  padding: 12px 8px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fff;
}

.qrcode-batch-item-label {
  font-size: 12px;
  color: #333;
  margin: 6px 0 2px;
  word-break: break-all;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.qrcode-batch-item-id {
  font-size: 11px;
  color: #bbb;
  margin: 0;
}

.qrcode-batch-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
