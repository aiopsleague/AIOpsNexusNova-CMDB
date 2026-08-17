<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import { subscribeRelationView } from '@/modules/cmdb/api/preference'

const emit = defineEmits<{ (e: 'refresh'): void }>()

const { t } = useI18n()

const drawerVisible = ref(false)
const crIds = ref<any[]>([])
const formRef = ref()

const form = reactive<{ name: string }>({
  name: '',
})

const rules = {
  name: [{ required: true, message: t('cmdb.preference_relation.tips2') }],
}

function handleCreate(nextCrIds: any[]) {
  crIds.value = nextCrIds
  drawerVisible.value = true
}

function onClose() {
  formRef.value?.resetFields()
  drawerVisible.value = false
}

function handleSubmit() {
  formRef.value
    .validate()
    .then((values: { name: string }) => {
      createRelationView(values)
    })
    .catch(() => {
      /* validation failed */
    })
}

function createRelationView(data: Record<string, any>) {
  data.cr_ids = crIds.value
  subscribeRelationView(data).then(() => {
    message.success(t('addSuccess'))
    onClose()
    emit('refresh')
  })
}

defineExpose({ handleCreate })
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <CustomDrawer
    :closable="false"
    :title="t('cmdb.preference_relation.newServiceTree')"
    :open="drawerVisible"
    @close="onClose"
    placement="right"
    width="30%"
  >
    <a-form ref="formRef" :model="form" :rules="rules" layout="vertical">
      <a-form-item
        :label="t('cmdb.preference_relation.serviceTreeName')"
        name="name"
      >
        <a-input v-model:value="form.name" placeholder="" />
      </a-form-item>

      <div class="custom-drawer-bottom-action">
        <a-button @click="onClose">{{ t('cancel') }}</a-button>
        <a-button @click="handleSubmit" type="primary">{{ t('submit') }}</a-button>
      </div>
    </a-form>
  </CustomDrawer>
</template>

<style lang="less" scoped>
.search {
  margin-bottom: 54px;
}

.fold {
  width: calc(100% - 216px);
  display: inline-block;
}

.operator {
  margin-bottom: 18px;
}
.action-btn {
  margin-bottom: 1rem;
}

@media screen and (max-width: 900px) {
  .fold {
    width: 100%;
  }
}
</style>
