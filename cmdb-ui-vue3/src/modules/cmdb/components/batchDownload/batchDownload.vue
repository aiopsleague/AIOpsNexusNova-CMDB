<script setup lang="ts">
import { computed, nextTick, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import { useCmdbStore } from '@/modules/cmdb/store'

/**
 * Batch export modal. Lets the user pick a filename, output format and the
 * attribute columns (tree) to export. `open({ preferenceAttrList, ciTypeName })`
 * is exposed so the parent list can launch it.
 */
interface ReplaceFields {
  children: string
  title: string
  key: string
}

const props = withDefaults(
  defineProps<{
    replaceFields?: ReplaceFields
    treeType?: string
    showFileTypeSelect?: boolean
  }>(),
  {
    replaceFields: () => ({ children: 'children', title: 'alias', key: 'name' }),
    treeType: 'default',
    showFileTypeSelect: true,
  }
)

const emit = defineEmits<{
  (e: 'batchDownload', payload: Record<string, unknown>): void
}>()

const { t } = useI18n()
const cmdbStore = useCmdbStore()

const formRef = ref()
const visible = ref(false)
const preferenceAttrList = ref<any[]>([])
const checkedKeys = ref<string[]>([])
const checkAll = ref(false)
const indeterminate = ref(false)
const defaultChecked = ref<string[]>([])

const formModel = reactive({
  filename: '',
  type: 'xlsx',
  exportQRCode: false,
})

const formRules = {
  filename: [{ required: true, message: t('cmdb.components.filenameInputTips') }],
  type: [{ required: true, message: t('cmdb.components.saveTypeTips') }],
}

const typeList = computed(() => [
  { id: 'xlsx', label: t('cmdb.components.xlsx') },
  { id: 'csv', label: t('cmdb.components.csv') },
  { id: 'html', label: t('cmdb.components.html') },
  { id: 'xml', label: t('cmdb.components.xml') },
  { id: 'txt', label: t('cmdb.components.txt') },
])

function open({
  preferenceAttrList: attrList,
  ciTypeName,
}: {
  preferenceAttrList: any[]
  ciTypeName?: string
}) {
  preferenceAttrList.value = attrList
  visible.value = true
  nextTick(() => {
    formModel.filename = ciTypeName
      ? `cmdb-${ciTypeName}-${dayjs().format('YYYYMMDDHHmmss')}`
      : `cmdb-${dayjs().format('YYYYMMDDHHmmss')}`
    if (props.treeType === 'tree') {
      const check = ['ci_type_alias']
      attrList.forEach((colGroup) => {
        if (colGroup.children && colGroup.children.length) {
          check.push(...colGroup.children.map((attr: any) => attr[`${props.replaceFields.key}`]))
        }
      })
      defaultChecked.value = check
      checkedKeys.value = check
    } else {
      checkedKeys.value = attrList.map((attr: any) => attr[`${props.replaceFields.key}`])
    }
    checkAll.value = true
    indeterminate.value = false
  })
}

function check(nextCheckedKeys: string[]) {
  if (props.treeType === 'tree') {
    checkedKeys.value = nextCheckedKeys.filter((item) => !item.startsWith('parent-'))
  } else {
    checkedKeys.value = nextCheckedKeys
  }
  if (props.treeType === 'tree') {
    const isEqual = checkedKeys.value.length === defaultChecked.value.length
    checkAll.value = isEqual
    indeterminate.value = !!nextCheckedKeys.length && !isEqual
    return
  }
  checkAll.value = checkedKeys.value.length === preferenceAttrList.value.length
  indeterminate.value =
    !!nextCheckedKeys.length && nextCheckedKeys.length < preferenceAttrList.value.length
}

function handleCancel() {
  visible.value = false
}

async function handleOk() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  cmdbStore.setIsTableLoading(true)
  await nextTick()
  emit('batchDownload', { ...formModel, checkedKeys: checkedKeys.value })
  setTimeout(() => {
    cmdbStore.setIsTableLoading(false)
    handleCancel()
  }, 2000)
}

function onCheckAllChange(e: { target: { checked: boolean } }) {
  checkedKeys.value = e.target.checked
    ? preferenceAttrList.value.map((attr) => attr[`${props.replaceFields.key}`])
    : []
  indeterminate.value = false
  checkAll.value = e.target.checked
}

defineExpose({ open })
</script>

<template>
  <a-modal
    v-model:open="visible"
    :title="t('cmdb.components.downloadCI')"
    width="700px"
    @cancel="handleCancel"
    @ok="handleOk"
  >
    <a-form ref="formRef" :model="formModel" :rules="formRules" :label-col="{ span: 6 }" :wrapper-col="{ span: 15 }">
      <a-form-item :label="t('cmdb.components.filename')" name="filename">
        <a-input v-model:value="formModel.filename" :placeholder="t('cmdb.components.filenameInputTips')" />
      </a-form-item>
      <a-form-item v-if="showFileTypeSelect" :label="t('cmdb.components.saveType')" name="type">
        <a-select v-model:value="formModel.type" :placeholder="t('cmdb.components.saveTypeTips')">
          <a-select-option v-for="item in typeList" :key="item.id" :value="item.id">
            {{ item.label }}
          </a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item :label="t('cmdb.ci.qrcodeExport')" name="exportQRCode">
        <a-checkbox v-model:checked="formModel.exportQRCode">
          {{ t('cmdb.ci.qrcodeExport') }}
        </a-checkbox>
      </a-form-item>
      <a-form-item :label="t('cmdb.ciType.selectAttributes')">
        <div
          :style="{
            paddingLeft: '26px',
            backgroundColor: '#e9e9e9',
            borderTopLeftRadius: '5px',
            borderTopRightRadius: '5px',
          }"
        >
          <a-checkbox
            :indeterminate="indeterminate"
            :checked="checkAll"
            :style="{ marginRight: '10px' }"
            @change="onCheckAllChange"
          />{{ t('checkAll') }}
        </div>
        <div
          :style="{
            height: '200px',
            overflow: 'auto',
            borderLeft: '1px solid #e9e9e9',
            borderBottom: '1px solid #e9e9e9',
          }"
        >
          <a-tree
            checkable
            default-expand-all
            :selectable="false"
            :auto-expand-parent="true"
            :tree-data="preferenceAttrList"
            :field-names="replaceFields"
            :checked-keys="checkedKeys"
            @check="check"
          />
        </div>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<style></style>
