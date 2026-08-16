<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { nextTick, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { DownOutlined, InfoCircleOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import RegSelect from '@/components/RegexSelect/index.vue'
import MonacoCodeEditor from '@/components/MonacoCodeEditor/index.vue'
import {
  updateAttributeById,
  updateCITypeAttributesById,
  canDefineComputed,
  calcComputedAttribute,
} from '@/modules/cmdb/api/CITypeAttr'
import { cloneDeep, getPropertyIcon, getPropertyType, valueTypeMap } from '../../utils/helper'

const props = withDefaults(
  defineProps<{
    CITypeId?: number | null
    CITypeName?: string
  }>(),
  { CITypeId: null, CITypeName: '' }
)

const emit = defineEmits<{ (e: 'ok'): void }>()

const { t } = useI18n()

const formRef = ref()

const drawerVisible = ref(false)
const drawerTitle = ref(t('cmdb.ciType.addAttribute'))

const record = ref<Record<string, any>>({})

const currentValueType = ref('0')
const defaultValueJsonText = ref('{}')
const defaultValueJsonRight = ref(true)

const canDefineComputedFlag = ref(false)
const isShowComputedArea = ref(false)

const defaultForDatetime = ref('')
const reCheck = ref<Record<string, any>>({})

const formModel = reactive<Record<string, any>>({
  id: null,
  name: '',
  alias: '',
  value_type: '0',
  default_value: undefined,
  is_required: false,
  default_show: false,
  is_list: false,
  is_unique: false,
  is_index: false,
  is_sortable: false,
  is_computed: false,
  is_dynamic: false,
  reference_type_id: null,
})

const rules = {
  name: [
    { required: true, message: t('cmdb.ciType.inputAttributeName') },
    { message: t('cmdb.ciType.attributeNameTips'), pattern: /^(?!\d)[a-zA-Z_0-9]+$/ },
  ],
  value_type: [{ required: true }],
}

const valueTypeOptions = computedValueTypeOptions()

function computedValueTypeOptions() {
  const map = valueTypeMap()
  const keys = ['0', '1', '2', '9', '3', '4', '5', '6', '7', '8', '10', '11', '12']
  return keys.map((key) => ({ key, value: map[key] }))
}

async function handleCreate() {
  try {
    await canDefineComputed()
    canDefineComputedFlag.value = true
  } catch {
    canDefineComputedFlag.value = false
  }

  drawerTitle.value = t('cmdb.ciType.addAttribute')
  drawerVisible.value = true
}

function onClose() {
  formRef.value?.resetFields()
  drawerVisible.value = false
}

function onChange(checked: boolean, property: string) {
  if (property === 'is_computed') {
    isShowComputedArea.value = checked
    if (checked) {
      formModel.is_list = false
      formModel.is_unique = false
      formModel.is_sortable = false
      if (currentValueType.value === '2') {
        formModel.is_index = true
      }
    }
  }
  if (property === 'is_list') {
    handleSwitchIsList(checked)
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

function handleSwitchIsList(checked: boolean) {
  let defaultValue: any = checked ? [] : ''

  switch (currentValueType.value) {
    case '2':
    case '9':
      defaultValue = ''
      break
    case '10':
      defaultValue = checked ? '' : false
      break
    default:
      break
  }

  formModel.default_value = defaultValue
}

async function handleEdit(attrRecord: Record<string, any>) {
  try {
    await canDefineComputed()
    canDefineComputedFlag.value = true
  } catch {
    canDefineComputedFlag.value = false
  }
  const _record = cloneDeep(attrRecord)
  _record.value_type = getPropertyType(_record)
  drawerTitle.value = t('cmdb.ciType.editAttribute')
  drawerVisible.value = true
  record.value = _record
  currentValueType.value = _record.value_type

  nextTick(() => {
    formModel.id = _record.id
    formModel.alias = _record.alias
    formModel.name = _record.name
    formModel.value_type = _record.value_type
    formModel.is_required = _record.is_required
    formModel.default_show = _record.default_show

    if (!['6', '7'].includes(_record.value_type)) {
      formModel.is_list = _record.is_list
      formModel.is_unique = _record.is_unique
      formModel.is_index = _record.is_index
      formModel.is_sortable = _record.is_sortable
      formModel.is_computed = _record.is_computed
      formModel.is_dynamic = _record.is_dynamic
    }
    if (_record.value_type === '11') {
      formModel.reference_type_id = _record.reference_type_id
    }

    if (!['6', '10', '11'].includes(_record.value_type) && _record.re_check) {
      reCheck.value = { value: _record.re_check }
    } else {
      reCheck.value = {}
    }

    if (_record.default) {
      if (_record.value_type === '10') {
        formModel.default_value = Boolean(_record.default.default)
      } else if (_record.value_type === '0') {
        if (_record.is_list) {
          formModel.default_value = _record.default.default ? _record.default.default : ''
        } else {
          formModel.default_value = _record.default.default ? [_record.default.default] : []
        }
      } else if (_record.value_type === '6') {
        defaultValueJsonText.value = JSON.stringify(_record?.default?.default ?? {}, null, 2)
      } else if ((_record.value_type === '3' || _record.value_type === '4') && !_record.is_list) {
        if (_record?.default?.default === '$created_at' || _record?.default?.default === '$updated_at') {
          defaultForDatetime.value = _record.default.default
          formModel.default_value = _record?.default?.default
        } else {
          defaultForDatetime.value = '$custom_time'
          formModel.default_value = _record.default && _record.default.default ? dayjs(_record.default.default) : null
        }
      } else {
        formModel.default_value = _record?.default?.default ?? null
      }
    } else {
      defaultValueJsonText.value = '{}'
      if (_record.value_type === '0') {
        formModel.default_value = []
      } else if (_record.value_type !== '6') {
        formModel.default_value = null
      }
    }

    isShowComputedArea.value = _record.is_computed
    // TODO: wire up <ComputedArea>/<PreValueArea>/<FontArea> once migrated.
  })
}

async function handleSubmit(isCalcComputed = false) {
  formRef.value
    .validate()
    .then(async () => {
      const values: Record<string, any> = { ...formModel }

      if (record.value.is_required !== values.is_required || record.value.default_show !== values.default_show) {
        await updateCITypeAttributesById(props.CITypeId as number, {
          attributes: [
            { attr_id: record.value.id, is_required: values.is_required, default_show: values.default_show },
          ],
        })
      }

      const { default_value } = values
      if (values.value_type === '10') {
        values.default = { default: values.is_list ? default_value : Boolean(default_value) }
      } else if (values.value_type === '0' && default_value) {
        if (values.is_list) {
          values.default = { default: default_value || null }
        } else {
          values.default = { default: default_value[0] || null }
        }
      } else if (values.value_type === '6') {
        values.default = { default: defaultValueJsonRight.value ? parseJsonSafe(defaultValueJsonText.value) : null }
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
        // TODO: wire up <ComputedArea> once migrated.
        Object.assign(values, {})
      } else if (!['6', '7', '10', '11'].includes(values.value_type)) {
        // TODO: wire up <PreValueArea> once migrated.
        Object.assign(values, {})
      }

      delete values.default_show
      delete values.is_required
      delete values.default_value

      // TODO: wire up <FontArea> once migrated.
      const fontOptions = {}

      if (!['6', '10', '11'].includes(values.value_type)) {
        values.re_check = reCheck.value?.value ?? null
      }

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

      if (values.id) {
        await updateAttribute(values.id, { ...values, option: { ...values.option, fontOptions } }, isCalcComputed)
      }
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

async function updateAttribute(attrId: number, data: Record<string, any>, isCalcComputed = false) {
  await updateAttributeById(attrId, data)
  if (isCalcComputed) {
    await calcComputedAttribute(attrId)
  }
  message.success(t('updateSuccess'))
  emit('ok')
  onClose()
}

function handleChangeValueType(value: string) {
  currentValueType.value = value
  nextTick(() => {
    formModel.default_value = formModel.is_list ? [] : null
  })
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

defineExpose({ handleCreate, handleEdit })
</script>

<template>
  <CustomDrawer
    :closable="true"
    :title="drawerTitle"
    :open="drawerVisible"
    placement="right"
    width="800"
    :body-style="{ paddingTop: 0 }"
    :header-style="{ borderBottom: 'none' }"
    wrap-class-name="attribute-edit-form"
    @close="onClose"
  >
    <a-form ref="formRef" :model="formModel" :rules="rules" :layout="'horizontal'">
      <a-divider style="font-size: 14px; margin-top: 6px">{{ t('cmdb.ciType.basicConfig') }}</a-divider>
      <a-col :span="12">
        <a-form-item :label-col="{ span: 8 }" :wrapper-col="{ span: 15 }" :label="t('cmdb.ciType.AttributeName')" name="name">
          <a-input v-model:value="formModel.name" :disabled="true" :placeholder="t('cmdb.ciType.English')" />
        </a-form-item>
      </a-col>
      <a-col :span="12">
        <a-form-item :label-col="{ span: 8 }" :wrapper-col="{ span: 15 }" :label="t('cmdb.common.alias')" name="alias">
          <a-input v-model:value="formModel.alias" :placeholder="t('cmdb.ciType.aliasPlaceholder')" />
        </a-form-item>
      </a-col>
      <a-col :span="12">
        <a-form-item :label-col="{ span: 8 }" :wrapper-col="{ span: 15 }" :label="t('cmdb.ciType.DataType')" name="value_type">
          <a-select v-model:value="formModel.value_type" :disabled="true" style="width: 100%" @change="handleChangeValueType">
            <a-select-option v-for="item in valueTypeOptions" :key="item.key" :value="item.key">
              <span class="value-type-icon"><component :is="getPropertyIcon({ value_type: item.key })" /></span>
              <span class="value-type-text">{{ item.value }}</span>
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-col>
      <a-col v-if="currentValueType !== '11'" :span="currentValueType === '6' ? 24 : 12">
        <a-form-item
          :label-col="{ span: currentValueType === '6' ? 4 : 8 }"
          :wrapper-col="{ span: currentValueType === '6' ? 18 : 15 }"
          :label="t('cmdb.ciType.defaultValue')"
        >
          <a-input v-if="formModel.is_list" v-model:value="formModel.default_value" :style="{ width: '100%' }" />
          <a-switch v-else-if="currentValueType === '10'" v-model:checked="formModel.default_value" />
          <a-select
            v-else-if="currentValueType === '0'"
            v-model:value="formModel.default_value"
            mode="tags"
            @select="selectIntDefaultValue"
          >
            <a-select-option key="$auto_inc_id">{{ t('cmdb.ciType.autoIncID') }}</a-select-option>
          </a-select>
          <a-input-number v-else-if="currentValueType === '1'" v-model:value="formModel.default_value" style="width: 100%" />
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
        <a-form-item :label="t('cmdb.ciType.referenceModel')">
          <!-- TODO: wire up <ReferenceModelSelect> once migrated -->
          <a-input v-model:value="formModel.reference_type_id" :placeholder="t('cmdb.ciType.referenceModelTip')" />
        </a-form-item>
      </a-col>

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
          <a-switch v-model:checked="formModel.is_list" :disabled="true || isShowComputedArea" @change="(c: boolean) => onChange(c, 'is_list')" />
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
            <!-- TODO: wire up <FontArea> once migrated -->
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
            <!-- TODO: wire up <PreValueArea> once migrated -->
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
            <!-- TODO: wire up <ComputedArea> once migrated -->
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item>
        <a-input v-model:value="formModel.id" type="hidden" />
      </a-form-item>
      <div class="custom-drawer-bottom-action">
        <a-button @click="onClose">{{ t('cancel') }}</a-button>
        <a-button type="primary" @click="handleSubmit(false)">{{ t('confirm') }}</a-button>
      </div>
    </a-form>
  </CustomDrawer>
</template>

<style lang="less" scoped>
.computed-attr-tip {
  font-size: 12px;
  line-height: 22px;
  color: #a5a9bc;
}
.value-type-text {
  margin-left: 4px;
}
.value-type-icon {
  color: @primary-color;
}
</style>
<style lang="less">
.attribute-edit-form {
  .jsoneditor-outer {
    height: var(--custom-height) !important;
    border: 1px solid #2f54eb;
  }
  div.jsoneditor-menu {
    background-color: #2f54eb;
  }
}
</style>
