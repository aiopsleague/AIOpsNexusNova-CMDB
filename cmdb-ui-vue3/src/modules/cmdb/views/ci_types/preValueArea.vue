<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { QuestionCircleOutlined } from '@ant-design/icons-vue'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import Webhook from '@/modules/cmdb/components/webhook/index.vue'
import MonacoCodeEditor from '@/components/MonacoCodeEditor/index.vue'
import { getCITypeGroups } from '@/modules/cmdb/api/ciTypeGroup'
import { getCITypeCommonAttributesByTypeIds, getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import AllAttrDrawer from './allAttrDrawer.vue'

const props = withDefaults(
  defineProps<{
    disabled?: boolean
    canDefineScript?: boolean
    CITypeId?: number | null
    enumValueType?: string
  }>(),
  { disabled: true, canDefineScript: false, CITypeId: null, enumValueType: 'input' }
)

const { t } = useI18n()

const isOpenSource = import.meta.env.VITE_APP_IS_OPEN_SOURCE === 'true'

type ActiveKey = 'define' | 'builtin' | 'webhook' | 'choice_other' | 'script'

const activeKey = ref<ActiveKey>('define')

interface ValueMeta {
  style: Record<string, any>
  icon: Record<string, any>
  label: string
}

const DEFAULT_VALUE_META: ValueMeta = { style: {}, icon: {}, label: '' }

const valueList = ref<[string, ValueMeta][]>([['', { ...DEFAULT_VALUE_META }]])
const form = reactive({ ret_key: '' })
const choiceOther = ref<{ type_ids?: any[]; attr_id?: number | string | null }>({
  type_ids: undefined,
  attr_id: undefined,
})
const ciTypeGroup = ref<any[]>([])
const typeAttrs = ref<any[]>([])
const filterExp = ref('')
const script = ref(t('cmdb.ciType.choiceScriptDemo'))
const curModelAttrList = ref<any[]>([])
const cascade_attributes = ref<any[]>([])

const webhookRef = ref<InstanceType<typeof Webhook>>()
const builtInRef = ref<any>()
const attrFilterRef = ref<any>()
const allAttrDrawerRef = ref<InstanceType<typeof AllAttrDrawer>>()

function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

const scriptCodeExtraText = computed(
  () => t('cmdb.ciType.cascadeAttrTip') + (isOpenSource ? ` (${t('cmdb.enterpriseVersionTip')})` : '')
)

function setInkBarColor() {
  const dom = document.querySelector('#preValueArea .ant-tabs-ink-bar') as HTMLElement | null
  if (!dom) {
    return
  }
  // A disabled tab should render its ink-bar greyed out.
  dom.style.backgroundColor = props.disabled ? '#00000040' : '#2f54eb'
}

function normalizeCiType(node: any) {
  return {
    id: node.id || -1,
    label: node.alias || node.name || t('cmdb.common.other'),
    title: node.alias || node.name || t('cmdb.common.other'),
    children: node.ci_types,
  }
}

function normalizeAttr(node: any) {
  return {
    id: node.id || -1,
    label: node.alias || node.name || t('cmdb.common.other'),
    title: node.alias || node.name || t('cmdb.common.other'),
  }
}

async function getCITypeAttributesByIdReq() {
  if (!props.CITypeId) {
    curModelAttrList.value = []
    return
  }
  const res = await getCITypeAttributesById(props.CITypeId)
  let list: any[] = []
  if (res?.attributes?.length) {
    list = res.attributes.filter((attr: any) => !attr.is_password)
  }
  curModelAttrList.value = list
}

function getData(): any {
  if (activeKey.value === 'builtin') {
    return { choice_value: [], choice_web_hook: null, choice_other: null }
  }
  if (activeKey.value === 'define') {
    if (validateDefine()) {
      return { isError: true }
    }
    return {
      choice_value: valueList.value.filter((item) => !['', null, undefined].includes(item?.[0])),
      choice_web_hook: null,
      choice_other: null,
    }
  }
  if (activeKey.value === 'webhook') {
    const choice_web_hook: any = webhookRef.value?.getParams() || {}
    choice_web_hook.ret_key = form.ret_key
    return { choice_value: [], choice_web_hook, choice_other: null }
  }
  if (activeKey.value === 'script') {
    return {
      choice_value: [],
      choice_web_hook: null,
      choice_other: { script: script.value, cascade_attributes: cascade_attributes.value },
    }
  }
  // choice_other
  let choice_other: any = {}
  if (choiceOther.value.type_ids && choiceOther.value.type_ids.length) {
    attrFilterRef.value?.handleSubmit()
    choice_other = { ...choiceOther.value, filter: filterExp.value }
  }
  return { choice_value: [], choice_web_hook: null, choice_other }
}

function validateDefine(): boolean {
  const list = valueList.value.filter((item) => !['', null, undefined].includes(item?.[0]))
  const isRepeat = Array.from(new Set(list.map((item) => item?.[0]))).length !== list.length
  if (isRepeat) {
    message.warning(t('cmdb.ciType.enumValueTip2'))
    return true
  }
  return false
}

function setData(data: { choice_value?: any[]; choice_web_hook?: any; choice_other?: any }) {
  const { choice_value, choice_web_hook, choice_other } = data || {}
  if (choice_web_hook) {
    activeKey.value = 'webhook'
    nextTick(() => {
      webhookRef.value?.setParams(choice_web_hook)
      form.ret_key = choice_web_hook.ret_key ?? ''
    })
  } else if (choice_other) {
    if (choice_other.script) {
      activeKey.value = 'script'
      script.value = choice_other.script
    } else {
      activeKey.value = 'choice_other'
      const { type_ids, attr_id, filter } = choice_other
      choiceOther.value = { type_ids, attr_id }
      filterExp.value = filter
      cascade_attributes.value = choice_other?.cascade_attributes || []
      if (type_ids && type_ids.length) {
        nextTick(() => {
          attrFilterRef.value?.init(true, false)
        })
      }
    }
  } else {
    let list: [string, ValueMeta][] = [['', { ...DEFAULT_VALUE_META }]]
    if (choice_value?.length) {
      list = choice_value.map((item) => [
        item[0],
        {
          icon: item?.[1]?.icon || {},
          style: item?.[1]?.style || {},
          label: item?.[1]?.label || item?.[0] || '',
        },
      ])
    }
    valueList.value = list
    activeKey.value = 'define'
  }
  setInkBarColor()
}

function resetData() {
  activeKey.value = 'define'
  valueList.value = [['', { ...DEFAULT_VALUE_META }]]

  nextTick(() => {
    builtInRef.value?.setData({})
    webhookRef.value?.setParams({})
    form.ret_key = ''
    script.value = ''
    cascade_attributes.value = []
    choiceOther.value = { type_ids: undefined, attr_id: undefined }
    attrFilterRef.value?.init(true, false)
  })
}

function initEnumValue() {
  if (valueList.value) {
    const list = cloneDeep(valueList.value)
    list.forEach((item) => {
      item[0] = ''
    })
    valueList.value = list
  }
}

function changeCodeContent(value: string) {
  script.value = value && value.replace('\t', '    ')
}

function showAllPropDrawer() {
  allAttrDrawerRef.value?.open()
}

watch(
  () => props.disabled,
  () => setInkBarColor()
)

watch(
  () => choiceOther.value.type_ids,
  (newValue) => {
    if (newValue && newValue.length) {
      getCITypeCommonAttributesByTypeIds({ type_ids: newValue.join(',') }).then((res) => {
        typeAttrs.value = res.attributes
      })
    }
  }
)

onMounted(() => {
  getCITypeGroups({ need_other: true }).then((res) => {
    ciTypeGroup.value = res
      .filter((item: any) => item.ci_types && item.ci_types.length)
      .map((item: any) => {
        item.id = `parent_${item.id || -1}`
        return { ...cloneDeep(item) }
      })
  })
  getCITypeAttributesByIdReq()
})

defineExpose({ getData, setData, resetData, initEnumValue })
</script>

<template>
  <a-tabs id="preValueArea" v-model:active-key="activeKey" size="small" :tab-bar-style="{ borderBottom: 'none' }">
    <a-tab-pane key="define" :disabled="disabled">
      <template #tab><span style="font-size: 14px">{{ t('cmdb.ciType.enum') }}</span></template>
      <!-- TODO: wire up <PreValueDefine v-model="valueList" :disabled="disabled" :enum-value-type="enumValueType" /> once migrated -->
    </a-tab-pane>
    <a-tab-pane key="builtin" :disabled="disabled">
      <template #tab>
        <div class="tab-builtin">
          <span class="tab-builtin-title">{{ t('cmdb.ciType.builtin') }}</span>
          <span v-if="isOpenSource" class="tab-builtin-tag">Pro</span>
        </div>
      </template>
      <!-- TODO: wire up <PreValueBuiltIn ref="builtInRef" /> once migrated -->
    </a-tab-pane>
    <a-tab-pane key="webhook" :disabled="disabled">
      <template #tab><span style="font-size: 14px">Webhook</span></template>
      <Webhook ref="webhookRef" style="margin-top: 10px" />
      <a-form :model="form">
        <a-col :span="24">
          <a-form-item name="ret_key" :label-col="{ span: 3 }" :wrapper-col="{ span: 18 }">
            <template #label>
              <span style="position: relative; white-space: pre">
                {{ t('cmdb.ciType.filter') }}
                <a-tooltip :title="t('cmdb.ciType.choiceWebhookTips')">
                  <QuestionCircleOutlined class="tab-webhook-filter-icon" />
                </a-tooltip>
              </span>
            </template>
            <a-input v-model:value="form.ret_key" style="width: 150px" placeholder="k1##k2" :disabled="disabled" />
          </a-form-item>
        </a-col>
      </a-form>
    </a-tab-pane>
    <a-tab-pane key="choice_other" :disabled="disabled">
      <template #tab><span style="font-size: 14px">{{ t('cmdb.ciType.choiceOther') }}</span></template>
      <a-row :gutter="[24, 24]">
        <a-col :span="24">
          <a-form-item
            :style="{ lineHeight: '24px', marginBottom: '5px' }"
            :label="t('cmdb.ciType.ciType')"
            :label-col="{ span: 3 }"
            :wrapper-col="{ span: 12 }"
          >
            <Treeselect
              v-model="choiceOther.type_ids"
              :disable-branch-nodes="true"
              class="custom-treeselect custom-treeselect-white"
              :style="{ '--custom-height': '32px', lineHeight: '32px', '--custom-multiple-lineHeight': '14px' }"
              :multiple="true"
              :clearable="true"
              searchable
              :options="ciTypeGroup"
              value-consists-of="LEAF_PRIORITY"
              :placeholder="t('cmdb.ciType.selectCIType')"
              :normalizer="normalizeCiType"
              append-to-body
              :z-index="1050"
              @select="choiceOther.attr_id = undefined"
            >
              <template #option-label="{ node }">
                <div
                  :title="node.label"
                  :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }"
                >
                  {{ node.label }}
                </div>
              </template>
            </Treeselect>
          </a-form-item>
        </a-col>
        <a-col v-if="choiceOther.type_ids && choiceOther.type_ids.length" :span="24">
          <a-form-item
            :style="{ marginBottom: '5px' }"
            :label="t('cmdb.ciType.attributes')"
            :label-col="{ span: 3 }"
            :wrapper-col="{ span: 12 }"
          >
            <Treeselect
              v-model="choiceOther.attr_id"
              :disable-branch-nodes="true"
              class="ops-setting-treeselect"
              :multiple="false"
              :clearable="true"
              searchable
              :options="typeAttrs"
              value-consists-of="LEAF_PRIORITY"
              :placeholder="t('cmdb.ciType.selectCITypeAttributes')"
              :normalizer="normalizeAttr"
              append-to-body
              :z-index="1050"
            >
              <template #option-label="{ node }">
                <div
                  :title="node.label"
                  :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }"
                >
                  {{ node.label }}
                </div>
              </template>
            </Treeselect>
          </a-form-item>
        </a-col>
        <a-col v-if="choiceOther.type_ids && choiceOther.type_ids.length" :span="24">
          <a-form-item
            :style="{ marginBottom: '5px' }"
            class="pre-value-filter"
            :label="t('cmdb.ciType.filter')"
            :label-col="{ span: 3 }"
            :wrapper-col="{ span: 19 }"
          >
            <!-- TODO: wire up <AttrFilter ref="attrFilterRef" ... @setExpFromFilter="setExpFromFilter" /> once migrated -->
          </a-form-item>
        </a-col>
      </a-row>
    </a-tab-pane>
    <a-tab-pane key="script" :disabled="disabled || !canDefineScript">
      <template #tab><span style="font-size: 14px">{{ t('cmdb.ciType.code') }}</span></template>
      <a-form-item
        :style="{ marginBottom: '5px' }"
        :label="t('cmdb.ciType.cascadeAttr')"
        :label-col="{ span: 2 }"
        :wrapper-col="{ span: 19 }"
        label-align="left"
      >
        <a-select
          v-model:value="cascade_attributes"
          mode="multiple"
          style="width: 100%"
          :placeholder="t('placeholder2')"
          option-filter-prop="title"
        >
          <a-select-option v-for="attr in curModelAttrList" :key="attr.id" :value="attr.id" :title="attr.name">
            {{ attr.name }}
          </a-select-option>
        </a-select>
        <div class="ant-form-explain">{{ scriptCodeExtraText }}</div>
      </a-form-item>

      <div class="script-tip">
        <div>1. {{ t('cmdb.ciType.computedAttrTip1') }}</div>
        <div>2. {{ t('cmdb.ciType.computedAttrTip2') }}</div>
        <div>3. {{ t('cmdb.ciType.computedAttrTip3') }}</div>
      </div>

      <div class="all-attr-btn">
        <a-button size="small" @click="showAllPropDrawer">{{ t('cmdb.ciType.viewAllAttr') }}</a-button>
      </div>
      <AllAttrDrawer ref="allAttrDrawerRef" />

      <MonacoCodeEditor
        v-model:value="script"
        language="python"
        :height="300"
        storage-key="cmdbPreValueMonacoEditorConfig"
        @change="changeCodeContent"
      />
    </a-tab-pane>
  </a-tabs>
</template>

<style lang="less" scoped>
.tab-builtin {
  display: flex;
  align-items: center;

  &-title {
    font-size: 14px;
  }

  &-tag {
    background-color: #e1efff;
    color: @primary-color;
    font-size: 10px;
    font-weight: 400;
    padding: 0 3px;
    margin-left: 3px;
  }
}

.tab-webhook-filter-icon {
  position: absolute;
  top: 3px;
  left: -17px;
  color: @primary-color;
}

.script-tip {
  font-size: 12px;
  line-height: 22px;
  color: #a5a9bc;
}

.all-attr-btn {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
  margin-bottom: 10px;
}
</style>

<style lang="less">
.pre-value-filter {
  .ant-form-item-control {
    line-height: 24px;
  }
  .table-filter-add {
    line-height: 40px;
  }
}
</style>
