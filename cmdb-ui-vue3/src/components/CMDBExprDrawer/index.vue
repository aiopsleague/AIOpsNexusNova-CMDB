<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import CustomDrawer from '@/components/CustomDrawer/index.vue'

withDefaults(
  defineProps<{
    placement?: 'right' | 'left' | 'top' | 'bottom'
    type?: string
    typeId?: number | null
  }>(),
  {
    placement: 'right',
    type: 'resourceSearch',
    typeId: null,
  }
)

const emit = defineEmits<{ (e: 'copySuccess', text: string): void }>()
const { t } = useI18n()

const visible = ref(false)

function open() {
  visible.value = true
}

function handleClose() {
  visible.value = false
}

function copySuccess(text: string) {
  emit('copySuccess', text)
  handleClose()
}

defineExpose({ open, copySuccess })
</script>

<template>
  <CustomDrawer
    width="1000px"
    :open="visible"
    :has-title="false"
    :has-footer="false"
    :closable="false"
    :placement="placement"
    @close="handleClose"
  >
    <div class="cmdb-expr-drawer-body">
      <!--
        The original component embeds `ResourceSearch` (from cmdb-ui's
        `modules/cmdb/views/resource_search`) with `fromCronJob=true`.
        That view has not been migrated to Vue 3 yet, so a placeholder is
        rendered here. The drawer's public API (`open()`, `copySuccess`
        event and the `placement`/`type`/`typeId` props) is preserved.
      -->
      <a-empty :description="t('cmdb.components.resourceSearchPending')" />
    </div>
  </CustomDrawer>
</template>

<style scoped>
.cmdb-expr-drawer-body {
  padding: 24px 12px;
}
</style>
