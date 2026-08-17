<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message, Modal } from 'ant-design-vue'
import {
  TableOutlined,
  ApartmentOutlined,
  SettingOutlined,
  CloseCircleOutlined,
  ThunderboltOutlined,
  HolderOutlined,
  ClockCircleOutlined,
  CaretDownOutlined,
  CaretRightOutlined,
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import { getCITypeGroups } from '@/modules/cmdb/api/ciTypeGroup'
import {
  getPreference,
  getPreference2,
  subscribeCIType,
  subscribeTreeView,
  preferenceCitypeOrder,
  getAutoSubscription as getAutoSubscriptionApi,
} from '@/modules/cmdb/api/preference'
import { getCITypeAttributesByName } from '@/modules/cmdb/api/CITypeAttr'
import { getCIAdcStatistics } from '@/modules/cmdb/api/ci'
import {
  SUB_NET_CITYPE_NAME,
  SCOPE_CITYPE_NAME,
  ADDRESS_CITYPE_NAME,
} from '@/modules/cmdb/views/ipam/constants'
import SubscribeSetting from '@/modules/cmdb/components/subscribeSetting/subscribeSetting.vue'
import AutoSubscribe from './components/autoSubscribe.vue'
import draggable from 'vuedraggable'

const { t } = useI18n()

const ciTypeData = ref<any[]>([])
const expandKeys = ref<Array<string | number>>([])
const self = ref<Record<string, any>>({ instance: [], tree: [] })
const type_id2users = ref<Record<string, any>>({})
const myPreferences = ref<any[]>([])
const searchValue = ref('')
const autoSub = ref<Record<string, any>>({})

const subscribeSettingRef = ref<InstanceType<typeof SubscribeSetting>>()
const autoSubRef = ref<InstanceType<typeof AutoSubscribe>>()

const windowHeight = computed(() => window.innerHeight)

const filterCiTypeData = computed(() => {
  if (searchValue.value) {
    const _ciTypeData = cloneDeep(ciTypeData.value)
    _ciTypeData.forEach((group) => {
      if (group.ci_types) {
        group.ci_types = group.ci_types.filter(
          (item: any) =>
            item.name.toLowerCase().includes(searchValue.value.toLowerCase()) ||
            item.alias.toLowerCase().includes(searchValue.value.toLowerCase())
        )
      }
    })
    return _ciTypeData
  }
  return ciTypeData.value
})

const enableAutoSub = computed(() => autoSub.value?.enabled ?? false)

const IPAM_CI = [SUB_NET_CITYPE_NAME, SCOPE_CITYPE_NAME, ADDRESS_CITYPE_NAME]

function subTypeIcon(icon: string) {
  return icon === 'cmdb-tree' ? ApartmentOutlined : TableOutlined
}

function initData() {
  getCITypes()
  getAutoSubscription()
}

async function getCITypes(isInit = false) {
  const [ciTypeGroup, pref, pref2, statistics] = await Promise.all([
    getCITypeGroups({ need_other: true }),
    getPreference(true, true),
    getPreference2(true, true),
    getCIAdcStatistics(),
  ])

  ciTypeGroup.forEach((group: any) => {
    if (group.ci_types && group.ci_types.length) {
      group.ci_types = group.ci_types.filter((type: any) => !IPAM_CI.includes(type.name))
      group.ci_types.forEach((type: any) => {
        const idx = pref.type_ids.findIndex((p: any) => p === type.id)
        if (idx > -1) {
          type.is_subscribed = true
        }
        const type_statistic = statistics[type.id]
        type.integrity = type_statistic
          ? Math.round((type_statistic.auto_discovery * 100) / type_statistic.total)
          : 0
      })
    }
    if (!group.id) {
      group.id = -1
      group.name = t('other')
    }
  })
  ciTypeData.value = ciTypeGroup
  const { self: _self, type_id2users: _type_id2users } = pref2
  self.value = _self
  type_id2users.value = _type_id2users

  const prefGroupTypes = pref.group_types.filter((group: any) => {
    group.ci_types = group?.ci_types?.filter((type: any) => !IPAM_CI.includes(type?.name)) || []
    return group?.ci_types?.length
  })
  const prefTreeTypes = pref?.tree_types?.filter((type: any) => !IPAM_CI.includes(type?.name)) || []

  myPreferences.value = [
    {
      name: t('cmdb.menu.ciTable'),
      groups: prefGroupTypes,
      icon: 'cmdb-ci',
      type: 'ci',
    },
    {
      name: t('cmdb.menu.ciTree'),
      groups: [
        {
          ci_types: prefTreeTypes,
          name: null,
        },
      ],
      icon: 'cmdb-tree',
      type: 'tree',
    },
  ]
  if (isInit) {
    setTimeout(() => {
      expandKeys.value = ciTypeGroup.map((item: any) => item.id)
    }, 300)
  }
}

async function getAutoSubscription() {
  const res = await getAutoSubscriptionApi()
  autoSub.value = res || {}
}

function getsubscribedDays(item: any) {
  const subscribedTime = self.value.type_id2subs_time?.[item.id]
  if (!subscribedTime) {
    return t('cmdb.preference.just')
  }
  const now = dayjs()
  const sub = dayjs(subscribedTime)
  const day = now.diff(sub, 'day')
  if (day > 0 && day < 1) {
    return `${now.diff(sub, 'hour')}` + t('cmdb.preference.hoursAgo')
  } else if (day >= 1 && day <= 31) {
    return `${day} ` + t('cmdb.preference.daysAgo')
  } else if (day > 31 && day < 365) {
    return `${now.diff(sub, 'month')}` + t('cmdb.preference.monthsAgo')
  } else if (day >= 365) {
    return `${now.diff(sub, 'year')}` + t('cmdb.preference.yearsAgo')
  }
  return t('cmdb.preference.just')
}

function unsubscribe(ciType: any, type = 'all') {
  Modal.confirm({
    title: t('warning'),
    content:
      t('cmdb.preference.confirmcancelSub') +
      ` ${ciType.alias || ciType.name} ${
        type !== 'all'
          ? t('cmdb.preference.of') + `${type === 'ci' ? t('cmdb.menu.ciTable') : t('cmdb.menu.ciTree')}`
          : ''
      } ？`,
    onOk() {
      const promises: Promise<any>[] = []
      if (type === 'all' || type === 'ci') {
        promises.push(subscribeCIType(ciType.id, ''))
      }
      if (type === 'all' || type === 'tree') {
        promises.push(subscribeTreeView(ciType.id, ''))
      }

      Promise.all(promises).then(() => {
        if (type === 'all' || type === 'ci') {
          const lastTypeId = window.localStorage.getItem('ops_ci_typeid') || undefined
          if (Number(ciType.id) === Number(lastTypeId)) {
            localStorage.setItem('ops_ci_typeid', '')
          }
        }
        message.success(t('cmdb.preference.cancelSubSuccess'))
        initData()
      })
    },
  })
}

async function handleSubscribeCIType(ciType: any) {
  try {
    const res = await getCITypeAttributesByName(ciType.id)
    const attributes = res?.attributes || []
    const subscribeList = attributes
      .filter((item: any) => item?.default_show)
      .map((item: any) => {
        return [item?.id?.toString(), false]
      })
    if (subscribeList.length === 0) {
      const uniqueItem = attributes.find((item: any) => item?.id === res?.unique_id)
      if (uniqueItem) {
        subscribeList.push([uniqueItem?.id?.toString(), false])
      }
    }

    await subscribeCIType(ciType.id, subscribeList)
    message.success(t('cmdb.components.subSuccess'))
    initData()
  } catch (error) {
    console.error('handleSubscribeCIType failed', error)
    message.error(t('cmdb.components.subFailed'))
  }
}

function openSubscribeSetting(ciType: any, activeKey = '1') {
  subscribeSettingRef.value?.open({ ...ciType, type_id: ciType.id }, activeKey)
}

function changeGroupExpand(group: any) {
  const _idx = expandKeys.value.findIndex((expand) => expand === group.id)
  if (_idx > -1) {
    expandKeys.value.splice(_idx, 1)
  } else {
    expandKeys.value.push(group.id)
  }
}

function handleChangeGroups() {
  const typeIds: any[] = []
  myPreferences.value[0].groups.forEach((groupTypes: any) => {
    groupTypes.ci_types.forEach((ciType: any) => {
      typeIds.push(ciType.id)
    })
  })
  preferenceCitypeOrder({ type_ids: typeIds, is_tree: false })
    .then(() => {
      initData()
    })
    .catch(() => {
      getCITypes(false)
    })
}

function orderChange(_e: any, group: any, isTree: boolean) {
  let typeIds: any[] = []
  if (!isTree) {
    myPreferences.value[0].groups.forEach((groupTypes: any) => {
      if (group.id === groupTypes.id) {
        group.ci_types.forEach((ciType: any) => {
          typeIds.push(ciType.id)
        })
      } else {
        groupTypes.ci_types.forEach((ciType: any) => {
          typeIds.push(ciType.id)
        })
      }
    })
  } else {
    typeIds = group.ci_types.map((item: any) => item.id)
  }
  preferenceCitypeOrder({ type_ids: typeIds, is_tree: isTree })
    .then(() => {
      if (!isTree) {
        initData()
      }
    })
    .catch(() => {
      getCITypes(false)
    })
}

function openAutoSubModal() {
  autoSubRef.value?.open()
}

onMounted(() => {
  getCITypes(true)
  getAutoSubscription()
})
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <div class="cmdb-preference" :style="{ height: `${windowHeight - 40}px` }">
    <div class="cmdb-preference-left">
      <div class="cmdb-preference-left-card">
        <span class="cmdb-preference-left-card-title">{{ t('cmdb.preference.mySub') }}</span>
        <span class="cmdb-preference-left-card-content">
          <TableOutlined :style="{ marginRight: '5px' }" />{{ t('cmdb.menu.ciTable') }}:
          <a-badge
            show-zero
            :count="self.instance.length"
            :overflow-count="99"
            :number-style="{
              backgroundColor: 'inherit',
              boxShadow: 'none',
              height: '23px',
              fontSize: '14px',
            }"
          />
        </span>
        <span class="cmdb-preference-left-card-content">
          <ApartmentOutlined :style="{ marginRight: '5px' }" />{{ t('cmdb.menu.ciTree') }}:
          <a-badge
            show-zero
            :count="self.tree.length"
            :overflow-count="99"
            :number-style="{
              backgroundColor: 'inherit',
              boxShadow: 'none',
              height: '23px',
              fontSize: '14px',
            }"
          />
        </span>
      </div>
      <div class="cmdb-preference-group" v-for="(subType, index) in myPreferences" :key="subType.name">
        <div class="cmdb-preference-group-title">
          <span>
            <component :is="subTypeIcon(subType.icon)" :style="{ marginRight: '10px' }" />
            {{ subType.name }}
          </span>
        </div>
        <draggable class="ci-types-left-content" :list="subType.groups" @end="handleChangeGroups" filter=".undraggable">
          <div v-for="group in subType.groups" :key="group.id ?? group.name">
            <div :class="`${group.id === undefined ? 'undraggable' : ''}`">
              <div v-if="index === 0 && subType.groups.length > 1" class="cmdb-preference-group-content">
                <HolderOutlined v-if="group.name" class="cmdb-preference-move-icon" />
                <span style="font-weight: 500; color: #a5a9bc" :title="group.name || t('other')">
                  {{ group.name || t('other') }}
                </span>
                <span :style="{ color: '#c3cdd7' }">({{ group.ci_types.length }})</span>
              </div>
            </div>
            <draggable v-model="group.ci_types" :animation="300" @change="(e) => orderChange(e, group, index === 1)">
              <div class="cmdb-preference-group-content" v-for="ciType in group.ci_types" :key="ciType.id">
                <HolderOutlined class="cmdb-preference-move-icon" />
                <div
                  :class="{
                    'cmdb-preference-avatar': true,
                    'cmdb-preference-avatar-noicon': !ciType.icon,
                  }"
                  :style="{ marginRight: '10px' }"
                >
                  <template v-if="ciType.icon">
                    <img
                      v-if="ciType.icon.split('$$')[2]"
                      :src="`/api/common-setting/v1/file/${ciType.icon.split('$$')[3]}`"
                      :style="{ maxHeight: '30px', maxWidth: '30px' }"
                    />
                    <TableOutlined
                      v-else
                      :style="{
                        color: ciType.icon.split('$$')[1],
                        fontSize: '14px',
                      }"
                    />
                  </template>
                  <span v-else :style="{ fontSize: '20px' }">{{ ciType.name[0].toUpperCase() }}</span>
                </div>
                <span class="cmdb-preference-group-content-title">{{ ciType.alias || ciType.name }}</span>
                <span class="cmdb-preference-group-content-action">
                  <template v-if="!enableAutoSub || subType.type === 'tree'">
                    <a-tooltip :title="t('cmdb.preference.cancelSub')">
                      <span @click="unsubscribe(ciType, group.type)">
                        <CloseCircleOutlined />
                      </span>
                    </a-tooltip>
                    <a-divider type="vertical" :style="{ margin: '0 3px' }" />
                  </template>
                  <a-tooltip :title="t('cmdb.preference.editSub')">
                    <span @click="openSubscribeSetting(ciType, `${index + 1}`)">
                      <SettingOutlined />
                    </span>
                  </a-tooltip>
                </span>
              </div>
            </draggable>
          </div>
        </draggable>
      </div>
    </div>
    <div class="cmdb-preference-right">
      <div class="cmdb-preference-right-header">
        <a-input-search
          v-model:value="searchValue"
          class="cmdb-preference-right-header-search"
          :placeholder="t('cmdb.preference.searchPlaceholder')"
        />
        <div
          :class="[
            'cmdb-preference-right-header-auto',
            enableAutoSub ? 'cmdb-preference-right-header-auto_enable' : '',
          ]"
          @click="openAutoSubModal"
        >
          <ThunderboltOutlined />
          <span>{{ enableAutoSub ? t('cmdb.preference.autoSub') : t('cmdb.preference.autoSub2') }}</span>
        </div>
      </div>
      <div v-for="group in filterCiTypeData" :key="group.id">
        <p
          @click="changeGroupExpand(group)"
          :style="{ display: 'inline-block', cursor: 'pointer' }"
          class="cmdb-preference-right-group-title"
        >
          <component :is="expandKeys.includes(group.id) ? CaretDownOutlined : CaretRightOutlined" />
          {{ group.name }}({{ group.ci_types ? group.ci_types.length : 0 }})
        </p>
        <div v-show="expandKeys.includes(group.id)" :key="group.id">
          <div class="cmdb-preference-content">
            <div class="cmdb-preference-type" v-for="item in group.ci_types" :key="item.id">
              <div class="cmdb-preference-header">
                <div
                  :class="{
                    'cmdb-preference-avatar': true,
                    'cmdb-preference-avatar-noicon': !item.icon,
                  }"
                >
                  <template v-if="item.icon">
                    <img
                      v-if="item.icon.split('$$')[2]"
                      :src="`/api/common-setting/v1/file/${item.icon.split('$$')[3]}`"
                      :style="{ maxHeight: '30px', maxWidth: '30px' }"
                    />
                    <TableOutlined
                      v-else
                      :style="{
                        color: item.icon.split('$$')[1],
                        fontSize: '14px',
                      }"
                    />
                  </template>
                  <span v-else>{{ item.name[0].toUpperCase() }}</span>
                </div>
                <span class="cmdb-preference-title" :title="item.alias || item.name">
                  {{ item.alias || item.name }}
                </span>
              </div>
              <div class="cmdb-preference-progress">
                <div class="cmdb-preference-progress-info">
                  <span>{{ t('cmdb.menu.ad') }}</span>
                  <span>{{ item.integrity }}%</span>
                </div>
                <div class="cmdb-preference-progress-gray">
                  <div class="cmdb-preference-progress-colors" :style="{ width: `${item.integrity}%` }"></div>
                </div>
              </div>
              <a-divider :style="{ margin: '10px 0 3px 0' }" />
              <div class="cmdb-preference-footor-subscribed" v-if="item.is_subscribed">
                <span :style="{ opacity: enableAutoSub ? 0 : 1 }">
                  <ClockCircleOutlined :style="{ marginRight: '3px' }" />{{ getsubscribedDays(item) }}
                </span>
                <span>
                  <template v-if="!enableAutoSub">
                    <a-tooltip :title="t('cmdb.preference.cancelSub')">
                      <span @click="unsubscribe(item)">
                        <CloseCircleOutlined />
                      </span>
                    </a-tooltip>
                    <a-divider type="vertical" :style="{ margin: '0 3px' }" />
                  </template>
                  <a-divider type="vertical" :style="{ margin: '0 3px' }" />
                  <a-tooltip :title="t('cmdb.preference.editSub')">
                    <span @click="openSubscribeSetting(item)">
                      <SettingOutlined />
                    </span>
                  </a-tooltip>
                </span>
              </div>
              <div v-else class="cmdb-preference-footor-unsubscribed">
                <template v-if="!enableAutoSub">
                  <a @click="handleSubscribeCIType(item)" class="cmdb-preference-footor-unsubscribed-item">
                    <TableOutlined />{{ t('cmdb.preference.subCITable') }}
                  </a>
                  <span class="cmdb-preference-footor-unsubscribed-gap"></span>
                </template>
                <a
                  @click="openSubscribeSetting(item, '2')"
                  class="cmdb-preference-footor-unsubscribed-item"
                >
                  <ApartmentOutlined />{{ t('cmdb.preference.subCITree') }}
                </a>
              </div>
            </div>
            <i></i><i></i><i></i><i></i><i></i>
          </div>
        </div>
      </div>
    </div>
    <SubscribeSetting ref="subscribeSettingRef" @reload="initData" />
    <AutoSubscribe ref="autoSubRef" :ci-type="ciTypeData" :auto-sub="autoSub" @ok="initData" />
  </div>
</template>

<style lang="less" scoped>
.cmdb-preference {
  margin: -24px;
  overflow: auto;
  position: relative;
  display: flex;
  flex-direction: row;
  &::before {
    content: '';
    position: absolute;
    box-shadow: 0px 1px 4px rgba(0, 21, 41, 0.5);
    width: 100%;
    left: 0;
    height: 1px;
    top: 0;
  }
  .cmdb-preference-left {
    width: 300px;
    height: 100%;
    padding: 24px 18px;
    .cmdb-preference-left-card {
      background: url('../../assets/preference_card.png');
      background-repeat: no-repeat;
      background-position-x: center;
      background-position-y: center;
      height: 172px;
      background-size: 90%;
      color: #fff;
      position: relative;
      .cmdb-preference-left-card-title {
        font-weight: 600;
        position: absolute;
        top: 32px;
        left: 36px;
      }
      .cmdb-preference-left-card-content {
        position: absolute;
        left: 36px;
      }
      .cmdb-preference-left-card-content:nth-child(2) {
        top: 65px;
      }
      .cmdb-preference-left-card-content:nth-child(3) {
        top: 95px;
      }
    }
    .cmdb-preference-group:nth-child(2) {
      margin-bottom: 20px;
    }
    .cmdb-preference-group {
      .ci-types-left-content {
        max-height: calc(100% - 45px);
        overflow: hidden;
        &:hover {
          overflow: auto;
        }
        .undraggable {
          .cmdb-preference-group-content {
            cursor: default;
            margin-left: 20px;
            &:hover {
              background: transparent;
              box-shadow: none;
            }
          }
        }
      }
      .cmdb-preference-group-title {
        text-align: center;
        margin-bottom: 12px;
        i {
          color: @primary-color;
        }
        > span {
          display: inline-block;
          color: @text-color_1;
          border-radius: 16px;
          font-weight: 600;
          font-size: 15px;
          padding: 8px 16px;
          background-color: #f7f8fa;
        }
      }
      .cmdb-preference-group-content {
        color: @text-color_1;
        font-weight: 400;
        display: flex;
        align-items: center;
        height: 45px;
        padding: 0 8px;
        cursor: move;
        justify-content: flex-start;
        &:hover {
          background: @primary-color_7;
          box-shadow: 0px 2px 8px fade(@primary-color, 15%);
          border-radius: 6px;
          transform: translateX(2px);
          .cmdb-preference-avatar {
            border-color: @primary-color;
            box-shadow: 0 2px 4px fade(@primary-color, 20%);
            transform: scale(1.05);
          }
          .cmdb-preference-group-content-action {
            display: inline;
            white-space: nowrap;
            margin-left: auto;
          }
          .cmdb-preference-move-icon {
            visibility: visible;
          }
        }
        .cmdb-preference-move-icon {
          width: 14px;
          height: 20px;
          cursor: move;
          visibility: hidden;
        }
        .cmdb-preference-group-content-title {
          flex: 1;
        }
        .cmdb-preference-group-content-action {
          margin-left: auto;
          font-size: 12px;
          color: @primary-color;
          cursor: pointer;
          display: none;
        }
      }
    }
  }
  .cmdb-preference-right {
    flex: 1;
    height: 100%;
    padding-top: 24px;

    &-header {
      margin-bottom: 20px;
      display: flex;
      align-items: center;

      &-search {
        width: 300px;
        margin-right: 14px;
      }

      &-auto {
        background: linear-gradient(90deg, #16d9e3 0%, #30c7ec 47%, #46aef7 100%);
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        color: #ffffff;
        cursor: pointer;
        padding: 0 12px;
        opacity: 0.5;
        transition: opacity 0.2s;

        span {
          margin-left: 4px;
          font-size: 14px;
          font-weight: 600;
        }

        &_enable {
          opacity: 1;
        }

        &:hover {
          opacity: 1;
        }
      }
    }

    &-group-title {
      width: 300px;
      margin-bottom: 20px;

      &:hover {
        color: @primary-color;
      }
    }

    .cmdb-preference-content {
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      > i {
        width: 195px;
        margin: 0 20px 0 0;
      }
      .cmdb-preference-type {
        display: inline-block;
        width: 195px;
        height: 127px;
        border-radius: @border-radius-box;
        background-color: #fff;
        box-shadow: ~'0px 2px 8px @{primary-color}15';
        margin: 0 20px 20px 0;
        padding: 12px;
        &:hover {
          box-shadow: ~'4px 25px 30px @{primary-color}15';
          transform: scale(1.1);
        }
        .cmdb-preference-header {
          display: flex;
          align-items: center;
          justify-content: flex-start;
          .cmdb-preference-title {
            color: rgba(0, 0, 0, 0.75);
            font-weight: 500;
            margin-left: 12px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            flex: 1;
          }
        }
        .cmdb-preference-colleague {
          color: rgba(0, 0, 0, 0.45);
          font-size: 12px;
          margin-top: 10px;
          height: 18px;
          display: flex;
          flex-direction: row;
          align-items: center;
          justify-content: space-between;
          .cmdb-preference-colleague-name > span:not(.cmdb-preference-colleague-ellipsis) {
            display: inline-block;
            color: rgba(0, 0, 0, 0.5);
            height: 14px;
            width: 14px;
            background-color: @primary-color_7;
            border-radius: 50%;
            font-size: 12px;
            line-height: 14px;
            text-align: center;
            margin-right: 2px;
          }
        }
        .cmdb-preference-progress {
          font-size: 12px;
          color: rgba(0, 0, 0, 0.76);
          margin-top: 10px;
          .cmdb-preference-progress-info {
            display: flex;
            justify-content: space-between;
          }
          .cmdb-preference-progress-gray {
            height: 5px;
            border-radius: 5px;
            background-color: @text-color_6;
            margin-top: 5px;
            width: 100%;
            position: relative;
            .cmdb-preference-progress-colors {
              height: 5px;
              position: absolute;
              top: 0;
              left: 0;
              border-radius: 5px;
              background: @primary-color_8;
            }
          }
        }
        .cmdb-preference-footor-unsubscribed {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 10px;

          &-item {
            display: flex;
            align-items: center;
            gap: 3px;
            font-size: 12px;
            color: @text-color_1;

            &:hover {
              color: @primary-color;
            }
          }

          &-gap {
            width: 1px;
            height: 18px;
            background-color: #e8e8e8;
          }
        }
        .cmdb-preference-footor-subscribed {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          > span:first-child {
            color: rgba(0, 0, 0, 0.45);
          }
          > span:nth-child(2) {
            color: @primary-color;
            cursor: pointer;
          }
        }
      }
    }
  }

  .cmdb-preference-avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    background: #fff;
    border: 1px solid #e8eaed;
    border-radius: 6px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s ease;
  }
  .cmdb-preference-avatar-noicon {
    > span {
      font-size: 18px;
      color: @text-color_4;
    }
  }
}
</style>
