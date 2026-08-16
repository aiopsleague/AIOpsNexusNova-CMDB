<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { CheckOutlined } from '@ant-design/icons-vue'
import type { TableColumnsType } from 'ant-design-vue'
import Pager from '@/components/Pager/index.vue'
import SearchForm from '../../module/searchForm.vue'
import { searchRoleHistory } from '@/modules/acl/api/history'
import { searchApp } from '@/modules/acl/api/app'
import { searchUser } from '@/modules/acl/api/user'

interface OptionItem {
  [name: string]: number
}

const { t } = useI18n()

const loading = ref(true)
const checked = ref(false)
const tableData = ref<any[]>([])

const allUsers = ref<OptionItem[]>([])
const allUsersMap = ref<Map<number, string>>(new Map())

const colorMap: Record<string, string> = {
  create: 'green',
  delete: 'red',
  update: 'orange',
  role_relation_add: 'green',
  role_relation_delete: 'red',
}

const queryParams = ref<Record<string, any>>({
  page: 1,
  page_size: 50,
  scope: 'role',
  start: '',
  end: '',
})

const roleTableAttrList = ref<any[]>([
  {
    alias: t('acl.date'),
    is_choice: false,
    name: 'datetime',
    value_type: '3',
  },
  {
    alias: t('acl.app'),
    is_choice: true,
    name: 'app_id',
    value_type: '2',
    choice_value: [],
  },
  {
    alias: t('acl.operator'),
    is_choice: true,
    name: 'operate_uid',
    value_type: '2',
    choice_value: [],
  },
  {
    alias: t('operation'),
    is_choice: true,
    name: 'operate_type',
    value_type: '2',
    choice_value: [
      { [t('create')]: 'create' },
      { [t('update')]: 'update' },
      { [t('delete')]: 'delete' },
      { [t('acl.roleRelationAdd')]: 'role_relation_add' },
      { [t('acl.roleRelationDelete')]: 'role_relation_delete' },
    ],
  },
])

const windowHeight = ref(window.innerHeight)
const scrollY = computed(() => Math.max(windowHeight.value - 310, 200))

const operateTypeMap = computed<Record<string, string>>(() => ({
  create: t('create'),
  update: t('update'),
  delete: t('delete'),
  role_relation_add: t('acl.roleRelationAdd'),
  role_relation_delete: t('acl.roleRelationDelete'),
}))

const columns = computed<TableColumnsType>(() => {
  const cols: TableColumnsType = [
    { title: t('acl.operateTime'), dataIndex: 'created_at', key: 'created_at', width: 144 },
    { title: t('acl.operator'), dataIndex: 'operate_uid', key: 'operate_uid', width: 130 },
    { title: t('operation'), dataIndex: 'operate_type', key: 'operate_type', width: 112 },
    { title: t('acl.role2'), dataIndex: 'current', key: 'role' },
    {
      title: checked.value ? t('acl.inheritedFrom') : t('acl.admin'),
      dataIndex: 'extra',
      key: 'admin',
      width: checked.value ? 350 : 80,
    },
  ]
  if (!checked.value) {
    cols.push({ title: t('desc'), dataIndex: 'description', key: 'description' })
  }
  cols.push({ title: t('acl.source'), dataIndex: 'source', key: 'source', width: 100 })
  return cols
})

const tableDataLength = computed(() => tableData.value.length)

function isEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

async function getTable(params: Record<string, any>) {
  try {
    loading.value = true
    const res = (await searchRoleHistory(handleQueryParams(params))) as unknown as {
      data: any[]
      id2roles: Record<string, { name: string }>
      id2perms: Record<string, { name: string }>
      id2resources: Record<string, { name: string }>
    }
    const { data, id2roles, id2perms, id2resources } = res
    data.forEach((item) => {
      item.operate_uid = allUsersMap.value.get(item.operate_uid)
      if (item.operate_type === 'role_relation_add' || item.operate_type === 'role_relation_delete') {
        item.extra.child_ids.forEach((subItem: number, index: number) => {
          item.extra.child_ids[index] = id2roles[subItem].name
        })
        item.extra.parent_ids.forEach((subItem: number, index: number) => {
          item.extra.parent_ids[index] = id2roles[subItem].name
        })
      } else {
        handleChangeDescription(item, item.operate_type, id2roles, id2perms, id2resources)
      }
    })
    tableData.value = data
  } finally {
    loading.value = false
  }
}

async function getAllApps() {
  const res = (await searchApp()) as unknown as { apps: Array<{ id: number; name: string }> }
  const apps: OptionItem[] = []
  res.apps.forEach((item) => {
    apps.push({ [item.name]: item.id })
  })
  roleTableAttrList.value[1].choice_value = apps
}

async function getAllUsers() {
  const res = (await searchUser({ page_size: 10000, app_id: 'acl' })) as unknown as {
    users: Array<{ uid: number; nickname: string }>
  }
  const users: OptionItem[] = []
  const usersMap = new Map<number, string>()
  res.users.forEach((item) => {
    users.push({ [item.nickname]: item.uid })
    usersMap.set(item.uid, item.nickname)
  })
  allUsers.value = users
  allUsersMap.value = usersMap
  roleTableAttrList.value[2].choice_value = users
}

function onShowSizeChange(size: number) {
  queryParams.value.page_size = size
  queryParams.value.page = 1
  getTable(queryParams.value)
}

function onChange(pageNum: number) {
  queryParams.value.page = pageNum
  getTable(queryParams.value)
}

function onSwitchChange(val: boolean) {
  checked.value = val
  queryParams.value.scope = val ? 'role_relation' : 'role'
  queryParams.value.page = 1
  getTable(queryParams.value)
}

function handleSearch(params: Record<string, any>) {
  queryParams.value = { ...queryParams.value, ...params, scope: checked.value ? 'role_relation' : 'role' }
  getTable(queryParams.value)
}

function searchFormReset() {
  checked.value = false
  queryParams.value = {
    page: 1,
    page_size: 50,
    scope: checked.value ? 'role_relation' : 'role',
  }
  getTable(queryParams.value)
}

function handleQueryParams(params: Record<string, any>): Record<string, any> {
  const qp = { ...params }
  let flag = false
  let q = qp.q ? qp.q : ''
  for (const key in qp) {
    if (key !== 'page' && key !== 'page_size' && key !== 'app_id' && key !== 'q' && key !== 'start' && key !== 'end' && qp[key] !== undefined) {
      flag = true
      if (q) q += `,${key}:${qp[key]}`
      else q += `${key}:${qp[key]}`
      delete qp[key]
    }
  }
  return flag ? { ...qp, q } : qp
}

function handleTagColor(operateType: string): string {
  return colorMap[operateType]
}

function handleChangeDescription(
  item: any,
  operateType: string,
  id2roles: Record<string, { name: string }>,
  id2perms: Record<string, { name: string }>,
  id2resources: Record<string, { name: string }>
) {
  switch (operateType) {
    case 'create': {
      item.description = `${t('acl.addRole')}${item.current.name}`
      break
    }
    case 'update': {
      item.description = ''
      for (const key in item.origin) {
        const newVal = item.current[key]
        const oldVal = item.origin[key]
        if (!isEqual(newVal, oldVal) && key !== 'updated_at' && key !== 'deleted_at' && key !== 'created_at') {
          if (oldVal === null) {
            item.description += ` 【 ${key} : -> ${newVal} 】 `
          } else {
            item.description += ` 【 ${key} : ${oldVal} -> ${newVal} 】 `
          }
        }
      }
      if (!item.description) item.description = t('acl.noChange')
      break
    }
    case 'delete': {
      const { child_ids, parent_ids, role_permissions } = item.extra
      child_ids.forEach((subItem: number, index: number) => {
        child_ids[index] = id2roles[subItem].name
      })
      parent_ids.forEach((subItem: number, index: number) => {
        parent_ids[index] = id2roles[subItem].name
      })

      const resourceMap = new Map<string, string>()
      const permsArr: string[] = []
      role_permissions.forEach((subItem: { resource_id: number; perm_id: number }) => {
        const resourceId = subItem.resource_id
        const permId = subItem.perm_id
        if (resourceMap.has(String(resourceId))) {
          const resourcePerms = resourceMap.get(String(resourceId)) as string
          resourceMap.set(String(resourceId), `${resourcePerms},${id2perms[permId].name}`)
        } else {
          resourceMap.set(String(resourceId), String(id2perms[permId].name))
        }
      })
      resourceMap.forEach((value, key) => {
        permsArr.push(`${id2resources[Number(key)].name}：${value}`)
      })
      item.description = `${t('acl.heir')}：${child_ids}\n${t('acl.inheritedFrom')}：${parent_ids}\n${t(
        'acl.involvingRP'
      )}：\n${permsArr.join('\n')}`
      break
    }
  }
}

function handleResize() {
  windowHeight.value = window.innerHeight
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  Promise.all([getAllApps(), getAllUsers()]).then(() => getTable(queryParams.value))
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div>
    <SearchForm
      :attr-list="roleTableAttrList"
      :has-switch="true"
      :switch-value="t('acl.roleRelation')"
      @on-switch-change="onSwitchChange"
      @search="handleSearch"
      @search-form-reset="searchFormReset"
    />
    <a-table
      :columns="columns"
      :data-source="tableData"
      :loading="loading"
      :pagination="false"
      :scroll="{ x: 900, y: scrollY }"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'operate_type'">
          <a-tag :color="handleTagColor(record.operate_type)">{{ operateTypeMap[record.operate_type] }}</a-tag>
        </template>
        <template v-else-if="column.key === 'role'">
          <template v-if="!checked">
            <a-tag color="blue">{{ record.current.name || record.origin.name }}</a-tag>
          </template>
          <template v-else>
            <a-tag v-for="(id, index) in record.extra.child_ids" :key="'child_ids_' + id + index" color="blue">
              {{ id }}
            </a-tag>
          </template>
        </template>
        <template v-else-if="column.key === 'admin'">
          <template v-if="!checked">
            <CheckOutlined v-if="record.current.is_app_admin" />
          </template>
          <template v-else>
            <a-tag v-for="(id, index) in record.extra.parent_ids" :key="'parent_ids_' + id + index" color="cyan">
              {{ id }}
            </a-tag>
          </template>
        </template>
        <template v-else-if="column.key === 'description'">
          <p>{{ record.description }}</p>
        </template>
      </template>
    </a-table>
    <Pager
      :current-page="queryParams.page"
      :page-size="queryParams.page_size"
      :page-sizes="[50, 100, 200]"
      :total="tableDataLength"
      :is-loading="loading"
      :style="{ marginTop: '10px' }"
      @change="onChange"
      @show-size-change="onShowSizeChange"
    />
  </div>
</template>

<style scoped>
.row {
  margin-top: 5px;
}
.ant-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}
p {
  margin-bottom: 0;
}
</style>
