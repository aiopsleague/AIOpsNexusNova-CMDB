<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { DeleteOutlined, EditOutlined, LockOutlined, SolutionOutlined } from '@ant-design/icons-vue'
import type { TableColumnsType } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'
import { deleteUserById, searchUser, getOnDutyUser as fetchOnDutyUser } from '@/modules/acl/api/user'
import UserForm from './module/userForm.vue'
import PermCollectForm from './module/permCollectForm.vue'

interface UserRow {
  uid: number
  username: string
  nickname: string
  date_joined?: string
  block?: boolean
  password?: string
  department?: string
  catalog?: string
  email?: string
  mobile?: string
}

const { t } = useI18n()
const userStore = useUserStore()

const loading = ref(false)
const onDutyUids = ref<number[]>([])
const allUsers = ref<UserRow[]>([])
const tableData = ref<UserRow[]>([])
const searchName = ref('')

const windowHeight = ref(window.innerHeight)
const scrollY = computed(() => Math.max(windowHeight.value - 165, 200))

const userFormRef = ref<{
  handleCreate: () => void
  handleEdit: (record: UserRow) => void
}>()

const permCollectFormRef = ref<{
  collect: (record: UserRow) => void
}>()

const isAclAdmin = computed(() => {
  const perms = (userStore.roles?.permissions ?? []) as unknown as string[]
  return perms.includes('acl_admin')
})

const columns = computed<TableColumnsType<UserRow>>(() => [
  {
    title: t('acl.username'),
    dataIndex: 'username',
    key: 'username',
    width: 140,
    fixed: 'left',
    sorter: (a, b) => (a.username || '').localeCompare(b.username || ''),
  },
  { title: t('acl.nickname'), dataIndex: 'nickname', key: 'nickname', width: 140 },
  {
    title: t('acl.joined_at'),
    dataIndex: 'date_joined',
    key: 'date_joined',
    width: 180,
    align: 'center',
    sorter: (a, b) => (a.date_joined || '').localeCompare(b.date_joined || ''),
  },
  { title: t('acl.block'), dataIndex: 'block', key: 'block', width: 150, align: 'center' },
  { title: t('operation'), dataIndex: 'action', key: 'action', width: 150, fixed: 'right', align: 'center' },
])

async function getOnDutyUser() {
  const res = await fetchOnDutyUser()
  const data = res as unknown as { uid: number }[]
  onDutyUids.value = (data || []).map((i) => i.uid)
}

function search() {
  searchUser({ page_size: 10000 }).then((res) => {
    const data = res as unknown as { users: UserRow[] }
    const ret = (data.users || []).filter((u) => onDutyUids.value.includes(u.uid))
    allUsers.value = ret
    tableData.value = ret
    loading.value = false
  })
}

function handleCreate() {
  userFormRef.value?.handleCreate()
}

function handleEdit(record: UserRow) {
  userFormRef.value?.handleEdit(record)
}

function handlePermCollect(record: UserRow) {
  permCollectFormRef.value?.collect(record)
}

async function handleOk() {
  searchName.value = ''
  await getOnDutyUser()
  search()
}

function deleteUser(uid: number) {
  deleteUserById(uid).then(() => {
    message.success(t('deleteSuccess'))
    handleOk()
  })
}

watch(searchName, (val) => {
  if (val) {
    const lower = val.toLowerCase()
    tableData.value = allUsers.value.filter(
      (item) =>
        (item.username || '').toLowerCase().includes(lower) ||
        (item.nickname || '').toLowerCase().includes(lower)
    )
  } else {
    tableData.value = allUsers.value
  }
})

function handleResize() {
  windowHeight.value = window.innerHeight
}

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  loading.value = true
  await getOnDutyUser()
  search()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="acl-users">
    <div class="acl-users-header">
      <a-button v-if="isAclAdmin" type="primary" @click="handleCreate">{{ t('acl.addUser') }}</a-button>
      <a-input-search
        v-model:value="searchName"
        class="ops-input"
        allow-clear
        :style="{ width: '300px', display: 'inline', marginLeft: '10px' }"
        :placeholder="`${t('search')} | ${t('acl.nickname')} 、 ${t('acl.username')}`"
      />
    </div>
    <a-spin :spinning="loading">
      <a-table
        :columns="columns"
        :data-source="tableData"
        :pagination="false"
        :scroll="{ x: 760, y: scrollY }"
        row-key="uid"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'block'">
            <LockOutlined v-if="record.block" />
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a :disabled="!isAclAdmin" @click="handleEdit(record)">
                <EditOutlined />
              </a>
              <a-tooltip :title="t('acl.summaryPermissions')">
                <a @click="handlePermCollect(record)"><SolutionOutlined /></a>
              </a-tooltip>
              <a-popconfirm :title="t('confirmDelete')" @confirm="deleteUser(record.uid)">
                <a style="color: red"><DeleteOutlined /></a>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-spin>

    <user-form ref="userFormRef" :handle-ok="handleOk" />
    <PermCollectForm ref="permCollectFormRef" />
  </div>
</template>

<style scoped>
.acl-users {
  border-radius: 4px;
  background-color: #fff;
  height: calc(100vh - 64px);
  margin-bottom: -24px;
  padding: 24px;
}
.acl-users-header {
  display: inline-flex;
  margin-bottom: 15px;
}
</style>
