<script setup lang="ts">
import { nextTick, onMounted, provide, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import EmployeeTreeSelect from '@/views/setting/components/employeeTreeSelect.vue'
import { getAllDepAndEmployee } from '@/api/company'
import { searchRole as searchRoleApi } from '@/modules/acl/api/role'

const emit = defineEmits<{
  (e: 'handleRevoke', form: { users?: unknown; roles?: unknown }): void
}>()

const { t } = useI18n()

const visible = ref(false)
const form = ref<{ users?: any; roles?: any }>({ users: undefined, roles: undefined })
const allTreeDepAndEmp = ref<any[]>([])
const allRoles = ref<any[]>([])
const filterAllRoles = ref<any[]>([])

provide('provide_allTreeDepAndEmp', () => allTreeDepAndEmp.value)

async function loadRoles() {
  const res: any = await searchRoleApi({ page_size: 9999, app_id: 'cmdb', is_all: true })
  allRoles.value = res.roles
  filterAllRoles.value = allRoles.value.slice(0, 100)
}

function loadDepAndEmployee() {
  getAllDepAndEmployee({ block: 0 }).then((res: any) => {
    allTreeDepAndEmp.value = res
  })
}

function open() {
  visible.value = true
  nextTick(() => {
    form.value = { users: undefined, roles: undefined }
  })
}

function handleCancel() {
  visible.value = false
}

function handleSearchRole(searchQuery: string) {
  filterAllRoles.value = allRoles.value
    .filter((item) => item.name.toLowerCase().includes(searchQuery.toLowerCase()))
    .slice(0, 100)
}

function handleOK() {
  emit('handleRevoke', form.value)
  handleCancel()
}

function normalizer(node: any) {
  return {
    id: node.id,
    label: node.name,
  }
}

onMounted(() => {
  loadDepAndEmployee()
  loadRoles()
})

defineExpose({ open })
</script>

<template>
  <a-modal :open="visible" :title="t('revoke')" @cancel="handleCancel" @ok="handleOK">
    <a-form :model="form" :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
      <a-form-item :label="t('user')">
        <EmployeeTreeSelect
          v-model:value="form.users"
          class="custom-treeselect custom-treeselect-white"
          :style="{
            '--custom-height': '32px',
            lineHeight: '32px',
            '--custom-multiple-lineHeight': '18px',
          }"
          :multiple="true"
          :placeholder="t('cmdb.serviceTree.userPlaceholder')"
          :id-type="2"
          department-key="acl_rid"
          employee-key="acl_rid"
        />
      </a-form-item>
      <a-form-item :label="t('role')">
        <Treeselect
          v-model="form.roles"
          :multiple="true"
          :options="filterAllRoles"
          class="custom-treeselect custom-treeselect-white"
          :style="{
            '--custom-height': '32px',
            lineHeight: '32px',
            '--custom-multiple-lineHeight': '18px',
          }"
          :limit="10"
          :limit-text="(count: number) => `+ ${count}`"
          :normalizer="normalizer"
          append-to-body
          :z-index="1050"
          :placeholder="t('cmdb.serviceTree.rolePlaceholder')"
          @search-change="handleSearchRole"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>
