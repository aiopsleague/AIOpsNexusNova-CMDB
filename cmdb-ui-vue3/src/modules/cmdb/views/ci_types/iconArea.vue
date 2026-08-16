<script setup lang="ts">
import { ref } from 'vue'
import CustomIconSelect from '@/components/CustomIconSelect/index.vue'

interface IconValue {
  name?: string
  color?: string
  id?: string | number
  url?: string
}

const customIcon = ref<IconValue>({ name: '', color: '' })

function getIcon(): IconValue | undefined {
  if (customIcon.value.name) {
    return customIcon.value
  }
  return undefined
}

function setIcon(icon: IconValue | undefined) {
  if (icon && icon.name) {
    customIcon.value = { ...icon }
  } else {
    customIcon.value = { name: '', color: '' }
  }
}

defineExpose({ getIcon, setIcon })
</script>

<template>
  <div class="icon-area">
    <div class="icon-area-item">
      <span :style="{ marginRight: '15px' }"></span>
      <CustomIconSelect :value="customIcon" @change="(v) => (customIcon = v)" />
    </div>
  </div>
</template>

<style lang="less" scoped>
.icon-area {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  .icon-area-item {
    display: inline-flex;
    justify-content: center;
    align-items: center;
    > span {
      font-size: 10px;
    }
  }
}
</style>
