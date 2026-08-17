<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'

const emit = defineEmits<{
  (e: 'submitServiceTree', form: Record<string, any>, type: string, originName?: string): void
}>()

const { t } = useI18n()

const visible = ref(false)
const type = ref('add')
const originTreeData = ref<Record<string, any>>({})
const formRef = ref()

const form = reactive<Record<string, any>>({
  name: '',
  is_public: true,
  is_show_leaf_node: true,
  is_show_tree_node: false,
  sort: 1,
})

const rules = {
  name: [{ required: true, message: t('cmdb.preference_relation.serviceTreeNamePlaceholder') }],
  is_public: [{ required: false }],
  is_show_leaf_node: [{ required: true }],
  is_show_tree_node: [{ required: false }],
}

const title = computed(() => {
  if (type.value === 'edit') {
    return t('cmdb.preference_relation.editServiceTree')
  }
  return t('cmdb.preference_relation.newServiceTree')
})

function open(treeData: Record<string, any> = {}, _type: string) {
  visible.value = true
  type.value = _type
  originTreeData.value = { ...treeData }
  Object.assign(form, {
    name: '',
    is_public: true,
    is_show_leaf_node: true,
    is_show_tree_node: false,
    sort: 1,
    ...treeData,
  })
}

function handleCancel() {
  formRef.value?.resetFields()
  visible.value = false
}

function handleOK() {
  formRef.value
    .validate()
    .then(() => {
      emit('submitServiceTree', { ...form }, type.value, originTreeData.value?.name ?? undefined)
      handleCancel()
    })
    .catch(() => {
      /* validation failed */
    })
}

function changeLeaf(e: any) {
  const checked = e.target.checked
  if (!checked) {
    message.warning(t('cmdb.preference_relation.tips4'))
    return
  }
  form.is_show_leaf_node = checked
}

defineExpose({ open })
</script>

<template>
  <a-modal width="700px" :title="title" :open="visible" @cancel="handleCancel" @ok="handleOK">
    <a-form ref="formRef" :model="form" :rules="rules" :label-col="{ span: 8 }" :wrapper-col="{ span: 14 }">
      <a-form-item :label="t('cmdb.preference_relation.serviceTreeName')" name="name">
        <a-input v-model:value="form.name" :placeholder="t('cmdb.preference_relation.serviceTreeNamePlaceholder')" />
      </a-form-item>
      <a-form-item :label="t('cmdb.preference_relation.public')" name="is_public">
        <a-checkbox v-model:checked="form.is_public"> </a-checkbox>
      </a-form-item>
      <a-form-item :label="t('cmdb.preference_relation.showLeafNode')" name="is_show_leaf_node">
        <a-checkbox :checked="form.is_show_leaf_node" @change="changeLeaf"> </a-checkbox>
      </a-form-item>
      <a-form-item :label="t('cmdb.preference_relation.showTreeNode')" name="is_show_tree_node">
        <a-checkbox v-model:checked="form.is_show_tree_node"> </a-checkbox>
      </a-form-item>
      <a-form-item
        v-if="form.is_show_leaf_node && form.is_show_tree_node"
        :label="t('cmdb.preference_relation.sort')"
        name="sort"
      >
        <a-radio-group v-model:value="form.sort">
          <a-radio :value="1">
            {{ t('cmdb.preference_relation.sort1') }}
          </a-radio>
          <a-radio :value="2">
            {{ t('cmdb.preference_relation.sort2') }}
          </a-radio>
        </a-radio-group>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<style></style>
