<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import EmployeeTransfer from '@/components/EmployeeTransfer/index.vue'
import RoleTransfer from '@/components/RoleTransfer/index.vue'

const props = withDefaults(
  defineProps<{
    customTitle?: string
  }>(),
  {
    customTitle: '',
  }
)

const emit = defineEmits<{
  (e: 'handleOk', params: any, type: string): void
}>()

const { t } = useI18n()

const visible = ref(false)
const type = ref<'depart' | 'role'>('depart')

const employeeTransferRef = ref<InstanceType<typeof EmployeeTransfer>>()
const roleTransferRef = ref<InstanceType<typeof RoleTransfer>>()

const title = computed(() => {
  if (props.customTitle) {
    return props.customTitle
  }
  if (type.value === 'depart') {
    return t('cmdb.components.grantUser')
  }
  return t('cmdb.components.grantRole')
})

function open(typeParam: 'depart' | 'role') {
  visible.value = true
  type.value = typeParam
}

function handleOk() {
  let params: any
  if (type.value === 'depart') {
    params = employeeTransferRef.value?.getValues()
  }
  if (type.value === 'role') {
    params = roleTransferRef.value?.getValues()
  }
  handleCancel()
  emit('handleOk', params, type.value)
}

function handleCancel() {
  visible.value = false
}

defineExpose({ open })
</script>

<template>
  <a-modal :title="title" :open="visible" destroy-on-close @ok="handleOk" @cancel="handleCancel">
    <EmployeeTransfer
      v-if="type === 'depart'"
      ref="employeeTransferRef"
      :is-disabled-all-company="true"
      unique-key="acl_rid"
      :height="350"
    />
    <RoleTransfer v-if="type === 'role'" ref="roleTransferRef" app_id="cmdb" :height="350" />
  </a-modal>
</template>
