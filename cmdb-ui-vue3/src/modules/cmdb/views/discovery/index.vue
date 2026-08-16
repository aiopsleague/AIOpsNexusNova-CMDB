<script setup lang="ts">
import { computed, onMounted, provide, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import { DownloadOutlined, PlusCircleOutlined, UploadOutlined } from '@ant-design/icons-vue'
import dataEmptyImg from '@/assets/data_empty.png'
import { getDiscovery, deleteDiscovery } from '@/modules/cmdb/api/discovery'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import { DISCOVERY_CATEGORY_TYPE } from '@/modules/cmdb/constants'
import DiscoveryCard from './discoveryCard.vue'
import EditDrawer from './editDrawer.vue'
import AccountConfig from './accountConfig/index.vue'

const props = withDefaults(
  defineProps<{
    isSelected?: boolean
  }>(),
  {
    isSelected: false,
  }
)

const { t } = useI18n()

interface DiscoveryCategory {
  type: string
  children: any[]
}

const typeCategoryChildren = ref<Record<string, DiscoveryCategory>>({})
const radioKey = ref('')
const searchValue = ref('')

const editDrawerRef = ref<InstanceType<typeof EditDrawer>>()
const accountConfigRef = ref<InstanceType<typeof AccountConfig>>()

const windowHeight = computed(() => window.innerHeight)

const typeCategory = computed(() => [
  { type: DISCOVERY_CATEGORY_TYPE.HTTP, label: t('cmdb.ad.http') },
  { type: DISCOVERY_CATEGORY_TYPE.PRIVATE_CLOUD, label: t('cmdb.ad.privateCloud') },
  { type: DISCOVERY_CATEGORY_TYPE.AGENT, label: t('cmdb.ad.agent') },
  { type: DISCOVERY_CATEGORY_TYPE.COMPONENT, label: t('cmdb.ad.component') },
  { type: DISCOVERY_CATEGORY_TYPE.SNMP, label: t('cmdb.ad.snmp') },
  { type: DISCOVERY_CATEGORY_TYPE.PLUGIN, label: t('cmdb.ad.plugin') },
])

const filterCategoryChildren = computed<Record<string, DiscoveryCategory>>(() => {
  const _typeCategoryChildren = cloneDeep(typeCategoryChildren.value)
  return Object.values(_typeCategoryChildren).reduce<Record<string, DiscoveryCategory>>((obj, category) => {
    if (radioKey.value === '' || category.type === radioKey.value) {
      category.children = category.children.filter((item) => {
        return item?.name?.indexOf(searchValue.value) !== -1
      })
      obj[category.type] = category
    }
    return obj
  }, {})
})

const showNullData = computed(() => {
  const showCount = Object.values(filterCategoryChildren.value).reduce((acc, item) => {
    return acc + (item?.children?.length || 0)
  }, 0)
  return showCount === 0
})

const showAddPlugin = computed(() => !props.isSelected && searchValue.value === '')

function getDiscoveryData() {
  const _typeCategoryChildren: Record<string, DiscoveryCategory> = {
    [DISCOVERY_CATEGORY_TYPE.HTTP]: { type: DISCOVERY_CATEGORY_TYPE.HTTP, children: [] },
    [DISCOVERY_CATEGORY_TYPE.PRIVATE_CLOUD]: { type: DISCOVERY_CATEGORY_TYPE.PRIVATE_CLOUD, children: [] },
    [DISCOVERY_CATEGORY_TYPE.AGENT]: { type: DISCOVERY_CATEGORY_TYPE.AGENT, children: [] },
    [DISCOVERY_CATEGORY_TYPE.COMPONENT]: { type: DISCOVERY_CATEGORY_TYPE.COMPONENT, children: [] },
    [DISCOVERY_CATEGORY_TYPE.SNMP]: { type: DISCOVERY_CATEGORY_TYPE.SNMP, children: [] },
    [DISCOVERY_CATEGORY_TYPE.PLUGIN]: { type: DISCOVERY_CATEGORY_TYPE.PLUGIN, children: [] },
  }
  getDiscovery().then((res: any[]) => {
    typeCategory.value.forEach(({ type }) => {
      let categoryChildren: any[] = []
      switch (type) {
        case DISCOVERY_CATEGORY_TYPE.PRIVATE_CLOUD:
          categoryChildren = res.filter((list) => list?.option?.category === 'private_cloud' && list?.type === 'http')
          break
        case DISCOVERY_CATEGORY_TYPE.HTTP:
          categoryChildren = res.filter((list) => list?.option?.category !== 'private_cloud' && list?.type === 'http')
          break
        case DISCOVERY_CATEGORY_TYPE.PLUGIN:
          categoryChildren = res.filter((list) => list.is_plugin)
          break
        case DISCOVERY_CATEGORY_TYPE.AGENT:
          categoryChildren = res.filter((list) => !list.is_plugin && list.type === type)
          break
        default:
          categoryChildren = res.filter((list) => list.type === type)
          break
      }
      _typeCategoryChildren[type].children = categoryChildren
    })
    typeCategoryChildren.value = _typeCategoryChildren
  })
}

function handleOpenEditDrawer(data: any, type: string, autoType: string) {
  editDrawerRef.value?.open(data, type, autoType)
}

function deleteRule(rule: any) {
  Modal.confirm({
    title: t('warning'),
    content: t('confirmDelete', { name: `${rule.name}` }),
    onOk() {
      deleteDiscovery(rule.id).then(() => {
        message.success(t('deleteSuccess'))
        getDiscoveryData()
      })
    },
  })
}

function download() {
  const xhr = new XMLHttpRequest()
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
  xhr.open('GET', `${baseUrl}/v0.1/adr/template/export/file`, true)
  xhr.responseType = 'blob'
  xhr.onload = () => {
    const url = window.URL.createObjectURL(xhr.response)
    const a = document.createElement('a')
    a.href = url
    a.download = t('cmdb.ad.rule')
    a.click()
  }
  xhr.send()
}

function beforeUpload(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const xhr = new XMLHttpRequest()
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
  xhr.open('POST', `${baseUrl}/v0.1/adr/template/import/file`)
  xhr.onreadystatechange = () => {
    if (Number(xhr.readyState) === 4) {
      if (xhr.status === 200) {
        message.success(t('cmdb.common.uploadSuccess'))
        getDiscoveryData()
      }
    }
  }
  xhr.ontimeout = () => {
    message.error(t('cmdb.ad.timeout'))
  }
  xhr.send(formData)
  return false
}

function onSearchDiscovery(v: string) {
  searchValue.value = v
}

function changeRadio(key: string) {
  radioKey.value = key === radioKey.value ? '' : key
}

function openAccountConfig(rule: any) {
  accountConfigRef.value?.open(rule)
}

provide('getDiscovery', getDiscoveryData)

onMounted(() => {
  getDiscoveryData()
})
</script>

<template>
  <div class="setting-discovery">
    <div v-if="!isSelected" class="setting-discovery-header">
      <a-input-search
        class="setting-discovery-search"
        :placeholder="t('cmdb.ad.pluginSearchTip')"
        @search="onSearchDiscovery"
      />
      <div class="setting-discovery-radio">
        <div
          v-for="{ type, label } in typeCategory"
          :key="type"
          :class="['setting-discovery-radio-item', radioKey === type ? 'setting-discovery-radio-item_active' : '']"
          @click="changeRadio(type)"
        >
          {{ label }}
        </div>
      </div>

      <div class="setting-discovery-header-action">
        <a-upload
          name="file"
          :multiple="false"
          accept=".json"
          :file-list="[]"
          :before-upload="beforeUpload"
        >
          <a-button type="primary" class="ops-button-ghost" ghost>
            <template #icon><UploadOutlined /></template>
            {{ t('cmdb.ad.upload') }}
          </a-button>
        </a-upload>
        <a-button type="primary" class="ops-button-ghost" ghost @click="download">
          <template #icon><DownloadOutlined /></template>
          {{ t('cmdb.ad.download') }}
        </a-button>
      </div>
    </div>
    <div
      class="setting-discovery-body"
      :style="{ height: !isSelected ? `${windowHeight - 160}px` : '' }"
    >
      <template v-if="!showNullData">
        <div v-for="{ type, label } in typeCategory" :key="type">
          <template
            v-if="filterCategoryChildren[type] && (filterCategoryChildren[type].children.length || (showAddPlugin && type === DISCOVERY_CATEGORY_TYPE.PLUGIN))"
          >
            <div class="type-header">
              <div>{{ label }}</div>
            </div>
            <a-row type="flex" justify="start">
              <DiscoveryCard
                v-for="rule in filterCategoryChildren[type].children"
                :key="rule.id"
                :rule="rule"
                :is-selected="isSelected"
                @edit-rule="handleOpenEditDrawer(rule, 'edit', type)"
                @delete-rule="deleteRule(rule)"
                @open-account-config="openAccountConfig(rule)"
              />
              <div
                v-if="showAddPlugin && type === DISCOVERY_CATEGORY_TYPE.PLUGIN"
                class="setting-discovery-add"
                @click="handleOpenEditDrawer(null, 'add', DISCOVERY_CATEGORY_TYPE.PLUGIN)"
              >
                <PlusCircleOutlined class="setting-discovery-add-icon" />
                <span class="setting-discovery-add-text">
                  {{ t('cmdb.ad.addPlugin') }}
                </span>
              </div>
            </a-row>
          </template>
        </div>
      </template>
      <div v-else class="setting-discovery-empty">
        <img class="setting-discovery-empty-img" :src="dataEmptyImg" />
        <p class="setting-discovery-empty-text">{{ t('noData') }}</p>
      </div>
    </div>
    <EditDrawer ref="editDrawerRef" :is-discovery-page="true" />
    <AccountConfig ref="accountConfigRef" />
  </div>
</template>

<style lang="less" scoped>
.setting-discovery {
  &-header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;

    &-action {
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;

      &-btn {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border: solid 1px @primary-color_8;
        background-color: #F4F9FF;
        color: @link-color;
      }
    }
  }

  &-search {
    width: 280px;
    flex-shrink: 0;

    :deep(.ant-input) {
      border-radius: 6px;
      border: 1px solid #e8eaed;
      transition: all 0.2s ease;

      &:hover {
        border-color: #c3cdd7;
      }

      &:focus {
        border-color: @primary-color;
        box-shadow: 0 0 0 2px fade(@primary-color, 10%);
      }
    }
  }

  &-radio {
    display: flex;
    align-items: center;
    margin-left: 16px;
    gap: 8px;
    overflow: auto;
    margin-right: 16px;

    &-item {
      padding: 6px 16px;
      font-size: 14px;
      font-weight: 400;
      line-height: 22px;
      cursor: pointer;
      flex-shrink: 0;
      border-radius: 6px;
      transition: all 0.2s ease;
      color: @text-color_2;

      &:hover {
        color: @primary-color;
        background-color: fade(@primary-color, 8%);
      }

      &_active {
        background-color: @primary-color;
        color: #fff;
        font-weight: 500;
      }
    }
  }

  &-body {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    padding: 24px;
    overflow: auto;

    .setting-discovery-add {
      height: 105px;
      width: 180px;
      border-radius: 6px;
      border: 2px dashed #d9d9d9;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.3s ease;
      background: #fafafa;

      &:hover {
        border-color: @primary-color;
        background: fade(@primary-color, 5%);

        .setting-discovery-add-icon {
          color: @primary-color;
          transform: scale(1.1);
        }
      }

      &-icon {
        color: #bfbfbf;
        font-size: 24px;
        transition: all 0.3s ease;
      }

      &-text {
        color: @text-color_2;
        font-size: 13px;
        font-weight: 400;
        margin-top: 8px;
      }
    }

    .setting-discovery-empty {
      text-align: center;
      padding: 40px 0;

      &-text {
        margin-top: 16px;
        color: @text-color_3;
        font-size: 14px;
      }

      &-img {
        width: 120px;
        opacity: 0.6;
      }
    }
  }

  .type-header {
    width: 100%;
    display: flex;
    align-items: center;
    height: 40px;
    padding-left: 12px;
    margin-bottom: 20px;
    border-left: 3px solid @primary-color;
    background: linear-gradient(90deg, fade(@primary-color, 5%) 0%, transparent 100%);
    border-radius: 0 4px 4px 0;

    > div {
      font-weight: 600;
      font-size: 15px;
      color: @text-color_1;
    }
  }
}
</style>
