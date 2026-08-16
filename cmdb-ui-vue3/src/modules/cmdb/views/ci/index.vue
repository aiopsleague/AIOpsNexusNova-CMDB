<script setup lang="ts">
import { computed, provide, ref } from 'vue'
import { MoreOutlined, SearchOutlined, StarOutlined, UserAddOutlined } from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { getPreference, subscribeCIType, subscribeTreeView, getAutoSubscription } from '@/modules/cmdb/api/preference'
import { roleHasPermissionToGrant } from '@/modules/acl/api/permission'
import { searchResourceType } from '@/modules/acl/api/resource'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import SplitPane from '@/components/SplitPane/SplitPane.vue'
import CMDBGrant from '@/modules/cmdb/components/cmdbGrant/index.vue'
import InstanceList from './instanceList.vue'

const { t } = useI18n()
const route = useRoute()

const paneLengthPixel = ref(205)
const searchValue = ref('')
const preferenceGroup = ref<any[]>([])
const currentTypeId = ref<number | null>(
  Number((route.params.typeId as string) || localStorage.getItem('ops_ci_typeid') || '') || null
)
const resourceType = ref<Record<string, any>>({})
const autoSub = ref<Record<string, any>>({})
const pageLoading = ref(false)

const cmdbGrantCITypeRef = ref<InstanceType<typeof CMDBGrant>>()

const currentCIType = computed<Record<string, any>>(() => {
  let CIType: Record<string, any> = {}
  preferenceGroup.value.some((group) => {
    const type = group.children.find((item: any) => item.id === currentTypeId.value)
    if (type) {
      CIType = type
    }
    return type
  })
  return CIType
})

const filterPreferenceGroup = computed<any[]>(() => {
  if (!preferenceGroup.value?.length) {
    return []
  }

  if (!searchValue.value) {
    return preferenceGroup.value
  }

  const cloned = cloneDeep(preferenceGroup.value)
  cloned.forEach((group) => {
    if (group?.name?.indexOf?.(searchValue.value) >= 0) {
      return
    }
    group.children =
      group?.children?.filter?.(
        (item: any) =>
          item?.alias?.indexOf?.(searchValue.value) >= 0 || item?.name?.indexOf?.(searchValue.value) >= 0
      ) || []
  })
  return cloned.filter((group) => group?.children?.length)
})

function iconImgSrc(icon?: string): string {
  const parts = icon ? icon.split('$$') : []
  return parts[2] && parts[3] ? `/api/common-setting/v1/file/${parts[3]}` : ''
}

provide('resource_type', () => resourceType.value)

async function getPreferenceData() {
  const res = await getPreference()
  const groupTypes = (res?.group_types || []).filter((group: any) => group?.ci_types?.length)
  const groups = groupTypes.map((group: any) => {
    const children = group.ci_types.map((type: any) => ({
      ...type,
      key: `ci_type_${type.id}`,
    }))
    return {
      name: group.name,
      id: group.id,
      key: `group_${group.id}`,
      children,
    }
  })

  preferenceGroup.value = groups

  if (!groups.length) {
    currentTypeId.value = null
    return
  }

  if (
    !currentTypeId.value ||
    !groups.some((group: any) => group.children.some((item: any) => item.id === currentTypeId.value))
  ) {
    updateTypeId(groups[0].children[0].id)
  }
}

async function getResourceType() {
  await searchResourceType({ page_size: 9999, app_id: 'cmdb' }).then((res: any) => {
    resourceType.value = { groups: res.groups, id2perms: res.id2perms }
  })
}

async function loadAutoSubscription() {
  const res = await getAutoSubscription()
  autoSub.value = res || {}
}

function updateTypeId(id: number) {
  if (id !== currentTypeId.value) {
    currentTypeId.value = id
    localStorage.setItem('ops_ci_typeid', String(id))
  }
}

function handleSearch(e: { target: { value: string } }) {
  searchValue.value = e.target.value
}

function handlePerm(type: any) {
  roleHasPermissionToGrant({
    app_id: 'cmdb',
    resource_type_name: 'CIType',
    perm: 'grant',
    resource_name: type.name,
  }).then((res: any) => {
    if (res.result) {
      cmdbGrantCITypeRef.value?.open({ name: type.name, cmdbGrantType: 'ci', CITypeId: type.id })
    } else {
      message.error(t('noPermission'))
    }
  })
}

function cancelSub(type: any) {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.preference.confirmcancelSub2', { name: type.alias || type.name }),
    onOk: () => {
      const unsubCIType = subscribeCIType(type.id, '')
      const unsubTree = subscribeTreeView(type.id, '')
      Promise.all([unsubCIType, unsubTree]).then(() => {
        message.success(t('cmdb.preference.cancelSubSuccess'))
        getPreferenceData()
      })
    },
  })
}

pageLoading.value = true
Promise.all([getPreferenceData(), getResourceType(), loadAutoSubscription()]).then(() => {
  pageLoading.value = false
})
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <div>
    <div v-if="pageLoading" class="page-loading">
      <a-spin size="large" />
    </div>

    <div v-else-if="preferenceGroup.length === 0">
      <a-alert banner>
        <template #message>
          <span>{{ t('cmdb.preference.tips1') }}</span>
          <router-link to="/cmdb/preference">{{ t('cmdb.preference.tips2') }}</router-link>
          <span>{{ t('cmdb.preference.tips3') }}</span>
        </template>
      </a-alert>
    </div>

    <SplitPane
      v-else
      app-name="cmdb-ci-page"
      :min="200"
      :max="500"
      v-model:pane-length-pixel="paneLengthPixel"
      :trigger-length="18"
      calc-based-parent
    >
      <template #one>
        <div class="ci-left">
          <a-input :placeholder="t('cmdb.preference.searchPlaceholder')" class="ci-types-left-header-input" @change="handleSearch">
            <template #prefix><SearchOutlined /></template>
          </a-input>

          <div class="ci-left-list">
            <div v-for="(group) in filterPreferenceGroup" :key="group.key" class="ci-left-group">
              <div class="ci-left-group-name">{{ group.name }}</div>
              <div
                v-for="(type) in group.children"
                :key="type.key"
                :class="['ci-left-item', currentTypeId === type.id ? 'ci-left-item_active' : '']"
                @click="updateTypeId(type.id)"
              >
                <span class="ci-icon" :style="{ width: '16px', height: '16px' }">
                  <img v-if="iconImgSrc(type.icon)" :src="iconImgSrc(type.icon)" />
                  <span v-else class="ci-icon-letter">{{ (type.alias || type.name)[0].toUpperCase() }}</span>
                </span>
                <span class="ci-left-item-name">{{ type.alias || type.name }}</span>
                <a-dropdown>
                  <a class="ci-left-item-more">
                    <MoreOutlined />
                  </a>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item @click="handlePerm(type)">
                        <UserAddOutlined />
                        {{ t('grant') }}
                      </a-menu-item>
                      <a-menu-item v-if="!autoSub.enabled" @click="cancelSub(type)">
                        <StarOutlined />
                        {{ t('cmdb.preference.cancelSub') }}
                      </a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </div>
            </div>
          </div>
        </div>

        <CMDBGrant ref="cmdbGrantCITypeRef" resource-type="CIType" app_id="cmdb" />
      </template>
      <template #two>
        <InstanceList
          v-if="currentTypeId"
          :key="Number(currentTypeId)"
          :type-id="Number(currentTypeId)"
          :c-i-type="currentCIType"
          :auto-sub="autoSub"
          @un-subscribe="getPreferenceData"
        />
      </template>
    </SplitPane>
  </div>
</template>

<style lang="less" scoped>
.page-loading {
  text-align: center;
  padding-top: 150px;
}

.ci-types-left-header-input {
  margin-bottom: 12px;

  :deep(input) {
    background-color: #fff;
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

  :deep(.ant-input-prefix) {
    color: @text-color_3;
  }
}

.ci-left {
  height: calc(100vh - 90px);
  width: 100%;
  background-color: #f7f8fa;
  border-right: 1px solid #e8eaed;
  padding: 0px 8px 12px;

  &-list {
    width: 100%;
    height: calc(100% - 40px);
    overflow: hidden;

    &:hover {
      overflow-y: auto;
    }
  }

  &-group {
    width: 100%;

    &:not(:last-child) {
      margin-bottom: 12px;
    }

    &-name {
      margin-bottom: 8px;
      font-weight: 600;
      font-size: 13px;
      color: #666;
      padding: 8px 12px;
    }
  }

  &-item {
    width: 100%;
    display: flex;
    align-items: center;
    padding: 6px 12px;
    margin: 0 4px 6px 4px;
    cursor: pointer;
    border-radius: 6px;
    height: 36px;
    position: relative;
    transition: all 0.2s ease;

    &::before {
      content: "";
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: @primary-color;
      border-radius: 0 2px 2px 0;
      opacity: 0;
      transition: opacity 0.2s ease;
    }

    .ci-icon {
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #fff;
      border: 1px solid #e8eaed;
      border-radius: 6px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      flex-shrink: 0;
      transition: transform 0.2s ease;

      img {
        max-width: 16px;
        max-height: 16px;
      }
    }

    &-name {
      margin-left: 8px;
      margin-right: 8px;
      text-wrap: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 14px;
      color: @text-color_1;
      transition: color 0.2s ease;
      flex: 1;
    }

    &-more {
      margin-left: auto;
      display: none;
      flex-shrink: 0;
    }

    &_active {
      background-color: @primary-color_6;
      box-shadow: 0 1px 3px fade(@primary-color, 10%);

      &::before {
        opacity: 1;
      }

      .ci-left-item-name {
        color: @primary-color;
        font-weight: 600;
      }

      .ci-icon {
        box-shadow: 0 2px 4px fade(@primary-color, 20%);
      }
    }

    &:hover {
      background-color: @primary-color_7;
      transform: translateX(2px);

      .ci-icon {
        transform: scale(1.05);
      }

      .ci-left-item-more {
        display: block;
      }
    }
  }
}

.ci-icon-letter {
  color: @primary-color;
  font-size: 12px;
  font-weight: 600;
}
</style>
