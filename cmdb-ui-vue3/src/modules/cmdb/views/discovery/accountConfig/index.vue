<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { getHTTPAccounts, postHTTPAccounts } from '@/modules/cmdb/api/discovery'
import { defaultConfig } from './constants'
import PublicTable from './publicTable.vue'
import VCenterTable from './vcenterTable.vue'

const { t } = useI18n()

const visible = ref(false)
const rule = ref<Record<string, any>>({})

const publicTableRef = ref<InstanceType<typeof PublicTable>>()
const vcenterTableRef = ref<InstanceType<typeof VCenterTable>>()

const title = computed(() => {
  if (rule.value?.option?.category === 'private_cloud') {
    return `${rule.value?.name || ''} ${t('cmdb.ciType.account')}`
  }
  return t('cmdb.ciType.cloudAccessKey')
})

const httpName = computed(() => {
  if (rule.value?.option?.category === 'private_cloud') {
    return rule.value?.option?.en || ''
  }
  return 'public'
})

async function open(targetRule: Record<string, any>) {
  if (!targetRule?.id) {
    return
  }
  rule.value = targetRule

  const res = await getHTTPAccounts({ adr_id: targetRule.id })

  visible.value = true
  nextTick(() => {
    const data = res?.length ? handleAccountsData(res) : []
    switch (httpName.value) {
      case 'public':
        publicTableRef.value?.setData(data)
        break
      case 'vcenter':
        vcenterTableRef.value?.setData(data)
        break
      default:
        break
    }
  })
}

function handleAccountsData(accounts: any[]): any[] {
  const config = defaultConfig[httpName.value] || {}

  return accounts.map((item) => {
    return {
      id: item?.id,
      name: item?.name || '',
      ...config,
      ...(item?.config || {}),
    }
  })
}

function handleCancel() {
  visible.value = false
}

async function handleOk() {
  let tableData: any = {}
  switch (httpName.value) {
    case 'public':
      tableData = publicTableRef.value?.getData()
      break
    case 'vcenter':
      tableData = vcenterTableRef.value?.getData()
      break
    default:
      break
  }
  if (tableData.isError) {
    return
  }
  const accounts = tableData.data.map((item: any) => {
    const { name, id, ...otherConfig } = item
    const newData: Record<string, any> = {
      name,
      config: otherConfig,
    }
    if (id) {
      newData.id = id
    }

    return newData
  })
  postHTTPAccounts({
    adr_id: rule.value.id,
    accounts,
  }).then(() => {
    message.success(t('updateSuccess'))
    handleCancel()
  })
}

defineExpose({ open })
</script>

<template>
  <a-modal :open="visible" :title="title" :width="880" :body-style="{ maxHeight: '60vh', overflowY: 'auto' }" @ok="handleOk" @cancel="handleCancel">
    <PublicTable v-if="httpName === 'public'" ref="publicTableRef" />
    <VCenterTable v-else-if="httpName === 'vcenter'" ref="vcenterTableRef" />
  </a-modal>
</template>

<style lang="less" scoped></style>
