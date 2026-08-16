<script setup lang="ts">
import { onBeforeMount, onBeforeUnmount, ref, shallowRef } from 'vue'
import { useI18n } from 'vue-i18n'
import '@wangeditor/editor/dist/css/style.css'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import { i18nChangeLanguage, type IDomEditor, type IEditorConfig, type IToolbarConfig } from '@wangeditor/editor'
import { COLOR_PRIMARY } from '@/theme/tokens'

 
const props = withDefaults(
  defineProps<{
    attrList?: Array<Record<string, any>>
    needOld?: boolean
    readOnly?: boolean
  }>(),
  { attrList: () => [], needOld: false, readOnly: false }
)
 

const { t, locale } = useI18n()

const editorRef = shallowRef<IDomEditor>()
const valueHtml = ref('<p><br></p>')

const toolbarConfig: Partial<IToolbarConfig> = {
  excludeKeys: [
    'emotion',
    'group-image',
    'group-video',
    'insertTable',
    'codeBlock',
    'blockquote',
    'fullScreen',
  ],
}

const editorConfig: Partial<IEditorConfig> = {
  placeholder: t('cmdb.components.noticeContentTips'),
  readOnly: props.readOnly,
}

function handleCreated(editor: IDomEditor) {
  editorRef.value = editor
}

function getContent() {
  const editor = editorRef.value
  if (!editor) {
    return { body_html: '', body: '' }
  }
  const html = editor.getHtml()
  const body = html.replace(
    /<span data-w-e-type="attachment" (data-w-e-is-void|data-w-e-is-void="") (data-w-e-is-inline|data-w-e-is-inline="").*?<\/span>/gm,
    (value) => {
      const match = value.match(/(?<=data-attachment(V|v)alue=").*?(?=")/)
      return match ? `{{${match[0]}}}` : value
    }
  )
  return { body_html: html, body }
}

function setContent(html: string) {
  const editor = editorRef.value
  if (editor) {
    editor.setHtml(html)
  }
}

function dblclickSidebar(value: string, label: string) {
  const editor = editorRef.value
  if (!editor || props.readOnly) {
    return
  }
  editor.restoreSelection()
  const node = {
    type: 'attachment',
    attachmentValue: value,
    attachmentLabel: `${label}`,
    children: [{ text: '' }],
  }
  editor.insertNode(node)
}

function destroy() {
  const editor = editorRef.value
  if (!editor) {
    return
  }
  editor.destroy()
  editorRef.value = undefined
}

onBeforeMount(() => {
  i18nChangeLanguage(locale.value === 'zh' ? 'zh-CN' : 'en')
})

onBeforeUnmount(destroy)

defineExpose({ getContent, setContent, dblclickSidebar, destroy })
</script>

<template>
  <div class="notice-content">
    <div class="notice-content-main">
      <Toolbar :editor="editorRef" :default-config="toolbarConfig" mode="default" />
      <Editor
        v-model="valueHtml"
        class="notice-content-editor"
        :default-config="editorConfig"
        mode="simple"
        @on-created="handleCreated"
      />
      <div class="notice-content-sidebar">
        <template v-if="needOld">
          <div class="notice-content-sidebar-divider">{{ t('cmdb.components.beforeChange') }}</div>
          <div
            v-for="attr in attrList"
            :key="`old_${attr.id}`"
            class="notice-content-sidebar-item"
            :title="attr.alias || attr.name"
            @dblclick="dblclickSidebar(`old_${attr.name}`, attr.alias || attr.name)"
          >
            {{ attr.alias || attr.name }}
          </div>
          <div class="notice-content-sidebar-divider">{{ t('cmdb.components.afterChange') }}</div>
        </template>
        <div
          v-for="attr in attrList"
          :key="attr.id"
          class="notice-content-sidebar-item"
          :title="attr.alias || attr.name"
          @dblclick="dblclickSidebar(attr.name, attr.alias || attr.name)"
        >
          {{ attr.alias || attr.name }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notice-content {
  width: 100%;
}
.notice-content-main {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  position: relative;
}
.notice-content-editor {
  height: 300px;
  width: 75%;
  border: 1px solid #e4e7ed;
  border-top: none;
  overflow: hidden;
}
.notice-content-sidebar {
  width: 25%;
  position: absolute;
  height: 300px;
  bottom: 0;
  left: 0;
  border: 1px solid #e4e7ed;
  border-top: none;
  border-right: none;
  overflow: auto;
}
.notice-content-sidebar-divider {
  position: sticky;
  top: 0;
  margin: 0;
  font-size: 12px;
  color: #afafaf;
  background-color: #fff;
  line-height: 20px;
  padding-left: 12px;
}
.notice-content-sidebar-divider::before,
.notice-content-sidebar-divider::after {
  content: '';
  position: absolute;
  border-top: 1px solid #d1d1d1;
  top: 50%;
  transition: translateY(-50%);
}
.notice-content-sidebar-divider::before {
  left: 3px;
  width: 5px;
}
.notice-content-sidebar-divider::after {
  right: 3px;
  width: 78px;
}
.notice-content-sidebar-item:first-child {
  margin-top: 10px;
}
.notice-content-sidebar-item {
  line-height: 1.5;
  padding: 4px 12px;
  cursor: pointer;
  user-select: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notice-content-sidebar-item:hover {
  background-color: #f0f5ff;
  color: v-bind(COLOR_PRIMARY);
}
</style>

<style>
.notice-content .w-e-bar {
  background-color: #f0f5ff;
}
.notice-content .w-e-text-placeholder {
  line-height: 1.5;
}
</style>
