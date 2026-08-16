<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { postIPAMAddress } from '@/modules/cmdb/api/ipam'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { searchCI } from '@/modules/cmdb/api/ci'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import CIReferenceAttr from '@/components/ciReferenceAttr/index.vue'

const props = withDefaults(
  defineProps<{
    attrList?: any[]
  }>(),
  {
    attrList: () => [],
  }
)

const emit = defineEmits<{
  (e: 'ok'): void
  (e: 'batchAssign', payload: { paramsList: any[]; ipList: any[] }): void
}>()

const { t } = useI18n()

const assignFormRef = ref()

const visible = ref(false)
const ipData = ref<Record<string, any>>({})
const ipList = ref<any[]>([])
const nodeId = ref<string | number>(-1)
const formList = ref<any[]>([])
const form = ref<Record<string, any>>({})
const formRules = ref<Record<string, any>>({})
const confirmLoading = ref(false)
const isBatch = ref(false)

/** Split an array into fixed-size chunks (drop-in for lodash.chunk). */
function chunk<T>(list: T[], size: number): T[][] {
  const result: T[][] = []
  for (let i = 0; i < list.length; i += size) {
    result.push(list.slice(i, i + size))
  }
  return result
}

async function open({ ipList: nextIpList = [], ipData: nextIpData = null, nodeId: nextNodeId }: any) {
  isBatch.value = nextIpList.length !== 0
  ipList.value = nextIpList.length ? cloneDeep(nextIpList) : [nextIpData?.ip ?? '']
  ipData.value = nextIpData || {}
  nodeId.value = nextNodeId || -1
  visible.value = true

  const nextForm: Record<string, any> = {}
  const nextFormRules: Record<string, any> = {}
  let nextFormList: any[] = []
  let attrList = cloneDeep(props.attrList)
  attrList = attrList?.filter?.((attr) => !attr.sys_computed && !attr.is_computed) || []

  if (nextIpData?.assign_status === 1) {
    nextIpData.assign_status = undefined
  }

  if (attrList.length) {
    attrList = attrList.filter(
      (item) => !['subnet_mask', 'gateway', 'name', 'mac_address', 'is_used', 'ip', 'ipam_address_id'].includes(item.name)
    )

    const assignStatusIndex = attrList.findIndex((attr) => attr.name === 'assign_status')
    if (assignStatusIndex > 0) {
      const [assignStatus] = attrList.splice(assignStatusIndex, 1)
      attrList.unshift(assignStatus)
    }

    attrList.forEach((attr) => {
      nextForm[attr.name] = nextIpData?.[attr.name] ?? undefined

      if (attr?.is_choice) {
        let choiceValue = attr?.choice_value || []
        if (attr.name === 'assign_status') {
          choiceValue = choiceValue.filter((item: any) => item?.[0] !== 1)
        }

        attr.selectOption = choiceValue.map((item: any) => {
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

async function handleReferenceAttr(list: any[], ci: Record<string, any>) {
  const map: Record<string, Record<string, Record<string, unknown>>> = {}
  list.forEach((attr) => {
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
    return list
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

  list.forEach((attr) => {
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

  return list
}

function handleCancel() {
  visible.value = false
  ipData.value = {}
  nodeId.value = -1
  form.value = {}
  formRules.value = {}
  formList.value = []
  confirmLoading.value = false
  isBatch.value = false

  assignFormRef.value?.clearValidate()
}

async function handleOk() {
  try {
    await assignFormRef.value?.validate()
  } catch {
    return
  }

  confirmLoading.value = true

  if (!isBatch.value) {
    await postIPAMAddress({
      ips: ipList.value,
      parent_id: nodeId.value,
      ...form.value,
      subnet_mask: ipData.value?.subnet_mask ?? undefined,
      gateway: ipData.value?.gateway ?? undefined,
    })

    emit('ok')
  } else {
    const ipChunk = chunk(ipList.value, 5)
    const paramsList = ipChunk.map((ips) => ({
      ips,
      parent_id: nodeId.value,
      ...form.value,
      subnet_mask: ipData.value?.subnet_mask ?? undefined,
      gateway: ipData.value?.gateway ?? undefined,
    }))
    emit('batchAssign', {
      paramsList,
      ipList: ipList.value,
    })
  }

  handleCancel()
  confirmLoading.value = false
}

function getInitReferenceSelectOption(attr: any) {
  return Object.keys(attr?.referenceShowAttrNameMap || {}).map((key) => {
    return {
      key: Number(key),
      title: attr?.referenceShowAttrNameMap?.[Number(key)] ?? '',
    }
  })
}

defineExpose({ open })
</script>

<template>
  <a-modal
    v-model:open="visible"
    :width="700"
    :title="t('cmdb.ipam.addressAssign')"
    :confirm-loading="confirmLoading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <a-form
      ref="assignFormRef"
      :model="form"
      :rules="formRules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
      class="assign-form"
    >
      <a-form-item label="IP">
        <span class="assign-form-ip">{{ ipList.join(', ') }}</span>
      </a-form-item>
      <a-form-item
        v-for="item in formList"
        :key="item.name"
        :label="item.alias || item.name"
        :name="item.name"
      >
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
          <a-select-option
            v-for="(choiceItem, choiceIndex) in item.selectOption"
            :key="choiceIndex"
            :value="choiceItem.value"
          >
            {{ choiceItem.label }}
          </a-select-option>
        </a-select>
        <a-switch
          v-else-if="item.is_bool"
          v-model:checked="form[item.name]"
        />
        <a-input
          v-else
          v-model:value="form[item.name]"
          :placeholder="t('placeholder1')"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<style lang="less" scoped>
.assign-form {
  padding-right: 12px;
  max-height: 400px;
  overflow-y: auto;
  overflow-x: hidden;

  &-ip {
    max-height: 100px;
    overflow-y: auto;
    overflow-x: hidden;
    display: block;
  }
}
</style>
