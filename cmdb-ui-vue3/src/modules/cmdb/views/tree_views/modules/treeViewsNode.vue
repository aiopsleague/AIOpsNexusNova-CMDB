<script setup lang="ts">
import { computed, ref } from 'vue'
import { CaretRightOutlined, CaretDownOutlined } from '@ant-design/icons-vue'

const props = withDefaults(
  defineProps<{
    title?: string | number | boolean
    treeKey?: string
    levels?: any[]
    isLeaf?: boolean
    childLength?: number
  }>(),
  {
    title: '',
    treeKey: '',
    levels: () => [],
    isLeaf: false,
    childLength: 0,
  }
)

const emit = defineEmits<{ (e: 'onNodeClick', treeKey: string): void }>()

const switchIcon = ref<'caret-right' | 'caret-down'>('caret-right')

const iconComponent = computed(() =>
  switchIcon.value === 'caret-right' ? CaretRightOutlined : CaretDownOutlined
)

function clickNode() {
  emit('onNodeClick', props.treeKey)
  switchIcon.value = switchIcon.value === 'caret-right' ? 'caret-down' : 'caret-right'
}
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <div @click="clickNode" class="tree-views-node">
    <component :is="iconComponent" v-if="childLength && !isLeaf"></component>
    <div v-else></div>
    <div class="tree-views-node-content">
      <span>{{ title }}</span>
      <span>{{ childLength }}</span>
    </div>
  </div>
</template>

<style lang="less" scoped>
.tree-views-node {
  width: 100%;
  display: inline-flex;
  justify-content: space-between;
  align-items: center;
  > div:first-child {
    width: 10px;
  }
  i {
    font-size: 10px;
    color: @text-color_5;
  }
  .tree-views-node-content {
    flex: 1;
    display: inline-flex;
    align-items: center;
    justify-content: space-between;
    margin-left: 5px;
    width: calc(100% - 10px);
    > span:first-child {
      width: calc(100% - 30px);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: @text-color_1;
    }
    > span:last-child {
      color: @text-color_4;
    }
  }
}
</style>
