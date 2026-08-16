<script setup lang="ts">
interface TransferItem {
  [key: string]: unknown
}

const props = defineProps<{
  dataSource: TransferItem[]
  targetKeys: (string | number)[]
}>()

function leftToRight(
  leftList: HTMLElement[],
  dataSource: TransferItem[],
  targetKeys: (string | number)[],
  sourceKey: string,
  targetKey: string
) {
  leftList.forEach((el) => {
    el.onclick = () => {}
    el.ondblclick = (e: MouseEvent) => {
      const text = (e.target as HTMLElement).innerText
      dataSource.forEach((item) => {
        if (item[sourceKey] === text) targetKeys.push(item[targetKey] as string | number)
      })
    }
  })
}

function rightToLeft(
  rightList: HTMLElement[],
  dataSource: TransferItem[],
  targetKeys: (string | number)[],
  sourceKey: string,
  targetKey: string
) {
  rightList.forEach((el) => {
    el.ondblclick = (e: MouseEvent) => {
      const text = (e.target as HTMLElement).innerText
      dataSource.forEach((item) => {
        if (item[sourceKey] === text) {
          const idx = targetKeys.findIndex((k) => k === item[targetKey])
          if (idx >= 0) targetKeys.splice(idx, 1)
        }
      })
    }
  })
}

function dbClick(
  _sourceSelectedKeys: (string | number)[],
  _targetSelectedKeys: (string | number)[],
  sourceKey: string,
  targetKey: string
) {
  window.setTimeout(() => {
    const element = document.getElementsByClassName('ant-transfer-list-content')
    if (props.dataSource.length !== props.targetKeys.length) {
      const leftList = Array.from(element[0].children) as HTMLElement[]
      const rightList = element[1] ? (Array.from(element[1].children) as HTMLElement[]) : []
      leftToRight(leftList, props.dataSource, props.targetKeys, sourceKey, targetKey)
      rightToLeft(rightList, props.dataSource, props.targetKeys, sourceKey, targetKey)
    }
    if (props.targetKeys.length && props.targetKeys.length === props.dataSource.length) {
      const rightList = Array.from(element[0].children) as HTMLElement[]
      rightToLeft(rightList, props.dataSource, props.targetKeys, sourceKey, targetKey)
    }
  }, 100)
}

defineExpose({ dbClick, leftToRight, rightToLeft })
</script>

<template>
  <a-transfer v-bind="$attrs" :data-source="dataSource" :target-keys="targetKeys" />
</template>
