<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TableColumnsType } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { patternResults } from '@/modules/acl/api/trigger'

interface RoleOption {
  id: number
  name: string
  uid?: number
  [key: string]: unknown
}

interface PatternRow {
  name: string
  uid?: number
  created_at?: string
  [key: string]: unknown
}

const { t } = useI18n()

const props = withDefaults(defineProps<{ roles?: RoleOption[] }>(), { roles: () => [] })

const patternVisible = ref(false)
const tableData = ref<PatternRow[]>([])

const windowHeight = ref(window.innerHeight)
const scrollY = computed(() => Math.max(windowHeight.value - 110, 200))

const columns = computed<TableColumnsType<PatternRow>>(() => [
  { title: t('acl.resourceName'), dataIndex: 'name', key: 'name' },
  { title: t('acl.creator'), dataIndex: 'uid', key: 'uid' },
  { title: t('created_at'), dataIndex: 'created_at', key: 'created_at' },
])

function open(params: Record<string, unknown>) {
  patternResults(params).then((res) => {
    patternVisible.value = true
    tableData.value = res as unknown as PatternRow[]
  })
}

function getRoleName(uid: number | undefined): string {
  if (uid != null) {
    const found = (props.roles || []).find((item) => item.uid === uid)
    if (found) {
      return found.name || ''
    }
    return ''
  }
  return ''
}

function handleResize() {
  windowHeight.value = window.innerHeight
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

defineExpose({ open })
</script>

<template>
  <CustomDrawer
    v-model:open="patternVisible"
    :has-footer="false"
    :title="t('acl.viewMatchResult')"
    placement="right"
    width="500px"
  >
    <a-table
      :columns="columns"
      :data-source="tableData"
      :pagination="false"
      :scroll="{ y: scrollY }"
      row-key="name"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'uid'">
          {{ getRoleName(record.uid) }}
        </template>
      </template>
    </a-table>
  </CustomDrawer>
</template>
