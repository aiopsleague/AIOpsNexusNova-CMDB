<script setup lang="ts">
import { computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { permMap } from './constants'
import { grantTopologyView, revokeTopologyView } from '@/modules/cmdb/api/topology'
import { getCurrentRowClass, type RowParams } from './utils'

const props = withDefaults(
  defineProps<{
    viewId?: number | null
    resourceTypeName?: string
    tableData?: Record<string, any>[]
    grantType?: string
    addedRids?: Array<{ rid: string | number }>
  }>(),
  {
    viewId: null,
    resourceTypeName: '',
    tableData: () => [],
    grantType: 'relation_view',
    addedRids: () => [],
  }
)

const emit = defineEmits<{
  (e: 'grantDepart', grantType: string): void
  (e: 'grantRole', grantType: string): void
  (e: 'getTableData'): void
}>()

const { t } = useI18n()

const isModal = inject<boolean>('isModal', false)

const columns = ['read', 'update', 'delete', 'grant']

const windowHeight = computed(() => window.innerHeight)

const tableHeight = computed(() => {
  if (isModal) {
    return (windowHeight.value - 104) / 2
  }
  return (windowHeight.value - 104) / 2 - 116
})

const permMapComputed = computed(() => permMap())

function grantDepart() {
  emit('grantDepart', props.grantType)
}

function grantRole() {
  emit('grantRole', props.grantType)
}

function handleChange(e: { target: { checked: boolean } }, col: string, row: Record<string, any>) {
  if (e.target.checked) {
    grantTopologyView(props.viewId as string | number, row.rid, { perms: [col], name: props.resourceTypeName }).catch(
      () => {
        emit('getTableData')
      }
    )
  } else {
    revokeTopologyView(props.viewId as string | number, row.rid, { perms: [col], name: props.resourceTypeName }).catch(
      () => {
        emit('getTableData')
      }
    )
  }
}
</script>

<template>
  <div class="topology-view-grant">
    <vxe-table
      ref="xTable"
      size="mini"
      stripe
      class="ops-stripe-table"
      :data="tableData"
      :max-height="`${tableHeight}px`"
      :row-class-name="(params: RowParams) => getCurrentRowClass(params, addedRids)"
    >
      <vxe-column field="name"></vxe-column>
      <vxe-column v-for="col in columns" :key="col" :field="col" :title="permMapComputed[col]">
        <template #default="{ row }">
          <a-checkbox v-model:checked="row[col]" @change="(e: any) => handleChange(e, col, row)"></a-checkbox>
        </template>
      </vxe-column>
    </vxe-table>
    <a-space>
      <span class="grant-button" @click="grantDepart">{{ t('cmdb.components.grantUser') }}</span>
      <span class="grant-button" @click="grantRole">{{ t('cmdb.components.grantRole') }}</span>
    </a-space>
  </div>
</template>

<style scoped>
.topology-view-grant {
  padding: 10px 0;
}
</style>
