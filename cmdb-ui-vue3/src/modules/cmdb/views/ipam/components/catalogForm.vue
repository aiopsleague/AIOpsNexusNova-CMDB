<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { postIPAMScope, putIPAMScope } from '@/modules/cmdb/api/ipam'

const emit = defineEmits<{
  (e: 'ok'): void
}>()

const { t } = useI18n()

const catelogFormRef = ref()
const visible = ref(false)
const nodeId = ref<string | number | null>(null)
const actionType = ref('create')
const form = ref({ name: '' })

const formRules = {
  name: [
    {
      required: true,
      message: t('placeholder1'),
    },
  ],
}

function open({ nodeId: id, type, name }: { nodeId?: string | number | null; type?: string; name?: string }) {
  nodeId.value = id || null
  actionType.value = type || 'create'
  form.value.name = name || ''
  visible.value = true
}

function handleCancel() {
  visible.value = false
  form.value.name = ''
  actionType.value = 'create'
  nodeId.value = null

  catelogFormRef.value?.clearValidate()
}

async function handleOk() {
  try {
    await catelogFormRef.value?.validate()
  } catch {
    return
  }

  if (actionType.value === 'edit') {
    await putIPAMScope(nodeId.value as string | number, {
      name: form.value.name,
    })
    message.success(t('editSuccess'))
  } else {
    await postIPAMScope({
      parent_id: nodeId.value,
      name: form.value.name,
    })
    message.success(t('addSuccess'))
  }

  emit('ok')
  handleCancel()
}

defineExpose({ open })
</script>

<template>
  <a-modal
    v-model:open="visible"
    :title="t(actionType === 'edit' ? 'cmdb.ipam.editCatalog' : 'cmdb.ipam.addCatalog')"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <a-form
      ref="catelogFormRef"
      :model="form"
      :rules="formRules"
      :label-col="{ span: 5 }"
      :wrapper-col="{ span: 19 }"
    >
      <a-form-item
        :label="t('cmdb.ipam.catalogName')"
        name="name"
      >
        <a-input
          v-model:value="form.name"
          :placeholder="t('placeholder1')"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<style lang="less" scoped>
</style>
