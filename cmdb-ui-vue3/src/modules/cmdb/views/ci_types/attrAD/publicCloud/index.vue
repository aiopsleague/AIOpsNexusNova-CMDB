<script setup lang="ts">
import { computed, inject, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getHTTPAccounts } from '@/modules/cmdb/api/discovery'
import { TAB_KEY } from '../constants'
import CloudTab from '../cloudTab/index.vue'

const props = withDefaults(
  defineProps<{
    value?: Record<string, any>
  }>(),
  {
    value: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'change', value: Record<string, any>): void
}>()

const { t } = useI18n()

const provide_labelCol = inject<() => any>('provide_labelCol')

const accountsList = ref<any[]>([])

const formData = computed({
  get: () => props.value,
  set: (newValue) => emit('change', newValue),
})

const labelCol = computed(() => provide_labelCol?.())

async function init(id: string | number) {
  const res = await getHTTPAccounts({ adr_id: id })
  accountsList.value = res?.length ? res : []

  nextTick(() => {
    const { _reference = '', key = '', tabActive } = props.value || {}
    const findSelect = accountsList.value?.find((item) => item.id === _reference)
    const newFormData = findSelect?.config || {}

    const changeData: Record<string, any> = {
      ...props.value,
      _reference: findSelect?.id ?? '',
    }
    if (tabActive === TAB_KEY.CONFIG) {
      changeData.key = newFormData?.key ?? key
    }
    emit('change', changeData)
  })
}

function handleTabChange(key: string) {
  // Keep the shared form object in sync, mirroring the legacy v-model binding.
  formData.value.tabActive = key
  if (key === TAB_KEY.CONFIG) {
    handleSelectChange(formData.value._reference)
  }
}

function handleSelectChange(id: any) {
  const accountConfig = accountsList.value.find((item) => item.id === id)?.config || {}
  const { key } = props.value
  emit('change', {
    ...props.value,
    key: accountConfig?.key ?? key ?? '',
  })
}

defineExpose({ init })
</script>

<template>
  <div class="public-cloud-wrap">
    <CloudTab
      :value="formData.tabActive"
      @change="handleTabChange"
    />
    <a-form
      :model="formData"
      label-align="right"
      :label-col="labelCol"
      :wrapper-col="{ span: 6 }"
      class="attr-ad-form"
    >
      <a-form-item
        v-if="formData.tabActive === TAB_KEY.CONFIG"
        :required="true"
        :label="t('cmdb.ad.tabConfig')"
      >
        <a-select
          v-model:value="formData._reference"
          show-search
          option-filter-prop="title"
          @change="handleSelectChange"
        >
          <a-select-option
            v-for="item in accountsList"
            :key="item.id"
            :value="item.id"
            :title="item.name"
          >
            {{ item.name }}
          </a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item :required="true" label="key">
        <a-input-password
          v-model:value="formData.key"
          :class="[formData.tabActive === TAB_KEY.CONFIG ? 'input-disabled' : '']"
        />
      </a-form-item>
      <a-form-item v-if="formData.tabActive === TAB_KEY.CUSTOM" :required="true" label="secret">
        <a-input-password v-model:value="formData.secret" />
      </a-form-item>
    </a-form>
  </div>
</template>

<style lang="less" scoped>
.public-cloud-wrap {
  margin-left: 17px;

  .input-disabled {
    :deep(input) {
      color: rgba(0, 0, 0, 0.25);
      background-color: #f5f5f5;
      pointer-events: none;
      opacity: 1;
    }
  }
}
</style>
