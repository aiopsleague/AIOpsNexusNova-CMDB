<script setup lang="ts">
import { computed } from 'vue'
import { DownOutlined, LeftOutlined, RightOutlined, UpOutlined } from '@ant-design/icons-vue'
import { COLOR_PRIMARY } from '@/theme/tokens'

const props = withDefaults(
  defineProps<{
    closable?: boolean
    placement?: 'right' | 'left' | 'top' | 'bottom'
    hasTitle?: boolean
    hasFooter?: boolean
    title?: string
    open?: boolean
  }>(),
  { closable: true, placement: 'right', hasTitle: true, hasFooter: true, title: '', open: false }
)

const emit = defineEmits<{ (e: 'update:open', v: boolean): void; (e: 'close'): void }>()

const closeIcon = computed(() => {
  if (props.placement === 'top') return UpOutlined
  if (props.placement === 'bottom') return DownOutlined
  if (props.placement === 'left') return LeftOutlined
  return RightOutlined
})

const bodyMaxHeight = computed(() => {
  const titleHeight = props.hasTitle ? 55 : 0
  const footerHeight = props.hasFooter ? 53 : 0
  return `calc(100vh - ${titleHeight + footerHeight}px)`
})

function onClose() {
  emit('update:open', false)
  emit('close')
}
</script>

<template>
  <a-drawer
    v-bind="$attrs"
    :open="open"
    :placement="placement"
    :closable="false"
    :keyboard="false"
    :body-style="{ maxHeight: bodyMaxHeight, overflow: 'auto' }"
    @close="onClose"
  >
    <div v-if="closable" :class="`custom-drawer-close custom-drawer-${placement}`" @click="onClose">
      <component :is="closeIcon" />
    </div>
    <template v-if="hasTitle" #title>
      <slot name="title">{{ title }}</slot>
    </template>
    <slot />
  </a-drawer>
</template>

<style scoped>
.custom-drawer-close {
  position: absolute;
  cursor: pointer;
  background: v-bind(COLOR_PRIMARY);
  color: white;
  text-align: center;
  transition: all 0.3s;
  z-index: 1;
}
.custom-drawer-close:hover {
  background: #597ef7;
}
.custom-drawer-right,
.custom-drawer-left {
  width: 14px;
  height: 50px;
  top: 50%;
  transform: translateY(-50%);
  line-height: 50px;
}
.custom-drawer-left {
  right: 0;
  border-top-left-radius: 4px;
  border-bottom-left-radius: 4px;
}
.custom-drawer-right {
  left: 0;
  border-top-right-radius: 4px;
  border-bottom-right-radius: 4px;
}
.custom-drawer-top,
.custom-drawer-bottom {
  width: 50px;
  height: 14px;
  left: 50%;
  transform: translateX(-50%);
  line-height: 14px;
}
.custom-drawer-top {
  bottom: 0;
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
}
.custom-drawer-bottom {
  top: 0;
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
}
</style>
