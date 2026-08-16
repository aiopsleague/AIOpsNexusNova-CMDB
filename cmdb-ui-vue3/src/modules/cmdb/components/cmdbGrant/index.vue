<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { ref } from 'vue'
import GrantComp from './grantComp.vue'

withDefaults(
  defineProps<{
    resourceType?: string
    app_id?: string
  }>(),
  {
    resourceType: 'CIType',
    app_id: '',
  }
)

const visible = ref(false)
const resourceTypeName = ref('')
const typeRelationIds = ref<Array<string | number>>([])
const cmdbGrantType = ref('')
const CITypeId = ref<number | null>(null)

function open({
  name,
  typeRelationIds: relationIds = [],
  cmdbGrantType: grantType,
  CITypeId: ciTypeId,
}: {
  name: string
  typeRelationIds?: Array<string | number>
  cmdbGrantType?: string
  CITypeId?: number | null
}) {
  visible.value = true
  resourceTypeName.value = name
  typeRelationIds.value = relationIds
  cmdbGrantType.value = grantType ?? ''
  CITypeId.value = ciTypeId ?? null
}

function handleOk() {
  handleCancel()
}

function handleCancel() {
  visible.value = false
}

defineExpose({ open })
</script>

<template>
  <a-modal
    width="800px"
    :open="visible"
    :body-style="{ padding: 0, paddingTop: '20px' }"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <GrantComp
      :resource-type="resourceType"
      :app_id="app_id"
      :cmdb-grant-type="cmdbGrantType"
      :resource-type-name="resourceTypeName"
      :type-relation-ids="typeRelationIds"
      :c-i-type-id="CITypeId"
      :is-modal="true"
    />
  </a-modal>
</template>
