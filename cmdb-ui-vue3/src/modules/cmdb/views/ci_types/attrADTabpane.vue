<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, nextTick, provide, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { MenuOutlined, EditOutlined, QuestionCircleOutlined } from '@ant-design/icons-vue'
import { uuidv4 } from '@/utils/uuid'
import { cloneDeep } from '../../utils/helper'
import { putCITypeDiscovery, postCITypeDiscovery } from '@/modules/cmdb/api/discovery'
import { DISCOVERY_CATEGORY_TYPE, PRIVATE_CLOUD_NAME } from '@/modules/cmdb/constants'
import { useUserStore } from '@/stores/user'
import Crontab from '@/components/Crontab/index.vue'
import HttpSnmpAD from '@/modules/cmdb/components/httpSnmpAD/index.vue'
import AttrMapTable from '@/modules/cmdb/components/attrMapTable/index.vue'
import CMDBExprDrawer from '@/components/CMDBExprDrawer/index.vue'
import AttrADTest from './attrADTest.vue'
import NodeSetting from './attrAD/nodeSetting/index.vue'
import SNMPConfig from './attrAD/SNMPConfig/index.vue'
import SNMPScanningConfig from './attrAD/SNMPScanningConfig/index.vue'
import CIDRTags from './attrAD/cidrTags/index.vue'
import VcenterForm from './attrAD/privateCloud/vcenterForm.vue'
import PublicCloud from './attrAD/publicCloud/index.vue'
import PortScanConfig from './attrAD/portScanConfig/index.vue'

const TAB_KEY = { CUSTOM: 'custom', CONFIG: 'config' } as const

const props = withDefaults(
  defineProps<{
    adr_id?: number
    adrList?: any[]
    adCITypeList?: any[]
    currentAdt?: Record<string, any>
    currentAdr?: Record<string, any>
    ciTypeAttributes?: any[]
    CITypeId?: number | null
  }>(),
  {
    adr_id: 0,
    adrList: () => [],
    adCITypeList: () => [],
    currentAdt: () => ({}),
    currentAdr: () => ({}),
    ciTypeAttributes: () => [],
    CITypeId: null,
  }
)

const emit = defineEmits<{
  (e: 'openEditDrawer', data: any, type: string, adType: string): void
  (e: 'handleSave', id: string | number): void
}>()

const { t, locale } = useI18n()
const userStore = useUserStore()

const tableData = ref<any[]>([])
const form = ref({
  agent_id: '',
  auto_accept: false,
  query_expr: '',
  enabled: true,
})
const publicCloudForm = ref<Record<string, any>>({
  key: '',
  secret: '',
  _reference: '',
  tabActive: TAB_KEY.CUSTOM,
})
const privateCloudForm = ref<Record<string, any>>({
  host: '',
  account: '',
  password: '',
  vcenterName: '',
  _reference: '',
  tabActive: TAB_KEY.CUSTOM,
})
const portScanConfigForm = ref<Record<string, any>>({
  cidr: '',
  ports: '',
  enable_cidr: '',
})
const SNMPScanningConfigForm = ref<Record<string, any>>({
  version: '2c',
  community: 'public',
  timeout: 5,
  retries: 3,
  initial_node: '',
  recursive_scan: true,
  max_depth: 5,
  cidr: [],
})

const cron = ref('')
const cronVisible = ref(false)
const agentType = ref('agent_id')
const uniqueKey = ref('')
const isPrivateCloud = ref(false)
const privateCloudName = ref('')
const isClient = ref(false)

const attrMapTableRef = ref<InstanceType<typeof AttrMapTable>>()
const httpSnmpAdRef = ref<InstanceType<typeof HttpSnmpAD>>()
const cmdbDrawerRef = ref<InstanceType<typeof CMDBExprDrawer>>()
const nodeSettingRef = ref<InstanceType<typeof NodeSetting>>()
const httpFormRef = ref<InstanceType<typeof VcenterForm> | InstanceType<typeof PublicCloud>>()

const windowHeight = computed(() => window.innerHeight)

const adrType = computed(() => props.currentAdr?.type || '')
const adrName = computed(() => props.currentAdr?.option?.en || props.currentAdr?.name || '')
const adrIsInner = computed(() => props.currentAdr?.is_inner || '')

const agentTypeRadioList = computed(() => {
  const radios = [
    { value: 'agent_id', label: t('cmdb.ciType.specifyNodes') },
    { value: 'query_expr', label: t('cmdb.ciType.selectFromCMDBTips') },
  ]

  const permissions: string[] = (userStore.roles?.permissions ?? []) as unknown as string[]
  if (
    (permissions.includes('cmdb_admin') || permissions.includes('admin')) &&
    adrType.value === DISCOVERY_CATEGORY_TYPE.AGENT
  ) {
    radios.unshift({ value: 'all', label: t('cmdb.ciType.allNodes') })
  }

  // NOTE: legacy code compared against a non-existent `AGENTv` key (always
  // undefined), so the master-node option is always appended.
  radios.unshift({ value: 'master', label: t('cmdb.ciType.masterNode') })

  return radios
})

const labelCol = computed(() => {
  const isEn = locale.value === 'en'
  return {
    xl: { span: isEn ? 4 : 3 },
    lg: { span: isEn ? 5 : 4 },
    sm: { span: isEn ? 6 : 5 },
  }
})

function pick(obj: Record<string, any>, keys: string[]) {
  const result: Record<string, any> = {}
  keys.forEach((key) => {
    result[key] = obj[key]
  })
  return result
}

function omit(obj: Record<string, any>, keys: string[]) {
  const result = { ...obj }
  keys.forEach((key) => {
    delete result[key]
  })
  return result
}

function omitBy(obj: Record<string, any>, predicate: (value: any) => boolean) {
  const result: Record<string, any> = {}
  Object.keys(obj).forEach((key) => {
    if (!predicate(obj[key])) {
      result[key] = obj[key]
    }
  })
  return result
}

function isEmpty(value: any) {
  return value === '' || value === null || value === undefined
}

function init() {
  const findAdr = props.adrList.find((item) => Number(item.id) === Number(props.adr_id))
  const findADT = props.adCITypeList.find((item) => Number(item.id) === Number(props.currentAdt.id))
  uniqueKey.value = findAdr?.unique_key ?? ''
  isClient.value = findADT?.isClient ?? false

  if (adrType.value === DISCOVERY_CATEGORY_TYPE.HTTP) {
    const {
      key = '',
      secret = '',
      host = '',
      account = '',
      password = '',
      vcenterName = '',
      _reference = '',
    } = findADT?.extra_option ?? {}

    if (findAdr?.option?.category === 'private_cloud') {
      isPrivateCloud.value = true
      privateCloudName.value = findAdr?.option?.en || ''

      if (privateCloudName.value === PRIVATE_CLOUD_NAME.VCenter) {
        privateCloudForm.value = {
          host,
          account,
          password,
          vcenterName,
          _reference,
          tabActive: _reference ? TAB_KEY.CONFIG : TAB_KEY.CUSTOM,
        }
      }
    } else {
      isPrivateCloud.value = false
      publicCloudForm.value = {
        key,
        secret,
        _reference,
        tabActive: _reference ? TAB_KEY.CONFIG : TAB_KEY.CUSTOM,
      }
    }

    nextTick(() => {
      httpFormRef.value?.init(props.adr_id)
    })
  }

  if (adrType.value === DISCOVERY_CATEGORY_TYPE.COMPONENT) {
    const { cidr = '', ports = '', enable_cidr = '' } = findADT?.extra_option ?? {}
    portScanConfigForm.value = {
      cidr,
      ports,
      enable_cidr,
    }
  }

  if (adrType.value === DISCOVERY_CATEGORY_TYPE.SNMP) {
    const extraOption = findADT?.extra_option ?? {}
    const { nodes, cidr = [] } = extraOption

    const initializeNodes = nodes?.length
      ? nodes
      : [
          {
            id: uuidv4(),
            ip: '',
            community: 'public',
            version: '',
          },
        ]
    nextTick(() => {
      nodeSettingRef.value?.initNodesFunc(initializeNodes)
    })

    let cidrList: any[] = []
    if (Array.isArray(cidr) && cidr?.length) {
      cidrList = cidr.map((v: any) => {
        return {
          id: uuidv4(),
          value: v?.value ? v.value : v,
        }
      })
    }
    SNMPScanningConfigForm.value = {
      version: extraOption?.version ?? '2c',
      community: extraOption?.community ?? 'public',
      timeout: extraOption?.timeout ?? 5,
      retries: extraOption?.retries ?? 3,
      initial_node: extraOption?.initial_node ?? '',
      recursive_scan: extraOption?.recursive_scan ?? true,
      max_depth: extraOption?.max_depth ?? 5,
      cidr: cidrList,
    }
  }

  if (adrType.value === DISCOVERY_CATEGORY_TYPE.AGENT) {
    tableData.value = (findAdr?.attributes || []).map((item: any) => {
      if (findADT.attributes) {
        return {
          ...item,
          attr: findADT.attributes[`${item.name}`],
        }
      } else {
        const found = props.ciTypeAttributes.find((ele: any) => ele.name === item.name)
        if (found) {
          return {
            ...item,
            attr: found.name,
          }
        }
        return item
      }
    })
  }

  form.value = {
    auto_accept: findADT?.auto_accept || false,
    agent_id: findADT?.agent_id && findADT?.agent_id !== '0x0000' ? findADT.agent_id : '',
    query_expr: findADT.query_expr || '',
    enabled: findADT?.enabled ?? true,
  }

  const allMachineIndex = agentTypeRadioList.value.findIndex((item) => item.value === 'all')

  if (findADT.query_expr) {
    agentType.value = 'query_expr'
  } else if (findADT.agent_id) {
    agentType.value = findADT.agent_id === '0x0000' ? 'master' : 'agent_id'
  } else if (findADT.agent_id === '' && allMachineIndex !== -1) {
    agentType.value = 'all'
  } else {
    agentType.value = agentTypeRadioList.value[0].value
  }

  cron.value = findADT?.cron || ''
}

function crontabFill(value: string) {
  cron.value = value
}

function hideCron() {
  cronVisible.value = false
}

function changeEnabled() {
  if (!isClient.value) {
    putCITypeDiscovery(props.currentAdt.id, {
      enabled: !form.value.enabled,
    }).then((res) => {
      form.value.enabled = !form.value.enabled
      message.success(t('saveSuccess'))
      emit('handleSave', res.id)
    })
  }
}

function handleOpenCmdb() {
  cmdbDrawerRef.value?.open()
}

function copySuccess(text: string) {
  form.value = {
    ...form.value,
    query_expr: `${text}`,
  }
}

function validateHTTPForm() {
  let isError = false
  let data: Record<string, any> = {}

  const formData = isPrivateCloud.value ? privateCloudForm.value : publicCloudForm.value
  if (formData.tabActive === TAB_KEY.CONFIG) {
    if (!formData._reference) {
      isError = true
      message.error(t('cmdb.ad.configErrTip'))
    }

    data._reference = formData._reference
    if (privateCloudName.value === PRIVATE_CLOUD_NAME.VCenter) {
      data.vcenterName = formData.vcenterName
    }

    return { isError, data }
  }

  if (isPrivateCloud.value) {
    if (privateCloudName.value === PRIVATE_CLOUD_NAME.VCenter) {
      data = pick(privateCloudForm.value, ['host', 'account', 'password', 'vcenterName'])
      const vcenterErrors: Record<string, string> = {
        host: `${t('placeholder1')} ${t('cmdb.ciType.host')}`,
        account: `${t('placeholder1')} ${t('cmdb.ciType.account')}`,
        password: `${t('placeholder1')} ${t('cmdb.ciType.password')}`,
      }
      const findError = Object.keys(privateCloudForm.value).find(
        (key) => !privateCloudForm.value[key] && vcenterErrors[key]
      )
      if (findError) {
        isError = true
        message.error(t(vcenterErrors[findError] as string))
      }
    }
  } else {
    data = pick(publicCloudForm.value, ['key', 'secret'])
    const publicCloudErrors: Record<string, string> = {
      key: `${t('placeholder1')} key`,
      secret: `${t('placeholder1')} secret`,
    }
    const findError = Object.keys(publicCloudForm.value).find(
      (key) => !publicCloudForm.value[key] && publicCloudErrors[key]
    )
    if (findError) {
      isError = true
      message.error(t(publicCloudErrors[findError] as string))
    }
  }

  return { isError, data }
}

function handleOldExtraOption(option: Record<string, any>) {
  let extraOption = cloneDeep(option)

  if (extraOption?.insecure) {
    Reflect.deleteProperty(extraOption, 'insecure')
  }

  const formData = isPrivateCloud.value ? privateCloudForm.value : publicCloudForm.value
  switch (formData.tabActive) {
    case TAB_KEY.CUSTOM:
      Reflect.deleteProperty(extraOption, '_reference')
      break
    case TAB_KEY.CONFIG:
      extraOption = omit(extraOption, ['host', 'account', 'password', 'key', 'secret'])
      break
    default:
      break
  }

  return extraOption
}

function handleSave() {
  const { currentAdt } = props
  let params: any

  if (adrType.value === DISCOVERY_CATEGORY_TYPE.HTTP) {
    const { isError, data: cloudOption } = validateHTTPForm()
    if (isError) {
      return
    }
    params = {
      extra_option: {
        ...cloudOption,
        category: props.currentAdt?.extra_option?.category,
      },
    }
  }

  if (adrType.value === DISCOVERY_CATEGORY_TYPE.COMPONENT) {
    const portScan = omitBy(portScanConfigForm.value, isEmpty) || {}
    params = {
      extra_option: {
        ...portScan,
      },
    }
  }

  if (adrType.value === DISCOVERY_CATEGORY_TYPE.SNMP) {
    const { cidr, ...otherConfigForm } = SNMPScanningConfigForm.value
    const nodes = nodeSettingRef.value?.getNodeValue() ?? []

    params = {
      extra_option: {
        ...otherConfigForm,
        nodes,
        cidr: cidr?.map((item: any) => item.value) || [],
      },
    }

    if (!otherConfigForm?.recursive_scan && nodes?.some((item) => !item?.ip)) {
      message.error(t('cmdb.ciType.recursiveTip'))
      return
    }
  }

  if (adrType.value === DISCOVERY_CATEGORY_TYPE.AGENT) {
    const table = attrMapTableRef.value
    const { fullData: agentTableData } = table?.getTableData() ?? { fullData: [] }
    const attributes: Record<string, any> = {}
    agentTableData.forEach((td: any) => {
      if (td.attr) {
        attributes[`${td.name}`] = td.attr
      }
    })
    params = {
      ...params,
      attributes,
    }
  } else {
    const httpSnmpTableData = httpSnmpAdRef.value?.getTableData() ?? []
    const attributes: Record<string, any> = {}
    httpSnmpTableData.forEach((td: any) => {
      if (td.attr) {
        attributes[`${td.name}`] = td.attr
      }
    })
    params = {
      ...params,
      attributes,
    }
  }

  params = {
    ...params,
    ...form.value,
    adr_id: currentAdt.adr_id,
    cron: cron.value,
  }

  if (agentType.value === 'agent_id' || agentType.value === 'all') {
    params.query_expr = ''
    if (agentType.value === 'agent_id' && !params.agent_id) {
      message.error(t('cmdb.ciType.specifyNodesTips'))
      return
    }
  }

  if (agentType.value === 'query_expr' || agentType.value === 'all') {
    params.agent_id = ''
    if (agentType.value === 'query_expr' && !params.query_expr) {
      message.error(t('cmdb.ciType.selectFromCMDBTips'))
      return
    }
  }

  if (agentType.value === 'master') {
    params.agent_id = '0x0000'
  }

  if (!cron.value) {
    message.error(t('cmdb.ciType.cronRequiredTip'))
    return
  }

  if (currentAdt?.extra_option) {
    params.extra_option = {
      ...(currentAdt?.extra_option || {}),
      ...(params?.extra_option || {}),
    }
  }

  if (params.extra_option) {
    params.extra_option = handleOldExtraOption(params.extra_option)
  }

  if (currentAdt?.isClient) {
    postCITypeDiscovery(props.CITypeId as number, params).then((res) => {
      message.success(t('saveSuccess'))
      emit('handleSave', res.id)
    })
  } else {
    putCITypeDiscovery(currentAdt.id, params).then((res) => {
      message.success(t('saveSuccess'))
      emit('handleSave', res.id)
    })
  }
}

provide('provide_labelCol', () => labelCol.value)

defineExpose({ init })
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order, vue/v-on-event-hyphenation -->
  <div class="attr-ad-tab-pane" :style="{ height: `${windowHeight - 254}px` }">
    <a
      v-if="!adrIsInner"
      :style="{ position: 'absolute', right: 0, top: 0 }"
      @click="() => { emit('openEditDrawer', currentAdr, 'edit', 'plugin') }"
    >
      <a-space>
        <EditOutlined />
        <span>{{ t('edit') }}</span>
      </a-space>
    </a>
    <div class="attr-ad-header attr-ad-header_between">
      <span>
        {{ t('cmdb.ciType.attributeMap') }}
        <a-tooltip :title="t('cmdb.ciType.attributeMapHint')">
          <QuestionCircleOutlined style="margin-left: 4px; color: #999; font-size: 14px; cursor: help" />
        </a-tooltip>
      </span>
      <div class="attr-ad-open">
        <span class="attr-ad-open-label">{{ t('cmdb.ciType.enable') }}</span>
        <a-switch v-model:checked="form.enabled" v-if="isClient" />
        <a-popconfirm
          v-else
          :title="t('cmdb.ciType.enableTip')"
          :ok-text="t('confirm')"
          :cancel-text="t('cancel')"
          @confirm="changeEnabled"
        >
          <a-switch :checked="form.enabled" />
        </a-popconfirm>
      </div>
    </div>
    <div class="attr-ad-attributemap-main">
      <AttrMapTable
        v-if="adrType === DISCOVERY_CATEGORY_TYPE.AGENT"
        ref="attrMapTableRef"
        :ruleType="adrType"
        :tableData="tableData"
        :ciTypeAttributes="ciTypeAttributes"
        :uniqueKey="uniqueKey"
      />
      <HttpSnmpAD
        v-else
        :isEdit="true"
        ref="httpSnmpAdRef"
        :ruleType="adrType"
        :ruleName="adrName"
        :ciTypeAttributes="ciTypeAttributes"
        :adCITypeList="adCITypeList"
        :currentTab="adr_id"
        :uniqueKey="uniqueKey"
        :currentAdt="currentAdt"
        :style="{ marginBottom: '20px' }"
      />
    </div>
    <template v-if="adrType === DISCOVERY_CATEGORY_TYPE.SNMP">
      <div class="attr-ad-header">{{ t('cmdb.ciType.scanningParameter') }}</div>
      <div class="attr-ad-form attr-ad-snmp-form">
        <div class="attr-ad-snmp-form-title">{{ t('cmdb.ciType.SNMPConfiguration') }}</div>
        <NodeSetting ref="nodeSettingRef" />
        <SNMPConfig :value="SNMPScanningConfigForm" @change="(v) => (SNMPScanningConfigForm = v)" />

        <div class="attr-ad-snmp-form-title">{{ t('cmdb.ciType.scanningConfiguration') }}</div>
        <SNMPScanningConfig :value="SNMPScanningConfigForm" @change="(v) => (SNMPScanningConfigForm = v)" />
        <CIDRTags :value="SNMPScanningConfigForm.cidr" @change="(v) => (SNMPScanningConfigForm.cidr = v)" />
      </div>
    </template>

    <div class="attr-ad-header">{{ t('cmdb.ciType.adExecConfig') }}</div>
    <a-form :model="form" :label-col="labelCol" label-align="right" :wrapper-col="{ span: 14 }" class="attr-ad-form">
      <a-form-item :required="true" :label="t('cmdb.ciType.adExecTarget')">
        <div class="custom-radio">
          <a-radio-group v-model:value="agentType">
            <a-radio v-for="radio in agentTypeRadioList" :key="radio.value" :value="radio.value">
              {{ radio.label }}
            </a-radio>
          </a-radio-group>
          <a-input
            :style="{ width: '300px' }"
            :placeholder="t('cmdb.ciType.oneagentIdTips')"
            v-show="agentType === 'agent_id'"
            v-model:value="form.agent_id"
          />
          <a-input
            :style="{ width: '300px' }"
            :placeholder="t('cmdb.ciType.selectFromCMDBTips')"
            v-show="agentType === 'query_expr'"
            v-model:value="form.query_expr"
          >
            <template #suffix><a @click="handleOpenCmdb"><MenuOutlined /></a></template>
          </a-input>
        </div>
        <div class="ant-form-explain" v-if="agentType === 'all'">{{ t('cmdb.ciType.allNodesTip') }}</div>
        <div class="ant-form-explain" v-if="agentType === 'query_expr'">{{ t('cmdb.ciType.queryExprTip') }}</div>
        <div class="ant-form-explain" v-if="agentType === 'master'">{{ t('cmdb.ciType.masterNodeTip') }}</div>
      </a-form-item>
      <a-form-item :label-col="labelCol" :label="t('cmdb.ciType.adAutoInLib')" :extra="t('cmdb.ciType.adAutoInLibTip')">
        <a-switch v-model:checked="form.auto_accept" />
        <div class="ant-form-explain">{{ t('cmdb.ciType.adAutoInLibTip') }}</div>
      </a-form-item>
      <a-form-item :label-col="labelCol" :wrapper-col="{ span: 6 }" :label="t('cmdb.ciType.adInterval')" :required="true">
        <a-popover v-model:open="cronVisible" trigger="click">
          <template #content>
            <Crontab
              v-if="adrType"
              :hide-component="['second', 'year']"
              :expression="cron"
              :has-footer="true"
              @fill="crontabFill"
              @hide="hideCron"
            />
          </template>
          <a-input v-model:value="cron" :placeholder="t('cmdb.ciType.cronTips')" />
        </a-popover>
      </a-form-item>
    </a-form>

    <template v-if="adrType === DISCOVERY_CATEGORY_TYPE.HTTP">
      <template v-if="isPrivateCloud">
        <template v-if="privateCloudName === PRIVATE_CLOUD_NAME.VCenter">
          <div class="attr-ad-header">{{ t('cmdb.ciType.privateCloud') }}</div>
          <VcenterForm ref="httpFormRef" :value="privateCloudForm" @change="(v) => (privateCloudForm = v)" />
        </template>
      </template>
      <template v-else>
        <div class="attr-ad-header">{{ t('cmdb.ciType.cloudAccessKey') }}</div>
        <PublicCloud ref="httpFormRef" :value="publicCloudForm" @change="(v) => (publicCloudForm = v)" />
      </template>
    </template>

    <template v-if="adrType === DISCOVERY_CATEGORY_TYPE.COMPONENT">
      <div class="attr-ad-header">{{ t('cmdb.ciType.portScanConfig') }}</div>
      <PortScanConfig :value="portScanConfigForm" @change="(v) => (portScanConfigForm = v)" />
    </template>

    <AttrADTest :adtId="currentAdt.id" />

    <div class="attr-ad-footer">
      <a-button type="primary" @click="handleSave">{{ t('save') }}</a-button>
    </div>
    <CMDBExprDrawer ref="cmdbDrawerRef" @copy-success="copySuccess" />
  </div>
</template>

<style lang="less" scoped>
.attr-ad-tab-pane {
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;

  .attr-ad-header_between {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 20px;
  }

  .attr-ad-open {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding: 0px 20px;

    &-label {
      font-size: 14px;
      font-weight: 600;
      margin-right: 6px;
    }
  }

  .attr-ad-attributemap-main {
    margin-left: 17px;
  }

  .attr-ad-form {
    :deep(.ant-form-item-label) {
      margin-left: 17px;
    }
  }

  .public-cloud-info {
    color: @text-color_3;
    font-size: 12px;
    font-weight: 400;
    margin-left: 17px;
    margin-bottom: 20px;
  }
}

.attr-ad-snmp-form {
  &-title {
    font-size: 16px;
    color: #000000;
    margin-bottom: 12px;
  }

  :deep(.ant-input-number) {
    width: 100%;
  }

  :deep(.ant-form-extra) {
    font-size: 12px;
  }
}

.custom-radio {
  .ant-input {
    display: block;
    margin-top: 4px;
  }
}
</style>
