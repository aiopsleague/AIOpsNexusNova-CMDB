<script setup lang="ts">
import { computed } from 'vue'
import { AppstoreOutlined } from '@ant-design/icons-vue'

/**
 * CI type icon.
 *
 * The `icon` prop is the legacy `name$$color$$id$$url` string produced by the
 * custom icon selector. When a custom image is uploaded (id + url present) it
 * is rendered as an `<img>`; otherwise a generic Ant Design icon is shown.
 * The Vue 2 iconfont (`ops-icon`) is not available in the Vue 3 shell, so the
 * glyph-only case falls back to a generic icon with the configured color.
 */
const props = withDefaults(
  defineProps<{
    icon?: string
    // When no icon is provided, the first character of `title` is shown.
    title?: string
    size?: string | number
  }>(),
  {
    icon: '',
    title: '',
    size: '12',
  }
)

const iconParts = computed(() => (props.icon || '').split('$$'))
const iconColor = computed(() => iconParts.value[1] || '')
const iconImgSrc = computed(() =>
  iconParts.value[2] && iconParts.value[3] ? `/api/common-setting/v1/file/${iconParts.value[3]}` : ''
)
const letter = computed(() => (props.title ? props.title.charAt(0).toUpperCase() : ''))
</script>

<template>
  <div
    v-if="icon || title"
    class="ci-icon"
    :style="{
      '--size': `${size}px`,
    }"
  >
    <img v-if="iconImgSrc" :src="iconImgSrc" />
    <AppstoreOutlined v-else-if="icon" :style="{ color: iconColor }" />
    <span v-else class="ci-icon-letter">
      <span>{{ letter }}</span>
    </span>
  </div>
</template>

<style lang="less" scoped>
.ci-icon {
  font-size: var(--size);
  width: var(--size);
  height: var(--size);
  display: flex;
  align-items: center;
  justify-content: center;

  & > img {
    width: var(--size);
    height: var(--size);
  }

  &-letter {
    background-color: #ffffff;
    color: #2f54eb;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 2px;
    box-shadow: 0px 1px 2px rgba(47, 84, 235, 0.2);

    & > span {
      transform-origin: center;
      transform: scale(0.7);
    }
  }
}
</style>
