<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  CodeOutlined,
  FullscreenExitOutlined,
  FullscreenOutlined,
  MinusOutlined,
  PlusOutlined,
  SwapOutlined,
} from '@ant-design/icons-vue'
import * as monaco from 'monaco-editor'
import { initVimMode } from 'monaco-vim'
import type { IDisposable } from 'monaco-editor'
import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import JsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'
import CssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker'
import HtmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker'
import TsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker'

// Configure Monaco's web workers for Vite. Without this Monaco falls back to
// running the worker code on the main thread (still functional, but noisy).
globalThis.MonacoEnvironment = {
  getWorker(_workerId: string, label: string): Worker {
    if (label === 'json') return new JsonWorker()
    if (label === 'css' || label === 'scss' || label === 'less') return new CssWorker()
    if (label === 'html' || label === 'handlebars' || label === 'razor') return new HtmlWorker()
    if (label === 'typescript' || label === 'javascript') return new TsWorker()
    return new EditorWorker()
  },
}

const DEFAULT_STORAGE_KEY = 'monacoEditorConfig'

const props = withDefaults(
  defineProps<{
    value?: string
    language?: string
    height?: string | number
    readOnly?: boolean
    storageKey?: string
  }>(),
  {
    value: '',
    language: 'python',
    height: 360,
    readOnly: false,
    storageKey: DEFAULT_STORAGE_KEY,
  }
)

const emit = defineEmits<{
  (e: 'input', value: string): void
  (e: 'change', value: string): void
  (e: 'update:value', value: string): void
  (e: 'blur'): void
  (e: 'focus'): void
}>()

const { t } = useI18n()

interface LocalConfig {
  theme?: string
  keymap?: string
  fontSize?: number
  wordWrap?: boolean
}

const editorRef = ref<HTMLElement | null>(null)
const vimStatusRef = ref<HTMLElement | null>(null)

let editor: monaco.editor.IStandaloneCodeEditor | null = null
let model: monaco.editor.ITextModel | null = null
let vimMode: (IDisposable & { dispose(): void }) | null = null
let isChangingValue = false

const isFullscreen = ref(false)
const currentLanguage = ref(props.language || 'python')
const currentTheme = ref('vs-dark')
const currentKeymap = ref('default')
const fontSize = ref(14)
const wordWrap = ref(false)

// Restore persisted editor preferences (theme/keymap/fontSize/wordWrap).
const localConfig = getLocalConfig()
currentTheme.value = localConfig.theme || 'vs-dark'
currentKeymap.value = localConfig.keymap || 'default'
fontSize.value = localConfig.fontSize || 14
wordWrap.value = localConfig.wordWrap ?? false

const editorHeight = computed(() => {
  if (isFullscreen.value) {
    return 'calc(100vh - 82px)'
  }
  return typeof props.height === 'number' ? `${props.height}px` : props.height
})

const keymapOptions = computed(() => [
  { value: 'default', label: t('default') },
  { value: 'vim', label: 'Vim' },
])

const themeOptions = computed(() => [
  { value: 'vs-dark', label: 'Dark' },
  { value: 'vs', label: 'Light' },
])

function getLocalConfig(): LocalConfig {
  try {
    return JSON.parse(localStorage.getItem(props.storageKey) || '{}')
  } catch {
    return {}
  }
}

function saveLocalConfig() {
  localStorage.setItem(
    props.storageKey,
    JSON.stringify({
      theme: currentTheme.value,
      keymap: currentKeymap.value,
      fontSize: fontSize.value,
      wordWrap: wordWrap.value,
    })
  )
}

function initEditor() {
  model = monaco.editor.createModel(props.value || '', currentLanguage.value)
  editor = monaco.editor.create(editorRef.value!, {
    model,
    theme: currentTheme.value,
    fontSize: fontSize.value,
    tabSize: 4,
    insertSpaces: true,
    automaticLayout: true,
    minimap: { enabled: true },
    scrollBeyondLastLine: false,
    readOnly: props.readOnly,
    wordWrap: wordWrap.value ? 'on' : 'off',
    renderLineHighlight: 'all',
    roundedSelection: false,
  })
  editor.onDidChangeModelContent(() => {
    if (isChangingValue || !editor) {
      return
    }
    const value = editor.getValue()
    emit('input', value)
    emit('update:value', value)
    emit('change', value)
  })
  editor.onDidBlurEditorText(() => emit('blur'))
  editor.onDidFocusEditorText(() => emit('focus'))
  changeKeymap(currentKeymap.value, false)
}

function disposeVimMode() {
  if (vimMode) {
    vimMode.dispose()
    vimMode = null
  }
}

function layoutEditor() {
  nextTick(() => {
    editor?.layout()
  })
}

function changeLanguage(language: string) {
  currentLanguage.value = language
  if (model) {
    monaco.editor.setModelLanguage(model, language)
  }
}

function changeTheme(theme: string) {
  currentTheme.value = theme
  monaco.editor.setTheme(theme)
  saveLocalConfig()
}

function changeKeymap(keymap: string, shouldSave = true) {
  currentKeymap.value = keymap
  disposeVimMode()
  if (keymap === 'vim' && editor) {
    nextTick(() => {
      vimMode = initVimMode(editor!, vimStatusRef.value)
    })
  }
  if (shouldSave) {
    saveLocalConfig()
  }
}

function changeFontSize(offset: number) {
  const nextFontSize = Math.min(24, Math.max(12, fontSize.value + offset))
  fontSize.value = nextFontSize
  editor?.updateOptions({ fontSize: nextFontSize })
  saveLocalConfig()
}

function toggleWordWrap() {
  wordWrap.value = !wordWrap.value
  editor?.updateOptions({ wordWrap: wordWrap.value ? 'on' : 'off' })
  saveLocalConfig()
}

function formatDocument() {
  editor?.getAction('editor.action.formatDocument')?.run()
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

function focus() {
  editor?.focus()
}

function getValue(): string {
  return editor ? editor.getValue() : ''
}

function setValue(value: string) {
  editor?.setValue(value || '')
}

watch(
  () => props.value,
  (value) => {
    if (!editor || editor.getValue() === value) {
      return
    }
    isChangingValue = true
    editor.setValue(value || '')
    isChangingValue = false
  }
)

watch(
  () => props.language,
  (value) => {
    if (!value || value === currentLanguage.value) {
      return
    }
    changeLanguage(value)
  }
)

watch(
  () => props.readOnly,
  (value) => {
    editor?.updateOptions({ readOnly: value })
  }
)

watch(
  () => props.height,
  () => layoutEditor()
)

watch(isFullscreen, () => layoutEditor())

onMounted(initEditor)

onBeforeUnmount(() => {
  disposeVimMode()
  editor?.dispose()
  model?.dispose()
})

defineExpose({ focus, getValue, setValue })
</script>

<template>
  <div :class="['monaco-editor', { 'monaco-editor_fullscreen': isFullscreen }]">
    <div class="monaco-editor-toolbar">
      <div class="monaco-editor-toolbar-left">
        <a-select
          size="small"
          :value="currentKeymap"
          class="monaco-editor-select"
          @change="changeKeymap"
        >
          <a-select-option v-for="item in keymapOptions" :key="item.value" :value="item.value">
            {{ item.label }}
          </a-select-option>
        </a-select>
        <a-select
          size="small"
          :value="currentTheme"
          class="monaco-editor-select"
          @change="changeTheme"
        >
          <a-select-option v-for="item in themeOptions" :key="item.value" :value="item.value">
            {{ item.label }}
          </a-select-option>
        </a-select>
      </div>
      <div class="monaco-editor-toolbar-right">
        <a-tooltip :title="t('editorDecreaseFont')">
          <a-button size="small" @click="changeFontSize(-1)">
            <template #icon><MinusOutlined /></template>
          </a-button>
        </a-tooltip>
        <span class="monaco-editor-font-size">{{ fontSize }}</span>
        <a-tooltip :title="t('editorIncreaseFont')">
          <a-button size="small" @click="changeFontSize(1)">
            <template #icon><PlusOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-tooltip :title="t('editorWordWrap')">
          <a-button
            size="small"
            :type="wordWrap ? 'primary' : 'default'"
            @click="toggleWordWrap"
          >
            <template #icon><SwapOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-tooltip :title="t('editorFormat')">
          <a-button size="small" @click="formatDocument">
            <template #icon><CodeOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-tooltip :title="isFullscreen ? t('editorExitFullscreen') : t('editorFullscreen')">
          <a-button size="small" @click="toggleFullscreen">
            <template #icon>
              <FullscreenExitOutlined v-if="isFullscreen" />
              <FullscreenOutlined v-else />
            </template>
          </a-button>
        </a-tooltip>
      </div>
    </div>
    <div ref="editorRef" class="monaco-editor-main" :style="{ height: editorHeight }"></div>
    <div v-show="currentKeymap === 'vim'" ref="vimStatusRef" class="monaco-editor-vim-status"></div>
  </div>
</template>

<style scoped>
.monaco-editor {
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: #ffffff;
  overflow: hidden;
}
.monaco-editor_fullscreen {
  position: fixed;
  z-index: 2000;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  border-radius: 0;
}
.monaco-editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px;
  border-bottom: 1px solid #d9d9d9;
  background: #f7f8fa;
  overflow: auto;
}
.monaco-editor-toolbar-left,
.monaco-editor-toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.monaco-editor-select {
  width: 116px;
}
.monaco-editor-font-size {
  min-width: 28px;
  color: #8c8c8c;
  text-align: center;
  font-size: 12px;
}
.monaco-editor-main {
  width: 100%;
}
.monaco-editor-vim-status {
  min-height: 24px;
  padding: 3px 8px;
  border-top: 1px solid #d9d9d9;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: Menlo, Monaco, Consolas, 'Courier New', monospace;
  font-size: 12px;
}
</style>
