<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { updateCI } from '@/modules/cmdb/api/ci'
import MonacoCodeEditor from '@/components/MonacoCodeEditor/index.vue'

/**
 * Modal JSON editor for JSON-valued CI attributes (value_type === '6').
 * Replaces the Vue 2 `vue-json-editor` dependency with the already-migrated
 * Monaco code editor. Preserves the legacy public API: `open(column, row)` and
 * the `jsonEditorOk(row, column, jsonData)` event.
 */
const { t } = useI18n()

const visible = ref(false)
const jsonData = ref('')
const row = ref<Record<string, any> | null>(null)
const column = ref<Record<string, any> | null>(null)

const editorHeight = computed(() => Math.max(240, window.innerHeight - 300))

function open(
  columnRef: Record<string, any>,
  rowRef: Record<string, any>,
  initialData?: Record<string, any>
) {
  visible.value = true
  if (rowRef && rowRef[columnRef.property]) {
    try {
      jsonData.value = JSON.stringify(JSON.parse(rowRef[columnRef.property]), null, 2)
    } catch {
      jsonData.value = '{}'
    }
  } else {
    jsonData.value = '{}'
  }
  if (initialData) {
    jsonData.value = JSON.stringify(initialData, null, 2)
  }

  row.value = rowRef
  column.value = columnRef
}

function handleCancel() {
  visible.value = false
}

function handleOk() {
  let parsed: unknown
  try {
    parsed = JSON.parse(jsonData.value)
  } catch {
    message.error(t('cmdb.ci.jsonParseError'))
    return
  }

  if (row.value && column.value) {
    updateCI(row.value.ci_id || row.value._id, {
      [`${column.value.property}`]: parsed,
    }).then(() => {
      message.success(t('saveSuccess'))
      handleCancel()
      emit('json-editor-ok', row.value, column.value, parsed)
    })
  } else {
    emit('json-editor-ok', parsed)
    handleCancel()
  }
}

const emit = defineEmits<{
  (e: 'json-editor-ok', ...args: any[]): void
}>()

defineExpose({ open })
</script>

<template>
  <a-modal
    :open="visible"
    wrap-class-name="ci-json-editor"
    :closable="false"
    :mask-closable="false"
    width="50%"
    @cancel="handleCancel"
    @ok="handleOk"
  >
    <MonacoCodeEditor
      v-model:value="jsonData"
      language="json"
      :height="editorHeight"
      :storage-key="'ciJsonEditor'"
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
