<script setup lang="ts">
import { computed, inject, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { CloseOutlined, DeleteOutlined, EditOutlined, PlusOutlined, SaveOutlined } from '@ant-design/icons-vue'
import { postDiscovery, putDiscovery } from '@/modules/cmdb/api/discovery'
import { DISCOVERY_CATEGORY_TYPE } from '@/modules/cmdb/constants'
import CustomDrawer from '@/components/CustomDrawer/index.vue'
import CustomIconSelect from '@/components/CustomIconSelect/index.vue'
import MonacoCodeEditor from '@/components/MonacoCodeEditor/index.vue'
import HttpSnmpAD from '@/modules/cmdb/components/httpSnmpAD/index.vue'
import AgentTable from './agentTable.vue'

const props = withDefaults(
  defineProps<{
    isDiscoveryPage?: boolean
  }>(),
  {
    isDiscoveryPage: false,
  }
)

const emit = defineEmits<{
  (e: 'updateNotInner', res: any): void
}>()

const { t } = useI18n()

const getDiscovery = inject<() => void>('getDiscovery', () => {})

const default_plugin_script = t('cmdb.ad.pluginScript')
const typeList = ['String', 'Integer', 'Float', 'Date', 'DateTime', 'Time', 'JSON']

const visible = ref(false)
const ruleData = ref<Record<string, any>>({})
const type = ref('add')
const adType = ref('')
const form = ref<{ name: string; is_plugin: boolean }>({ name: '', is_plugin: true })
const rules = ref<Record<string, any>>({})
const customIcon = ref<Record<string, any>>({ name: '', color: '' })
const tableData = ref<any[]>([])
const plugin_script = ref('')
const loading = ref(false)

const autoDiscoveryFormRef = ref()
const xTableRef = ref<any>()

const title = computed(() => {
  if (
    [DISCOVERY_CATEGORY_TYPE.HTTP, DISCOVERY_CATEGORY_TYPE.SNMP, DISCOVERY_CATEGORY_TYPE.AGENT, DISCOVERY_CATEGORY_TYPE.PRIVATE_CLOUD, DISCOVERY_CATEGORY_TYPE.COMPONENT].includes(
      adType.value
    )
  ) {
    return ruleData.value.name
  }
  if (type.value === 'edit') {
    return t('edit') + `：${ruleData.value.name}`
  }
  return t('new')
})

const ruleName = computed(() => ruleData.value?.option?.en || ruleData.value?.name || '')

function open(data: any, openType: string, autoType: string) {
  visible.value = true
  type.value = openType
  ruleData.value = data
  adType.value = autoType
  form.value = { name: '', is_plugin: true }
  if (adType.value === DISCOVERY_CATEGORY_TYPE.HTTP || adType.value === DISCOVERY_CATEGORY_TYPE.SNMP) {
    return
  }
  nextTick(() => {
    if ([DISCOVERY_CATEGORY_TYPE.HTTP, DISCOVERY_CATEGORY_TYPE.SNMP, DISCOVERY_CATEGORY_TYPE.PRIVATE_CLOUD].includes(adType.value)) {
      tableData.value = data?.attributes ?? []
      return
    }

    if (type.value === 'edit') {
      form.value = {
        name: data.name,
        is_plugin: data.is_plugin,
      }
      customIcon.value = data?.option?.icon ?? { name: 'caise-chajian', color: '' }
      tableData.value = data?.attributes ?? []
      plugin_script.value = data?.plugin_script ?? default_plugin_script
    }
    if (type.value === 'add') {
      customIcon.value = { name: 'caise-chajian', color: '' }
      plugin_script.value = default_plugin_script
    }
  })
}

function handleClose() {
  tableData.value = []
  customIcon.value = { name: '', color: '' }
  form.value = { name: '', is_plugin: false }
  if (adType.value === DISCOVERY_CATEGORY_TYPE.PLUGIN) {
    autoDiscoveryFormRef.value?.clearValidate()
  }
  visible.value = false
}

async function insertEvent(row: number) {
  const $table = xTableRef.value
  const record = {}
  const { row: newRow } = await $table.insertAt(record, row)
  await $table.setActiveRow(newRow)
}

function editRowEvent(row: any) {
  const $table = xTableRef.value
  $table.setActiveRow(row)
}

function saveRowEvent() {
  const $table = xTableRef.value
  $table.clearActived().then(() => {
    loading.value = true
    setTimeout(() => {
      loading.value = false
    }, 300)
  })
}

function cancelRowEvent(row: any) {
  const $table = xTableRef.value
  $table.clearActived().then(() => {
    $table.revertData(row)
  })
}

function deleteRowEvent(row: any) {
  const $table = xTableRef.value
  $table.remove(row)
}

async function handleSubmit(isUpdateAttr = false) {
  const $table = xTableRef.value
  const { fullData: _tableData } = $table.getTableData()
  const submitType = adType.value === DISCOVERY_CATEGORY_TYPE.PLUGIN ? DISCOVERY_CATEGORY_TYPE.AGENT : adType.value
  const params: Record<string, any> = {
    ...form.value,
    type: submitType,
    is_inner: !form.value.is_plugin,
    option: { icon: customIcon.value },
    attributes: form.value.is_plugin
      ? undefined
      : _tableData.map(({ name, alias, desc, type: attrType }: any) => ({ name, alias, desc, type: attrType })),
    plugin_script: form.value.is_plugin ? plugin_script.value : undefined,
  }
  let res: any
  if (type.value === 'add') {
    res = await postDiscovery(params)
  } else {
    res = await putDiscovery(ruleData.value.id, params)
  }
  if (isUpdateAttr) {
    tableData.value = res.attributes
    type.value = 'edit'
    ruleData.value = res
    message.success(t('updateSuccess'))
    if (props.isDiscoveryPage) {
      getDiscovery()
    }
    return
  }
  handleClose()

  if (props.isDiscoveryPage) {
    message.success(t('saveSuccess'))
    getDiscovery()
  } else {
    emit('updateNotInner', res)
  }
}

defineExpose({ open })
</script>

<template>
  <CustomDrawer width="980px" :title="title" :open="visible" @close="handleClose">
    <AgentTable v-if="adType === DISCOVERY_CATEGORY_TYPE.AGENT" :table-data="tableData" />
    <template v-else-if="adType === DISCOVERY_CATEGORY_TYPE.PLUGIN">
      <a-form
        ref="autoDiscoveryFormRef"
        :model="form"
        :rules="rules"
        :label-col="{ span: 2 }"
        :wrapper-col="{ span: 20 }"
      >
        <a-divider :style="{ margin: '5px 0' }">{{ t('cmdb.ciType.basicConfig') }}</a-divider>
        <a-form-item :label="t('name')" name="name">
          <a-input v-model:value="form.name" />
        </a-form-item>
        <a-form-item :label="t('icon')">
          <CustomIconSelect :value="customIcon" :style="{ marginTop: '6px' }" @change="(v) => (customIcon = v)" />
        </a-form-item>
        <a-form-item :label="t('cmdb.ad.mode')" name="is_plugin">
          <a-radio-group v-model:value="form.is_plugin" :disabled="true">
            <a-radio :value="false">{{ t('cmdb.custom_dashboard.default') }}</a-radio>
            <a-radio :value="true">plugin</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
      <a-divider :style="{ margin: '5px 0' }">{{ t('cmdb.ad.collectSettings') }}</a-divider>
      <MonacoCodeEditor
        v-if="form.is_plugin"
        v-model:value="plugin_script"
        language="python"
        :height="380"
        storage-key="cmdbAutoDiscoveryPluginEditor"
      />
      <div style="margin:10px 0;text-align:right;">
        <a-button v-show="form.is_plugin" size="small" type="primary" ghost @click="handleSubmit(true)">
          {{ t('cmdb.ad.updateFields') }}
        </a-button>
      </div>
      <a-button
        v-show="!form.is_plugin"
        size="small"
        type="primary"
        ghost
        :style="{ marginBottom: '10px' }"
        @click="insertEvent(-1)"
      >
        <template #icon><PlusOutlined /></template>
        {{ t('new') }}
      </a-button>
      <vxe-table
        ref="xTableRef"
        size="mini"
        stripe
        class="ops-stripe-table"
        show-overflow
        keep-source
        max-height="400"
        :data="tableData"
        :edit-config="{ trigger: 'manual', mode: 'row' }"
      >
        <vxe-column field="name" :title="t('name')" :edit-render="{ autofocus: '.vxe-input--inner' }">
          <template #edit="{ row }">
            <vxe-input v-model="row.name" type="text"></vxe-input>
          </template>
        </vxe-column>
        <vxe-column field="type" :title="t('type')" :edit-render="{}">
          <template #edit="{ row }">
            <vxe-select v-model="row.type" transfer>
              <vxe-option v-for="item in typeList" :key="item" :value="item" :label="item"></vxe-option>
            </vxe-select>
          </template>
        </vxe-column>
        <vxe-column field="desc" :title="t('desc')" :edit-render="{ autofocus: '.vxe-input--inner' }">
          <template #edit="{ row }">
            <vxe-input v-model="row.desc" type="text"></vxe-input>
          </template>
        </vxe-column>
        <vxe-column v-if="!form.is_plugin" :title="t('operation')" width="60">
          <template #default="{ row }">
            <a-space v-if="xTableRef?.isActiveByRow(row)">
              <a @click="saveRowEvent()"><SaveOutlined /></a>
              <a @click="cancelRowEvent(row)"><CloseOutlined /></a>
            </a-space>
            <a-space v-else>
              <a @click="editRowEvent(row)"><EditOutlined /></a>
              <a :style="{ color: 'red' }" @click="deleteRowEvent(row)"><DeleteOutlined /></a>
            </a-space>
          </template>
        </vxe-column>
      </vxe-table>

      <div class="custom-drawer-bottom-action">
        <a-button @click="handleClose">{{ t('cancel') }}</a-button>
        <a-button type="primary" @click="handleSubmit(false)">{{ t('save') }}</a-button>
      </div>
    </template>
    <template v-else>
      <HttpSnmpAD :rule-type="adType" :rule-name="ruleName" />
    </template>
  </CustomDrawer>
</template>

<style></style>
