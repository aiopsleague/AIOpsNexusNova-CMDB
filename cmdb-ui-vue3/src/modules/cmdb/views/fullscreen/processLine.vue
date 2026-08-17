<script setup lang="ts">
withDefaults(
  defineProps<{
    total?: number
    number?: number
    name?: string
    type?: string
  }>(),
  {
    total: 0,
    number: 0,
    name: '',
    type: 'application',
  }
)
</script>

<template>
  <div class="line-wrapper">
    <span class="name">{{ name }}</span>
    <div class="default-process">
      <div class="real-process" :style="{ '--custom-width': `${(number * 100) / total}%` }">
        <!-- TODO: restore process-line assets (fullscreen images not present in the repo) -->
        <img class="image_dot" :src="`../../assets/fullscreen/process_line_dot-${type}.png`" />
        <img class="image_funnel" :src="`../../assets/fullscreen/process_line_funnel-${type}.png`" />
      </div>
    </div>
    <span class="number">
      <span>{{ number }}</span>
      <span>/{{ total }}</span>
    </span>
  </div>
</template>

<style lang="less">
@import './index.less';
</style>
