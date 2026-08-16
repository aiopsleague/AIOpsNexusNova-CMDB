<script setup lang="ts">
import { computed, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { getUsersUnderRole, delParentRole, addBatchParentRole } from '@/modules/acl/api/role'

interface RoleOption {
  id?: number
  name?: string
}

interface UnderRoleUser {
  id?: number
  nickname?: string
  role?: { id?: number; name?: string }
}

const { t } = useI18n()
const route = useRoute()

const props = defineProps<{ allRoles: RoleOption[] }>()

const visible = ref(false)
const records = ref<UnderRoleUser[]>([])
const roleId = ref(0)
const selectedChildrenRole = ref<number[]>([])

const roleOptions = computed(() =>
  (props.allRoles || []).map((role) => ({ value: role.id, label: role.name || '' }))
)

function appId(): string {
  return String(route.name ?? '').split('_')[0]
}

function loadRecords(rid: number) {
  getUsersUnderRole(rid, { app_id: appId() }).then((res) => {
    const data = res as unknown as { users: UnderRoleUser[] }
    records.value = data.users || []
  })
}

function handleProcessRole(rid: number) {
  roleId.value = rid
  visible.value = true
  loadRecords(rid)
}

async function handleAddRole() {
  await addBatchParentRole(roleId.value, {
    child_ids: selectedChildrenRole.value,
    app_id: appId(),
  })
  loadRecords(roleId.value)
  message.success(t('addSuccess'))
  selectedChildrenRole.value = []
}

function handleRevokeUser(record: UnderRoleUser) {
  const cid = record.role?.id
  if (!cid) return
  Modal.confirm({
    content: t('acl.deleteUserConfirm'),
    onOk() {
      return delParentRole(cid, roleId.value, { app_id: appId() }).then(() => {
        message.success(t('deleteSuccess'))
        loadRecords(roleId.value)
      })
    },
  })
}

defineExpose({ handleProcessRole })
</script>

<template>
  <CustomDrawer v-model:open="visible" :closable="true" width="500px" :title="t('acl.groupUser')">
    <a-form-item :label="t('acl.addUser')" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
      <a-row>
        <a-col :span="15">
          <a-select
            v-model:value="selectedChildrenRole"
            mode="multiple"
            :options="roleOptions"
            :placeholder="t('placeholder2')"
            style="width: 100%"
            allow-clear
            show-search
            option-filter-prop="label"
          />
        </a-col>
        <a-col :span="5" :offset="1">
          <a-button style="display: inline-block" @click="handleAddRole">{{ t('confirm') }}</a-button>
        </a-col>
      </a-row>
    </a-form-item>

    <a-card>
      <a-row
        v-for="(record, index) in records"
        :key="record.id"
        :gutter="24"
        :style="{ marginBottom: '5px' }"
      >
        <a-col :span="20">{{ index + 1 }}、{{ record.nickname }}</a-col>
        <a-col :span="4">
          <a-button type="danger" size="small" @click="handleRevokeUser(record)">{{ t('acl.remove') }}</a-button>
        </a-col>
      </a-row>
    </a-card>
  </CustomDrawer>
</template>
