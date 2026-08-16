<script setup lang="ts">
import { ref } from 'vue'
import { FontColorsOutlined, FontSizeOutlined } from '@ant-design/icons-vue'

const color = ref('#2f2f2f')
const fontSize = ref(50)

function getConfig(): { color: string; fontSize: string } {
  return {
    color: color.value || '#2f2f2f',
    fontSize: `${fontSize.value || 50}px`,
  }
}

function setConfig(config: { color?: string; fontSize?: string } = {}) {
  const { color: c = '#2f2f2f', fontSize: fs = '50px' } = config
  color.value = c
  fontSize.value = Number(fs.split('px')[0])
}

defineExpose({ getConfig, setConfig })
</script>

<template>
  <a-space>
    <a-input v-model:value="color" size="small" style="width: 100px" type="color">
      <template #addonBefore><FontColorsOutlined /></template>
    </a-input>
    <a-input v-model:value="fontSize" size="small">
      <template #addonBefore><FontSizeOutlined /></template>
      <template #addonAfter>px</template>
    </a-input>
  </a-space>
</template>

<style></style>
