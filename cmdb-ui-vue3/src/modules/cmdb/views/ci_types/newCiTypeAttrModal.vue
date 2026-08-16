<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, nextTick, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { searchAttributes, createCITypeAttributes, updateCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { createCITypeGroupById, getCITypeGroupById } from '@/modules/cmdb/api/CIType'
import CreateNewAttribute from './ceateNewAttribute.vue'
import AttributesTransfer from '../../components/attributesTransfer/index.vue'
import { cloneDeep } from '../../utils/helper'

interface GroupData {
  id: number
  name: string
  order: number
  attributes: any[]
  [key: string]: any
}

const props = withDefaults(
  defineProps<{
    linkedIds: number[]
    CITypeId?: number | null
  }>(),
  { CITypeId: null }
)

const emit = defineEmits<{ (e: 'ok'): void }>()

const { t } = useI18n()

const createNewAttributeRef = ref<{ handleSubmit: (isCloseModal?: boolean) => void; checkCanDefineComputed: () => void }>()

const activeKey = ref('1')
const visible = ref(false)
const totalAttributes = ref<any[]>([])
const targetKeys = ref<string[]>([])
const currentGroup = ref<GroupData | null>(null)
const confirmLoading = ref(false)

const unLinkdAttrs = computed(() =>
  totalAttributes.value
    .filter((attr) => !props.linkedIds.includes(attr.id))
    .map((attr) => ({ key: String(attr.id), title: attr.alias || attr.name, name: attr.name }))
)

async function handleSubmit(isCloseModal = true) {
  if (activeKey.value === '2') {
    if (targetKeys.value.length) {
      confirmLoading.value = true
      await handleLinkAttrToCiType({ attr_id: targetKeys.value.map((i) => Number(i)) })
      if (currentGroup.value) {
        await updateCurrentGroup()
        const { name, order, attributes } = currentGroup.value
        const attrIds = attributes.filter((i) => !i.inherited).map((i) => i.id)
        targetKeys.value.forEach((key) => {
          attrIds.push(Number(key))
        })
        await createCITypeGroupById(props.CITypeId as number, { name, order, attributes: [...new Set(attrIds)] })
      }
      confirmLoading.value = false
      handleClose(isCloseModal)
    }
  } else {
    try {
      createNewAttributeRef.value?.handleSubmit(isCloseModal)
    } catch {
      /* validation failed */
    }
  }
}

function handleEdit(group: GroupData | null) {
  targetKeys.value = []
  visible.value = true
  currentGroup.value = group
  activeKey.value = '1'
  loadTotalAttrs()
  nextTick(() => {
    createNewAttributeRef.value?.checkCanDefineComputed()
  })
}

async function loadTotalAttrs() {
  const res = await searchAttributes({ page_size: 9999 })
  totalAttributes.value = res.attributes
}

async function handleAddNewAttr(newAttrId: number, data: Record<string, unknown>, isCloseModal = true) {
  const { is_required, default_show } = data as { is_required?: boolean; default_show?: boolean }
  confirmLoading.value = true
  await handleLinkAttrToCiType({ attr_id: [newAttrId] })
  await updateCITypeAttributesById(props.CITypeId as number, {
    attributes: [{ attr_id: newAttrId, is_required: is_required || false, default_show: default_show || false }],
  })
  if (currentGroup.value) {
    await updateCurrentGroup()
    const { name, order, attributes } = currentGroup.value
    const attrIds = attributes.filter((i) => !i.inherited).map((i) => i.id)
    attrIds.push(newAttrId)
    await createCITypeGroupById(props.CITypeId as number, { name, order, attributes: attrIds })
  }
  confirmLoading.value = false
  loadTotalAttrs()
  nextTick(() => {
    handleClose(isCloseModal)
  })
}

async function handleLinkAttrToCiType(data: Record<string, unknown>) {
  return createCITypeAttributes(props.CITypeId as number, data)
}

function handleClose(isCloseModal = true) {
  emit('ok')
  message.success(t('addSuccess'))
  if (isCloseModal) {
    visible.value = false
  }
  confirmLoading.value = false
}

function setTargetKeys(keys: Array<string | number>) {
  targetKeys.value = keys.map(String)
}

function changeSingleItem(item: { key: string | number }) {
  const key = String(item.key)
  const idx = targetKeys.value.findIndex((k) => k === key)
  if (idx > -1) {
    targetKeys.value.splice(idx, 1)
  } else {
    targetKeys.value.push(key)
  }
}

async function updateCurrentGroup() {
  await getCITypeGroupById(props.CITypeId as number).then((res) => {
    const _find = res.find((item: GroupData) => item.id === currentGroup.value?.id)
    if (_find && currentGroup.value) {
      currentGroup.value.attributes = cloneDeep(_find.attributes)
    }
  })
}

defineExpose({ handleEdit })
</script>

<template>
<!-- eslint-disable vue/attribute-hyphenation -->
  <a-modal
    width="800px"
    :open="visible"
    wrap-class-name="new-ci_type-attr-modal"
    :body-style="{ overflow: 'auto', maxHeight: '600px' }"
    :destroy-on-close="true"
    @cancel="() => (visible = false)"
  >
    <template #footer>
      <a-button @click="() => (visible = false)">{{ t('cancel') }}</a-button>
      <a-button :loading="confirmLoading" type="primary" @click="handleSubmit(false)">{{
        t('cmdb.ciType.continueAdd')
      }}</a-button>
      <a-button :loading="confirmLoading" type="primary" @click="handleSubmit()">{{ t('confirm') }}</a-button>
    </template>
    <a-tabs v-model:active-key="activeKey">
      <a-tab-pane key="1" :tab="t('cmdb.ciType.addAttribute')">
        <div :style="{ overflow: 'auto', maxHeight: '480px' }">
          <CreateNewAttribute
            ref="createNewAttributeRef"
            :has-footer="false"
            :CITypeId="CITypeId"
            @done="handleAddNewAttr"
          />
        </div>
      </a-tab-pane>
      <a-tab-pane key="2" :tab="t('cmdb.ciType.existedAttributes')" force-render>
        <AttributesTransfer
          :data-source="unLinkdAttrs"
          :target-keys="targetKeys"
          :has-footer="false"
          :is-sortable="false"
          :is-fixable="false"
          @set-target-keys="setTargetKeys"
          @change-single-item="changeSingleItem"
        />
      </a-tab-pane>
    </a-tabs>
  </a-modal>
</template>

<style lang="less">
.new-ci_type-attr-modal {
  .ant-modal-header {
    border-bottom: none;
    padding-bottom: 0;
  }

  .ant-tabs-ink-bar {
    background-color: @primary-color;
  }

  .ant-tabs-tab-active {
    color: @primary-color;
  }
}
</style>
