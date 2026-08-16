<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, inject, nextTick, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import {
  MailOutlined,
  WechatOutlined,
  DingdingOutlined,
  SendOutlined,
  RobotOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons-vue'
import { addTrigger, updateTrigger, deleteTrigger, testTrigger } from '@/modules/cmdb/api/CIType'
import FilterComp from '@/components/CMDBFilterComp/index.vue'
import EmployeeTreeSelect from '@/views/setting/components/employeeTreeSelect.vue'
import Webhook from '@/modules/cmdb/components/webhook'
import NoticeContent from '@/modules/cmdb/components/noticeContent/index.vue'
import { getNoticeByEmployeeIds } from '@/api/employee'
import { getNoticeConfigAppBot } from '@/api/noticeSetting'
import { cloneDeep } from '../../utils/helper'
import CustomDrawer from '@/components/CustomDrawer/index.vue'

const props = withDefaults(defineProps<{ CITypeId?: number | null }>(), { CITypeId: null })

const { t } = useI18n()

const defaultForm = { name: '', description: '', enable: true, action: '0', attr_ids: [] as number[] }
const defaultDateForm = { attr_id: undefined as number | undefined, before_days: 0, notify_at: '08:00' }
const defaultNotify = {
  employee_ids: undefined as string[] | undefined,
  custom_email: '',
  subject: '',
  body: '',
  method: ['wechatApp'] as string[],
}

const visible = ref(false)
const category = ref<1 | 2>(1)
const form = ref(cloneDeep(defaultForm))
const rules = {
  name: [{ required: true, message: t('cmdb.ciType.nameInputTips') }],
}
const dateForm = ref(cloneDeep(defaultDateForm))
const dateFormRules = {
  attr_id: [{ required: true, message: t('cmdb.ciType.selectAttributes') }],
}
const notifies = ref<any>(cloneDeep(defaultNotify))
const notifiesRules: Record<string, unknown> = {}

const triggerId = ref<number | null>(null)
const title = ref(t('cmdb.ciType.newTrigger'))
const attrList = ref<any[]>([])
const filterExp = ref('')
const triggerAction = ref<'1' | '2' | '3'>('1')
const searchValue = ref('')
const dags = ref<any[]>([])
const isShow = ref(false)
const dagId = ref<number | null>(null)
const showCustomEmail = ref(false)
const appBot = ref<any[]>([])
const selectedBot = ref<string[] | undefined>(undefined)

const formRef = ref()
const dateFormRef = ref()
const filterCompRef = ref()
const noticeContentRef = ref<InstanceType<typeof NoticeContent>>()
const webhookRef = ref<InstanceType<typeof Webhook>>()

const refresh = inject<(() => void) | null>('refresh', null)

const canAddTriggerAttr = computed(() => attrList.value.filter((attr) => attr.value_type === '3' || attr.value_type === '4'))

const filterList = computed(() => {
  if (searchValue.value) {
    return dags.value.filter((item) => item.label.toLowerCase().includes(searchValue.value.toLowerCase()))
  }
  return dags.value
})

const tips = computed(() => t('cmdb.ciType.refAttributeTips'))
const webhookTips = computed(() => t('cmdb.ciType.webhookRefAttributeTips'))

function botNormalizer(node: any) {
  return {
    id: node.name,
    label: node.label || node.name,
    children: node.bot,
  }
}

async function getNoticeConfigAppBotData() {
  await getNoticeConfigAppBot().then((res) => {
    appBot.value = res
  })
}

function createFromTriggerTable(attrs: any[]) {
  visible.value = true
  getNoticeConfigAppBotData()
  attrList.value = attrs
  triggerId.value = null
  title.value = t('cmdb.ciType.newTrigger')
  form.value = cloneDeep(defaultForm)
  dateForm.value = cloneDeep(defaultDateForm)
  notifies.value = cloneDeep(defaultNotify)
  category.value = 1
  triggerAction.value = '1'
  filterExp.value = ''
  nextTick(() => {
    filterCompRef.value?.visibleChange(true, false)
    setTimeout(() => {
      noticeContentRef.value?.setContent('')
    }, 100)
  })
}

async function open(property: any, attrs: any[]) {
  visible.value = true
  await getNoticeConfigAppBotData()
  attrList.value = attrs
  if (property.has_trigger) {
    triggerId.value = property.trigger.id
    title.value = t('cmdb.ciType.editTriggerTitle', { name: `${property.alias || property.name}` })
    const { name, description, enable, action = '0', attr_ids, filter = '' } = property?.trigger?.option ?? {}
    filterExp.value = filter
    nextTick(() => {
      filterCompRef.value?.visibleChange(true, false)
    })
    form.value = { name, description, enable, action, attr_ids }
    const { attr_id } = property?.trigger ?? {}
    if (attr_id) {
      category.value = 2
      const { before_days, notify_at } = property?.trigger?.option?.notifies ?? {}
      dateForm.value = {
        attr_id,
        before_days,
        notify_at,
      }
    } else {
      category.value = 1
    }
    const { notifies: notifyOpt = undefined, webhooks = undefined, dag_id = undefined } =
      property?.trigger?.option ?? {}
    if (webhooks) {
      triggerAction.value = '2'
      nextTick(() => {
        webhookRef.value?.setParams(webhooks)
      })
    } else if (dag_id) {
      triggerAction.value = '3'
      dagId.value = dag_id
      const findDag = dags.value.find((item) => item.id === dag_id)
      searchValue.value = findDag?.label
    } else if (notifyOpt) {
      triggerAction.value = '1'
      const { tos = [], subject = '', body_html = '', method = ['wechatApp'] } =
        property?.trigger?.option?.notifies ?? {}
      const employee_ids = property?.trigger?.option?.employee_ids ?? undefined
      const custom_email =
        tos
          .filter((t: any) => !t.employee_id && t.email)
          .map((t: any) => t.email)
          .join(';') ?? ''

      if (custom_email) {
        showCustomEmail.value = true
      }
      if (body_html) {
        setTimeout(() => {
          noticeContentRef.value?.setContent(body_html)
        }, 100)
      }
      const methodFiltered = method.filter((item: string) =>
        ['email', 'wechatApp', 'dingdingApp', 'feishuApp'].includes(item)
      )
      const flatAppBot: string[] = []
      appBot.value.forEach((item) => {
        flatAppBot.push(...item.bot.map((b: any) => b.name))
      })
      const selectedBotList = method.filter(
        (item: string) =>
          !['email', 'wechatApp', 'dingdingApp', 'feishuApp'].includes(item) && flatAppBot.includes(item)
      )
      selectedBot.value = selectedBotList
      notifies.value = { employee_ids, custom_email, subject, method: methodFiltered }
    }
  } else {
    title.value = t('cmdb.ciType.newTriggerTitle', { name: `${property.alias || property.name}` })
    triggerId.value = null
    form.value = cloneDeep(defaultForm)
  }
}

function handleCancel() {
  formRef.value?.clearValidate()
  formRef.value?.resetFields()
  form.value = cloneDeep(defaultForm)
  dateForm.value = cloneDeep(defaultDateForm)
  notifies.value = cloneDeep(defaultNotify)
  category.value = 1
  filterExp.value = ''
  selectedBot.value = undefined
  noticeContentRef.value?.destroy()

  nextTick(() => {
    visible.value = false
  })
}

async function handleOk() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  filterCompRef.value?.handleSubmit()
  const { name, description, enable, action, attr_ids } = form.value
  const params: any = {
    attr_id: '',
    option: {
      filter: filterExp.value,
      name,
      description,
      enable,
    },
  }

  switch (triggerAction.value) {
    case '1': {
      const { employee_ids, custom_email, subject, method } = notifies.value
      const { body, body_html } = noticeContentRef.value?.getContent() ?? {}
      let tos: any[] = []
      if (employee_ids && employee_ids.length) {
        await getNoticeByEmployeeIds({
          employee_ids: employee_ids.map((item: string) => item.split('-')[1]),
        }).then((res) => {
          tos = tos.concat(res)
        })
        params.option.employee_ids = employee_ids
      }
      if (showCustomEmail.value) {
        custom_email.split(';').forEach((email: string) => {
          tos.push({ email })
        })
      }
      if (selectedBot.value && selectedBot.value.length) {
        selectedBot.value.forEach((bot) => {
          tos.push({ [`${bot}`]: bot })
        })
      }
      if (category.value === 2) {
        const { before_days, notify_at } = dateForm.value
        params.option.notifies = {
          tos,
          subject,
          body,
          body_html,
          method: [...method, ...(selectedBot.value ?? [])],
          before_days,
          notify_at,
        }
      } else {
        params.option.notifies = {
          tos,
          subject,
          body,
          body_html,
          method: [...method, ...(selectedBot.value ?? [])],
        }
      }
      break
    }
    case '2': {
      const webhooks = webhookRef.value?.getParams()
      params.option.webhooks = webhooks
      break
    }
    case '3': {
      params.option.dag_id = dagId.value
      break
    }
  }

  if (category.value === 1) {
    params.option.action = action
    if (action === '2') {
      params.option.attr_ids = attr_ids
    }
  }

  if (category.value === 2) {
    try {
      await dateFormRef.value?.validate()
    } catch {
      return
    }
    const { attr_id, before_days, notify_at } = dateForm.value
    params.attr_id = attr_id
    params.option.notifies = { ...cloneDeep(params.option.notifies ?? {}), before_days, notify_at }
  }

  if (triggerId.value) {
    await updateTrigger(props.CITypeId as number, triggerId.value, params)
    message.success(t('editSuccess'))
  } else {
    const res = await addTrigger(props.CITypeId as number, params)
    triggerId.value = res.id
    message.success(t('createSuccess'))
  }

  refresh?.()
}

function handleDetele() {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ciType.confirmDeleteTrigger'),
    onOk() {
      deleteTrigger(props.CITypeId as number, triggerId.value as number).then(() => {
        message.success(t('deleteSuccess'))
        handleCancel()
        refresh?.()
      })
    },
  })
}

function setExpFromFilter(exp: string) {
  if (exp) {
    filterExp.value = `${exp}`
  } else {
    filterExp.value = ''
  }
}

function handleBlurInput() {
  setTimeout(() => {
    isShow.value = false
  }, 100)
}

function focusOnInput() {
  isShow.value = true
}

function handleClickSelect(item: any) {
  searchValue.value = item.label
  dagId.value = item.id
}

async function clickTestSend() {
  if (!triggerId.value) {
    message.warning(t('cmdb.ciType.testSendTip'))
    return
  }
  await testTrigger(props.CITypeId as number, triggerId.value)
  message.success(t('cmdb.ciType.testSendSuccess'))
}

defineExpose({ createFromTriggerTable, open })
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order, vue/v-on-event-hyphenation -->
  <CustomDrawer
    wrap-class-name="trigger-form"
    :width="910"
    :title="title"
    :open="visible"
    :destroy-on-close="true"
    @close="handleCancel"
  >
    <div class="custom-drawer-bottom-action">
      <a-button type="primary" ghost @click="handleCancel">{{ t('cancel') }}</a-button>
      <a-button v-if="triggerId" danger @click="handleDetele">{{ t('delete') }}</a-button>
      <a-button @click="handleOk" type="primary">{{ t('confirm') }}</a-button>
    </div>
    <a-form ref="formRef" :model="form" :rules="rules" :label-col="{ span: 3 }" :wrapper-col="{ span: 18 }">
      <p>
        <strong>{{ t('cmdb.ciType.basicInfo') }}</strong>
      </p>
      <a-form-item :label="t('name')" name="name">
        <a-input v-model:value="form.name" :placeholder="t('cmdb.ciType.nameInputTips')" />
      </a-form-item>
      <a-form-item :label="t('type')">
        <a-radio-group v-model:value="category">
          <a-radio-button :value="1">{{ t('cmdb.ciType.triggerDataChange') }}</a-radio-button>
          <a-radio-button :value="2">{{ t('cmdb.ciType.triggerDate') }}</a-radio-button>
        </a-radio-group>
        <div class="ant-form-explain" v-if="category === 1">{{ t('cmdb.ciType.triggerDataChangeDesc') }}</div>
        <div class="ant-form-explain" v-if="category === 2">{{ t('cmdb.ciType.triggerDateDesc') }}</div>
      </a-form-item>
      <a-form-item :label="t('desc')" name="description">
        <a-input v-model:value="form.description" :placeholder="t('cmdb.ciType.descInput')" />
      </a-form-item>
      <a-form-item :label="t('cmdb.ciType.triggerEnable')" name="enable">
        <a-switch v-model:checked="form.enable" />
      </a-form-item>
      <template v-if="category === 1">
        <p>
          <strong>{{ t('cmdb.ciType.triggerCondition') }}</strong>
        </p>
        <a-form-item :label="t('cmdb.ciType.event')" name="action">
          <a-radio-group v-model:value="form.action">
            <a-radio value="0">{{ t('cmdb.ciType.addInstance') }}</a-radio>
            <a-radio value="1">{{ t('cmdb.ciType.deleteInstance') }}</a-radio>
            <a-radio value="2">{{ t('cmdb.ciType.changeInstance') }}</a-radio>
          </a-radio-group>
          <div class="ant-form-explain" v-if="form.action === '2'">{{ t('cmdb.ciType.changeInstanceDesc') }}</div>
        </a-form-item>
        <a-form-item v-if="form.action === '2'" :label="t('cmdb.ciType.attributes')" name="attr_ids">
          <a-select
            v-model:value="form.attr_ids"
            show-search
            mode="multiple"
            :placeholder="t('cmdb.ciType.selectMutipleAttributes')"
          >
            <a-select-option v-for="attr in attrList" :key="attr.id" :value="attr.id">{{
              attr.alias || attr.name
            }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item class="trigger-form-filter">
          <template #label>
            <span style="position: relative; white-space: pre">
              {{ t('cmdb.ciType.filter') }}
              <a-tooltip :title="t('cmdb.ciType.filterDesc')">
                <InfoCircleOutlined
                  style="position: absolute; top: 2px; left: -17px; color: #a5a9bc"
                  @click="(e) => { e.stopPropagation(); e.preventDefault() }"
                />
              </a-tooltip>
            </span>
          </template>
          <FilterComp
            ref="filterCompRef"
            :is-dropdown="false"
            :can-search-preference-attr-list="attrList"
            :expression="filterExp ? `q=${filterExp}` : ''"
            @set-exp-from-filter="setExpFromFilter"
          />
        </a-form-item>
      </template>
    </a-form>

    <template v-if="category === 2">
      <p>
        <strong>{{ t('cmdb.ciType.triggerCondition') }}</strong>
      </p>
      <a-form ref="dateFormRef" :model="dateForm" :rules="dateFormRules" :label-col="{ span: 3 }" :wrapper-col="{ span: 18 }">
        <a-form-item :label="t('cmdb.ciType.attributes')" name="attr_id">
          <a-select v-model:value="dateForm.attr_id" :placeholder="t('cmdb.ciType.selectSingleAttribute')">
            <a-select-option v-for="attr in canAddTriggerAttr" :key="attr.id" :value="attr.id">{{
              attr.alias || attr.name
            }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item class="trigger-form-filter">
          <template #label>
            <span style="position: relative; white-space: pre">
              {{ t('cmdb.ciType.filter') }}
              <a-tooltip :title="t('cmdb.ciType.filterDesc')">
                <InfoCircleOutlined
                  style="position: absolute; top: 2px; left: -17px; color: #a5a9bc"
                  @click="(e) => { e.stopPropagation(); e.preventDefault() }"
                />
              </a-tooltip>
            </span>
          </template>
          <FilterComp
            ref="filterCompRef"
            :is-dropdown="false"
            :can-search-preference-attr-list="attrList"
            :expression="filterExp ? `q=${filterExp}` : ''"
            @set-exp-from-filter="setExpFromFilter"
          />
        </a-form-item>
        <a-form-item :label="t('cmdb.ciType.beforeDays')" name="before_days">
          <a-input-number v-model:value="dateForm.before_days" :min="0" />
          {{ t('cmdb.ciType.days') }}
        </a-form-item>
        <a-form-item :label="t('cmdb.ciType.notifyAt')" name="notify_at">
          <a-time-picker v-model:value="dateForm.notify_at" format="HH:mm" value-format="HH:mm" />
          <div class="ant-form-explain">{{ t('cmdb.ciType.dateTriggerdesc') }}</div>
        </a-form-item>
      </a-form>
    </template>

    <p>
      <strong>{{ t('cmdb.ciType.triggerAction') }}</strong>
    </p>
    <a-radio-group
      v-model:value="triggerAction"
      :style="{ width: '100%', display: 'flex', justifyContent: 'space-around', marginBottom: '10px' }"
    >
      <a-radio value="1">{{ t('cmdb.ciType.notify') }}</a-radio>
      <a-radio value="2">Webhook</a-radio>
    </a-radio-group>

    <a-form
      ref="notifiesForm"
      :model="notifies"
      :rules="notifiesRules"
      :label-col="{ span: 3 }"
      :wrapper-col="{ span: 18 }"
      v-if="triggerAction === '1'"
    >
      <a-form-item label=" " :colon="false">
        <span class="trigger-tips">{{ tips }}</span>
      </a-form-item>
      <a-form-item :label="t('cmdb.ciType.receivers')" name="employee_ids" class="trigger-form-employee">
        <EmployeeTreeSelect multiple v-model="notifies.employee_ids" />
        <div class="trigger-form-custom-email">
          <a-textarea
            v-if="showCustomEmail"
            v-model:value="notifies.custom_email"
            :placeholder="t('cmdb.ciType.emailTips')"
            :rows="1"
          />
          <a-button
            @click="() => { showCustomEmail = !showCustomEmail }"
            type="primary"
            size="small"
          >{{ `${showCustomEmail ? t('delete') : t('add')}` }}{{ t('cmdb.ciType.customEmail') }}</a-button>
        </div>
      </a-form-item>
      <a-form-item :label="t('cmdb.ciType.notifySubject')" name="subject">
        <a-input v-model:value="notifies.subject" :placeholder="t('cmdb.ciType.notifySubjectTips')" />
      </a-form-item>
      <a-form-item :label="t('cmdb.ciType.notifyContent')" name="body" :wrapper-col="{ span: 21 }">
        <NoticeContent :needOld="category === 1 && form.action === '2'" :attrList="attrList" ref="noticeContentRef" />
      </a-form-item>
      <a-form-item :label="t('cmdb.ciType.notifyMethod')" name="method">
        <a-checkbox-group v-model:value="notifies.method">
          <a-row :style="{ marginTop: '4px' }" :gutter="[0, 12]">
            <a-col :span="6">
              <a-checkbox value="email"><MailOutlined style="margin-right: 5px" />{{ t('email') }}</a-checkbox>
            </a-col>
            <a-col :span="6">
              <a-checkbox value="wechatApp"><WechatOutlined style="margin-right: 5px" />{{ t('wechat') }}</a-checkbox>
            </a-col>
            <a-col :span="6">
              <a-checkbox value="dingdingApp"><DingdingOutlined style="margin-right: 5px" />{{ t('dingding') }}</a-checkbox>
            </a-col>
            <a-col :span="6">
              <a-checkbox value="feishuApp"><SendOutlined style="margin-right: 5px" />{{ t('feishu') }}</a-checkbox>
            </a-col>
            <a-col :span="4" :style="{ lineHeight: '32px' }">
              <RobotOutlined style="margin-right: 5px" />{{ t('bot') }}：
            </a-col>
            <a-col :span="18">
              <treeselect
                :disable-branch-nodes="true"
                :class="{
                  'custom-treeselect': true,
                  'custom-treeselect-white': true,
                }"
                :style="{
                  '--custom-height': '32px',
                  lineHeight: '32px',
                  '--custom-multiple-lineHeight': '14px',
                }"
                v-model="selectedBot"
                :multiple="true"
                :clearable="true"
                searchable
                :options="appBot"
                value-consists-of="LEAF_PRIORITY"
                :placeholder="t('cmdb.ciType.botSelect')"
                :normalizer="botNormalizer"
                append-to-body
                :z-index="1050"
                :no-children-text="t('noData')"
              >
                <template #value-label="{ node }">
                  <span>{{ node.label }}</span>
                </template>
              </treeselect>
            </a-col>
          </a-row>
        </a-checkbox-group>

        <a-row v-if="category === 2">
          <a-button
            @click="clickTestSend"
            :disabled="!dateForm.attr_id"
            type="primary"
            ghost
            class="ops-button-ghost"
          >
            {{ t('cmdb.ciType.testSend') }}
          </a-button>
        </a-row>
      </a-form-item>
    </a-form>

    <div class="auto-complete-wrapper" v-if="triggerAction === '3'">
      <a-input
        id="auto-complete-wrapper-input"
        v-model:value="searchValue"
        @focus="focusOnInput"
        @blur="handleBlurInput"
        allow-clear
      />
      <div id="auto-complete-wrapper-popover" class="auto-complete-wrapper-popover" v-if="isShow">
        <div
          class="auto-complete-wrapper-popover-item"
          @click="handleClickSelect(item)"
          v-for="item in filterList"
          :key="item.id"
          :title="item.label"
        >
          {{ item.label }}
        </div>
      </div>
    </div>
    <span v-if="triggerAction === '2'" class="trigger-tips">{{ webhookTips }}</span>
    <Webhook ref="webhookRef" style="margin-top: 10px" v-if="triggerAction === '2'" />
  </CustomDrawer>
</template>

<style lang="less">
.trigger-form {
  .ant-form-item {
    margin-bottom: 5px;
  }
  .trigger-form-employee,
  .trigger-form-filter {
    .ant-form-item-control {
      line-height: 24px;
    }
  }
  .trigger-form-filter {
    .table-filter-add {
      line-height: 40px;
    }
  }
}
</style>

<style lang="less" scoped>
.auto-complete-wrapper {
  position: relative;
  margin-left: 25px;
  width: 250px;
  margin-top: 20px;
  .auto-complete-wrapper-popover {
    position: fixed;
    width: 250px;
    max-height: 200px;
    overflow-y: auto;
    overflow-x: hidden;
    background-color: #fff;
    z-index: 10;
    box-shadow: 0 2px 8px #00000026;
    .auto-complete-wrapper-popover-item {
      .ops_popover_item();
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.trigger-form-custom-email {
  margin-top: 10px;
  text-align: right;
}

.trigger-tips {
  border: 1px solid @primary-color;
  background-color: #e6f7ff;
  padding: 2px 10px;
  border-radius: 4px;
  color: @primary-color;
  line-height: 1.5;
}
</style>
