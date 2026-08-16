<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import type { FormInstance } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { addResource, addResourceGroup, searchResourceType } from '@/modules/acl/api/resource'

interface ResourceTypeRow {
  id?: number
  name?: string
  [key: string]: unknown
}

const { t } = useI18n()
const route = useRoute()

const props = defineProps<{ handleOk?: () => void }>()

const formRef = ref<FormInstance>()
const visible = ref(false)
const allTypes = ref<ResourceTypeRow[]>([])
const isGroup = ref(false)
const selectedTypeId = ref<number | undefined>(undefined)

const form = reactive({
  name: '',
})

const rules = {
  name: [{ required: true, message: t('acl.resourceNameInput') }],
}

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function getAllResourceTypes() {
  searchResourceType({ page_size: 9999, app_id: appId() }).then((res) => {
    const data = res as unknown as { groups: ResourceTypeRow[] }
    allTypes.value = data.groups || []
  })
}

function handleCreate(defaultType: ResourceTypeRow) {
  visible.value = true
  selectedTypeId.value = defaultType.id
}

function handleClose() {
  formRef.value?.clearValidate()
  form.name = ''
  visible.value = false
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    const payload = {
      name: form.name,
      type_id: selectedTypeId.value,
      app_id: appId(),
    }
    const create = isGroup.value ? addResourceGroup(payload) : addResource(payload)
    await create
    message.success(t('addSuccess'))
    props.handleOk?.()
    handleClose()
  } catch {
    // validation failed
  }
}

watch(
  () => route.name,
  () => {
    getAllResourceTypes()
  }
)

defineExpose({ handleCreate })
</script>

<template>
  <CustomDrawer v-model:open="visible" :closable="false" :title="t('acl.addResource')" placement="right" width="30%">
    <a-form ref="formRef" :model="form" :rules="rules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
      <a-form-item :label="t('acl.resourceName')" name="name">
        <a-input v-model:value="form.name" :placeholder="t('acl.resourceNameInput')" />
      </a-form-item>

      <a-form-item :label="t('acl.resourceType')">
        <a-select v-model:value="selectedTypeId">
          <a-select-option v-for="type in allTypes" :key="type.id" :value="type.id">
            {{ type.name }}
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="t('acl.isGroup')">
        <a-radio-group v-model:value="isGroup">
          <a-radio :value="true">{{ t('yes') }}</a-radio>
          <a-radio :value="false">{{ t('no') }}</a-radio>
        </a-radio-group>
      </a-form-item>

      <div class="custom-drawer-bottom-action">
        <a-button @click="handleClose">{{ t('cancel') }}</a-button>
        <a-button type="primary" @click="handleSubmit">{{ t('confirm') }}</a-button>
      </div>
    </a-form>
  </CustomDrawer>
</template>
