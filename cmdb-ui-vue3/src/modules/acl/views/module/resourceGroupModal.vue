<script setup lang="ts">
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { updateResourceGroup, searchResource, getResourceGroupItems } from '@/modules/acl/api/resource'

interface GroupRecord {
  id?: number
  name?: string
  app_id?: number
  resource_type_id?: number
  [key: string]: unknown
}

interface TransferOption {
  id: number
  name: string
  key: string
  description: string
  title: string
}

const { t } = useI18n()

const visible = ref(false)
const editRecord = ref<GroupRecord>({})
const resources = ref<TransferOption[]>([])
const targetKeys = ref<string[]>([])
const selectedKeys = ref<string[]>([])

function handleSubmit() {
  const items = targetKeys.value.map((key) => {
    const matched = resources.value.find((item) => item.name === key)
    return matched ? matched.id : 0
  })
  updateResourceGroup(editRecord.value.id ?? 0, { items: items.join(',') }).then(() => {
    visible.value = false
    message.success(t('updateSuccess'))
  })
}

async function handleEdit(record: GroupRecord) {
  editRecord.value = record
  visible.value = true
  selectedKeys.value = []
  await loadChildren(record.id ?? 0)
  await loadResource()
}

function loadChildren(id: number) {
  return getResourceGroupItems(id).then((res) => {
    const data = res as unknown as { name: string }[]
    targetKeys.value = (data || []).map((item) => item.name)
  })
}

function loadResource() {
  const params = {
    app_id: editRecord.value.app_id,
    resource_type_id: editRecord.value.resource_type_id,
    page_size: 9999,
  }
  return searchResource(params).then((res) => {
    const data = res as unknown as { resources: { id: number; name: string }[] }
    resources.value = (data.resources || []).map((item) => ({
      id: item.id,
      name: item.name,
      key: item.name,
      description: item.name,
      title: item.name,
    }))
  })
}

function renderItem(item: Record<string, unknown>): string {
  return String(item.title ?? '')
}

function handleChange(newTargetKeys: string[], _direction: string, moveKeys: string[]) {
  selectedKeys.value = selectedKeys.value.filter((key) => !moveKeys.includes(key))
  targetKeys.value = newTargetKeys
}

function selectChange(sourceSelectedKeys: string[], targetSelectedKeys: string[]) {
  const list = [
    { data: sourceSelectedKeys, name: 'source' },
    { data: targetSelectedKeys, name: 'target' },
  ]
  list.forEach((item) => {
    if (item.data.length) {
      item.data.forEach((key) => {
        if (!selectedKeys.value.includes(key)) {
          selectedKeys.value.push(key)
        }
      })
    } else {
      selectedKeys.value =
        item.name === 'source'
          ? selectedKeys.value.filter((key) => targetKeys.value.includes(key))
          : selectedKeys.value.filter((key) => !targetKeys.value.includes(key))
    }
  })
}

defineExpose({ handleEdit })
</script>

<template>
  <a-modal v-model:open="visible" :title="`${t('acl.memberManage')}${editRecord.name || ''}`" :width="690" @ok="handleSubmit">
    <a-transfer
      :data-source="resources"
      :target-keys="targetKeys"
      :selected-keys="selectedKeys"
      :show-search="true"
      :titles="[]"
      :render="renderItem"
      @change="handleChange"
      @select-change="selectChange"
    />
  </a-modal>
</template>
