<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { postDCIM, putDCIM } from '@/modules/cmdb/api/dcim'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { searchCI } from '@/modules/cmdb/api/ci'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import { DCIM_TYPE } from '../constants'
import CIReferenceAttr from '@/components/ciReferenceAttr/index.vue'

const props = withDefaults(
  defineProps<{
    allAttrList?: Record<string, any>
  }>(),
  {
    allAttrList: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'ok', payload: { dcimType: string; editType: string }): void
}>()

interface OpenPayload {
  nodeId?: string | number | null
  parentId?: string | number | null
  dcimType?: string
}

const { t } = useI18n()

const formRef = ref()

const visible = ref(false)
const nodeId = ref<string | number | null>(null)
const parentId = ref<string | number | null>(null)
const dcimType = ref('')

const formList = ref<any[]>([])
const form = ref<Record<string, any>>({})
const formRules = ref<Record<string, any>>({})

const confirmLoading = ref(false)

const modalTitle = computed(() => {
  switch (dcimType.value) {
    case DCIM_TYPE.REGION:
      return nodeId.value ? 'cmdb.dcim.editRegion' : 'cmdb.dcim.addRegion'
    case DCIM_TYPE.IDC:
      return nodeId.value ? 'cmdb.dcim.editIDC' : 'cmdb.dcim.addIDC'
    case DCIM_TYPE.SERVER_ROOM:
      return nodeId.value ? 'cmdb.dcim.editServerRoom' : 'cmdb.dcim.addServerRoom'
    case DCIM_TYPE.RACK:
      return nodeId.value ? 'cmdb.dcim.editRack' : 'cmdb.dcim.addRack'
    default:
      return ''
  }
})

async function open({ nodeId: id = null, parentId: pid = null, dcimType: type = '' }: OpenPayload = {}) {
  nodeId.value = id

  let nodeData: Record<string, any> = {}
  if (id) {
    const res = await searchCI({
      q: `_id:${id}`,
      count: 9999,
    })
    nodeData = res?.result?.[0] || {}
  }

  parentId.value = pid
  dcimType.value = type
  visible.value = true

  const nextForm: Record<string, any> = {}
  const nextFormRules: Record<string, any> = {}
  let nextFormList: any[] = []

  let attrList: any[] = cloneDeep(props.allAttrList?.[type]?.attributes ?? [])
  attrList = attrList?.filter?.((attr) => !attr.sys_computed && !attr.is_computed) || []

  if (attrList.length) {
    attrList.forEach((attr) => {
      let value = nodeData?.[attr.name] ?? attr?.default?.default ?? undefined

      if (Array.isArray(value) && ['0', '1', '2', '9'].includes(attr.value_type)) {
        value = value.join(',')
      }
      nextForm[attr.name] = value

      if (attr?.is_choice) {
        const choice_value = attr?.choice_value || []
        attr.selectOption = choice_value.map((item: any) => {
          return {
            label: item?.[1]?.label || item?.[0] || '',
            value: item?.[0],
          }
        })
      }
      nextFormList.push(attr)

      if (attr.is_required) {
        nextFormRules[attr.name] = [
          {
            required: true,
            message: attr?.is_choice ? t('placeholder2') : t('placeholder1'),
          },
        ]
      }
    })
  }

  nextFormList = await handleReferenceAttr(nextFormList, nextForm)

  form.value = nextForm
  formList.value = nextFormList
  formRules.value = nextFormRules
}

async function handleReferenceAttr(formListParam: any[], ci: Record<string, any>) {
  const map: Record<string, Record<string, Record<string, unknown>>> = {}
  formListParam.forEach((attr) => {
    if (attr?.is_reference && attr?.reference_type_id && ci[attr.name]) {
      const ids = Array.isArray(ci[attr.name]) ? ci[attr.name] : ci[attr.name] ? [ci[attr.name]] : []
      if (ids.length) {
        if (!map?.[attr.reference_type_id]) {
          map[attr.reference_type_id] = {}
        }
        ids.forEach((id: string | number) => {
          map[attr.reference_type_id][id] = {}
        })
      }
    }
  })
  if (!Object.keys(map).length) {
    return formListParam
  }

  const ciTypesRes = await getCITypes({
    type_ids: Object.keys(map).join(','),
  })
  const showAttrNameMap: Record<string, string> = {}
  ciTypesRes.ci_types.forEach((ciType: any) => {
    showAttrNameMap[ciType.id] = ciType?.show_name || ciType?.unique_name || ''
  })

  const allRes = await Promise.all(
    Object.keys(map).map((key) => {
      return searchCI({
        q: `_type:${key},_id:(${Object.keys(map[key]).join(';')})`,
        count: 9999,
      })
    })
  )

  const ciNameMap: Record<string, any> = {}
  allRes.forEach((res: any) => {
    res.result.forEach((item: any) => {
      ciNameMap[item._id] = item
    })
  })

  formListParam.forEach((attr) => {
    if (attr?.is_reference && attr?.reference_type_id) {
      attr.showAttrName = showAttrNameMap?.[attr?.reference_type_id] || ''

      const referenceShowAttrNameMap: Record<string, any> = {}
      const referenceCIIds = ci[attr.name]
      ;(Array.isArray(referenceCIIds) ? referenceCIIds : referenceCIIds ? [referenceCIIds] : []).forEach(
        (id: string | number) => {
          referenceShowAttrNameMap[id] = ciNameMap?.[id]?.[attr.showAttrName] ?? id
        }
      )
      attr.referenceShowAttrNameMap = referenceShowAttrNameMap
    }
  })

  return formListParam
}

function handleCancel() {
  visible.value = false
  nodeId.value = null
  parentId.value = null
  dcimType.value = ''
  form.value = {}
  formRules.value = {}
  formList.value = []
  confirmLoading.value = false

  formRef.value?.clearValidate()
}

async function handleOk() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  confirmLoading.value = true

  try {
    if (nodeId.value) {
      await putDCIM(dcimType.value, nodeId.value, {
        ...form.value,
        parent_id: Number(parentId.value),
      })
    } else {
      await postDCIM(dcimType.value, {
        ...form.value,
        parent_id: Number(parentId.value),
      })
    }
    emit('ok', {
      dcimType: dcimType.value,
      editType: nodeId.value ? 'edit' : 'create',
    })
    handleCancel()
  } catch (error) {
    console.log('submit fail', error)
  }

  confirmLoading.value = false
}

function getInitReferenceSelectOption(attr: any) {
  const option = Object.keys(attr?.referenceShowAttrNameMap || {}).map((key) => {
    return {
      key: Number(key),
      title: attr?.referenceShowAttrNameMap?.[Number(key)] ?? '',
    }
  })
  return option
}

defineExpose({ open })
</script>

<template>
  <a-modal
    v-model:open="visible"
    :width="700"
    :title="t(modalTitle)"
    :confirm-loading="confirmLoading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <a-form
      ref="formRef"
      :model="form"
      :rules="formRules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
      class="dcim-form"
    >
      <a-form-item v-for="item in formList" :key="item.name" :label="item.alias || item.name" :name="item.name">
        <CIReferenceAttr
          v-if="item.is_reference"
          :reference-type-id="item.reference_type_id"
          :is-list="item.is_list"
          :reference-show-attr-name="item.showAttrName"
          :init-select-option="getInitReferenceSelectOption(item)"
          :value="form[item.name]"
          @change="(val: any) => (form[item.name] = val)"
        />
        <a-select
          v-else-if="item.is_choice"
          v-model:value="form[item.name]"
          :mode="item.is_list ? 'multiple' : undefined"
          show-search
          allow-clear
        >
          <a-select-option v-for="(choiceItem, choiceIndex) in item.selectOption" :key="choiceIndex" :value="choiceItem.value">
            {{ choiceItem.label }}
          </a-select-option>
        </a-select>
        <a-switch v-else-if="item.is_bool" v-model:checked="form[item.name]" />

        <a-input-number
          v-else-if="(item.value_type === '0' || item.value_type === '1') && !item.is_list"
          v-model:value="form[item.name]"
          class="dcim-form-input"
        />

        <a-date-picker
          v-else-if="(item.value_type === '4' || item.value_type === '3') && !item.is_list"
          v-model:value="form[item.name]"
          class="dcim-form-input"
          :format="item.value_type === '4' ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss'"
          :value-format="item.value_type === '4' ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss'"
          :show-time="item.value_type === '4' ? false : { format: 'HH:mm:ss' }"
        />

        <a-input v-else v-model:value="form[item.name]" :placeholder="t('placeholder1')" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<style lang="less" scoped>
.dcim-form {
  padding-right: 12px;
  max-height: 400px;
  overflow-y: auto;
  overflow-x: hidden;

  &-input {
    width: 100%;
  }
}
</style>
