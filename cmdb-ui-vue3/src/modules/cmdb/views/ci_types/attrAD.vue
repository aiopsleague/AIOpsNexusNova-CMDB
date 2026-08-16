<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, h, nextTick, onMounted, provide, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { PlusOutlined } from '@ant-design/icons-vue'
import dataEmptyImg from '@/assets/data_empty.png'
import {
  getDiscovery,
  getCITypeDiscovery,
  deleteCITypeDiscovery,
  deleteDiscovery,
  putCITypeDiscovery,
} from '@/modules/cmdb/api/discovery'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import AttrADTabpane from './attrADTabpane.vue'
import AttrADTabs from './attrADTabs.vue'

const props = withDefaults(defineProps<{ CITypeId?: number | null }>(), { CITypeId: null })

const { t } = useI18n()

const ciTypeAttributes = ref<any[]>([])
const adrList = ref<any[]>([])
const serviceCITYpeList = ref<any[]>([])
const clientCITypeList = ref<any[]>([])
const currentTab = ref<string | number>('')
const deletePlugin = ref(false)
const queryLoaded = ref(false)

const attrAdTabpaneRef = ref<InstanceType<typeof AttrADTabpane>>()

const windowHeight = computed(() => window.innerHeight)

const currentADData = computed(
  () => adCITypeList.value.find((item) => item?.id === currentTab.value) ?? {}
)

const adCITypeList = computed(() => {
  const uniqueArray = differenceBy(clientCITypeList.value, serviceCITYpeList.value, 'id')
  return [...serviceCITYpeList.value, ...uniqueArray]
})

function differenceBy(a: any[], b: any[], key: string) {
  const ids = new Set(b.map((item) => item[key]))
  return a.filter((item) => !ids.has(item[key]))
}

watch(currentTab, () => {
  if (currentTab.value && queryLoaded.value) {
    nextTick(() => {
      attrAdTabpaneRef.value?.init()
    })
  }
})

async function getDiscoveryData() {
  await getDiscovery().then((res) => {
    adrList.value = res
  })
}

async function getCITypeDiscoveryData(currentTabId?: string | number) {
  await getCITypeDiscovery(props.CITypeId as number).then((res) => {
    const serviceList = res.filter((item: any) => item.adr_id)
    serviceList.forEach((item: any) => {
      const find = adrList.value.find((adr) => adr.id === item.adr_id)
      item.icon = find?.option?.icon || {}
    })

    serviceCITYpeList.value = serviceList
    nextTick(() => {
      if (adCITypeList.value && adCITypeList.value.length && !currentTab.value) {
        currentTab.value = adCITypeList.value[0].id
      }
      if (currentTabId) {
        currentTab.value = currentTabId
      }
    })
  })
}

function getADCITypeParam(adr_id: number | string, params = 'name', isAll = false) {
  const find = adrList.value.find((item) => item.id === adr_id)
  if (find) {
    if (isAll) {
      return find
    }
    return find[`${params}`]
  }
}

async function deleteADT(item: any) {
  const isPlugin = getADCITypeParam(item.adr_id, 'is_plugin')

  Modal.confirm({
    title: t('cmdb.ciType.confirmDeleteADT', {
      pluginName: `${item?.extra_option?.alias || getADCITypeParam(item.adr_id)}`,
    }),
    content: () => {
      if (!isPlugin) {
        return ''
      }
      return h('div', [
        h(
          'a-checkbox',
          { checked: deletePlugin.value, 'onUpdate:checked': (v: boolean) => (deletePlugin.value = v) },
          () => t('cmdb.ciType.deletePlugin')
        ),
      ])
    },
    onOk() {
      if (item.isClient) {
        const adtIndex = clientCITypeList.value.findIndex((listItem) => listItem.id === item.id)
        if (adtIndex !== -1) {
          clientCITypeList.value.splice(adtIndex, 1)
          currentTab.value = adCITypeList.value?.[0]?.id ?? ''

          if (isPlugin && deletePlugin.value) {
            deleteDiscoveryData(item.adr_id)
          }
        }
      } else {
        deleteCITypeDiscovery(item.id).then(async () => {
          if (currentTab.value === item.id) {
            currentTab.value = ''
          }
          message.success(t('deleteSuccess'))
          getCITypeDiscoveryData()
          if (isPlugin && deletePlugin.value) {
            deleteDiscoveryData(item.adr_id)
          }
          deletePlugin.value = false
        })
      }
    },
    onCancel() {
      deletePlugin.value = false
    },
  })
}

function deleteDiscoveryData(id: number) {
  deleteDiscovery(id).finally(async () => {
    deletePlugin.value = false
    await getDiscoveryData()
  })
}

// TODO: wire up <ADModal> / <EditDrawer> once migrated.
function openAdModal() {}

function openEditDrawer(_data: any, _type: string, _adType: string) {}

function changeTab(id: string | number) {
  currentTab.value = id
}

function changeAlias({ id, value, isClient }: { id: string | number; value: string; isClient: boolean }) {
  if (isClient) {
    const adtIndex = clientCITypeList.value.findIndex((item) => item.id === id)
    clientCITypeList.value[adtIndex].extra_option.alias = value
  } else {
    const adtIndex = adCITypeList.value.findIndex((item) => item.id === id)
    const oldExtraOption = adCITypeList.value?.[adtIndex]?.extra_option

    const params = {
      extra_option: {
        ...(oldExtraOption || {}),
        alias: value,
      },
    }
    putCITypeDiscovery(id, params).then(async () => {
      message.success(t('saveSuccess'))
      await getCITypeDiscoveryData()
    })
  }
}

function saveTabpane(id: string | number) {
  const adtIndex = clientCITypeList.value.findIndex((listItem) => listItem.id === currentTab.value)
  if (adtIndex !== -1) {
    clientCITypeList.value.splice(adtIndex, 1)
  }
  getCITypeDiscoveryData(id)
}

provide('getCITypeDiscovery', getCITypeDiscoveryData)

onMounted(async () => {
  await getDiscoveryData()
  await getCITypeDiscoveryData()
  getCITypeAttributesById(props.CITypeId as number).then((res) => {
    ciTypeAttributes.value = res.attributes.map((item: any) => {
      return { ...item, value: item.name, label: item.name }
    })
    queryLoaded.value = true
    if (currentTab.value) {
      nextTick(() => {
        attrAdTabpaneRef.value?.init()
      })
    }
  })
})
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order, vue/v-on-event-hyphenation -->
  <div class="attr-ad" :style="{ height: `${windowHeight - 130}px` }">
    <div v-if="adCITypeList && adCITypeList.length">
      <AttrADTabs
        :adCITypeList="adCITypeList"
        :currentTab="currentTab"
        :getADCITypeParam="getADCITypeParam"
        @changeTab="changeTab"
        @changeAlias="changeAlias"
        @deleteADT="deleteADT"
        @clickAdd="openAdModal"
      />
      <AttrADTabpane
        :key="`attrAdTabpane_${currentTab}`"
        ref="attrAdTabpaneRef"
        :adr_id="currentADData.adr_id"
        :CITypeId="CITypeId"
        :adrList="adrList"
        :adCITypeList="adCITypeList"
        :currentAdt="currentADData"
        :ciTypeAttributes="ciTypeAttributes"
        :currentAdr="getADCITypeParam(currentADData.adr_id, undefined, true)"
        @openEditDrawer="(data, type, adType) => openEditDrawer(data, type, adType)"
        @handleSave="saveTabpane"
      />
    </div>
    <a-empty v-else :image-style="{ height: '60px' }">
      <template #image><img :src="dataEmptyImg" /></template>
      <template #description><span>{{ t('noData') }}</span></template>
      <a-button @click="openAdModal" type="primary" size="small">
        <template #icon><PlusOutlined /></template>
        {{ t('add') }}
      </a-button>
    </a-empty>
    <!-- TODO: wire up <ADModal> and <EditDrawer> once migrated. -->
  </div>
</template>

<style lang="less">
.attr-ad {
  position: relative;
  padding: 0 20px;

  .attr-ad-header {
    width: 100%;
    display: inline-flex;
    height: 32px;
    line-height: 32px;
    padding-left: 10px;
    margin-bottom: 20px;
    border-left: 4px solid @primary-color;
    font-size: 16px;
    color: rgba(0, 0, 0, 0.75);
    margin-top: 30px;
  }

  .attr-ad-header-margin {
    margin-bottom: 0px;
  }

  .attr-ad-footer {
    width: 60%;
    text-align: right;
    margin-bottom: 10px;
  }
}
</style>

<style lang="less">
.attr-ad {
  .ant-empty {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
  &:not(.ant-tabs-tab-active).ant-tabs-tab {
    color: #a5a9bc;
  }
  .ant-form-item {
    margin-bottom: 8px;
  }
}
</style>
