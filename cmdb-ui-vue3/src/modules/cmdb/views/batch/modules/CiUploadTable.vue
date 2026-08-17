<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileExcelOutlined } from '@ant-design/icons-vue'
import { cloneDeep } from '@/modules/cmdb/utils/helper'

const props = withDefaults(
  defineProps<{
    ciTypeAttrs: Record<string, any>
    uploadData?: any[]
  }>(),
  { uploadData: () => [] }
)

const { t } = useI18n()

const xTableRef = ref<any>()
const errorIndexList = ref<number[]>([])

const columns = computed(() => {
  const _columns: Array<Record<string, any>> = []
  if (props.ciTypeAttrs.attributes) {
    _columns.push(
      ...props.ciTypeAttrs.attributes.map((item: any) => {
        return {
          title: item.alias || item.name,
          field: item.alias || item.name,
        }
      })
    )
  }
  if (props.uploadData && props.uploadData.length) {
    Object.keys(props.uploadData[0]).forEach((key) => {
      if (key.startsWith('$')) {
        _columns.push({ title: key, field: key })
      }
    })
  }
  return _columns
})

const dataSource = computed(() => cloneDeep(props.uploadData))

watch(
  () => props.uploadData,
  () => {
    errorIndexList.value = []
  }
)

function uploadResultError(index: number) {
  const _errorIndexList = cloneDeep(errorIndexList.value)
  _errorIndexList.push(index)
  errorIndexList.value = _errorIndexList
}

function rowStyle({ rowIndex }: any) {
  if (errorIndexList.value.includes(rowIndex)) {
    return 'color:red;'
  }
}

function downloadError() {
  const data = props.uploadData.filter((_item, index) => errorIndexList.value.includes(index))
  xTableRef.value?.getVxetableRef()?.exportData({
    data,
    type: 'xlsx',
    columnFilterMethod({ column }: any) {
      return column.field
    },
  })
}

defineExpose({ uploadResultError, downloadError })
</script>

<template>
  <div class="cmdb-batch-upload-table">
    <vxe-table
      v-if="uploadData && uploadData.length"
      ref="xTableRef"
      stripe
      show-header-overflow
      show-overflow
      size="small"
      class="ops-stripe-table"
      height="auto"
      :data="dataSource"
      resizable
      :row-style="rowStyle"
    >
      <vxe-column type="seq" width="40" />
      <vxe-column
        v-for="item in columns"
        :key="item.field"
        :field="item.field"
        :title="item.title"
        :min-width="100"
      ></vxe-column>
    </vxe-table>
    <div v-else class="upload-placeholder">
      <div class="upload-placeholder-content">
        <FileExcelOutlined class="upload-placeholder-icon" />
        <div class="upload-placeholder-text">
          <p class="upload-placeholder-title">{{ t('cmdb.batch.pleaseUploadFile') }}</p>
          <p class="upload-placeholder-hint">{{ t('cmdb.batch.uploadFileHint') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.cmdb-batch-upload-table {
  min-height: 200px;

  .upload-placeholder {
    height: 240px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #d9d9d9;
    background: #fafafa;
    transition: all 0.3s ease;

    &:hover {
      border-color: @primary-color;
      background: fade(@primary-color, 5%);

      .upload-placeholder-icon {
        color: @primary-color;
        transform: translateY(-4px);
      }
    }

    &-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
    }

    &-icon {
      font-size: 72px;
      color: #bfbfbf;
      transition: all 0.3s ease;
    }

    &-text {
      text-align: center;
    }

    &-title {
      margin: 0 0 8px 0;
      font-size: 16px;
      font-weight: 500;
      color: @text-color_1;
    }

    &-hint {
      margin: 0;
      font-size: 14px;
      color: @text-color_3;
    }
  }
}
</style>
