<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const props = withDefaults(
  defineProps<{
    initColor?: string
    colorFormat?: 'hex' | 'rgb'
  }>(),
  { initColor: '#f00', colorFormat: 'hex' }
)

const emit = defineEmits<{ (e: 'changColorPicker', color: string): void }>()
const { t } = useI18n()

interface ColorConfig {
  h: number
  s: number
  v: number
  alpha: number
  value: string
  basicColor: string
}

const colorConfig = reactive<ColorConfig>({ h: 360, s: 100, v: 100, alpha: 1, value: '', basicColor: '' })
const colorBar = reactive({ top: 0, height: 0 })
const colorPannel = reactive({ top: 0, left: 300, backgroundColor: '#f00', height: 0, width: 0 })
const realShowColor = ref('#f00')

const colorPannelEl = ref<HTMLElement | null>(null)
const colorBarEl = ref<HTMLElement | null>(null)

interface RGB {
  r: number
  g: number
  b: number
}

interface HSV {
  h: number
  s: number
  v: number
}

function getRGB(rgbStr: string): RGB {
  const matchArr = rgbStr.match(/\(.+?\)/g)![0].match(/\w+/g)!
  return { r: parseInt(matchArr[0]), g: parseInt(matchArr[1]), b: parseInt(matchArr[2]) }
}

function zeroFill(val: string): string {
  return val.length > 1 ? val : '0' + val
}

function hexToRGB(hexStr: string): string {
  let hexArr: string[]
  if (hexStr.length === 4) {
    const arr = hexStr.match(/\w{1}/g)!
    hexArr = [arr[0] + arr[0], arr[1] + arr[1], arr[2] + arr[2]]
  } else {
    hexArr = hexStr.match(/\w{2}/g)!
  }
  return `rgb(${parseInt(hexArr[0], 16)},${parseInt(hexArr[1], 16)},${parseInt(hexArr[2], 16)})`
}

function rgbToHex(rgbStr: string): string {
  const { r, g, b } = getRGB(rgbStr)
  return `#${zeroFill(r.toString(16))}${zeroFill(g.toString(16))}${zeroFill(b.toString(16))}`
}

function hueToRGB(h: number): string {
  if (h === 360) {
    h = 0
  }
  const doHandle = (num: number) => {
    if (num > 255) {
      return 255
    } else if (num < 0) {
      return 0
    }
    return Math.round(num)
  }

  const hueRGB = (h / 60) * 255
  const r = doHandle(Math.abs(hueRGB - 765) - 255)
  const g = doHandle(510 - Math.abs(hueRGB - 510))
  const b = doHandle(510 - Math.abs(hueRGB - 1020))
  return `rgb(${r},${g},${b})`
}

function hsvToRGB(h: number, s: number, v: number): string {
  s = s / 100
  v = v / 100
  let r = 0
  let g = 0
  let b = 0
  const i = Math.floor(h / 60)
  const f = h / 60 - i
  const p = v * (1 - s)
  const q = v * (1 - f * s)
  const t = v * (1 - (1 - f) * s)
  switch (i) {
    case 0:
      r = v
      g = t
      b = p
      break
    case 1:
      r = q
      g = v
      b = p
      break
    case 2:
      r = p
      g = v
      b = t
      break
    case 3:
      r = p
      g = q
      b = v
      break
    case 4:
      r = t
      g = p
      b = v
      break
    case 5:
      r = v
      g = p
      b = q
      break
  }
  return `rgb(${Math.round(r * 255)},${Math.round(g * 255)},${Math.round(b * 255)})`
}

function rgbToHSV(rgbStr: string): HSV {
  let { r, g, b } = getRGB(rgbStr)
  r = parseFloat(parseFloat(String(r / 255)).toFixed(4))
  g = parseFloat(parseFloat(String(g / 255)).toFixed(4))
  b = parseFloat(parseFloat(String(b / 255)).toFixed(4))
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h: number
  const v = max
  const d = max - min
  const s = max === 0 ? 0 : d / max

  if (max === min) {
    h = 0
  } else {
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0)
        break
      case g:
        h = (b - r) / d + 2
        break
      case b:
        h = (r - g) / d + 4
        break
      default:
        h = 0
    }
    h /= 6
  }
  return { h: h * 360, s: s * 100, v: v * 100 }
}

function hsvToPosition(s: number, v: number, width: number, height: number) {
  colorPannel.top = height - (v * height) / 100
  colorPannel.left = (s * width) / 100
}

function hueToPosition(h: number, height: number) {
  colorBar.top = (h * height) / 360
}

function colorFormatTransform() {
  if (props.colorFormat === 'hex') {
    colorConfig.basicColor = hsvToRGB(colorConfig.h, colorConfig.s, colorConfig.v)
    colorConfig.value = rgbToHex(colorConfig.basicColor)
  }
  if (props.colorFormat === 'rgb') {
    colorConfig.basicColor = hsvToRGB(colorConfig.h, colorConfig.s, colorConfig.v)
    colorConfig.value = colorConfig.basicColor
  }
}

function initShowColor(color: string) {
  let hsvObj: HSV | undefined
  if (color.indexOf('#') !== -1) {
    const initRgb = hexToRGB(color)
    hsvObj = rgbToHSV(initRgb)
  } else if (color.indexOf('rgb') !== -1) {
    hsvObj = rgbToHSV(color)
  } else {
    throw new Error(t('cmdb.components.colorPickerError'))
  }

  if (hsvObj) {
    colorConfig.h = hsvObj.h
    colorConfig.s = hsvObj.s
    colorConfig.v = hsvObj.v
  }
  colorBar.height = colorBarEl.value?.getBoundingClientRect().height ?? 0
  colorPannel.height = colorPannelEl.value?.getBoundingClientRect().height ?? 0
  colorPannel.width = colorPannelEl.value?.getBoundingClientRect().width ?? 0
  colorPannel.backgroundColor = hueToRGB(colorConfig.h)
  hsvToPosition(colorConfig.s, colorConfig.v, colorPannel.width, colorPannel.height)
  hueToPosition(colorConfig.h, colorBar.height)
  colorFormatTransform()
  realShowColor.value = colorConfig.value || color
}

function applyPannel(e: MouseEvent) {
  const elemInfo = colorPannelEl.value!.getBoundingClientRect()
  colorPannel.top = e.clientY - elemInfo.top
  colorPannel.left = e.clientX - elemInfo.left
  colorPannel.left = Math.max(0, colorPannel.left)
  colorPannel.left = Math.min(colorPannel.left, elemInfo.width)
  colorPannel.top = Math.max(0, colorPannel.top)
  colorPannel.top = Math.min(colorPannel.top, elemInfo.height)

  colorConfig.s = (parseInt(String(colorPannel.left)) / elemInfo.width) * 100
  colorConfig.v = (1 - parseInt(String(colorPannel.top)) / elemInfo.height) * 100
  colorFormatTransform()
  realShowColor.value = colorConfig.value
}

function pannelMouseClick(e: MouseEvent) {
  applyPannel(e)
  emit('changColorPicker', realShowColor.value)
}

function pannelMouseHandler(e: MouseEvent) {
  if (e.type === 'mousedown') {
    document.body.addEventListener('mousemove', pannelMouseHandler)
    document.body.addEventListener('mouseup', pannelMouseHandler)
  } else if (e.type === 'mousemove') {
    applyPannel(e)
  } else if (e.type === 'mouseup') {
    document.body.removeEventListener('mousemove', pannelMouseHandler)
    document.body.removeEventListener('mouseup', pannelMouseHandler)
  }
  emit('changColorPicker', realShowColor.value)
}

function thumbMouseHandler(e: MouseEvent) {
  if (e.type === 'mousedown') {
    document.body.addEventListener('mousemove', thumbMouseHandler)
    document.body.addEventListener('mouseup', thumbMouseHandler)
  } else if (e.type === 'mousemove') {
    const elemInfo = colorBarEl.value!.getBoundingClientRect()
    colorBar.top = e.clientY - elemInfo.top
    colorBar.top = Math.max(0, colorBar.top)
    colorBar.top = Math.min(colorBar.top, elemInfo.height)
    colorConfig.h = ((parseInt(String(colorBar.top)) / elemInfo.height) * 360 * 100) / 100
    if (colorConfig.h === 360) {
      colorConfig.h = 0
    }
    colorPannel.backgroundColor = hueToRGB(colorConfig.h)
    colorFormatTransform()
    realShowColor.value = colorConfig.value
  } else if (e.type === 'mouseup') {
    document.body.removeEventListener('mousemove', thumbMouseHandler)
    document.body.removeEventListener('mouseup', thumbMouseHandler)
  }
  emit('changColorPicker', realShowColor.value)
}

function changeInputColor(e: KeyboardEvent) {
  const value = (e.target as HTMLInputElement).value
  initShowColor(value)
  emit('changColorPicker', value)
}

onMounted(() => initShowColor(props.initColor))
</script>

<template>
  <div class="color-picker">
    <div class="color-dropdown">
      <div class="color-dropdown-picker">
        <div
          ref="colorPannelEl"
          class="color-pannel-box"
          :style="{ backgroundColor: colorPannel.backgroundColor }"
          @click="pannelMouseClick"
        >
          <div
            class="color-select-circle"
            :style="{ top: colorPannel.top + 'px', left: colorPannel.left + 'px' }"
            @mousedown="pannelMouseHandler"
          ></div>
        </div>
        <div ref="colorBarEl" class="color-slider-box">
          <div class="color-slider"></div>
          <div class="color-thumb" :style="{ top: colorBar.top + 'px' }" @mousedown="thumbMouseHandler"></div>
        </div>
      </div>
      <div class="color-input">
        <a-input
          v-model="realShowColor"
          size="small"
          class="color-input-box"
          style="width:130px"
          @press-enter="changeInputColor"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.color-picker {
  width: 150px;
  margin: auto;
  height: 100px;
  margin-top: 0px;
  position: relative;
}
.color-dropdown {
  margin: auto;
  width: 140px;
  height: 92px;
  position: absolute;
  top: 0;
  left: 0;
  overflow: hidden;
}
.color-dropdown-picker {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  justify-content: space-around;
}
.color-pannel-box {
  position: relative;
  width: 110px;
  height: 64px;
  background: linear-gradient(to top, #000, transparent), linear-gradient(to right, #fff, transparent);
}
.color-select-circle {
  position: absolute;
  transform: translate(-4px, -4px);
  border: 1px solid #fff;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.color-slider-box {
  cursor: pointer;
  width: 10px;
  position: relative;
}
.color-slider {
  background: linear-gradient(180deg, #f00, #ff0 17%, #0f0 33%, #0ff 50%, #00f 67%, #f0f 83%, #f00);
  width: 10px;
  height: 64px;
}
.color-thumb {
  width: 10px;
  height: 7px;
  position: absolute;
  left: 0;
  transform: translate(0, -3px);
  border-radius: 2px;
  background-color: rgb(10, 10, 10);
  border: 3px solid #fff;
  margin-left: 0;
}
.color-input {
  width: 100%;
  margin: auto;
  display: flex;
  padding: 3px 6px;
  justify-content: space-between;
}
.color-input button {
  color: #000;
}
.color-input-box {
  color: #000;
  border: 1px solid rgba(0, 0, 0, 0.1);
}
</style>
