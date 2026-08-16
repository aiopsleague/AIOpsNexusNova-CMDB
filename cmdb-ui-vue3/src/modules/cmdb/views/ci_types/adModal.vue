<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { provide, ref } from 'vue'
import { useI18n } from 'vue-i18n'

withDefaults(defineProps<{ CITypeId?: number | null }>(), { CITypeId: null })

const emit = defineEmits<{
  (e: 'pushCITypeList', list: any[]): void
  (e: 'addPlugin'): void
}>()

const { t } = useI18n()

const visible = ref(false)
const selectedIds = ref<any[]>([])

function open() {
  visible.value = true
}

function handleCancel() {
  selectedIds.value = []
  visible.value = false
}

async function handleOK() {
  if (selectedIds.value && selectedIds.value.length) {
    const adCITypeList = selectedIds.value.map((item, index) => {
      return {
        adr_id: item.id,
        id: new Date().getTime() + index,
        extra_option: {
          alias: '',
        },
        isClient: true,
      }
    })
    emit('pushCITypeList', adCITypeList)
  }
  handleCancel()
}

function setSelectedIds(id: string | number, type: string) {
  const _selectedIds = selectedIds.value.map((item) => ({ ...item }))
  const _idx = _selectedIds.findIndex((item) => item.id === id)
  if (_idx > -1) {
    _selectedIds.splice(_idx, 1)
  } else {
    _selectedIds.push({ id, type })
  }
  selectedIds.value = _selectedIds
}

function addPlugin() {
  handleCancel()
  emit('addPlugin')
}

provide('setSelectedIds', setSelectedIds)
provide('selectedIds', () => selectedIds.value)

defineExpose({ open })
</script>

<template>
  <a-modal
    width="800px"
    :open="visible"
    :closable="false"
    @ok="handleOK"
    @cancel="handleCancel"
  >
    <!-- TODO: wire up <Discovery> (from '@/modules/cmdb/views/discovery') once migrated. -->
    <template #footer>
      <a-space>
        <a-button @click="handleCancel">{{ t('cancel') }}</a-button>
        <a-button type="primary" @click="handleOK">{{ t('confirm') }}</a-button>
        <a-button type="primary" @click="addPlugin">{{ t('cmdb.ciType.addPlugin') }}</a-button>
      </a-space>
    </template>
  </a-modal>
</template>

<style></style>
