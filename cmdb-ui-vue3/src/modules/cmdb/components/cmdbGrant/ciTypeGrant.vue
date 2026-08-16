<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { QuestionCircleOutlined, LoadingOutlined } from '@ant-design/icons-vue'
import { Modal } from 'ant-design-vue'
import { permMap, permDescMap } from './constants'
import { grantCiType, revokeCiType } from '@/modules/cmdb/api/CIType'
import ReadCheckbox from './readCheckbox.vue'
import { getCurrentRowClass, type RowParams } from './utils'
import emptyImg from '@/assets/data_empty.png'

const props = withDefaults(
  defineProps<{
    CITypeId?: number | null
    tableData?: Record<string, any>[]
    grantType?: string
    addedRids?: Array<{ rid: string | number }>
  }>(),
  {
    CITypeId: null,
    tableData: () => [],
    grantType: 'ci_type',
    addedRids: () => [],
  }
)

const emit = defineEmits<{
  (e: 'grantDepart', grantType: string): void
  (e: 'grantRole', grantType: string): void
  (e: 'getTableData'): void
  (e: 'openReadGrantModal', col: string, row: Record<string, any>): void
}>()

const { t } = useI18n()

const loading = inject<() => boolean>('loading', () => false)
const isModal = inject<boolean>('isModal', false)

const permMapComputed = computed(() => permMap())
const permDescMapComputed = computed(() => permDescMap())

const columns = computed(() => {
  if (props.grantType === 'ci_type') {
    return ['config', 'grant']
  }
  return ['read_attr', 'read_ci', 'create', 'update', 'delete']
})

function intersection(a: string[], b: string[]): string[] {
  return a.filter((item) => b.includes(item))
}

function uniqByRid(list: Record<string, any>[]): Record<string, any>[] {
  const seen = new Set<string | number>()
  return list.filter((item) => {
    if (seen.has(item.rid)) {
      return false
    }
    seen.add(item.rid)
    return true
  })
}

const filterTableData = computed(() => {
  const filtered = props.tableData.filter((data) => {
    const inter = intersection(Object.keys(data), columns.value.map((col) => col.split('_')[0]))
    return inter && inter.length
  })
  return uniqByRid(filtered)
})

const windowHeight = computed(() => window.innerHeight)

const tableHeight = computed(() => {
  if (isModal) {
    return (windowHeight.value - 104) / 2
  }
  return (windowHeight.value - 104) / 2 - 116
})

async function handleChange(e: { target: { checked: boolean } }, col: string, row: Record<string, any>) {
  if (e.target.checked) {
    await grantCiType(props.CITypeId as number, row.rid, { perms: [col] }).catch(() => {
      emit('getTableData')
    })
  } else {
    await revokeCiType(props.CITypeId as number, row.rid, { perms: [col] }).catch(() => {
      emit('getTableData')
    })
  }
}

function grantDepart() {
  emit('grantDepart', props.grantType)
}

function grantRole() {
  emit('grantRole', props.grantType)
}

function openReadGrantModal(col: string, row: Record<string, any>) {
  emit('openReadGrantModal', col, row)
}

function clickGrant(col: string, row: Record<string, any>) {
  if (!row[col]) {
    handleChange({ target: { checked: true } }, col, row)
    row.grant = true
  } else {
    Modal.confirm({
      title: t('warning'),
      content: t('cmdb.components.confirmRevoke', { name: `${row.name}` }),
      onOk() {
        handleChange({ target: { checked: false } }, col, row)
        row.grant = false
      },
    })
  }
}
</script>

<template>
  <div class="ci-type-grant">
    <vxe-table
      ref="xTable"
      size="mini"
      stripe
      class="ops-stripe-table"
      :data="filterTableData"
      :max-height="`${tableHeight}px`"
      :row-class-name="(params: RowParams) => getCurrentRowClass(params, addedRids)"
    >
      <vxe-column field="name"></vxe-column>
      <vxe-column v-for="col in columns" :key="col" :field="col">
        <template #header>
          <span>{{ permMapComputed[col] }}</span>
          <a-tooltip v-if="permDescMapComputed[col]" :title="permDescMapComputed[col]">
            <QuestionCircleOutlined style="margin-left: 4px; color: #999; cursor: help" />
          </a-tooltip>
        </template>
        <template #default="{ row }">
          <ReadCheckbox
            v-if="['read'].includes(col.split('_')[0])"
            :value="row[col.split('_')[0]]"
            :value-key="col"
            :rid="row.rid"
            @open-read-grant-modal="() => openReadGrantModal(col, row)"
          />
          <a-checkbox v-else-if="col === 'grant'" :checked="row[col]" @click="clickGrant(col, row)"></a-checkbox>
          <a-checkbox v-else v-model:checked="row[col]" @change="(e: any) => handleChange(e, col, row)"></a-checkbox>
        </template>
      </vxe-column>
      <template #empty>
        <div v-if="loading()" class="ci-type-grant-loading">
          <LoadingOutlined /> {{ t('loading') }}
        </div>
        <div v-else>
          <img :style="{ width: '100px' }" :src="emptyImg" />
          <div>{{ t('noData') }}</div>
        </div>
      </template>
    </vxe-table>
    <a-space>
      <span class="grant-button" @click="grantDepart">{{ t('cmdb.components.grantUser') }}</span>
      <span class="grant-button" @click="grantRole">{{ t('cmdb.components.grantRole') }}</span>
    </a-space>
  </div>
</template>

<style scoped>
.ci-type-grant {
  padding: 10px 0;
}
.ci-type-grant-loading {
  height: 200px;
  line-height: 200px;
  color: #2f54eb;
}
</style>
