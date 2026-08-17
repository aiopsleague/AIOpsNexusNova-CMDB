<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { putAutoSubscription } from '@/modules/cmdb/api/preference'

const props = withDefaults(
  defineProps<{
    ciType?: any[]
    autoSub?: Record<string, any>
  }>(),
  {
    ciType: () => [],
    autoSub: () => ({}),
  }
)

const emit = defineEmits<{ (e: 'ok'): void }>()

const { t } = useI18n()

const visible = ref(false)
const autuSubFormRef = ref()

const form = reactive<{
  base_strategy: string
  group_ids: any[]
  type_ids: any[]
  enabled: boolean
}>({
  base_strategy: 'all',
  group_ids: [],
  type_ids: [],
  enabled: true,
})

const rules = {
  base_strategy: [{ required: true, message: t('placeholder2') }],
}

const baseStrategyOptions = [
  { label: t('cmdb.preference.subscribeAllModel'), value: 'all' },
  { label: t('cmdb.preference.selectiveSubscription'), value: 'none' },
]

const groupSelectOptions = ref<any[]>([])
const modelSelectOptions = ref<any[]>([])

function open() {
  form.base_strategy = props.autoSub?.base_strategy || 'all'
  form.group_ids = props.autoSub?.group_ids || []
  form.type_ids = props.autoSub?.type_ids || []
  form.enabled = props.autoSub?.enabled ?? true

  groupSelectOptions.value = props.ciType.map((group: any) => {
    return {
      label: group.name,
      title: group.name,
      value: group.id,
    }
  })

  const _modelSelectOptions = props.ciType.filter((group: any) => group?.ci_types?.length)
  modelSelectOptions.value = _modelSelectOptions.map((group: any) => {
    return {
      label: group.name,
      value: group.id,
      children: group.ci_types.map((type: any) => {
        return {
          label: type.alias || type.name,
          value: type.id,
        }
      }),
    }
  })

  visible.value = true
}

function handleCancel() {
  visible.value = false
}

function handleOk() {
  autuSubFormRef.value
    .validate()
    .then(() => {
      const { base_strategy, group_ids, type_ids, enabled } = form
      const params = {
        base_strategy,
        group_ids: group_ids.join(','),
        type_ids: type_ids.join(','),
        enabled,
      }
      putAutoSubscription(params).then(() => {
        message.success(t('saveSuccess'))
        handleCancel()
        emit('ok')
      })
    })
    .catch(() => {
      /* validation failed */
    })
}

defineExpose({ open })
</script>

<template>
  <a-modal
    :title="t('cmdb.preference.autoSub')"
    :open="visible"
    :width="600"
    @cancel="handleCancel"
    @ok="handleOk"
  >
    <a-form
      ref="autuSubFormRef"
      :model="form"
      :rules="rules"
      :label-col="{ span: 7 }"
      :wrapper-col="{ span: 15 }"
    >
      <a-form-item :label="t('cmdb.preference.autoSubScope')" name="base_strategy">
        <a-radio-group v-model:value="form.base_strategy" :options="baseStrategyOptions" />
        <div class="ant-form-explain">{{ t('cmdb.preference.autoSubScopeHint') }}</div>
      </a-form-item>
      <a-form-item
        :label="
          form.base_strategy === 'all' ? t('cmdb.preference.excludeGroup') : t('cmdb.preference.selectGroup')
        "
        name="group_ids"
      >
        <a-select
          v-model:value="form.group_ids"
          mode="multiple"
          option-filter-prop="title"
          :options="groupSelectOptions"
          :placeholder="
            form.base_strategy === 'all'
              ? t('cmdb.preference.excludeGroupPlaceholder')
              : t('cmdb.preference.selectGroupPlaceholder')
          "
        />
        <div class="ant-form-explain">
          {{ form.base_strategy === 'all' ? t('cmdb.preference.excludeGroupHint') : t('cmdb.preference.selectGroupHint') }}
        </div>
      </a-form-item>

      <a-form-item
        :label="
          form.base_strategy === 'all' ? t('cmdb.preference.excludeModel') : t('cmdb.preference.selectModel')
        "
        name="type_ids"
      >
        <a-select
          v-model:value="form.type_ids"
          mode="multiple"
          option-filter-prop="title"
          :placeholder="
            form.base_strategy === 'all'
              ? t('cmdb.preference.excludeModelPlaceholder')
              : t('cmdb.preference.selectModelPlaceholder')
          "
        >
          <a-select-opt-group v-for="group in modelSelectOptions" :key="group.value" :label="group.label">
            <a-select-option
              v-for="type in group.children"
              :key="type.value"
              :value="type.value"
              :title="type.label"
            >
              {{ type.label }}
            </a-select-option>
          </a-select-opt-group>
        </a-select>
        <div class="ant-form-explain">
          {{ form.base_strategy === 'all' ? t('cmdb.preference.excludeModelHint') : t('cmdb.preference.selectModelHint') }}
        </div>
      </a-form-item>

      <a-form-item :label="t('cmdb.preference.isEnable')" name="enabled">
        <a-switch v-model:checked="form.enabled" />
        <div class="ant-form-explain">{{ t('cmdb.preference.enableAutoSubTip') }}</div>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<style lang="less" scoped></style>
