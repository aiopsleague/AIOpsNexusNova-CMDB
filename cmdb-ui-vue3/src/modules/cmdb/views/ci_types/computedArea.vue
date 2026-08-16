<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Modal } from 'ant-design-vue'
import { QuestionCircleOutlined } from '@ant-design/icons-vue'
import MonacoCodeEditor from '@/components/MonacoCodeEditor/index.vue'
import AllAttrDrawer from './allAttrDrawer.vue'

const props = withDefaults(
  defineProps<{
    canDefineComputed?: boolean
    showCalcComputed?: boolean
  }>(),
  { canDefineComputed: true, showCalcComputed: false }
)

const emit = defineEmits<{ (e: 'handleCalcComputed'): void }>()

const { t } = useI18n()

const activeKey = ref<'expr' | 'script'>('expr')
const compute_expr = ref('')
const compute_script = ref(t('cmdb.ciType.computedScriptTemplate'))

const allAttrDrawer = ref<InstanceType<typeof AllAttrDrawer>>()

interface ComputeData {
  compute_expr?: string | null
  compute_script?: string | null
}

function getData(): ComputeData {
  if (activeKey.value === 'expr') {
    return { compute_expr: compute_expr.value, compute_script: null }
  }
  return { compute_script: compute_script.value, compute_expr: null }
}

function setData(data: { compute_expr?: string; compute_script?: string }) {
  const { compute_expr: expr, compute_script: script } = data || {}
  compute_expr.value = expr || ''
  compute_script.value = script || t('cmdb.ciType.computedScriptTemplate')
  activeKey.value = script ? 'script' : 'expr'
}

function handleCalcComputed() {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ciType.confirmcomputeForAllCITips'),
    onOk() {
      emit('handleCalcComputed')
    },
  })
}

function onCodeChange(v: string) {
  compute_script.value = v.replace('\t', '    ')
}

function showAllPropDrawer() {
  allAttrDrawer.value?.open()
}

function handleTabsChange(active: string | number) {
  console.log('handleTabsChange', active)
}

defineExpose({ getData, setData })
</script>

<template>
  <a-tabs v-model:active-key="activeKey" size="small" :tab-bar-style="{ borderBottom: 'none' }" @change="handleTabsChange">
    <a-tab-pane key="expr" :disabled="!props.canDefineComputed">
      <template #tab><span style="font-size: 12px">{{ t('cmdb.ciType.expr') }}</span></template>
      <a-textarea
        v-model:value="compute_expr"
        :placeholder="`{{a}}+{{b}}`"
        :rows="2"
        :disabled="!props.canDefineComputed"
      />
    </a-tab-pane>
    <a-tab-pane key="script" :disabled="!props.canDefineComputed">
      <template #tab><span style="font-size: 12px">{{ t('cmdb.ciType.code') }}</span></template>
      <MonacoCodeEditor
        v-model:value="compute_script"
        language="python"
        :height="360"
        storage-key="cmdbComputedAreaMonacoEditorConfig"
        @change="onCodeChange"
      />
    </a-tab-pane>
    <template #tabBarExtraContent>
      <a-button size="small" @click="showAllPropDrawer">{{ t('cmdb.ciType.viewAllAttr') }}</a-button>
      <AllAttrDrawer ref="allAttrDrawer" />

      <template v-if="props.showCalcComputed">
        <a-button style="margin: 0px 5px" type="primary" size="small" @click="handleCalcComputed">
          {{ t('cmdb.ciType.apply') }}
        </a-button>
        <a-tooltip :title="t('cmdb.ciType.computeForAllCITips')">
          <QuestionCircleOutlined />
        </a-tooltip>
      </template>
    </template>
  </a-tabs>
</template>

<style lang="less" scoped></style>
