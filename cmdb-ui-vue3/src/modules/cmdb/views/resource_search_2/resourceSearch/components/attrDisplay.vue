<script setup lang="ts">
import { AppstoreOutlined } from '@ant-design/icons-vue'
import PasswordField from '@/modules/cmdb/components/passwordField/index.vue'
import CiFileField from '@/modules/cmdb/components/CiFileField.vue'

const props = withDefaults(
  defineProps<{
    attr: Record<string, any>
    ci: Record<string, any>
    isEllipsis?: boolean
    referenceShowAttrNameMap?: Record<string, string>
    referenceCIIdMap?: Record<string, Record<string, any>>
    searchValue?: string
  }>(),
  {
    attr: () => ({}),
    ci: () => ({}),
    isEllipsis: false,
    referenceShowAttrNameMap: () => ({}),
    referenceCIIdMap: () => ({}),
    searchValue: '',
  }
)

function markSearchValue(text: unknown): string {
  if (!text || !props.searchValue) {
    return String(text)
  }
  const regex = new RegExp(`(${props.searchValue})`, 'gi')
  return String(text).replace(regex, `<span style="background-color: #D3EEFE; padding: 0 2px;">$1</span>`)
}

function getChoiceValueStyle(attrValue: unknown): Record<string, any> {
  const found = props.attr?.choice_value?.find?.((item: any[]) => String(item?.[0]) === String(attrValue))
  if (found) {
    return found?.[1]?.style || {}
  }
  return {}
}

function getChoiceValueIcon(attrValue: unknown): Record<string, any> {
  const found = props.attr?.choice_value?.find((item: any[]) => String(item?.[0]) === String(attrValue))
  if (found) {
    return found?.[1]?.icon || {}
  }
  return {}
}

function getChoiceValueLabel(attrValue: unknown): string {
  const found = props.attr?.choice_value?.find((item: any[]) => String(item?.[0]) === String(attrValue))
  if (found) {
    return found?.[1]?.label || ''
  }
  return ''
}

function getReferenceAttrValue(id: string | number): string {
  if (props.attr.referenceShowAttrNameMap?.[id]) {
    return props.attr.referenceShowAttrNameMap[id]
  }

  const ci = props.referenceCIIdMap?.[props.attr?.reference_type_id]?.[id]
  if (!ci) {
    return String(id)
  }

  const attrName = props.referenceShowAttrNameMap?.[props.attr.reference_type_id]
  return ci?.[attrName] || String(id)
}
</script>

<template>
  <!-- eslint-disable vue/no-v-html, vue/no-mutating-props -->
  <div :class="['attr-display', isEllipsis ? 'attr-display-ellipsis' : '']">
    <template v-if="attr.is_reference && ci[attr.name]">
      <a
        v-for="ciId in (attr.is_list ? ci[attr.name] : [ci[attr.name]])"
        :key="ciId"
        :href="`/cmdb/cidetail/${attr.reference_type_id}/${ciId}`"
        target="_blank"
      >
        {{ getReferenceAttrValue(ciId) }}
      </a>
    </template>
    <span v-else-if="attr.value_type === '6' && ci[attr.name]">{{ JSON.stringify(ci[attr.name]) }}</span>
    <template v-else-if="attr.is_link && ci[attr.name]">
      <a
        v-for="(item, linkIndex) in (attr.is_list ? ci[attr.name] : [ci[attr.name]])"
        :key="linkIndex"
        :href="
          item.startsWith('http') || item.startsWith('https')
            ? `${item}`
            : `http://${item}`
        "
        target="_blank"
      >
        {{ getChoiceValueLabel(item) || item }}
      </a>
    </template>
    <PasswordField
      v-else-if="attr.is_password && ci[attr.name]"
      :ci_id="ci._id"
      :attr_id="attr.id"
    />
    <CiFileField
      v-else-if="attr.is_file"
      :value="ci[attr.name]"
      :is-list="attr.is_list"
      :is-edit="false"
      :attr-id="attr.id"
      :ci-id="ci._id"
      :attr-name="attr.name"
      @input="(val: string) => { ci[attr.name] = val }"
    />
    <template v-else-if="attr.is_choice">
      <span
        v-for="value in (attr.is_list ? ci[attr.name] : [ci[attr.name]])"
        :key="value"
        :style="{
          borderRadius: '4px',
          padding: '1px 5px',
          margin: '2px',
          ...getChoiceValueStyle(value),
        }"
      >
        <img
          v-if="getChoiceValueIcon(value).id && getChoiceValueIcon(value).url"
          :src="`/api/common-setting/v1/file/${getChoiceValueIcon(value).url}`"
          :style="{ maxHeight: '13px', maxWidth: '13px', marginRight: '5px' }"
        />
        <AppstoreOutlined
          v-else-if="getChoiceValueIcon(value).name"
          :style="{ color: getChoiceValueIcon(value).color, marginRight: '5px' }"
        />
        <span v-html="markSearchValue(getChoiceValueLabel(value) || value)"></span>
      </span>
    </template>
    <span
      v-else
      :style="{ whiteSpace: isEllipsis ? 'nowrap' : 'pre-wrap' }"
      v-html="markSearchValue((attr.is_list && Array.isArray(ci[attr.name])) ? ci[attr.name].join(',') : ci[attr.name])"
    ></span>
  </div>
</template>

<style lang="less" scoped>
.attr-display {
  width: 100%;
  font-size: 14px;
  font-weight: 400;
  word-break: break-all;

  &-ellipsis {
    overflow: hidden;
    text-overflow: ellipsis;
    text-wrap: nowrap;
  }
}
</style>
