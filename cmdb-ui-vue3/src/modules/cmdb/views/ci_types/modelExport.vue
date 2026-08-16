<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { exportCITypeGroups } from '@/modules/cmdb/api/ciTypeGroup'

const props = withDefaults(
  defineProps<{
    visible?: boolean
    CITypeGroups?: any[]
  }>(),
  { visible: false, CITypeGroups: () => [] }
)

const emit = defineEmits<{ (e: 'cancel'): void }>()

const { t } = useI18n()

const formRef = ref()
const formModel = reactive({ name: 'cmdb_template' })
const formRules = {
  name: [{ required: true, message: t('cmdb.ciType.filenameInputTips') }],
}

const targetKeys = ref<string[]>([])
const btnLoading = ref(false)

function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

const transferDataSource = computed(() => {
  return props.CITypeGroups.reduce((acc: any[], group: any) => {
    const types = cloneDeep(group?.ci_types || [])
    types.forEach((item: any) => {
      item.key = `${group.id}-${item.id}`
      item.title = item?.alias || item?.name || t('cmdb.common.other')
    })
    return acc.concat(types)
  }, [])
})

const treeData = computed(() => {
  const groups = cloneDeep(props.CITypeGroups)
  let newTreeData = groups.map((item: any) => {
    const childrenKeys: string[] = []
    const children = (item.ci_types || []).map((child: any) => {
      const key = `${item.id}-${child.id}`
      const disabled = targetKeys.value.includes(key)
      childrenKeys.push(key)
      return {
        key,
        title: child?.alias || child?.name || t('cmdb.common.other'),
        disabled,
        children: [],
      }
    })
    return {
      key: String(item?.id),
      title: item?.name || t('cmdb.common.other'),
      children,
      childrenKeys,
      disabled: children.every((child: any) => child.disabled),
    }
  })
  newTreeData = newTreeData.filter((item) => item.children.length > 0)
  return newTreeData
})

function onChange(newTargetKeys: string[], direction: string) {
  const childKeys: string[] = []
  const merged = [...newTargetKeys]

  if (direction === 'right') {
    // When a parent group is selected, drop the parent and add its children instead.
    treeData.value.forEach((item: any) => {
      const parentIndex = merged.findIndex((key) => item.key === key)
      if (parentIndex !== -1) {
        merged.splice(parentIndex, 1)
        childKeys.push(...item.childrenKeys)
      }
    })
  }

  targetKeys.value = Array.from(new Set([...merged, ...childKeys]))
}

function onChecked(e: any, onItemSelectAll: (keys: string[]) => void, selectedKeys: string[]) {
  const eventKey = e.node.eventKey as string
  const preCheckedKeys = [...selectedKeys, ...targetKeys.value]
  const selected = preCheckedKeys.indexOf(eventKey) === -1
  const childrenKeys = treeData.value.find((item: any) => item.key === eventKey)?.childrenKeys || []

  // When clicking a child node, keep its parent group selection in sync.
  let next = [...selectedKeys]
  treeData.value.forEach((item: any) => {
    if (item.childrenKeys.includes(eventKey)) {
      if (selected && item.childrenKeys.every((childKey: string) => [eventKey, ...preCheckedKeys].includes(childKey))) {
        if (!next.includes(item.key)) {
          next.push(item.key)
        }
      } else if (!selected) {
        next = next.filter((key) => key !== item.key)
      }
    }
  })

  if (selected) {
    next = Array.from(new Set([...next, eventKey, ...childrenKeys]))
  } else {
    next = next.filter((key) => ![eventKey, ...childrenKeys].includes(key))
  }

  onItemSelectAll(next)
}

function handleCancel() {
  emit('cancel')
  formModel.name = 'cmdb_template'
  targetKeys.value = []
}

async function handleOK() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  if (!targetKeys.value.length || btnLoading.value) {
    return
  }
  btnLoading.value = true
  const hide = message.loading(t('cmdb.common.loading'), 0)

  try {
    const typeIds = getTypeIds(targetKeys.value)
    const res = await exportCITypeGroups({ type_ids: typeIds })
    console.log('exportCITypeGroups res', res)

    if (res) {
      const jsonStr = JSON.stringify(res)
      const blob = new Blob([jsonStr], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = formModel.name
      a.click()
      URL.revokeObjectURL(url)
    }
  } catch (error) {
    console.log('exportCITypeGroups fail', error)
  } finally {
    hide()
    btnLoading.value = false
  }
}

function getTypeIds(keys: string[]) {
  const typeIds = keys
    ?.map((key) => transferDataSource.value.find((node) => node?.key === key)?.id || '')
    .filter((id) => id)
  return typeIds?.join(',')
}
</script>

<template>
  <a-modal
    :open="visible"
    :title="t('cmdb.ciType.modelExport')"
    :width="560"
    @cancel="handleCancel"
    @ok="handleOK"
  >
    <a-form ref="formRef" :model="formModel" :rules="formRules" :label-col="{ span: 5 }" :wrapper-col="{ span: 19 }">
      <a-form-item :label="t('cmdb.ciType.filename')" name="name">
        <a-input v-model:value="formModel.name" />
      </a-form-item>
      <a-form-item :label="t('cmdb.ciType.selectModel')">
        <a-transfer
          class="model-export-transfer"
          :data-source="transferDataSource"
          :target-keys="targetKeys"
          :render="(item: any) => item.title"
          :titles="[t('cmdb.ciType.unselectModel'), t('cmdb.ciType.selectedModel')]"
          :list-style="{ width: '180px', height: '262px' }"
          @change="onChange"
        >
          <template #children="{ direction, selectedKeys, onItemSelectAll }">
            <a-tree
              v-if="direction === 'left'"
              block-node
              checkable
              :checked-keys="[...selectedKeys, ...targetKeys]"
              :tree-data="treeData"
              :check-strictly="false"
              @check="(_keys: any, e: any) => onChecked(e, onItemSelectAll, selectedKeys)"
              @select="(_keys: any, e: any) => onChecked(e, onItemSelectAll, selectedKeys)"
            />
          </template>
        </a-transfer>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<style lang="less" scoped>
.model-export-transfer {
  :deep(.ant-transfer-list) {
    .ant-transfer-list-body {
      overflow: auto;
    }

    &:first-child {
      .ant-transfer-list-header {
        .ant-transfer-list-header-selected {
          span:first-child {
            display: none;
          }
        }
      }
    }

    .ant-transfer-list-header-title {
      color: @primary-color;
      font-weight: 400;
      font-size: 12px;
    }
  }
}
</style>
