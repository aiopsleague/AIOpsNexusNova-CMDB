<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { EditOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { updateCI } from '@/modules/cmdb/api/ci'
import { getAttrPassword } from '@/modules/cmdb/api/CITypeAttr'
import CIReferenceAttr from '@/components/ciReferenceAttr/index.vue'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    ci?: Record<string, any>
    attr?: Record<string, any>
    showEdit?: boolean
  }>(),
  {
    ci: () => ({}),
    attr: () => ({}),
    showEdit: true,
  }
)

const emit = defineEmits<{
  (e: 'refresh', name: string): void
  (e: 'updateCIByself', params: Record<string, any>, name: string): void
  (e: 'refreshReferenceAttr'): void
}>()

const isEdit = ref(false)
const formModel = reactive<Record<string, any>>({})

function isLongText(attr: Record<string, any>): boolean {
  return (
    attr.value_type === '2' &&
    attr.is_index === false &&
    !attr.is_link &&
    !attr.is_file &&
    !attr.is_password
  )
}

function eventListener(e: MouseEvent) {
  const datePickerContainer = document.getElementsByClassName('ant-picker-dropdown')
  if (isEdit.value && !datePickerContainer.length) {
    const dom = document.getElementById(`ci-detail-attr-${props.attr.name}`)
    e.stopPropagation()
    e.preventDefault()
    if (dom) {
      const isSelf = dom.contains(e.target as Node)
      if (!isSelf) {
        handleCloseEdit()
      }
    }
  }
}

onMounted(() => {
  document.addEventListener('click', eventListener)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', eventListener)
})

function handleEdit(e: MouseEvent) {
  e.stopPropagation()
  e.preventDefault()
  if (props.attr.value_type === '6') {
    // TODO: wire up JsonEditor (JSON value_type editor not yet ported)
    return
  }
  isEdit.value = true
  const attrName = props.attr.name
  if (props.attr.is_list && !props.attr.is_choice && !props.attr.is_reference) {
    formModel[attrName] = Array.isArray(props.ci[attrName])
      ? props.ci[attrName].join(',')
      : props.ci[attrName]
    return
  }
  if (props.attr.is_password) {
    getAttrPassword(props.ci._id, props.attr.id).then((res) => {
      formModel[attrName] = res.value ?? null
    })
    return
  }
  formModel[attrName] = props.ci[attrName] ?? null
}

async function handleCloseEdit() {
  const attrName = props.attr.name
  const newData = formModel[attrName]
  if (JSON.stringify(props.ci[attrName]) !== JSON.stringify(newData)) {
    await updateCI(props.ci._id, { [attrName]: newData ?? null })
      .then(() => {
        message.success(t('updateSuccess'))
        emit('updateCIByself', { [attrName]: newData }, attrName)
        if (props.attr.is_reference) {
          emit('refreshReferenceAttr')
        }
      })
      .catch(() => {
        emit('refresh', attrName)
      })
  }
  isEdit.value = false
}

function getChoiceValueStyle(col: Record<string, any>, colValue: any): Record<string, any> {
  const _find = (col.choice_value || []).find((item: any) => String(item[0]) === String(colValue))
  return _find?.[1]?.style || {}
}

function getChoiceValueLabel(col: Record<string, any>, colValue: any): string {
  const _find = (col.choice_value || []).find((item: any) => String(item[0]) === String(colValue))
  return _find?.[1]?.label || ''
}

function getName(name: any): string {
  return name ?? ''
}

function getInitReferenceSelectOption(attr: Record<string, any>): { key: number; title: string }[] {
  return Object.keys(attr?.referenceShowAttrNameMap || {}).map((key) => ({
    key: Number(key),
    title: attr?.referenceShowAttrNameMap?.[key] ?? '',
  }))
}
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <span :id="`ci-detail-attr-${attr.name}`">
    <span class="ci-detail-attr-preview" v-if="!isEdit || attr.value_type === '6'">
      <template v-if="attr.is_reference">
        <a
          v-for="(ciId) in (attr.is_list ? ci[attr.name] : [ci[attr.name]])"
          :key="ciId"
          :href="`/cmdb/cidetail/${attr.reference_type_id}/${ciId}`"
          target="_blank"
        >
          {{ attr.referenceShowAttrNameMap ? attr.referenceShowAttrNameMap[ciId] || ciId : ciId }}
        </a>
      </template>
      <!-- TODO: wire up CiFileField (file attribute display not yet ported) -->
      <span v-else-if="attr.is_file">{{ ci[attr.name] }}</span>
      <!-- TODO: wire up PasswordField (password attribute display not yet ported) -->
      <span v-else-if="attr.is_password && ci[attr.name]">********</span>
      <a-tooltip
        v-else-if="attr.value_type === '6'"
        :title="JSON.stringify(ci[attr.name] || {})"
        overlay-class-name="ci-detail-attr-json-tooltip"
      >
        <span class="ci-detail-attr-json">
          {{ JSON.stringify(ci[attr.name] || {}) }}
        </span>
      </a-tooltip>
      <template v-else-if="attr.is_choice">
        <template v-if="attr.is_list">
          <span
            v-for="value in ci[attr.name]"
            :key="value"
            :style="{
              borderRadius: '4px',
              padding: '1px 0',
              margin: '0 2px',
              ...getChoiceValueStyle(attr, value),
              display: 'inline-flex',
              alignItems: 'center',
            }"
          >
            {{ getChoiceValueLabel(attr, value) || value }}
          </span>
        </template>
        <span
          v-else
          :style="{
            borderRadius: '4px',
            padding: '1px 0',
            margin: '0',
            ...getChoiceValueStyle(attr, ci[attr.name]),
            display: 'inline-flex',
            alignItems: 'center',
          }"
        >
          {{ getChoiceValueLabel(attr, ci[attr.name]) || ci[attr.name] }}
        </span>
      </template>
      <template v-else-if="attr.is_list">
        <span> {{ ci[attr.name] && Array.isArray(ci[attr.name]) ? ci[attr.name].join(',') : ci[attr.name] }}</span>
      </template>
      <template v-else>{{ getName(ci[attr.name]) }}</template>
    </span>
    <template v-else>
      <a-form :model="formModel">
        <a-form-item label="" :colon="false">
          <CIReferenceAttr
            v-if="attr.is_reference"
            :reference-type-id="attr.reference_type_id"
            :is-list="attr.is_list"
            :reference-show-attr-name="attr.showAttrName"
            :init-select-option="getInitReferenceSelectOption(attr)"
            :value="formModel[attr.name]"
            @change="(v: any) => (formModel[attr.name] = v)"
          />
          <!-- TODO: wire up CiFileField (file attribute editing not yet ported) -->
          <a-input v-else-if="attr.is_file" v-model:value="formModel[attr.name]" size="small" style="width: 100%" />
          <a-switch
            v-else-if="attr.is_bool"
            :checked="!!formModel[attr.name]"
            @change="(checked: boolean) => (formModel[attr.name] = checked)"
          />
          <a-textarea
            v-else-if="isLongText(attr)"
            v-model:value="formModel[attr.name]"
            size="small"
            style="width: 100%"
          />
          <a-select
            v-else-if="attr.is_choice"
            v-model:value="formModel[attr.name]"
            :mode="attr.is_list ? 'multiple' : undefined"
            show-search
            allow-clear
            size="small"
            style="width: 200px"
            :placeholder="t('placeholder2')"
            :get-popup-container="(trigger: HTMLElement) => trigger.parentElement"
          >
            <a-select-option
              v-for="(choice, choice_idx) in attr.choice_value"
              :value="choice[0]"
              :key="'New_' + attr.name + choice_idx"
            >
              <span :style="{ ...(choice[1] ? choice[1].style : {}), display: 'inline-flex', alignItems: 'center' }">
                {{ choice[1] ? choice[1].label || choice[0] : choice[0] }}
              </span>
            </a-select-option>
          </a-select>
          <a-input-number
            v-else-if="(attr.value_type === '0' || attr.value_type === '1') && !attr.is_list"
            v-model:value="formModel[attr.name]"
            size="small"
            style="width: 100%"
          />
          <a-date-picker
            v-else-if="(attr.value_type === '4' || attr.value_type === '3') && !attr.is_list"
            v-model:value="formModel[attr.name]"
            size="small"
            style="width: 100%"
            :format="attr.value_type === '4' ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss'"
            :value-format="attr.value_type === '4' ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss'"
            :show-time="attr.value_type === '4' ? false : { format: 'HH:mm:ss' }"
          />
          <a-input v-else v-model:value="formModel[attr.name]" size="small" style="width: 100%" />
        </a-form-item>
      </a-form>
    </template>
    <a v-if="!isEdit && !attr.is_computed && !attr.sys_computed && showEdit" @click="handleEdit" :style="{ opacity: 0 }">
      <EditOutlined />
    </a>
    <!-- TODO: wire up JsonEditor (jsonEditorOk handler retained above) -->
  </span>
</template>

<style lang="less" scoped>
.ci-detail-attr-preview {
  width: calc(100% - 28px);
  white-space: pre-wrap;
}

.ci-detail-attr-json {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
</style>

<style lang="less">
.ci-detail-attr-json-tooltip {
  .ant-tooltip-content {
    max-height: 300px;
    overflow-y: auto;
  }
}
</style>
