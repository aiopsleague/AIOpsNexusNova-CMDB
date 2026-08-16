<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import MonacoCodeEditor from '@/components/MonacoCodeEditor/index.vue'

const { t } = useI18n()

const visible = ref(false)
const jsonData = ref('{}')

const editorHeight = computed(() => Math.max(240, window.innerHeight - 300))

function open(data: Record<string, any>) {
  visible.value = true
  try {
    jsonData.value = JSON.stringify(data ?? {}, null, 2)
  } catch {
    jsonData.value = '{}'
  }
}

function handleCancel() {
  visible.value = false
  jsonData.value = '{}'
}

defineExpose({ open })
</script>

<template>
  <a-modal
    :title="t('cmdb.ad.viewRawData')"
    :open="visible"
    wrap-class-name="ci-json-editor"
    width="50%"
    :footer="null"
    @cancel="handleCancel"
  >
    <MonacoCodeEditor
      v-model:value="jsonData"
      language="json"
      :height="editorHeight"
      storage-key="cmdbAdcRawDataEditor"
    />
  </a-modal>
</template>

<style lang="less">
.ci-json-editor {
  .jsoneditor-outer {
    height: var(--custom-height) !important;
    border: 1px solid #2f54eb;
  }
  div.jsoneditor-menu {
    background-color: #2f54eb;
  }
}
</style>
