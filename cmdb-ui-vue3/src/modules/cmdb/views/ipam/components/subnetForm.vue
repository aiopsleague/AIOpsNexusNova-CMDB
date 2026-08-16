<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { postIPAMSubnet, getIPAMSubnetById, putIPAMSubnet } from '@/modules/cmdb/api/ipam'
import { getCITypeGroupById, getCITypes } from '@/modules/cmdb/api/CIType'
import { searchCI } from '@/modules/cmdb/api/ci'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import Crontab from '@/components/Crontab/index.vue'
import CIReferenceAttr from '@/components/ciReferenceAttr/index.vue'

const props = withDefaults(
  defineProps<{
    subnetCIType?: Record<string, any>
  }>(),
  {
    subnetCIType: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'ok'): void
}>()

const { t } = useI18n()

const subnetFormRef = ref()
const nodeId = ref<string | number | null>(null)
const parentId = ref<string | number | null>(null)
const actionType = ref('create')
const visible = ref(false)
const form = ref<Record<string, any>>({
  scan_enabled: true,
  cron: '',
})
const basicFormGroup = ref<any[]>([])
const formRules = ref<Record<string, any>>({})

const agentTypeRadioList = computed(() => [
  { value: 'master', label: t('cmdb.ipam.masterMachine') },
  { value: 'agent_id', label: t('cmdb.ipam.specifyMachine') },
])
const agentType = ref('master')
const agentId = ref('')

const cronVisible = ref(false)

async function open(id: string | number | null, type: string, pid: string | number | null) {
  visible.value = true
  actionType.value = type
  nodeId.value = id
  parentId.value = pid || null

  let nodeData: Record<string, any> = {}
  if (type === 'edit') {
    nodeData = await getIPAMSubnetById(id as string | number)
    form.value.scan_enabled = !!nodeData.scan_enabled

    if (nodeData?.scan_enabled) {
      form.value.cron = nodeData.cron

      if (nodeData.agent_id) {
        if (nodeData.agent_id === '0x0000') {
          agentType.value = 'master'
        } else {
          agentType.value = 'agent_id'
          agentId.value = nodeData.agent_id
        }
      }
    }
  }

  const groupAttr = await getCITypeGroupById(props.subnetCIType.id)
  const nextForm: Record<string, any> = {
    ...form.value,
  }
  const nextFormRules: Record<string, any> = {}
  let nextBasicFormGroup: any[] = []

  groupAttr.map((group: any) => {
    group.attributes = group?.attributes?.filter?.((attr: any) => !attr.sys_computed && !attr.is_computed) || []
    if (group.attributes.length) {
      group.attributes.forEach((attr: any) => {
        nextForm[attr.name] = nodeData?.[attr.name] ?? undefined

        if (attr?.is_choice) {
          let choice_value = attr?.choice_value || []
          if (attr.name === 'assign_status') {
            choice_value = choice_value.filter((item: any) => item?.[0] !== 1)
          }

          attr.selectOption = choice_value.map((item: any) => {
            return {
              label: item?.[1]?.label || item?.[0] || '',
              value: item?.[0],
            }
          })
        }

        if (attr.is_required) {
          nextFormRules[attr.name] = [
            {
              required: true,
              message: t('placeholder1'),
            },
          ]
        }
      })

      nextBasicFormGroup.push({
        name: group.name,
        attributes: group.attributes,
      })
    }
  })

  nextBasicFormGroup = await handleReferenceAttr(nextBasicFormGroup, nextForm)

  form.value = nextForm
  basicFormGroup.value = nextBasicFormGroup
  formRules.value = nextFormRules
}

async function handleReferenceAttr(formListParam: any[], ci: Record<string, any>) {
  const map: Record<string, Record<string, Record<string, unknown>>> = {}
  formListParam.forEach((group: any) => {
    group.attributes.forEach((attr: any) => {
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

  formListParam.forEach((group: any) => {
    group.attributes.forEach((attr: any) => {
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
  })

  return formListParam
}

function handleClose() {
  form.value = {
    scan_enabled: true,
    cron: '',
  }
  basicFormGroup.value = []
  formRules.value = {}
  agentType.value = 'master'
  agentId.value = ''
  cronVisible.value = false
  nodeId.value = null
  parentId.value = null
  actionType.value = 'create'

  subnetFormRef.value?.clearValidate()

  visible.value = false
}

async function handleSubmit() {
  try {
    await subnetFormRef.value?.validate()
  } catch {
    return
  }

  if (!validateScan()) {
    return
  }

  const { cron, ...otherParams } = form.value
  const params: Record<string, any> = {
    ...otherParams,
  }

  if (form.value.scan_enabled) {
    params.cron = cron

    switch (agentType.value) {
      case 'master':
        params.agent_id = '0x0000'
        break
      case 'agent_id':
        params.agent_id = agentId.value
        break
      default:
        break
    }
  }

  if (actionType.value === 'edit') {
    if (parentId.value) {
      params.parent_id = parentId.value
    }
    await putIPAMSubnet(nodeId.value as string | number, params)
    message.success(t('editSuccess'))
  } else {
    params.parent_id = nodeId.value
    await postIPAMSubnet(params)
    message.success(t('addSuccess'))
  }

  emit('ok')
  handleClose()
}

function validateScan() {
  if (form.value.scan_enabled) {
    switch (agentType.value) {
      case 'agent_id':
        if (!agentId.value) {
          message.error(t('cmdb.ipam.specifyMachineTips'))
          return false
        }
        break
      default:
        break
    }

    if (!form.value.cron) {
      message.error(t('cmdb.ipam.cronRequiredTip'))
      return false
    }
  }

  return true
}

function crontabFill(cron: string) {
  form.value.cron = cron
}

function hideCron() {
  cronVisible.value = false
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
  <CustomDrawer
    v-model:open="visible"
    width="800px"
    :title="t(actionType === 'edit' ? 'cmdb.ipam.editSubnet' : 'cmdb.ipam.addSubnet')"
    @close="handleClose"
  >
    <a-form
      ref="subnetFormRef"
      :model="form"
      :rules="formRules"
      :label-col="{ span: 4 }"
      :wrapper-col="{ span: 17 }"
    >
      <div
        v-for="(group, groupIndex) in basicFormGroup"
        :key="groupIndex"
      >
        <div class="subnet-form-title">
          {{ group.name }}
        </div>

        <a-form-item
          v-for="attr in group.attributes"
          :key="attr.name"
          :label="attr.alias || attr.name"
          :name="attr.name"
        >
          <CIReferenceAttr
            v-if="attr.is_reference"
            :reference-type-id="attr.reference_type_id"
            :is-list="attr.is_list"
            :reference-show-attr-name="attr.showAttrName"
            :init-select-option="getInitReferenceSelectOption(attr)"
            :value="form[attr.name]"
            @change="(val: any) => (form[attr.name] = val)"
          />
          <a-select
            v-else-if="attr.is_choice"
            v-model:value="form[attr.name]"
            :mode="attr.is_list ? 'multiple' : undefined"
            show-search
            allow-clear
          >
            <a-select-option
              v-for="(choiceItem, choiceIndex) in attr.selectOption"
              :key="choiceIndex"
              :value="choiceItem.value"
            >
              {{ choiceItem.label }}
            </a-select-option>
          </a-select>
          <a-switch
            v-else-if="attr.is_bool"
            v-model:checked="form[attr.name]"
          />
          <a-input
            v-else
            v-model:value="form[attr.name]"
            :placeholder="t('placeholder1')"
          />
        </a-form-item>
      </div>

      <div class="subnet-form-title">
        <a-row>
          <a-col :span="4">
            {{ t('cmdb.ipam.scanRule') }}
          </a-col>
          <a-switch v-model:checked="form.scan_enabled" />
        </a-row>
      </div>

      <template v-if="form.scan_enabled">
        <a-form-item :label="t('cmdb.ipam.adExecTarget')">
          <div class="custom-radio">
            <a-radio-group v-model:value="agentType">
              <a-radio
                v-for="radio in agentTypeRadioList"
                :key="radio.value"
                :value="radio.value"
              >
                {{ radio.label }}
              </a-radio>
            </a-radio-group>
            <span
              v-show="agentType === 'master'"
              class="subnet-form-agent-tip"
            >
              {{ t('cmdb.ipam.masterMachineTip') }}
            </span>
            <a-input
              v-show="agentType === 'agent_id'"
              v-model:value="agentId"
              :style="{ width: '300px' }"
              :placeholder="t('cmdb.ipam.oneagentIdTips')"
            />
          </div>
        </a-form-item>

        <a-form-item :label="t('cmdb.ipam.adInterval')">
          <a-popover v-model:open="cronVisible" trigger="click">
            <template #content>
              <Crontab
                :hide-component="['second', 'year']"
                :expression="form.cron"
                :has-footer="true"
                @fill="crontabFill"
                @hide="hideCron"
              />
            </template>
            <a-input
              v-model:value="form.cron"
              :placeholder="t('cmdb.ipam.cronTips')"
            />
          </a-popover>
        </a-form-item>
      </template>
    </a-form>

    <div class="custom-drawer-bottom-action">
      <a-button @click="handleClose">{{ t('cancel') }}</a-button>
      <a-button type="primary" @click="handleSubmit">{{ t('save') }}</a-button>
    </div>
  </CustomDrawer>
</template>

<style lang="less" scoped>
.subnet-form-title {
  font-size: 14px;
  font-weight: 700;
  color: #000000;
  margin-bottom: 20px;
}

.subnet-form-agent-tip {
  font-size: 12px;
  color: #86909c;
  line-height: 14px;
}
</style>
