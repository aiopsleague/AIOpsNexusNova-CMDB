<script setup lang="ts">
import { computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { permMap } from './constants'
import { grantTypeRelation, revokeTypeRelation } from '@/modules/cmdb/api/CITypeRelation'
import { getCurrentRowClass, type RowParams } from './utils'

const props = withDefaults(
  defineProps<{
    tableData?: Record<string, any>[]
    grantType?: string
    typeRelationIds?: Array<string | number> | null
    addedRids?: Array<{ rid: string | number }>
  }>(),
  {
    tableData: () => [],
    grantType: 'type_relation',
    typeRelationIds: null,
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

const columns = ['create', 'grant', 'delete']

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
  const first = props.typeRelationIds?.[0]
  const second = props.typeRelationIds?.[1]
  if (e.target.checked) {
    grantTypeRelation(first as string | number, second as string | number, row.rid, { perms: [col] }).catch(() => {
      emit('getTableData')
    })
  } else {
    revokeTypeRelation(first as string | number, second as string | number, row.rid, { perms: [col] }).catch(() => {
      emit('getTableData')
    })
  }
}
</script>

<template>
  <div class="ci-relation-grant">
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
.ci-relation-grant {
  padding: 10px 0;
}
</style>
