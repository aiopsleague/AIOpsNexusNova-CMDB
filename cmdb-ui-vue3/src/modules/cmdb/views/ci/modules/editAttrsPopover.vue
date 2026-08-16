<script setup lang="ts">
import { ref } from 'vue'
import { SettingOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import AttributesTransfer from '@/modules/cmdb/components/attributesTransfer/index.vue'
import { subscribeCIType, getSubscribeAttributes } from '@/modules/cmdb/api/preference'
import { getCITypeAttributesByName } from '@/modules/cmdb/api/CITypeAttr'
import { CI_DEFAULT_ATTR } from '@/modules/cmdb/constants'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    typeId?: number | null
  }>(),
  {
    typeId: null,
  }
)

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const visible = ref(false)
const attrList = ref<any[]>([])
const selectedAttrList = ref<string[]>([])
const fixedList = ref<string[]>([])

function visibleChange(open: boolean) {
  if (open) {
    getAttrs()
  }
}

function getAttrs() {
  const updatedByKey = CI_DEFAULT_ATTR.UPDATE_USER
  const updatedAtKey = CI_DEFAULT_ATTR.UPDATE_TIME

  getCITypeAttributesByName(props.typeId as number).then((res) => {
    const attributes = res.attributes.filter((item: any) => ![updatedByKey, updatedAtKey].includes(item.name))
    ;[updatedByKey, updatedAtKey].forEach((key) => {
      attributes.push({
        alias: key,
        name: key,
        id: key,
      })
    })

    getSubscribeAttributes(props.typeId as number).then((_res) => {
      const selectedAttrListRes = _res.attributes.map((item: any) => item.id.toString())

      const attrListRes = attributes.map((item: any) => {
        return {
          key: item.id.toString(),
          title: item.alias || item.name,
          name: item.name,
        }
      })

      attrList.value = attrListRes
      selectedAttrList.value = selectedAttrListRes
      fixedList.value = _res.attributes.filter((item: any) => item.is_fixed).map((item: any) => item.id.toString())
      visible.value = true
    })
  })
}

function handleSubmit() {
  if (selectedAttrList.value.length) {
    const customAttr: string[] = []
    const defaultAttr: string[] = []
    selectedAttrList.value.forEach((attr) => {
      if ([CI_DEFAULT_ATTR.UPDATE_USER, CI_DEFAULT_ATTR.UPDATE_TIME].includes(attr)) {
        defaultAttr.push(attr)
      } else {
        customAttr.push(attr)
      }
    })
    const selected = [...customAttr, ...defaultAttr]

    subscribeCIType(
      props.typeId as number,
      selected.map((item) => [item, !!fixedList.value.includes(item)])
    ).then(() => {
      message.success(t('cmdb.components.subSuccess'))
      visible.value = false
      emit('refresh')
    })
  } else {
    message.error(t('cmdb.ci.tips4'))
  }
}

function setTargetKeys(targetKeys: Array<string | number>) {
  selectedAttrList.value = targetKeys.map(String)
}

function changeSingleItem(item: { key: string | number }) {
  const key = String(item.key)
  const idx = selectedAttrList.value.findIndex((k) => k === key)
  if (idx > -1) {
    selectedAttrList.value.splice(idx, 1)
  } else {
    selectedAttrList.value.push(key)
  }
}

function setFixedList(list: Array<string | number>) {
  fixedList.value = list.map(String)
}
</script>

<template>
  <a-popover v-model:open="visible" trigger="click" placement="leftBottom" @open-change="visibleChange">
    <template #content>
      <AttributesTransfer
        :data-source="attrList"
        :target-keys="selectedAttrList"
        :show-default-attr="true"
        :fixed-list="fixedList"
        @set-target-keys="setTargetKeys"
        @change-single-item="changeSingleItem"
        @handle-submit="handleSubmit"
        @set-fixed-list="setFixedList"
      />
    </template>
    <slot>
      <div :style="{ height: '100%', width: '30px', float: 'right', borderLeft: '1px solid #e8eaec' }">
        <SettingOutlined :style="{ margin: '13px 0 0 10px' }" />
      </div>
    </slot>
  </a-popover>
</template>
