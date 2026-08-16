<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, nextTick, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { DownOutlined, InfoCircleOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import RegSelect from '@/components/RegexSelect/index.vue'
import MonacoCodeEditor from '@/components/MonacoCodeEditor/index.vue'
import { createAttribute, canDefineComputed } from '@/modules/cmdb/api/CITypeAttr'
import { getPropertyIcon, valueTypeMap } from '../../utils/helper'
import ComputedArea from './computedArea.vue'
import PreValueArea from './preValueArea.vue'
import FontArea from './fontArea.vue'
import ReferenceModelSelect from './attributeEdit/referenceModelSelect.vue'

const ENUM_VALUE_TYPE = {
  INPUT: 'input',
  DATE: 'date',
  DATE_TIME: 'dateTIme',
  NUMBER: 'number',
} as const

withDefaults(
  defineProps<{
    hasFooter?: boolean
    CITypeId?: number | null
  }>(),
  { hasFooter: true, CITypeId: null }
)

const emit = defineEmits<{
  (e: 'done', attrId: number, data: Record<string, unknown>, isCloseModal: boolean): void
  (e: 'cancel'): void
}>()

const { t } = useI18n()

const formRef = ref()

const formModel = reactive<Record<string, any>>({
  name: '',
  alias: '',
  value_type: '2',
  default_value: undefined,
  is_unique: false,
  is_required: false,
  default_show: false,
  is_sortable: false,
  is_list: false,
  is_dynamic: false,
  is_computed: false,
  reference_type_id: null,
})

const rules = {
  name: [
    { required: true, message: t('cmdb.ciType.inputAttributeName') },
    { message: t('cmdb.ciType.attributeNameTips'), pattern: /^(?!\d)[a-zA-Z_0-9]+$/ },
    { message: t('cmdb.ciType.buildinAttribute'), pattern: /^(?!(id|_id|ci_id|type|_type|ci_type)$).*$/ },
  ],
  value_type: [{ required: true }],
}

const currentValueType = ref('2')
const defaultValueJsonText = ref('{}')
const defaultValueJsonRight = ref(true)

const canDefineComputedFlag = ref(false)
const isShowComputedArea = ref(false)

const defaultForDatetime = ref('')
const reCheck = ref<Record<string, any>>({})
const enumValueType = ref<string>(ENUM_VALUE_TYPE.INPUT)

const computedAreaRef = ref<{
  setData: (data: { compute_expr?: string; compute_script?: string }) => void
  getData: () => Record<string, any>
}>()
const preValueAreaRef = ref<{
  setData: (data: { choice_value?: any[]; choice_web_hook?: any; choice_other?: any }) => void
  getData: () => Record<string, any>
  resetData: () => void
  initEnumValue: () => void
}>()
const fontAreaRef = ref<{
  setData: (data: { fontOptions?: Record<string, any> }) => void
  getData: () => Record<string, any> | undefined
}>()

const canDefineScript = computed(() => canDefineComputedFlag.value)

const valueTypeOptions = computed(() => {
  const map = valueTypeMap()
  const keys = ['0', '1', '2', '9', '3', '4', '5', '6', '7', '8', '10', '11', '12']
  return keys.map((key) => ({ key, value: map[key] }))
})

function handleSubmit(isCloseModal = true) {
  formRef.value
    .validate()
    .then(async () => {
      let values = { ...formModel }

      const { is_required, default_show, default_value, is_dynamic } = values
      const data = { is_required, default_show, is_dynamic }

      if (values.value_type === '10') {
        values.default = { default: values.is_list ? default_value || null : Boolean(default_value) }
      } else if (values.value_type === '0' && default_value) {
        if (values.is_list) {
          values.default = { default: default_value || null }
        } else {
          values.default = { default: default_value[0] || null }
        }
      } else if (values.value_type === '6') {
        if (defaultValueJsonRight.value) {
          values.default = { default: parseJsonSafe(defaultValueJsonText.value) }
        } else {
          values.default = { default: null }
        }
      } else if (default_value || default_value === 0) {
        if (values.value_type === '3' && !values.is_list) {
          if (default_value === '$created_at' || default_value === '$updated_at') {
            values.default = { default: default_value }
          } else {
            values.default = { default: dayjs(default_value).format('YYYY-MM-DD HH:mm:ss') }
          }
        } else if (values.value_type === '4' && !values.is_list) {
          values.default = { default: dayjs(default_value).format('YYYY-MM-DD') }
        } else {
          values.default = { default: default_value }
        }
      } else {
        values.default = { default: null }
      }

      if (values.is_computed) {
        const computedAreaData = computedAreaRef.value?.getData()
        values = { ...values, ...computedAreaData }
      } else if (!['6', '7', '10', '11'].includes(values.value_type)) {
        const preValueAreaData = preValueAreaRef.value?.getData()
        if (preValueAreaData?.isError) {
          return
        }
        values = { ...values, ...preValueAreaData }
      }

      delete values.is_required
      delete values.default_show
      delete values.default_value

      const fontOptions = fontAreaRef.value?.getData()

      values.is_index = !['6', '7', '8', '9', '11'].includes(values.value_type)

      switch (values.value_type) {
        case '7':
          values.value_type = '2'
          values.is_password = true
          break
        case '8':
          values.value_type = '2'
          values.is_link = true
          break
        case '9':
          values.value_type = '2'
          break
        case '10':
          values.value_type = '7'
          values.is_bool = true
          break
        case '11':
          values.value_type = '0'
          values.is_reference = true
          break
        case '12':
          values.value_type = '2'
          values.is_file = true
          break
        default:
          break
      }

      const { attr_id } = await createAttribute({ ...values, option: { fontOptions } })

      formRef.value.resetFields()
      currentValueType.value = '2'
      emit('done', attr_id, data, isCloseModal)
    })
    .catch(() => {
      throw new Error('validate failed')
    })
}

function parseJsonSafe(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    defaultValueJsonRight.value = false
    return null
  }
}

function handleClose() {
  emit('cancel')
}

async function checkCanDefineComputed() {
  try {
    await canDefineComputed()
    canDefineComputedFlag.value = true
  } catch {
    canDefineComputedFlag.value = false
  }
}

function handleChangeValueType(value: string) {
  nextTick(() => {
    currentValueType.value = value
    if (['6', '10', '11'].includes(value)) {
      reCheck.value = {}
    }

    switch (value) {
      case '0':
      case '1':
        enumValueType.value = ENUM_VALUE_TYPE.NUMBER
        break
      case '3':
        enumValueType.value = ENUM_VALUE_TYPE.DATE_TIME
        break
      case '4':
        enumValueType.value = ENUM_VALUE_TYPE.DATE
        break
      default:
        enumValueType.value = ENUM_VALUE_TYPE.INPUT
        break
    }

    if (['0', '1', '3', '4'].includes(value)) {
      preValueAreaRef.value?.initEnumValue()
    }

    handleSwitchType({ valueType: value })
  })
}

function onChange(checked: boolean, property: string) {
  if (property === 'is_computed') {
    isShowComputedArea.value = checked
    if (checked) {
      formModel.is_list = false
      formModel.is_unique = false
      formModel.is_sortable = false
    }
  }
  if (property === 'is_list') {
    handleSwitchType({ checked })
  }
  if (checked && property === 'is_sortable') {
    message.warning(t('cmdb.ciType.addAttributeTips1'))
    formModel.is_required = true
  }
  if (!checked && property === 'is_required' && formModel.is_sortable) {
    message.warning(t('cmdb.ciType.addAttributeTips1'))
    nextTick(() => {
      formModel.is_required = true
    })
  }
}

function handleSwitchType({ checked, valueType }: { checked?: boolean; valueType?: string } = {}) {
  const isList = checked ?? formModel.is_list
  const type = valueType ?? currentValueType.value

  let defaultValue: any = isList || type === '0' ? [] : ''

  switch (type) {
    case '2':
    case '9':
      defaultValue = ''
      break
    case '10':
      defaultValue = isList ? '' : false
      break
    default:
      break
  }

  formModel.default_value = defaultValue
}

function onJsonChange() {
  defaultValueJsonRight.value = true
}

function selectIntDefaultValue(value: string) {
  formModel.default_value = [value]
}

function changeDefaultForDatetime(value: string) {
  defaultForDatetime.value = value
  switch (value) {
    case '$custom_time':
      formModel.default_value = undefined
      break
    case '$updated_at':
      formModel.is_dynamic = true
      break
    default:
      break
  }
}

function onClickDateTime({ key }: { key: string }) {
  defaultForDatetime.value = key
  formModel.default_value = key
}

function getLimitedFormat(): string[] {
  if (['0'].includes(currentValueType.value)) {
    return ['number', 'phone', 'landline', 'zipCode', 'IDCard', 'monetaryAmount', 'custom']
  }
  if (['1'].includes(currentValueType.value)) {
    return ['number', 'monetaryAmount', 'custom']
  }
  if (['3', '4', '5'].includes(currentValueType.value)) {
    return ['custom']
  }
  if (currentValueType.value === '8') {
    return ['link', 'custom']
  }
  return []
}

function resetPreValue() {
  preValueAreaRef.value?.resetData()
}

defineExpose({ handleSubmit, checkCanDefineComputed })
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <a-form ref="formRef" :model="formModel" :rules="rules" class="create-new-attribute" :label-col="{ span: 8 }" :wrapper-col="{ span: 15 }">
    <a-divider style="font-size: 14px; margin-top: 6px">{{ t('cmdb.ciType.basicConfig') }}</a-divider>
    <a-row>
      <a-col :span="12">
        <a-form-item :label="t('cmdb.ciType.AttributeName')" name="name">
          <a-input v-model:value="formModel.name" :placeholder="t('cmdb.ciType.English')" />
          <div class="ant-form-explain">{{ t('cmdb.ciType.fieldCannotModify') }}</div>
        </a-form-item>
      </a-col>
      <a-col :span="12">
        <a-form-item :label="t('cmdb.common.alias')" name="alias">
          <a-input v-model:value="formModel.alias" :placeholder="t('cmdb.ciType.aliasPlaceholder')" />
        </a-form-item>
      </a-col>
    </a-row>
    <a-row>
      <a-col :span="12">
        <a-form-item :label="t('cmdb.ciType.DataType')" name="value_type">
          <a-select v-model:value="formModel.value_type" style="width: 100%" @change="handleChangeValueType">
            <a-select-option v-for="item in valueTypeOptions" :key="item.key" :value="item.key">
              <span class="value-type-icon"><component :is="getPropertyIcon({ value_type: item.key })" /></span>
              <span class="value-type-text">{{ item.value }}</span>
              <span v-if="item.key === '2'" class="value-type-des">{{ t('cmdb.ciType.shortTextTip') }}</span>
              <span v-if="item.key === '3'" class="value-type-des">yyyy-mm-dd HH:MM:SS</span>
              <span v-if="item.key === '4'" class="value-type-des">yyyy-mm-dd</span>
              <span v-if="item.key === '5'" class="value-type-des">HH:MM:SS</span>
            </a-select-option>
          </a-select>
          <div class="ant-form-explain">{{ t('cmdb.ciType.fieldCannotModify') }}</div>
        </a-form-item>
      </a-col>
      <a-col v-if="currentValueType !== '11'" :span="currentValueType === '6' ? 24 : 12">
        <a-form-item
          :label-col="{ span: currentValueType === '6' ? 4 : 8 }"
          :wrapper-col="{ span: currentValueType === '6' ? 18 : 15 }"
          :label="t('cmdb.ciType.defaultValue')"
        >
          <a-input
            v-if="formModel.is_list"
            v-model:value="formModel.default_value"
            :style="{ width: '100%' }"
          />
          <a-switch v-else-if="currentValueType === '10'" v-model:checked="formModel.default_value" />
          <a-input-number
            v-else-if="currentValueType === '1'"
            v-model:value="formModel.default_value"
            style="width: 100%"
          />
          <a-select
            v-else-if="currentValueType === '0'"
            v-model:value="formModel.default_value"
            mode="tags"
            @select="selectIntDefaultValue"
          >
            <a-select-option key="$auto_inc_id">{{ t('cmdb.ciType.autoIncID') }}</a-select-option>
          </a-select>
          <a-input
            v-else-if="['2', '5', '7', '8', '9'].includes(currentValueType)"
            v-model:value="formModel.default_value"
            style="width: 100%"
          />
          <a-select
            v-else-if="currentValueType === '3' && defaultForDatetime !== '$custom_time'"
            v-model:value="formModel.default_value"
            allow-clear
            @select="changeDefaultForDatetime"
          >
            <a-select-option key="$created_at">{{ t('created_at') }}</a-select-option>
            <a-select-option key="$updated_at">{{ t('updated_at') }}</a-select-option>
            <a-select-option key="$custom_time">{{ t('cmdb.ciType.customTime') }}</a-select-option>
          </a-select>
          <template v-else-if="currentValueType === '4' || currentValueType === '3'">
            <a-date-picker
              v-model:value="formModel.default_value"
              style="width: 100%"
              :format="currentValueType === '4' ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss'"
              :show-time="currentValueType === '4' ? false : { format: 'HH:mm:ss' }"
            />
            <a-dropdown v-if="currentValueType === '3'" :trigger="['click']">
              <a><DownOutlined /></a>
              <template #overlay>
                <a-menu @click="onClickDateTime">
                  <a-menu-item key="$created_at">
                    <a>{{ t('created_at') }}</a>
                  </a-menu-item>
                  <a-menu-item key="$updated_at">
                    <a>{{ t('updated_at') }}</a>
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </template>
          <MonacoCodeEditor
            v-else-if="currentValueType === '6'"
            v-model:value="defaultValueJsonText"
            language="json"
            :height="200"
            @change="onJsonChange"
          />
        </a-form-item>
      </a-col>
      <a-col v-if="currentValueType === '11'" :span="12">
        <ReferenceModelSelect v-model="formModel.reference_type_id" />
      </a-col>
    </a-row>

    <a-col v-if="currentValueType !== '6' && currentValueType !== '7'" :span="6">
      <a-form-item :label-col="{ span: 16 }" :wrapper-col="{ span: 4 }">
        <template #label>
          <span style="position: relative; white-space: pre">{{ t('cmdb.ciType.unique') }}
            <a-tooltip :title="t('cmdb.ciType.uniqueHint')">
              <InfoCircleOutlined style="position: absolute; top: 2px; left: -17px; color: #a5a9bc" />
            </a-tooltip>
          </span>
        </template>
        <a-switch v-model:checked="formModel.is_unique" :disabled="isShowComputedArea" @change="(c: boolean) => onChange(c, 'is_unique')" />
      </a-form-item>
    </a-col>
    <a-col :span="6">
      <a-form-item :label-col="{ span: 16 }" :wrapper-col="{ span: 4 }" :label="t('cmdb.common.required')">
        <a-switch v-model:checked="formModel.is_required" @change="(c: boolean) => onChange(c, 'is_required')" />
      </a-form-item>
    </a-col>
    <a-col :span="6">
      <a-form-item :label-col="{ span: 16 }" :wrapper-col="{ span: 4 }">
        <template #label>
          <span style="position: relative; white-space: pre">{{ t('cmdb.ciType.defaultShow') }}
            <a-tooltip :title="t('cmdb.ciType.defaultShowTips')">
              <InfoCircleOutlined style="position: absolute; top: 2px; left: -17px; color: #a5a9bc" />
            </a-tooltip>
          </span>
        </template>
        <a-switch v-model:checked="formModel.default_show" @change="onChange" />
      </a-form-item>
    </a-col>
    <a-col v-if="currentValueType !== '6' && currentValueType !== '7'" :span="6">
      <a-form-item :label-col="{ span: 16 }" :wrapper-col="{ span: 4 }">
        <template #label>
          <span style="position: relative; white-space: pre">{{ t('cmdb.ciType.isSortable') }}
            <a-tooltip :title="t('cmdb.ciType.sortableHint')">
              <InfoCircleOutlined style="position: absolute; top: 2px; left: -17px; color: #a5a9bc" />
            </a-tooltip>
          </span>
        </template>
        <a-switch v-model:checked="formModel.is_sortable" :disabled="isShowComputedArea" @change="(c: boolean) => onChange(c, 'is_sortable')" />
      </a-form-item>
    </a-col>
    <a-col v-if="!['6', '7', '10'].includes(currentValueType)" :span="6">
      <a-form-item :label-col="{ span: 16 }" :wrapper-col="{ span: 4 }">
        <template #label>
          <span style="position: relative; white-space: pre">
            <a-tooltip :title="t('cmdb.ciType.listTips')">
              <InfoCircleOutlined style="position: absolute; top: 3px; left: -17px; color: #a5a9bc" />
            </a-tooltip>
            {{ t('cmdb.ciType.list') }}
          </span>
        </template>
        <a-switch v-model:checked="formModel.is_list" :disabled="isShowComputedArea" @change="(c: boolean) => onChange(c, 'is_list')" />
      </a-form-item>
    </a-col>
    <a-col :span="6">
      <a-form-item :label-col="{ span: 16 }" :wrapper-col="{ span: 4 }">
        <template #label>
          <span style="position: relative; white-space: pre">
            <a-tooltip :title="t('cmdb.ciType.dynamicTips')">
              <InfoCircleOutlined style="position: absolute; top: 3px; left: -17px; color: #a5a9bc" />
            </a-tooltip>
            {{ t('cmdb.ciType.isDynamic') }}
          </span>
        </template>
        <a-switch v-model:checked="formModel.is_dynamic" @change="(c: boolean) => onChange(c, 'is_dynamic')" />
      </a-form-item>
    </a-col>

    <a-divider style="font-size: 14px; margin-top: 6px">{{ t('cmdb.ciType.advancedSettings') }}</a-divider>
    <a-row>
      <a-col :span="24">
        <a-form-item :label-col="{ span: 4 }" :wrapper-col="{ span: 12 }" :label="t('cmdb.ciType.reg')">
          <RegSelect
            :value="reCheck"
            :is-show-error-msg="false"
            :limited-format="getLimitedFormat()"
            :disabled="['6', '10', '11'].includes(currentValueType)"
            @change="(v) => (reCheck = v)"
          />
          <div class="ant-form-explain">{{ t('cmdb.ciType.regCheckHint') }}</div>
        </a-form-item>
      </a-col>
      <a-col :span="24">
        <a-form-item :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }" :label="t('cmdb.ciType.font')">
          <FontArea ref="fontAreaRef" :font-color-disabled="['8', '11'].includes(currentValueType)" />
          <div class="ant-form-explain">{{ t('cmdb.ciType.fontHint') }}</div>
        </a-form-item>
      </a-col>
      <a-col v-if="!['6', '7', '10', '11'].includes(currentValueType)" :span="24">
        <a-form-item :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
          <template #label>
            <span style="position: relative; white-space: pre">{{ t('cmdb.ciType.choiceValue') }}
              <a-tooltip :title="t('cmdb.ciType.choiceValueHint')">
                <InfoCircleOutlined style="position: absolute; top: 2px; left: -17px; color: #a5a9bc" />
              </a-tooltip>
            </span>
          </template>
          <PreValueArea
            ref="preValueAreaRef"
            :can-define-script="canDefineScript"
            :disabled="isShowComputedArea"
            :CITypeId="CITypeId"
            :enum-value-type="enumValueType"
          />
          <a-button type="primary" size="small" ghost style="margin-top: 8px" @click="resetPreValue">{{
            t('reset')
          }}</a-button>
        </a-form-item>
      </a-col>
      <a-col v-if="!['6', '7', '10', '11'].includes(currentValueType)" :span="24">
        <a-form-item :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
          <template #label>
            <span style="position: relative; white-space: pre">
              <a-tooltip :title="t('cmdb.ciType.computedAttributeTips')">
                <InfoCircleOutlined style="position: absolute; top: 3px; left: -17px; color: #a5a9bc" />
              </a-tooltip>
              {{ t('cmdb.ciType.computedAttribute') }}
            </span>
          </template>
          <a-switch v-model:checked="formModel.is_computed" :disabled="!canDefineComputedFlag" @change="(c: boolean) => onChange(c, 'is_computed')" />
          <div v-show="isShowComputedArea" class="computed-attr-tip">
            <div>1. {{ t('cmdb.ciType.computedAttrTip1') }}</div>
            <div>2. {{ t('cmdb.ciType.computedAttrTip2') }}</div>
            <div>3. {{ t('cmdb.ciType.computedAttrTip3') }}</div>
          </div>
          <ComputedArea ref="computedAreaRef" v-if="isShowComputedArea" :can-define-computed="canDefineComputedFlag" />
        </a-form-item>
      </a-col>
    </a-row>
    <a-form-item v-if="hasFooter" :wrapper-col="{ offset: 18 }">
      <a-button type="primary" @click="handleSubmit()">{{ t('new') }}</a-button>
      <a-divider type="vertical" />
      <a-button @click="handleClose">{{ t('cancel') }}</a-button>
    </a-form-item>
  </a-form>
</template>

<style lang="less" scoped>
.computed-attr-tip {
  font-size: 12px;
  line-height: 22px;
  color: #a5a9bc;
}
.value-type-text {
  margin: 0 4px;
}
.value-type-icon {
  color: @primary-color;
}
</style>
<style lang="less">
.create-new-attribute {
  .jsoneditor-outer {
    height: var(--custom-height) !important;
    border: 1px solid #2f54eb;
  }
  div.jsoneditor-menu {
    background-color: #2f54eb;
  }
}
.value-type-des {
  font-size: 10px;
  color: #a9a9a9;
}
</style>
