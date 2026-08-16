<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getCITypeParent } from '@/modules/cmdb/api/CITypeRelation'

const { t } = useI18n()

const props = defineProps<{
  typeId: number
}>()

const emit = defineEmits<{
  (e: 'submit', values: Record<string, any>): void
  (e: 'refresh', value: boolean): void
}>()

const visible = ref(false)
const parentCITypes = ref<any[]>([])
const formModel = reactive<Record<string, any>>({})

const formItemLayout = {
  labelCol: { xs: { span: 24 }, sm: { span: 8 } },
  wrapperCol: { xs: { span: 24 }, sm: { span: 16 } },
}

function getParentCITypes() {
  getCITypeParent(props.typeId).then((res) => {
    parentCITypes.value = res.parents
  })
}

function commitUpdateRelation() {
  emit('submit', { ...formModel })
}

function handleClose() {
  visible.value = false
  emit('refresh', true)
}

onMounted(() => {
  getParentCITypes()
})
</script>

<template>
  <a-drawer
    :title="t('cmdb.ci.batchAddRelation')"
    width="50%"
    :open="visible"
    :wrap-style="{ overflow: 'auto' }"
    @close="handleClose"
  >
    <a-form :model="formModel" :layout="'horizontal'">
      <a-button type="primary" @click="commitUpdateRelation">{{ t('submit') }}</a-button>
      <a-form-item
        v-for="item in parentCITypes"
        :key="item.id"
        v-bind="formItemLayout"
        :label="item.alias || item.name"
      >
        <template v-for="_item in item.attributes" :key="_item.id">
          <a-input
            v-if="_item.id == item.unique_id"
            v-model:value="formModel[_item.name]"
            style="width: 100%"
            :placeholder="_item.alias || _item.name"
          />
        </template>
      </a-form-item>
    </a-form>
  </a-drawer>
</template>
