<script setup lang="ts">
import { reactive, ref } from 'vue'
import { Modal, message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { getCIsBaseline, CIBaselineRollback } from '@/modules/cmdb/api/history'
import dataEmptyImg from '@/assets/data_empty.png'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    ciIds?: any[]
  }>(),
  {
    ciIds: () => [],
  }
)

const emit = defineEmits<{
  (e: 'batchRollbackAsync', values: Record<string, any>): void
  (e: 'getCIHistory'): void
}>()

const formRef = ref()
const drawerVisible = ref(false)
const drawerTitle = ref('')

const formModel = reactive<Record<string, any>>({
  before_date: undefined,
})

const formRules = {
  before_date: [{ required: true, message: t('cmdb.ci.rollbackToTips') }],
}

const tableData = ref<any[]>([])
const dataLoad = ref('')
const loading = ref(false)
const hasDiff = ref(false)
const batched = ref(false)

function onClose() {
  drawerVisible.value = false
  formRef.value?.resetFields()
  tableData.value = []
  dataLoad.value = t('noData')
}

function onOpen(isBatched = false) {
  drawerTitle.value = t('cmdb.ci.rollbackHeader')
  drawerVisible.value = true
  batched.value = isBatched
}

function handleSubmit() {
  formRef.value.validate().then((values: Record<string, any>) => {
    Modal.confirm({
      title: t('warning'),
      content: t('cmdb.ci.rollbackConfirm'),
      onOk() {
        if (batched.value) {
          emit('batchRollbackAsync', values)
        } else {
          rollbackCI(values)
        }
      },
    })
  })
}

function rollbackCI(params: Record<string, any>) {
  CIBaselineRollback(props.ciIds[0] as string | number, params).then(() => {
    message.success(t('cmdb.ci.rollbackSuccess'))
    formRef.value?.resetFields()
    emit('getCIHistory')
  })
}

function getBaselineDiff(value: string) {
  dataLoad.value = 'loading...'
  loading.value = true
  hasDiff.value = false
  getCIsBaseline({ ci_ids: props.ciIds.join(','), before_date: value }).then((res) => {
    tableData.value = res
    loading.value = false
    if (!res.length) {
      dataLoad.value = t('cmdb.ci.noDiff', { baseline: value })
    } else {
      hasDiff.value = true
    }
  })
}

function mergeRowMethod({ row, _rowIndex, column, visibleData }: any) {
  const fields = ['instance']
  const cellValue1 = row.instance
  if (cellValue1 && fields.includes(column.property)) {
    const prevRow = visibleData[_rowIndex - 1]
    let nextRow = visibleData[_rowIndex + 1]
    if (prevRow && prevRow.instance === cellValue1) {
      return { rowspan: 0, colspan: 0 }
    } else {
      let countRowspan = 1
      while (nextRow && nextRow.instance === cellValue1) {
        nextRow = visibleData[++countRowspan + _rowIndex]
      }
      if (countRowspan > 1) {
        return { rowspan: countRowspan, colspan: 1 }
      }
    }
  }
}

defineExpose({ onOpen })
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <CustomDrawer
    :closable="true"
    :title="drawerTitle"
    v-model:open="drawerVisible"
    @close="onClose"
    placement="right"
    width="800"
    :body-style="{ paddingTop: 0 }"
  >
    <div class="custom-drawer-bottom-action">
      <a-button @click="onClose">{{ t('cancel') }}</a-button>
      <a-button type="primary" @click="handleSubmit" :loading="loading" :disabled="!hasDiff">
        {{ t('submit') }}
      </a-button>
    </div>
    <a-form ref="formRef" :model="formModel" :rules="formRules" :style="{ paddingTop: '20px' }">
      <a-form-item :label="t('cmdb.ci.rollbackTo')" required :help="t('cmdb.ci.baselineTips')" name="before_date">
        <a-date-picker
          v-model:value="formModel.before_date"
          :style="{ width: '278px' }"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          @ok="getBaselineDiff"
          :show-time="{ format: 'HH:mm:ss' }"
          :placeholder="t('cmdb.ci.rollbackToTips')"
        />
      </a-form-item>
      <span :style="{ fontWeight: 'bold' }">{{ t('cmdb.ci.baselineDiff') }}</span>
      <vxe-table
        show-overflow
        show-header-overflow
        resizable
        border
        size="small"
        :span-method="mergeRowMethod"
        :data="tableData"
        :scroll-y="{ enabled: false, gt: 20 }"
        :scroll-x="{ enabled: false, gt: 0 }"
        class="ops-unstripe-table"
      >
        <template #empty>
          <a-empty :image="dataEmptyImg" :image-style="{ height: '100px' }" :style="{ paddingTop: '10%' }">
            <template #description>{{ dataLoad }}</template>
          </a-empty>
        </template>
        <vxe-column field="instance" min-width="80" :title="t('cmdb.ci.instance')"> </vxe-column>
        <vxe-column field="attr_name" min-width="80" :title="t('cmdb.attribute')"> </vxe-column>
        <vxe-column field="cur" min-width="80" :title="t('cmdb.ci.rollbackBefore')">
          <template #default="{ row }">
            <span v-if="row.value_type === '6'">{{ JSON.stringify(row.cur) }}</span>
            <span v-else>{{ row.cur }}</span>
          </template>
        </vxe-column>
        <vxe-column field="to" min-width="80" :title="t('cmdb.ci.rollbackAfter')">
          <template #default="{ row }">
            <span v-if="row.value_type === '6'">{{ JSON.stringify(row.to) }}</span>
            <span v-else>{{ row.to }}</span>
          </template>
        </vxe-column>
      </vxe-table>
    </a-form>
  </CustomDrawer>
</template>
