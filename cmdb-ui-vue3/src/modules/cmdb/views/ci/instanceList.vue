<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { onMounted, provide, ref, watch } from 'vue'
import {
  InfoCircleOutlined,
  MoreOutlined,
  PlusOutlined,
  SettingOutlined,
  StarOutlined,
  UserAddOutlined,
} from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { searchCI, deleteCI } from '@/modules/cmdb/api/ci'
import { getSubscribeAttributes, subscribeCIType, subscribeTreeView } from '@/modules/cmdb/api/preference'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { roleHasPermissionToGrant } from '@/modules/acl/api/permission'
import { searchResourceType } from '@/modules/acl/api/resource'
import { getCITableColumns, cloneDeep } from '@/modules/cmdb/utils/helper'
import CMDBGrant from '@/modules/cmdb/components/cmdbGrant/index.vue'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    typeId?: number
    CIType?: Record<string, any>
    autoSub?: Record<string, any>
  }>(),
  {
    typeId: undefined,
    CIType: () => ({}),
    autoSub: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'unSubscribe'): void
}>()

const searchRef = ref<any>()
const xTableRef = ref<any>()
const cmdbGrantRef = ref<InstanceType<typeof CMDBGrant>>()

const loading = ref(false)
const currentPage = ref(1)
const pageSizeOptions = ref(['50', '100', '200', '100000'])
const pageSize = ref(50)
const totalNumber = ref(0)
const loadTip = ref('')

const preferenceAttrList = ref<any[]>([])
const instanceList = ref<any[]>([])
const columns = ref<any[]>([])
const selectedRowKeys = ref<any[]>([])
const initialInstanceList = ref<any[]>([])
const sortByTable = ref<string | undefined>(undefined)

const attrList = ref<any[]>([])
const attributes = ref<Record<string, any>>({})
const resourceType = ref<Record<string, any>>({})

const initialPasswordValue = ref<Record<string, string>>({})
const passwordValue = ref<Record<string, string>>({})
const visible = ref(false)

provide('handleSearch', handleSearch)
provide('setPreferenceSearchCurrent', setPreferenceSearchCurrent)
provide('attrList', () => attrList.value)
provide('attributes', () => attributes.value)
provide('filterCompPreferenceSearch', () => ({ type_id: props.typeId }))
provide('resource_type', () => resourceType.value)

async function getAttributeList() {
  await getCITypeAttributesById(props.typeId as number).then((res) => {
    attrList.value = res.attributes
    attributes.value = res
  })
}

function handleSearch() {
  xTableRef.value?.clearSort()
  sortByTable.value = undefined
  if (currentPage.value === 1) {
    reloadData()
  } else {
    currentPage.value = 1
  }
}

function setPreferenceSearchCurrent(_id: number | null = null) {
  // TODO: wire up PreferenceSearch (preference search state not yet ported)
}

function reloadData() {
  loadTableData()
}

async function loadTableData(sortBy?: string) {
  try {
    loading.value = true
    const fuzzySearch = searchRef.value?.fuzzySearch
    const expression = searchRef.value?.expression || ''
    const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
    const regSort = /(?<=sort=).+/g

    const exp = expression.match(regQ) ? expression.match(regQ)[0] : null
    let sort
    if (sortBy) {
      sort = sortBy
    } else {
      sort = expression.match(regSort) ? expression.match(regSort)[0] : undefined
    }
    const res = await searchCI({
      q: `_type:${props.typeId}${exp ? `,${exp}` : ''}${fuzzySearch ? `,*${fuzzySearch}*` : ''}`,
      count: pageSize.value,
      page: currentPage.value,
      sort,
    })
    totalNumber.value = res['numfound']
    columns.value = getColumns(res.result, preferenceAttrList.value)
    columns.value.forEach((col) => {
      if (col.is_password) {
        initialPasswordValue.value[col.field] = ''
        passwordValue.value[col.field] = ''
      }
    })
    const jsonAttrList = attrList.value.filter((attr) => attr.value_type === '6')
    instanceList.value = res['result'].map((item: any) => {
      jsonAttrList.forEach((jsonAttr) => {
        item[jsonAttr.name] = item[jsonAttr.name] ? JSON.stringify(item[jsonAttr.name]) : ''
      })
      return { ...cloneDeep(item) }
    })
    initialInstanceList.value = cloneDeep(instanceList.value)
    xTableRef.value?.refreshColumn()
  } finally {
    loading.value = false
  }
}

function getColumns(data: any[], attrList: any[]) {
  const el = document.getElementById('ciIndex')
  const width = el ? el.clientWidth - 50 : 1600
  return getCITableColumns(data, attrList, width)
}

async function loadPreferenceAttrList() {
  const subscribed = await getSubscribeAttributes(props.typeId as number)
  preferenceAttrList.value = subscribed.attributes
}

function onShowSizeChange(_current: number, nextPageSize: number) {
  pageSize.value = nextPageSize
  if (currentPage.value === 1) {
    reloadData()
  } else {
    currentPage.value = 1
  }
}

function columnDrop() {
  // TODO: wire up Sortable (column drag reorder not yet ported)
}

function handleMenuClick(e: { key: string }) {
  if (e.key === 'grant') {
    visible.value = false
  }
}

function handlePerm() {
  roleHasPermissionToGrant({
    app_id: 'cmdb',
    resource_type_name: 'CIType',
    perm: 'grant',
    resource_name: props.CIType.name,
  }).then((res: any) => {
    if (res.result) {
      searchResourceType({ page_size: 9999, app_id: 'cmdb' }).then((resourceRes: any) => {
        resourceType.value = { groups: resourceRes.groups, id2perms: resourceRes.id2perms }
        cmdbGrantRef.value?.open({
          name: props.CIType.name,
          cmdbGrantType: 'ci',
          CITypeId: props.typeId,
        })
      })
    } else {
      message.error(t('noPermission'))
    }
  })
}

function unsubscribe() {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.preference.confirmcancelSub2', {
      name: `${props.CIType.alias || props.CIType.name}`,
    }),
    onOk: () => {
      const promises = [subscribeCIType(props.typeId as number, ''), subscribeTreeView(props.typeId as number, '')]
      Promise.all(promises).then(() => {
        message.success(t('cmdb.preference.cancelSubSuccess'))
        emit('unSubscribe')
      })
    },
  })
}

function handleCITypeConfig() {
  const { id, name } = props.CIType || {}
  if (id && name) {
    roleHasPermissionToGrant({
      app_id: 'cmdb',
      resource_type_name: 'CIType',
      perm: 'config',
      resource_name: name,
    }).then((res: any) => {
      if (res?.result) {
        const storageId = `null%${id}%${name}`
        localStorage.setItem('ops_cityps_currentId', storageId)
        localStorage.setItem('ops_model_config_tab_key', '1')
        window.open('/cmdb/ci_types', '_blank')
      } else {
        message.error(t('noPermission'))
      }
    })
  }
}

function openUpdate() {
  // TODO: wire up CreateInstanceForm (batch update flow not yet ported)
}

function openBatchQRCode() {
  // TODO: wire up QRCodeBatchExport (batch QR code export not yet ported)
}

function openBatchDownload() {
  // TODO: wire up BatchDownload (batch download not yet ported)
}

function batchRollback() {
  // TODO: wire up CiRollbackForm (baseline rollback not yet ported)
}

function batchDelete() {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete'),
    onOk() {
      batchDeleteAsync()
    },
  })
}

async function batchDeleteAsync() {
  let successNum = 0
  let errorNum = 0
  loading.value = true
  loadTip.value = t('cmdb.ci.batchDeleting')
  const floor = Math.ceil(selectedRowKeys.value.length / 6)
  for (let i = 0; i < floor; i++) {
    const itemList = selectedRowKeys.value.slice(6 * i, 6 * i + 6)
    const promises = itemList.map((x) => deleteCI(x, false))
    await Promise.allSettled(promises)
      .then((res) => {
        res.forEach((r) => {
          if (r.status === 'fulfilled') {
            successNum += 1
          } else {
            errorNum += 1
          }
        })
      })
      .finally(() => {
        loadTip.value = t('cmdb.ci.batchDeleting2', {
          total: selectedRowKeys.value.length,
          successNum,
          errorNum,
        })
      })
  }
  loading.value = false
  loadTip.value = ''
  selectedRowKeys.value = []
  xTableRef.value?.clearCheckboxRow()
  xTableRef.value?.clearCheckboxReserve()
  if (currentPage.value === 1) {
    loadTableData()
  } else {
    currentPage.value = 1
  }
}

watch(currentPage, () => {
  loadTableData(sortByTable.value)
})

onMounted(async () => {
  loading.value = true
  await getAttributeList()
  await loadPreferenceAttrList()
  await loadTableData()
  loading.value = false

  setTimeout(() => {
    columnDrop()
  }, 1000)
})
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <div id="ciIndex" class="cmdb-ci">
    <a-spin :tip="loadTip" :spinning="loading">
      <div class="cmdb-views-header">
        <span>
          <span class="cmdb-views-header-title">{{ CIType.alias || CIType.name }}</span>
          <!-- TODO: wire up MetadataDrawer (attributeDesc trigger) -->
          <span class="cmdb-views-header-metadata">
            <InfoCircleOutlined />{{ t('cmdb.ci.attributeDesc') }}
          </span>
        </span>
        <a-space>
          <!-- TODO: wire up CreateInstanceForm (create trigger) -->
          <a-button type="primary" class="ops-button-ghost" ghost>
            <template #icon><PlusOutlined /></template>
            {{ t('create') }}
          </a-button>
          <!-- TODO: wire up EditAttrsPopover (config table trigger) -->
          <a-button type="primary" ghost class="ops-button-ghost">
            <template #icon><SettingOutlined /></template>{{ t('cmdb.configTable') }}
          </a-button>
          <a-dropdown>
            <a-button type="primary" ghost class="ops-button-ghost"><MoreOutlined /></a-button>
            <template #overlay>
              <a-menu @click="handleMenuClick">
                <a-menu-item key="grant" @click="handlePerm">
                  <UserAddOutlined />
                  {{ t('grant') }}
                </a-menu-item>
                <a-menu-item v-if="!autoSub.enabled" key="cancelSub" @click="unsubscribe">
                  <StarOutlined />
                  {{ t('cmdb.preference.cancelSub') }}
                </a-menu-item>
                <a-menu-item key="citypeConfig" @click="handleCITypeConfig">
                  {{ t('cmdb.menu.citypeManage') }}
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </a-space>
      </div>
      <div class="cmdb-ci-main">
        <!-- TODO: wire up SearchForm / PreferenceSearch -->
        <div class="ops-list-batch-action" v-show="!!selectedRowKeys.length">
          <span @click="openUpdate">{{ t('update') }}</span>
          <a-divider type="vertical" />
          <span @click="openBatchQRCode">{{ t('cmdb.ci.qrcodeExport') }}</span>
          <a-divider type="vertical" />
          <span @click="openBatchDownload">{{ t('download') }}</span>
          <a-divider type="vertical" />
          <span @click="batchDelete">{{ t('delete') }}</span>
          <a-divider type="vertical" />
          <span @click="batchRollback">{{ t('cmdb.ci.rollback') }}</span>
          <span>{{ t('cmdb.ci.selectRows', { rows: selectedRowKeys.length }) }}</span>
        </div>

        <!-- TODO: wire up CiDetailDrawer -->
        <!-- TODO: wire up CITable (the instance table) -->

        <div :style="{ textAlign: 'right', marginTop: '4px' }">
          <a-pagination
            show-size-changer
            :current="currentPage"
            size="small"
            :total="totalNumber"
            show-quick-jumper
            :page-size="pageSize"
            :page-size-options="pageSizeOptions"
            @show-size-change="onShowSizeChange"
            :show-total="(total: number, range: number[]) => t('pagination.total', { range0: range[0], range1: range[1], total })"
            @change="(page: number) => (currentPage = page)"
          />
        </div>
        <CMDBGrant ref="cmdbGrantRef" resource-type="CIType" app_id="cmdb" />
      </div>
    </a-spin>
  </div>
</template>

<style lang="less">
.cmdb-views-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;

  &-title {
    font-size: 18px;
    font-weight: 600;
    color: @text-color_1;
  }

  &-metadata {
    margin-left: 8px;
    color: @text-color_3;
    cursor: pointer;
  }
}

.ops-list-batch-action {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;

  span {
    cursor: pointer;
    color: @primary-color;
  }
}
</style>

<style lang="less" scoped>
.cmdb-ci {
  background-color: #fff;
  padding: 20px;
  border-radius: @border-radius-box;
  height: calc(100vh - 64px);
  overflow: auto;
  margin-bottom: -24px;
}
</style>
