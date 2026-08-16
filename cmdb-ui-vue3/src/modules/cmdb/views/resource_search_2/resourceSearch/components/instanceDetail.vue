<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { DatabaseOutlined, RightOutlined, ShareAltOutlined, StarFilled, StarOutlined } from '@ant-design/icons-vue'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import { getCIById, searchCI } from '@/modules/cmdb/api/ci'
import { getCITypeGroupById, getCITypes, getCIType } from '@/modules/cmdb/api/CIType'

import AttrDisplay from './attrDisplay.vue'
import CIIcon from '@/modules/cmdb/components/ciIcon/index.vue'
import noPermissionImg from '@/modules/cmdb/assets/no_permission.png'

const props = withDefaults(
  defineProps<{
    CIId?: string | number
    CITypeId?: string | number
    favorList?: any[]
  }>(),
  {
    CIId: -1,
    CITypeId: -1,
    favorList: () => [],
  }
)

const emit = defineEmits<{
  (e: 'addCollect', data: Record<string, any>): void
  (e: 'deleteCollect', id: string | number): void
  (e: 'hideDetail'): void
}>()

const { t } = useI18n()
const router = useRouter()

const ci = ref<Record<string, any>>({})
const ciType = ref<Record<string, any>>({})
const attributeGroups = ref<any[]>([])
const isNullData = ref(false)

const watchParams = computed(() => ({
  CIId: props.CIId,
  CITypeId: props.CITypeId,
}))

const detailTitle = computed(() => {
  const attrName = ciType.value?.show_name || ciType.value?.unique_name || ''
  return attrName ? ci.value?.[attrName] || '' : ''
})

const favorId = computed(() => {
  const id = props.favorList.find((item: any) => item?.option?.CIId === props.CIId)?.id
  return id ?? null
})

watch(
  watchParams,
  (newVal) => {
    if (newVal?.CIId !== -1 && newVal?.CITypeId !== -1) {
      initData()
    }
  },
  { immediate: true, deep: true }
)

async function initData() {
  const ciData = await getCI()
  if (!ciData) {
    isNullData.value = true
    return
  }
  await getCITypeData()
  await getAttributes()
}

async function getCI() {
  const res = await getCIById(props.CIId)
  const ciData = res.result?.[0] || {}
  ci.value = ciData
  return ciData
}

async function getCITypeData() {
  const res = await getCIType(props.CITypeId)
  ciType.value = res?.ci_types?.[0] || {}
}

async function getAttributes() {
  const res = await getCITypeGroupById(props.CITypeId, { need_other: 1 })
  attributeGroups.value = res
  handleReferenceAttr()
}

async function handleReferenceAttr() {
  const map: Record<string, Record<string, any>> = {}
  attributeGroups.value.forEach((group: any) => {
    group.attributes.forEach((attr: any) => {
      if (attr?.is_reference && attr?.reference_type_id && ci.value[attr.name]) {
        const ids = Array.isArray(ci.value[attr.name]) ? ci.value[attr.name] : ci.value[attr.name] ? [ci.value[attr.name]] : []
        if (ids.length) {
          if (!map?.[attr.reference_type_id]) {
            map[attr.reference_type_id] = {}
          }
          ids.forEach((id: any) => {
            map[attr.reference_type_id][id] = {}
          })
        }
      }
    })
  })

  if (!Object.keys(map).length) {
    return
  }

  const ciTypesRes = await getCITypes({
    type_ids: Object.keys(map).join(','),
  })
  const showAttrNameMap: Record<string, string> = {}
  ciTypesRes.ci_types.forEach((ciTypeItem: any) => {
    showAttrNameMap[ciTypeItem.id] = ciTypeItem?.show_name || ciTypeItem?.unique_name || ''
  })

  const allRes = await Promise.all(
    Object.keys(map).map((key) => {
      return searchCI({
        q: `_type:${key},_id:(${Object.keys(map[key]).join(';')})`,
        count: 9999,
      })
    })
  )

  const ciNameMap: Record<string, any> = {}
  allRes.forEach((res: any) => {
    res.result.forEach((item: any) => {
      ciNameMap[item._id] = item
    })
  })

  const newAttrGroups = cloneDeep(attributeGroups.value)

  newAttrGroups.forEach((group: any) => {
    group.attributes.forEach((attr: any) => {
      if (attr?.is_reference && attr?.reference_type_id) {
        attr.showAttrName = showAttrNameMap?.[attr?.reference_type_id] || ''

        const referenceShowAttrNameMap: Record<string, any> = {}
        const referenceCIIds = ci.value[attr.name]
        ;(Array.isArray(referenceCIIds) ? referenceCIIds : referenceCIIds ? [referenceCIIds] : []).forEach((id: any) => {
          referenceShowAttrNameMap[id] = ciNameMap?.[id]?.[attr.showAttrName] ?? id
        })
        attr.referenceShowAttrNameMap = referenceShowAttrNameMap
      }
    })
  })

  attributeGroups.value = newAttrGroups
}

function shareCi() {
  const text = `${document.location.host}/cmdb/cidetail/${props.CITypeId}/${props.CIId}`
  navigator.clipboard
    .writeText(text)
    .then(() => {
      message.success(t('copySuccess'))
    })
    .catch(() => {
      message.error(t('cmdb.ci.copyFailed'))
    })
}

function goToResourceDetail() {
  localStorage.setItem('ops_ci_typeid', String(props.CITypeId))
  localStorage.setItem('ops_ci_detail_id', String(props.CIId))
  router.push('/cmdb/instances/types')
}

function clickCollect() {
  if (favorId.value) {
    emit('deleteCollect', favorId.value)
  } else {
    emit('addCollect', {
      CIId: props.CIId,
      CITypeId: props.CITypeId,
      title: detailTitle.value,
      icon: ciType.value?.icon,
      CITypeTitle: ciType.value?.name || '',
    })
  }
}

function hideDetail() {
  emit('hideDetail')
}
</script>

<template>
  <div class="instance-detail">
    <div class="instance-detail-hide" @click="hideDetail">
      <RightOutlined class="instance-detail-hide-icon" />
    </div>

    <div v-if="!ci._id" class="instance-detail-null">
      <img :src="noPermissionImg" class="instance-detail-null-img" />
      <span class="instance-detail-null-text">{{ t('noData') }}</span>
    </div>
    <template v-else>
      <div class="instance-detail-header">
        <div class="instance-detail-header-line-1"></div>
        <div class="instance-detail-header-line-2"></div>
        <div class="instance-detail-header-row">
          <CIIcon :icon="ciType.icon" :title="ciType.name || ''" :size="20" />
          <div class="instance-detail-header-title">
            {{ detailTitle }}
          </div>

          <StarFilled
            v-if="favorId"
            :style="{ color: '#FAD337' }"
            class="instance-detail-header-collect"
            @click="clickCollect"
          />
          <StarOutlined v-else :style="{ color: '#A5A9BC' }" class="instance-detail-header-collect" @click="clickCollect" />

          <a class="instance-detail-header-share" @click="shareCi">
            <ShareAltOutlined />
            {{ t('cmdb.ci.share') }}
          </a>

          <a class="instance-detail-header-resource" @click="goToResourceDetail">
            <DatabaseOutlined />
            {{ t('cmdb.ci.resourceDetail') }}
          </a>
        </div>
      </div>

      <div class="instance-detail-attr">
        <div v-for="group in attributeGroups" :key="group.id" class="instance-detail-attr-group">
          <span class="instance-detail-attr-group-name">{{ group.name || t('other') }}</span>

          <div class="instance-detail-attr-list">
            <div v-for="attr in group.attributes" :key="attr.id" class="instance-detail-attr-item">
              <a-tooltip :title="attr.alias || attr.name || ''">
                <div class="instance-detail-attr-item-label">
                  <span class="instance-detail-attr-item-label-text">
                    {{ attr.alias || attr.name || '' }}
                  </span>
                  <span class="instance-detail-attr-item-label-colon">:</span>
                </div>
              </a-tooltip>

              <div class="instance-detail-attr-item-value">
                <AttrDisplay :attr="attr" :ci="ci" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style lang="less" scoped>
.instance-detail {
  width: 100%;
  height: 100%;
  border-radius: 2px;
  border: 1px solid #e4e7ed;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  position: relative;

  &-hide {
    position: absolute;
    left: 0;
    top: 50%;
    margin-top: -21px;
    border-radius: 0px 2px 2px 0px;
    background-color: #2f54eb;
    width: 13px;
    height: 43px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
    cursor: pointer;

    &-icon {
      color: #ffffff;
      font-size: 12px;
    }

    &:hover {
      background-color: #597ef7;
    }
  }

  &-null {
    display: flex;
    flex-direction: column;
    width: 100%;
    align-items: center;
    padding-top: 100px;

    &-img {
      width: 180px;
    }

    &-text {
      color: #86909c;
      margin-top: 20px;
    }
  }

  &-header {
    width: 100%;
    height: 75px;
    background-color: @primary-color_3;
    overflow: hidden;
    position: relative;
    display: flex;
    align-items: center;
    padding: 0 20px;
    flex-shrink: 0;

    &-line-1 {
      height: 44px;
      width: 300px;
      position: absolute;
      right: -20px;
      top: 0px;
      transform: rotate(40deg);
      background-color: @primary-color_5;
    }

    &-line-2 {
      height: 44px;
      width: 300px;
      position: absolute;
      right: -110px;
      top: 0px;
      transform: rotate(40deg);
      background-color: @primary-color_5;
    }

    &-row {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      position: relative;
      z-index: 2;
    }

    &-title {
      font-size: 16px;
      font-weight: 700;
      color: #1d2129;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      text-wrap: nowrap;
      margin-left: 9px;
    }

    &-collect {
      margin-left: 8px;
      margin-right: 8px;
    }

    &-share {
      margin-left: auto;
      flex-shrink: 0;
    }

    &-resource {
      margin-left: 12px;
      flex-shrink: 0;
    }
  }

  &-attr {
    width: 100%;
    overflow-y: auto;
    height: 100%;
    padding: 20px;

    &-group {
      &:not(:first-child) {
        margin-top: 15px;
      }

      &-name {
        font-size: 14px;
        font-weight: 700;
        color: #1d2129;
      }
    }

    &-item {
      margin-top: 15px;
      display: flex;
      align-items: flex-start;

      &-label {
        font-size: 14px;
        font-weight: 400;
        color: #86909c;
        width: 25%;
        flex-shrink: 0;
        display: flex;
        align-items: center;

        &-text {
          overflow: hidden;
          text-overflow: ellipsis;
          text-wrap: nowrap;
        }

        &-colon {
          flex-shrink: 0;
        }
      }

      &-value {
        margin-left: 12px;
      }
    }
  }
}
</style>
