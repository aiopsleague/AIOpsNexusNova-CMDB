<script setup lang="ts">
import { computed, inject, nextTick, provide, reactive, ref } from 'vue'
import { AppstoreOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import { getCIType, getCITypeGroupById } from '@/modules/cmdb/api/CIType'
import { addCI } from '@/modules/cmdb/api/ci'
import { getCITypeParent, getCanEditByParentIdChildId } from '@/modules/cmdb/api/CITypeRelation'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import CreateInstanceFormByGroup from './createInstanceFormByGroup.vue'
import CIReferenceAttr from '@/components/ciReferenceAttr/index.vue'
import CiFileField from '@/modules/cmdb/components/CiFileField.vue'
import JsonEditor from '@/modules/cmdb/components/JsonEditor/jsonEditor.vue'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    typeIdFromProp?: number
    typeIdFromRelation?: number
  }>(),
  {
    typeIdFromProp: 0,
    typeIdFromRelation: 0,
  }
)

const emit = defineEmits<{
  (e: 'submit', values: Record<string, any>): void
  (e: 'reload', payload: { ci_id: number }): void
}>()

const attrListProvider = inject<() => any[]>('attrList', () => [])

const visible = ref(false)
const action = ref('')
const batchFormRef = ref()
const jsonEditorRef = ref<InstanceType<typeof JsonEditor>>()

const attributeList = ref<any[]>([])
const CIType = ref<Record<string, any>>({})
const batchUpdateLists = ref<Array<{ name: string; operation: string }>>([])
const editAttr = ref<Record<string, any> | null>(null)
const attributesByGroup = ref<any[]>([])
const parentsType = ref<any[]>([])
const parentsForm = reactive<Record<string, { attr: string; value: string }>>({})
const canEdit = ref<Record<string, boolean>>({})

const groupRefs = new Map<number | string, any>()

const batchFormModel = reactive<Record<string, any>>({})

const listOperationOptions = [
  { value: 'cover', label: 'cmdb.ci.cover' },
  { value: 'add', label: 'add' },
  { value: 'delete', label: 'delete' },
]

const typeId = computed(() => (props.typeIdFromRelation ? props.typeIdFromRelation : props.typeIdFromProp))

const title = computed(() => (action.value === 'create' ? t('create') + ' ' : t('cmdb.ci.batchUpdate') + ' '))

const batchFormRules = computed<Record<string, any>>(() => {
  const rules: Record<string, any> = {}
  batchUpdateLists.value.forEach((list) => {
    if (list.name) {
      rules[list.name] = getDecoratorRules(list)
    }
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

function getFieldType(name: string): string {
  const _find = attributeList.value.find((item) => item.name === name)
  if (_find) {
    if (_find.is_choice) {
      if (_find.is_list) return 'select%%multiple'
      return 'select'
    } else if ((_find.value_type === '0' || _find.value_type === '1') && !_find.is_list) {
      return 'input_number'
    } else if (_find.value_type === '4' || _find.value_type === '3') {
      return _find.value_type
    } else if (isLongText(_find)) {
      return 'textarea'
    } else {
      return 'input'
    }
  }
  return 'input'
}

function getAttr(name: string): Record<string, any> {
  return attributeList.value.find((item) => item.name === name) ?? {}
}

function getSelectFieldOptions(name: string): any[] {
  const _find = attributeList.value.find((item) => item.name === name)
  if (_find) {
    return _find.choice_value
  }
  return []
}

function showListOperation(name: string): boolean {
  if (!name) {
    return false
  }
  const attr = attributeList.value.find((attr) => attr.name === name)
  return !!(attr && attr.is_list)
}

function getDecoratorRules(data: { name: string; operation: string }): any[] {
  const { name, operation } = data
  const isList = showListOperation(name)
  const rules: any[] = [{ required: false }]
  if (isList && ['delete', 'add'].includes(operation)) {
    rules[0] = { required: true, message: t('placeholder1') }
  }
  return rules
}

function filterAttributes(attributes: any[]): any[] {
  return attributes.filter((attr) => !attr.is_bool && !attr.is_reference)
}

function setGroupRef(group: Record<string, any>, el: any) {
  if (el) {
    groupRefs.set(group.id, el)
  } else {
    groupRefs.delete(group.id)
  }
}

async function getCITypeData() {
  await getCIType(typeId.value).then((res) => {
    CIType.value = res.ci_types[0]
  })
}

async function getAttributeList() {
  const _attrList = attrListProvider()
  attributeList.value = _attrList.sort((x: any, y: any) => y.is_required - x.is_required)
  await getCITypeGroupById(typeId.value).then((res1) => {
    const _attributesByGroup = res1.map((g: any) => {
      g.attributes = g.attributes.filter((attr: any) => !attr.is_computed && !attr.sys_computed)
      return g
    })
    const attrHasGroupIds: any[] = []
    res1.forEach((g: any) => {
      const id = g.attributes.map((attr: any) => attr.id)
      attrHasGroupIds.push(...id)
    })
    const otherGroupAttr = attributeList.value.filter(
      (attr: any) => !attrHasGroupIds.includes(attr.id) && !attr.is_computed && !attr.sys_computed
    )
    if (otherGroupAttr.length) {
      _attributesByGroup.push({ id: -1, name: t('other'), attributes: otherGroupAttr })
    }
    attributesByGroup.value = _attributesByGroup
  })
}

function initBatchFormModel() {
  Object.keys(batchFormModel).forEach((key) => delete batchFormModel[key])
  batchUpdateLists.value.forEach((list) => {
    if (list.name) {
      const attr = getAttr(list.name)
      if (attr.is_reference) {
        batchFormModel[list.name] = attr.is_list ? [] : ''
      } else if (attr.is_bool) {
        batchFormModel[list.name] = false
      }
    }
  })
}

async function handleOpen(v: boolean, act: string) {
  visible.value = v
  action.value = act
  await nextTick()
  batchFormRef.value?.resetFields()
  await Promise.all([getCITypeData(), getAttributeList()]).then(() => {
    batchUpdateLists.value = [{ name: attributeList.value?.[0]?.name || '', operation: 'cover' }]
    initBatchFormModel()
  })
  if (act === 'create') {
    getCITypeParent(typeId.value).then(async (res) => {
      for (let i = 0; i < res.parents.length; i++) {
        await getCanEditByParentIdChildId(res.parents[i].id, typeId.value).then((p_res) => {
          canEdit.value = { ...cloneDeep(canEdit.value), [res.parents[i].id]: p_res.result }
        })
      }
      parentsType.value = res.parents.filter((parent: any) => canEdit.value[parent.id])
      const _parentsForm: Record<string, { attr: string; value: string }> = {}
      res.parents.forEach((item: any) => {
        const _find = item.attributes.find((attr: any) => attr.id === item.unique_id)
        _parentsForm[item.name] = { attr: _find.name, value: '' }
      })
      Object.keys(parentsForm).forEach((key) => delete parentsForm[key])
      Object.assign(parentsForm, _parentsForm)
    })
  }
}

function handleClose() {
  visible.value = false
}

function processValues(values: Record<string, any>, wrapListOperation: boolean): Record<string, any> {
  const result = { ...values }
  Object.keys(result).forEach((k) => {
    const _tempFind = attributeList.value.find((item) => item.name === k)
    if (!_tempFind) return

    if (_tempFind.is_reference) {
      result[k] = result[k] ? result[k] : null
    }

    if (_tempFind.value_type === '3' && result[k] && typeof result[k] === 'object' && result[k].format) {
      result[k] = dayjs(result[k]).format('YYYY-MM-DD HH:mm:ss')
    }
    if (_tempFind.value_type === '4' && result[k] && typeof result[k] === 'object' && result[k].format) {
      result[k] = dayjs(result[k]).format('YYYY-MM-DD')
    }
    if (_tempFind.value_type === '6') {
      result[k] = result[k] ? (typeof result[k] === 'string' ? JSON.parse(result[k]) : result[k]) : undefined
    }

    if (wrapListOperation && _tempFind.is_list) {
      const operation = batchUpdateLists.value?.find((item) => item.name === k)?.operation || 'cover'
      switch (operation) {
        case 'add':
        case 'delete':
          result[k] = {
            op: operation,
            v: result[k],
          }
          break
        default:
          break
      }
    }
  })
  return result
}

async function createInstance() {
  if (action.value === 'update') {
    let values: Record<string, any>
    try {
      values = await batchFormRef.value.validate()
    } catch {
      return
    }
    const processed = processValues(values, true)
    emit('submit', processed)
    return
  }

  let values: Record<string, any> = {}
  for (const group of attributesByGroup.value) {
    const data = await groupRefs.get(group.id)?.getData()
    if (!data || data === 'error') {
      return
    }
    values = { ...values, ...data }
  }

  values = processValues(values, false)
  values.ci_type = typeId.value

  Object.keys(parentsForm).forEach((type) => {
    if (parentsForm[type].value) {
      values[`$${type}.${parentsForm[type].attr}`] = parentsForm[type].value
    }
  })

  addCI(values).then((res) => {
    message.success(t('addSuccess'))
    visible.value = false
    emit('reload', { ci_id: res.ci_id })
  })
}

function handleAdd() {
  batchUpdateLists.value.push({ name: '', operation: 'cover' })
}

function handleDelete(name: string) {
  const _idx = batchUpdateLists.value.findIndex((item) => item.name === name)
  if (_idx > -1) {
    batchUpdateLists.value.splice(_idx, 1)
  }
}

function handleFocusInput(e: FocusEvent, attr: Record<string, any>) {
  const _tempFind = attributeList.value.find((item) => item.name === attr.name)
  if (_tempFind && _tempFind.value_type === '6') {
    editAttr.value = attr
    ;(e.target as HTMLInputElement)?.blur()
    const jsonData = batchFormModel[attr.name]
    jsonEditorRef.value?.open(null, null, jsonData ? JSON.parse(jsonData) : {})
  } else {
    editAttr.value = null
  }
}

function jsonEditorOk(jsonData: any) {
  if (editAttr.value) {
    batchFormModel[editAttr.value.name] = JSON.stringify(jsonData)
  }
}

provide('getFieldType', getFieldType)

defineExpose({ handleOpen, handleClose, visible })
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <CustomDrawer
    :title="title + CIType.alias"
    width="800"
    @close="handleClose"
    :mask-closable="false"
    v-model:open="visible"
    wrap-class-name="create-instance-form"
    :body-style="{ paddingTop: 0 }"
    :header-style="{ borderBottom: 'none' }"
  >
    <div class="custom-drawer-bottom-action">
      <a-button @click="handleClose">{{ t('cancel') }}</a-button>
      <a-button type="primary" @click="createInstance">{{ t('submit') }}</a-button>
    </div>
    <template v-if="action === 'create'">
      <template v-for="group in attributesByGroup" :key="group.id || group.name">
        <CreateInstanceFormByGroup
          :ref="(el: any) => setGroupRef(group, el)"
          :group="group"
          :attribute-list="attributeList"
        />
      </template>
      <template v-if="parentsType && parentsType.length">
        <a-divider style="font-size:14px;margin:14px 0;font-weight:700;">{{ t('cmdb.menu.citypeRelation') }}</a-divider>
        <a-form>
          <a-row :gutter="24" align="top">
            <a-col :span="12" v-for="item in parentsType" :key="item.id">
              <a-form-item :label="item.alias || item.name" :colon="false">
                <a-input-group compact style="width: 100%">
                  <a-select v-model:value="parentsForm[item.name].attr">
                    <a-select-option
                      v-for="attr in filterAttributes(item.attributes)"
                      :key="attr.name"
                      :value="attr.name"
                      :title="attr.alias || attr.name"
                    >
                      {{ attr.alias || attr.name }}
                    </a-select-option>
                  </a-select>
                  <a-input
                    v-model:value="parentsForm[item.name].value"
                    :placeholder="t('cmdb.ci.tips1')"
                    style="width: 50%"
                  />
                </a-input-group>
              </a-form-item>
            </a-col>
          </a-row>
        </a-form>
      </template>
    </template>
    <template v-if="action === 'update'">
      <a-form ref="batchFormRef" :model="batchFormModel" :rules="batchFormRules">
        <p>{{ t('cmdb.ci.tips2') }}</p>
        <a-row :gutter="8" v-for="list in batchUpdateLists" :key="list.name">
          <a-col :span="6">
            <a-form-item>
              <a-select
                v-model:value="list.name"
                show-search
                size="small"
                :placeholder="t('cmdb.ci.tips3')"
              >
                <a-select-option
                  v-for="attr in attributeList"
                  :key="attr.name"
                  :value="attr.name"
                  :disabled="batchUpdateLists.findIndex((item) => item.name === attr.name) > -1"
                >
                  {{ attr.alias || attr.name }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col v-if="showListOperation(list.name)" :span="3">
            <a-form-item>
              <a-select v-model:value="list.operation" size="small" :placeholder="t('placeholder2')">
                <a-select-option v-for="option in listOperationOptions" :key="option.value" :value="option.value">
                  {{ t(option.label) }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="showListOperation(list.name) ? 10 : 13">
            <a-form-item :name="list.name">
              <CIReferenceAttr
                v-if="getAttr(list.name).is_reference"
                :reference-type-id="getAttr(list.name).reference_type_id"
                :is-list="getAttr(list.name).is_list"
                v-model:value="batchFormModel[list.name]"
              />
              <a-switch v-else-if="getAttr(list.name).is_bool" v-model:checked="batchFormModel[list.name]" />
              <CiFileField
                v-else-if="getAttr(list.name).is_file"
                :is-edit="true"
                :is-list="getAttr(list.name).is_list"
                :attr-id="getAttr(list.name).id"
                :value="batchFormModel[list.name]"
                @input="(val: string) => (batchFormModel[list.name] = val)"
              />
              <a-textarea
                v-else-if="getFieldType(list.name) === 'textarea'"
                v-model:value="batchFormModel[list.name]"
              />
              <a-select
                v-else-if="getFieldType(list.name).split('%%')[0] === 'select'"
                v-model:value="batchFormModel[list.name]"
                :style="{ width: '100%' }"
                :placeholder="t('placeholder2')"
                :mode="getFieldType(list.name).split('%%')[1] === 'multiple' ? 'multiple' : undefined"
                show-search
                allow-clear
              >
                <a-select-option
                  v-for="(choice, choice_idx) in getSelectFieldOptions(list.name)"
                  :key="'New_' + choice + choice_idx"
                  :value="choice[0]"
                >
                  <span :style="choice[1] ? choice[1].style || {} : {}">
                    <AppstoreOutlined
                      v-if="choice[1] && choice[1].icon && choice[1].icon.name"
                      :style="{ color: choice[1].icon.color }"
                    />
                    <a-tooltip placement="topLeft" :title="choice[1] ? choice[1].label || choice[0] : choice[0]">
                      {{ choice[1] ? choice[1].label || choice[0] : choice[0] }}
                    </a-tooltip>
                  </span>
                </a-select-option>
              </a-select>
              <a-input-number
                v-else-if="getFieldType(list.name) === 'input_number'"
                v-model:value="batchFormModel[list.name]"
                style="width: 100%"
              />
              <a-date-picker
                v-else-if="getFieldType(list.name) === '4' || getFieldType(list.name) === '3'"
                v-model:value="batchFormModel[list.name]"
                style="width: 100%"
                :format="getFieldType(list.name) === '4' ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss'"
                :value-format="getFieldType(list.name) === '4' ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss'"
                :show-time="getFieldType(list.name) === '4' ? false : { format: 'HH:mm:ss' }"
              />
              <a-input
                v-else-if="getFieldType(list.name) === 'input'"
                v-model:value="batchFormModel[list.name]"
                @focus="(e: FocusEvent) => handleFocusInput(e, list)"
              />
            </a-form-item>
          </a-col>
          <a-col :span="2">
            <a-form-item>
              <a :style="{ color: 'red', marginTop: '2px' }" @click="handleDelete(list.name)">
                <DeleteOutlined />
              </a>
            </a-form-item>
          </a-col>
        </a-row>
        <a-button type="primary" ghost @click="handleAdd">
          <PlusOutlined />{{ t('cmdb.ci.newUpdateField') }}
        </a-button>
      </a-form>
    </template>
    <JsonEditor ref="jsonEditorRef" @json-editor-ok="jsonEditorOk" />
  </CustomDrawer>
</template>

<style lang="less">
.create-instance-form {
  .ant-form-item {
    margin-bottom: 5px;
  }
  .ant-drawer-body {
    overflow-y: auto;
    height: calc(100vh - 110px);
  }
}
</style>
