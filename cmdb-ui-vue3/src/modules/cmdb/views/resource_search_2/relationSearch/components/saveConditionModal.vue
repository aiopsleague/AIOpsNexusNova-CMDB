<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = withDefaults(
  defineProps<{
    visible?: boolean
  }>(),
  {
    visible: false,
  }
)

const emit = defineEmits<{
  (e: 'ok', data: { name: string }): void
  (e: 'cancel'): void
}>()

const { t, locale } = useI18n()

const saveConditionFormRef = ref()

const form = reactive<{ name: string }>({
  name: '',
})

const formRule = computed(() => ({
  name: [{ required: true, message: t('placeholder1') }],
}))

const labelCol = computed(() => ({
  span: locale.value === 'en' ? 7 : 4,
}))

const wrapperCol = computed(() => ({
  span: locale.value === 'en' ? 17 : 20,
}))

function handleOk() {
  saveConditionFormRef.value
    .validate()
    .then(() => {
      emit('ok', {
        name: form.name,
      })
      handleCancel()
    })
    .catch(() => {
      /* validation failed */
    })
}

function handleCancel() {
  saveConditionFormRef.value?.clearValidate()
  form.name = ''
  emit('cancel')
}

watch(
  () => props.visible,
  (visible) => {
    if (!visible) {
      saveConditionFormRef.value?.clearValidate()
    }
  }
)
</script>

<template>
  <a-modal
    :title="t('cmdb.relationSearch.saveCondition')"
    :open="visible"
    dialog-class="save-condition-modal"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <a-form
      ref="saveConditionFormRef"
      :model="form"
      :rules="formRule"
      :label-col="labelCol"
      :wrapper-col="wrapperCol"
    >
      <a-form-item :label="t('cmdb.relationSearch.conditionName')" name="name">
        <a-input v-model:value="form.name" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>
