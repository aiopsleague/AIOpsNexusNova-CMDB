<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { LeftOutlined, RightOutlined } from '@ant-design/icons-vue'

const props = withDefaults(
  defineProps<{
    direction?: 'row' | 'column'
    min?: number
    max?: number
    paneLengthPixel?: number
    triggerLength?: number
    appName?: string
    collapsable?: boolean
    triggerColor?: string
    calcBasedParent?: boolean
  }>(),
  {
    direction: 'row',
    min: 10,
    max: 90,
    paneLengthPixel: 220,
    triggerLength: 8,
    appName: 'viewer',
    collapsable: false,
    triggerColor: 'var(--ops-pane-trigger-bg, #f7f8fa)',
    calcBasedParent: false,
  }
)

const emit = defineEmits<{
  (e: 'update:paneLengthPixel', v: number): void
  (e: 'expand', v: boolean): void
}>()

const splitPaneRef = ref<HTMLElement | null>(null)
const twoRef = ref<HTMLElement | null>(null)

function readExpanded(): boolean {
  const raw = localStorage.getItem(`${props.appName}-isExpanded`)
  return raw ? JSON.parse(raw) : false
}

// Offset of the mouse relative to the trigger's top/left edge.
const triggerOffset = ref(0)
const isExpanded = ref(readExpanded())

const lengthType = computed<'width' | 'height'>(() => (props.direction === 'row' ? 'width' : 'height'))

const paneLengthPercent = computed(() => {
  const root = splitPaneRef.value
  const clientRectWidth = root && props.calcBasedParent ? root.clientWidth : document.documentElement.getBoundingClientRect().width
  return (props.paneLengthPixel / clientRectWidth) * 100
})

const paneLengthValue1 = computed(() => `calc(${paneLengthPercent.value}% - ${props.triggerLength / 2}px)`)
const paneLengthValue2 = computed(() => `calc(${100 - paneLengthPercent.value}% - ${props.triggerLength / 2}px)`)

function applyExpanded() {
  if (twoRef.value) {
    twoRef.value.style.display = isExpanded.value ? 'none' : ''
  }
}

function handleMouseDown(e: MouseEvent) {
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  const trigger = e.currentTarget as HTMLElement
  if (props.direction === 'row') {
    triggerOffset.value = e.pageX - trigger.getBoundingClientRect().left
  } else {
    triggerOffset.value = e.pageY - trigger.getBoundingClientRect().top
  }
}

function handleMouseMove(e: MouseEvent) {
  isExpanded.value = false
  emit('expand', isExpanded.value)
  const clientRect = splitPaneRef.value!.getBoundingClientRect()
  let paneLengthPixel = 0

  if (props.direction === 'row') {
    paneLengthPixel = e.pageX - clientRect.left - triggerOffset.value + props.triggerLength / 2
  } else {
    paneLengthPixel = e.pageY - clientRect.top - triggerOffset.value + props.triggerLength / 2
  }

  if (paneLengthPixel < props.min) {
    paneLengthPixel = props.min
  }
  if (paneLengthPixel > props.max) {
    paneLengthPixel = props.max
  }

  emit('update:paneLengthPixel', paneLengthPixel)
  localStorage.setItem(`${props.appName}-paneLengthPixel`, String(paneLengthPixel))
}

function handleMouseUp() {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}

function handleExpand() {
  isExpanded.value = !isExpanded.value
  emit('expand', isExpanded.value)
  localStorage.setItem(`${props.appName}-isExpanded`, String(isExpanded.value))
}

onMounted(() => {
  const stored = localStorage.getItem(`${props.appName}-paneLengthPixel`)
  if (stored) {
    emit('update:paneLengthPixel', Number(stored))
  }
  applyExpanded()
})

watch(isExpanded, applyExpanded)
</script>

<template>
  <div
    ref="splitPaneRef"
    class="split-pane"
    :class="`${direction} ${appName}`"
    :style="{ flexDirection: direction }"
  >
    <div class="pane pane-one" :style="{ [lengthType]: paneLengthValue1 }">
      <slot name="one"></slot>
    </div>

    <div class="spliter-wrap">
      <a-button v-show="collapsable" class="collapse-btn" @click="handleExpand">
        <template #icon>
          <LeftOutlined v-if="isExpanded" :style="{ color: '#7cb0fe' }" />
          <RightOutlined v-else :style="{ color: '#7cb0fe' }" />
        </template>
      </a-button>
      <div
        class="pane-trigger"
        :style="{ backgroundColor: triggerColor, width: `${triggerLength}px` }"
        @mousedown="handleMouseDown"
      ></div>
    </div>

    <div ref="twoRef" class="pane pane-two" :style="{ [lengthType]: paneLengthValue2 }">
      <slot name="two"></slot>
    </div>
  </div>
</template>

<style scoped>
.split-pane {
  height: 100%;
  display: flex;
}

.split-pane .pane-two {
  flex: 1;
}

.split-pane .pane-trigger {
  user-select: none;
}

.split-pane.row .pane-one {
  width: 20%;
  height: 100%;
}

.split-pane.column .pane {
  width: 100%;
}

.split-pane.row .pane-trigger {
  width: 8px;
  height: 100%;
  cursor: e-resize;
  background: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAQAAAAPCAYAAADDNm69AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAeSURBVBhXY/4PBMzMzA379u1rANFMDGhgGAswMAAAn6EH6K9ktYAAAAAASUVORK5CYII=')
    1px 50% no-repeat #f0f2f5;
}

.split-pane .collapse-btn {
  width: 25px;
  height: 70px;
  position: absolute;
  right: 8px;
  top: calc(50% - 35px);
  background-color: #f0f2f5;
  border-color: transparent;
  border-radius: 8px 0px 0px 8px;
}

.split-pane .spliter-wrap {
  position: relative;
}
</style>
