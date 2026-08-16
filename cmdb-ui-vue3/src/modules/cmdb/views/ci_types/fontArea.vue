<script setup lang="ts">
import { reactive } from 'vue'
import { BoldOutlined, ItalicOutlined, UnderlineOutlined, FontColorsOutlined } from '@ant-design/icons-vue'

const props = withDefaults(defineProps<{ fontColorDisabled?: boolean }>(), { fontColorDisabled: false })

interface FontOptions {
  color?: string
  fontWeight?: string
  textDecoration?: string
  fontStyle?: string
  [key: string]: unknown
}

const DEFAULT_FONT_OPTIONS: FontOptions = {
  color: '#606266',
  fontWeight: 'initial',
  textDecoration: 'initial',
  fontStyle: 'initial',
}

const fontOptions = reactive<FontOptions>({ ...DEFAULT_FONT_OPTIONS })

function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function isEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

function changeFontStyle(key: keyof FontOptions, value: string) {
  fontOptions[key] = fontOptions[key] === value ? 'initial' : value
}

function getData(): FontOptions | undefined {
  if (isEqual(fontOptions, DEFAULT_FONT_OPTIONS)) {
    return undefined
  }
  const result = cloneDeep(fontOptions)
  if (props.fontColorDisabled) {
    delete result.color
  }
  return result
}

function setData(data: { fontOptions?: FontOptions }) {
  Object.assign(fontOptions, DEFAULT_FONT_OPTIONS, data?.fontOptions || {})
}

defineExpose({ getData, setData })
</script>

<template>
  <div class="attributes-font">
    <div
      class="attributes-font-icon"
      :class="{ 'attributes-font-icon-selected': fontOptions.fontWeight === 'bold' }"
      @click="changeFontStyle('fontWeight', 'bold')"
    >
      <BoldOutlined />
    </div>
    <div
      class="attributes-font-icon"
      :class="{ 'attributes-font-icon-selected': fontOptions.fontStyle === 'italic' }"
      @click="changeFontStyle('fontStyle', 'italic')"
    >
      <ItalicOutlined />
    </div>
    <div
      class="attributes-font-icon"
      :class="{ 'attributes-font-icon-selected': fontOptions.textDecoration === 'underline' }"
      @click="changeFontStyle('textDecoration', 'underline')"
    >
      <UnderlineOutlined />
    </div>
    <div :style="{ width: '100px', marginLeft: '10px', display: 'inline-flex', alignItems: 'center' }">
      <FontColorsOutlined />
      <input v-model="fontOptions.color" type="color" :disabled="fontColorDisabled" />
    </div>
  </div>
</template>

<style lang="less" scoped>
.attributes-font {
  display: flex;
  align-items: center;
  height: 40px;
  .attributes-font-icon {
    cursor: pointer;
    display: inline-block;
    width: 30px;
    height: 30px;
    position: relative;
    margin: 0 5px;
    border: 1px solid #fff;
    &:hover {
      background-color: #eeeeee;
      border-color: #606266;
    }
    > i {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
    }
  }
  .attributes-font-icon-selected {
    background-color: #eeeeee;
  }
}
</style>
