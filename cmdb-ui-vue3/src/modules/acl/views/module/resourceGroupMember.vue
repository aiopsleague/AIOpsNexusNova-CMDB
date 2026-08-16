<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getResourceGroupItems } from '@/modules/acl/api/resource'

interface GroupRecord {
  id?: number
  name?: string
  [key: string]: unknown
}

interface MemberItem {
  name?: string
  [key: string]: unknown
}

const { t } = useI18n()

const visible = ref(false)
const editRecord = ref<GroupRecord>({})
const members = ref<MemberItem[]>([])

function handleEdit(record: GroupRecord) {
  editRecord.value = record
  visible.value = true
  loadMembers(record.id ?? 0)
}

function loadMembers(id: number) {
  getResourceGroupItems(id).then((res) => {
    const data = res as unknown as MemberItem[]
    members.value = data || []
  })
}

defineExpose({ handleEdit })
</script>

<template>
  <a-modal v-model:open="visible" :title="`${t('acl.groupMember')}${editRecord.name || ''}`" :width="800" :footer="null">
    <div :style="{ maxHeight: '500px', overflow: 'auto' }">
      <a-tag v-for="mem in members" :key="mem.name" :style="{ marginBottom: '5px' }">
        {{ mem.name }}
      </a-tag>
    </div>
  </a-modal>
</template>
