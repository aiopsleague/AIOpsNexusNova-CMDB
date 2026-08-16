<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { AppstoreOutlined } from '@ant-design/icons-vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import JsonEditor from '@/modules/cmdb/components/JsonEditor/jsonEditor.vue'
import CIReferenceAttr from '@/components/ciReferenceAttr/index.vue'
import CiFileField from '@/modules/cmdb/components/CiFileField.vue'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    group?: Record<string, any>
    attributeList?: any[]
    ciTypeId?: number | string
  }>(),
  {
    group: () => ({}),
    attributeList: () => [],
    ciTypeId: '',
  }
)

const formRef = ref()
const jsonEditorRef = ref<InstanceType<typeof JsonEditor>>()
const editAttr = ref<Record<string, any> | null>(null)

const formModel = reactive<Record<string, any>>({})

const filteredAttributes = computed<any[]>(() =>
  (props.group?.attributes || []).filter(
    (item: any) =>
      !(
        item.default &&
        item.default.default &&
        typeof item.default.default === 'string' &&
        item.default.default.startsWith('$')
      )
  )
)

const formRules = computed<Record<string, any>>(() => {
  const rules: Record<string, any> = {}
  filteredAttributes.value.forEach((attr: any) => {
    rules[attr.name] = [{ required: attr.is_required, message: t('placeholder2') + `${attr.alias || attr.name}` }]
  })
  return rules
})

function isLongText(attr: Record<string, any>): boolean {
  return (
    attr.value_type === '2' &&
    attr.is_index === false &&
    !attr.is_link &&
    !attr.is_file &&
    !attr.is_password
  )
}

function isNil(value: unknown): boolean {
  return value === null || value === undefined
}

function getChoiceDefault(attr: any): any {
  if (isNil(attr?.default?.default)) {
    return attr.is_list ? [] : null
  }

  if (attr.is_list) {
    let defaultValue: any[] = []
    if (Array.isArray(attr.default.default)) {
      defaultValue = attr.default.default
    } else {
      defaultValue = String(attr.default.default).split(',')
    }
    if (['0', '1', '11'].includes(attr.value_type)) {
      defaultValue = defaultValue?.map((item) => {
        const numberValue = Number(item)
        return Number.isNaN(numberValue) ? item : numberValue
      })
    }
    return defaultValue
  }

  let defaultValue = attr.default.default
  if (['0', '1', '11'].includes(attr.value_type)) {
    const numberValue = Number(defaultValue)
    defaultValue = Number.isNaN(numberValue) ? attr.default.default : numberValue
  }
  return defaultValue
}

function getInitialValue(attr: any): any {
  if (attr.is_reference) return attr.is_list ? [] : ''
  if (attr.is_bool) return attr.default && attr.default.default ? Boolean(attr.default.default) : false
  if (attr.is_file) return undefined
  if (attr.is_choice) return getChoiceDefault(attr)
  if (isLongText(attr)) return attr.default && attr.default.default ? attr.default.default : null
  if (attr.is_list) {
    return attr.default && attr.default.default
      ? Array.isArray(attr.default.default)
        ? attr.default.default.join(',')
        : attr.default.default
      : ''
  }
  if (attr.value_type === '0' || attr.value_type === '1') {
    return attr.default && attr.default.default !== undefined && attr.default.default !== null
      ? attr.default.default
      : null
  }
  if (attr.value_type === '4' || attr.value_type === '3') {
    return attr.default && attr.default.default ? dayjs(attr.default.default) : null
  }
  if (attr.value_type === '6') {
    return attr.default && attr.default.default ? JSON.stringify(attr.default.default) : ''
  }
  return attr.default && attr.default.default ? attr.default.default : null
}

function initFormModel() {
  filteredAttributes.value.forEach((attr: any) => {
    formModel[attr.name] = getInitialValue(attr)
  })
}

watch(() => props.group, initFormModel, { immediate: true, deep: true })

function handleFocusInput(e: FocusEvent, attr: any) {
  const _tempFind = props.attributeList.find((item: any) => item.name === attr.name)
  if (_tempFind && _tempFind.value_type === '6') {
    editAttr.value = attr
    ;(e.target as HTMLInputElement)?.blur()
    const jsonData = formModel[attr.name]
    jsonEditorRef.value?.open(null, null, jsonData ? JSON.parse(jsonData) : {})
  } else {
    editAttr.value = null
  }
}

async function getData(): Promise<Record<string, any> | 'error'> {
  try {
    return await formRef.value.validate()
  } catch {
    return 'error'
  }
}

function jsonEditorOk(jsonData: any) {
  if (editAttr.value) {
    formModel[editAttr.value.name] = JSON.stringify(jsonData)
  }
}

defineExpose({ getData })
</script>

<template>
  <a-form ref="formRef" :model="formModel" :rules="formRules">
    <a-divider style="font-size:14px;margin:14px 0;font-weight:700;">{{ group.name || t('other') }}</a-divider>
    <a-row :gutter="24" align="top">
      <a-col v-for="(attr, attr_idx) in filteredAttributes" :key="attr.name + attr_idx" :span="12">
        <a-form-item :label="attr.alias || attr.name" :colon="false" :name="attr.name">
          <CIReferenceAttr
            v-if="attr.is_reference"
            v-model:value="formModel[attr.name]"
            :reference-type-id="attr.reference_type_id"
            :is-list="attr.is_list"
          />
          <a-switch v-else-if="attr.is_bool" v-model:checked="formModel[attr.name]" />
          <CiFileField
            v-else-if="attr.is_file"
            :is-edit="true"
            :is-list="attr.is_list"
            :attr-id="attr.id"
            :value="formModel[attr.name]"
            @input="(val: string) => (formModel[attr.name] = val)"
          />
          <a-textarea
            v-else-if="isLongText(attr)"
            v-model:value="formModel[attr.name]"
            style="width: 100%"
          />
          <a-select
            v-else-if="attr.is_choice"
            v-model:value="formModel[attr.name]"
            :style="{ width: '100%' }"
            :placeholder="t('placeholder2')"
            :mode="attr.is_list ? 'multiple' : undefined"
            show-search
            allow-clear
          >
            <a-select-option
              v-for="(choice, choice_idx) in attr.choice_value"
              :key="'New_' + attr.name + choice_idx"
              :value="choice[0]"
            >
              <span :style="{ ...(choice[1] ? choice[1].style : {}), display: 'inline-flex', alignItems: 'center' }">
                <template v-if="choice[1] && choice[1].icon && choice[1].icon.name">
                  <img
                    v-if="choice[1].icon.id && choice[1].icon.url"
                    :src="`/api/common-setting/v1/file/${choice[1].icon.url}`"
                    :style="{ maxHeight: '13px', maxWidth: '13px', marginRight: '5px' }"
                  />
                  <AppstoreOutlined
                    v-else
                    :style="{ color: choice[1].icon.color, marginRight: '5px' }"
                  />
                </template>
                <a-tooltip placement="topLeft" :title="choice[1] ? choice[1].label || choice[0] : choice[0]">
                  {{ choice[1] ? choice[1].label || choice[0] : choice[0] }}
                </a-tooltip>
              </span>
            </a-select-option>
          </a-select>
          <a-input v-else-if="attr.is_list" v-model:value="formModel[attr.name]" :style="{ width: '100%' }" />
          <a-input-number
            v-else-if="attr.value_type === '0' || attr.value_type === '1'"
            v-model:value="formModel[attr.name]"
            style="width: 100%"
          />
          <a-date-picker
            v-else-if="attr.value_type === '4' || attr.value_type === '3'"
            v-model:value="formModel[attr.name]"
            style="width: 100%"
            :format="attr.value_type === '4' ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss'"
            :show-time="attr.value_type === '4' ? false : { format: 'HH:mm:ss' }"
          />
          <a-input
            v-else
            v-model:value="formModel[attr.name]"
            style="width: 100%"
            @focus="(e: FocusEvent) => handleFocusInput(e, attr)"
          />
        </a-form-item>
      </a-col>
    </a-row>
    <JsonEditor ref="jsonEditorRef" @json-editor-ok="jsonEditorOk" />
  </a-form>
</template>
