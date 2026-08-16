<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, nextTick, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import { InfoCircleOutlined, CopyOutlined, MinusCircleOutlined, PlusCircleOutlined } from '@ant-design/icons-vue'
import { uuidv4 } from '@/utils/uuid'
import { cloneDeep } from '../../utils/helper'
import {
  getCITypeAttributes as fetchADAttributes,
  getCITypeRelations as fetchADRelations,
  postCITypeRelations,
} from '@/modules/cmdb/api/discovery'
import { getCITypeChildren, getCITypeParent } from '@/modules/cmdb/api/CITypeRelation'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'

const props = withDefaults(defineProps<{ CITypeId?: number | null }>(), { CITypeId: null })

const { t } = useI18n()

const relationList = ref<any[]>([])
const ciTypeADTAttributes = ref<any[]>([])
const adtId = ref<number | null>(null)
const relationOptions = ref<any[]>([])

const windowHeight = computed(() => window.innerHeight)

function ciTypeADTNormalizer(node: any) {
  return {
    id: node.value,
    label: node.label,
  }
}

function relationNormalizer(node: any) {
  return {
    id: node.value || t('other'),
    label: node.alias || node.name || t('other'),
    title: node.alias || node.name || t('other'),
    children: node.ci_types,
  }
}

function attrNormalizer(node: any) {
  return {
    id: node.value,
    label: node.alias || node.name,
    title: node.alias || node.name,
  }
}

async function getCITypeAttributes() {
  const res = await fetchADAttributes(props.CITypeId as number)
  const attr = await getCITypeAttributesById(props.CITypeId as number)

  const filterAttr = res.filter((name: any) => {
    const currentAttr = attr?.attributes?.find((item: any) => item?.name === name)
    if (!currentAttr) {
      return true
    }
    return filterAttributes(currentAttr)
  })

  ciTypeADTAttributes.value = filterAttr.map((item: any) => {
    return {
      id: item,
      value: item,
      label: item,
    }
  })
}

async function getCITypeRelationOptions() {
  const childRes = await getCITypeChildren(props.CITypeId as number)
  const parentRes = await getCITypeParent(props.CITypeId as number)
  const options = [...childRes.children, ...parentRes.parents]

  options.forEach((item: any) => {
    item.value = item.id
    item.label = item.alias || item.name
    const attributes = item?.attributes?.filter(
      (attr: any) => !attr.is_password && !attr.is_list && attr.value_type !== '6'
    )
    attributes.forEach((attr: any) => {
      attr.value = attr.id
      attr.label = attr.alias || attr.name
    })
    item.attributes = attributes
  })
  relationOptions.value = options
}

async function getCITypeRelations() {
  fetchADRelations(props.CITypeId as number).then(async (res: any[]) => {
    if (res?.length) {
      const nextRelationList: any[] = []
      res.forEach((item: any) => {
        const attributes =
          relationOptions.value.find((option) => option?.value === item.peer_type_id)?.attributes || []
        nextRelationList.push({
          id: uuidv4(),
          ad_key: item.ad_key,
          peer_type_id: item.peer_type_id,
          peer_attr_id: item.peer_attr_id,
          attributes,
        })
      })
      relationList.value = nextRelationList.length
        ? nextRelationList
        : [
            {
              id: uuidv4(),
              ad_key: undefined,
              peer_type_id: undefined,
              peer_attr_id: undefined,
              attributes: [],
            },
          ]
    } else {
      adtId.value = null
      relationList.value = [
        {
          id: uuidv4(),
          ad_key: undefined,
          peer_type_id: undefined,
          peer_attr_id: undefined,
          attributes: [],
        },
      ]
    }
  })
}

function changeType(item: any) {
  nextTick(() => {
    const peerTypeId = item.peer_type_id
    const attributes = relationOptions.value.find((option) => option?.value === peerTypeId)?.attributes
    item.attributes = attributes.filter((attr: any) => filterAttributes(attr))
    item.peer_attr_id = undefined
  })
}

function addRelation() {
  const nextRelationList = cloneDeep(relationList.value)
  nextRelationList.push({
    id: uuidv4(),
    ad_key: undefined,
    peer_type_id: undefined,
    peer_attr_id: undefined,
    attributes: [],
  })
  relationList.value = nextRelationList
}

function copyRelation(item: any) {
  const nextRelationList = cloneDeep(relationList.value)
  nextRelationList.push({
    ...item,
    id: uuidv4(),
  })
  relationList.value = nextRelationList
}

function deleteRelation(item: any) {
  if (relationList.value.length <= 1) {
    message.error(t('cmdb.ciType.deleteRelationAdTip'))
    return
  }
  const idx = relationList.value.findIndex(({ id }) => item.id === id)
  if (idx > -1) {
    relationList.value.splice(idx, 1)
  }
}

async function handleSave() {
  const relations = relationList.value.map(({ ad_key, peer_attr_id, peer_type_id }) => {
    return {
      ad_key,
      peer_attr_id,
      peer_type_id,
    }
  })
  if (relations.length) {
    await postCITypeRelations(props.CITypeId as number, { relations })
    message.success(t('saveSuccess'))
    getCITypeRelations()
  }
}

function filterAttributes(attr: any) {
  if (attr?.value_type === '2' && !attr?.is_index) {
    return false
  }
  return (
    !attr?.is_password && !attr?.is_list && attr?.value_type !== '6' && !attr?.is_bool && !attr?.is_reference
  )
}

async function init() {
  await getCITypeAttributes()
  await getCITypeRelationOptions()
  getCITypeRelations()
}

init()
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order, vue/v-on-event-hyphenation -->
  <div class="relation-ad" :style="{ height: `${windowHeight - 200}px` }">
    <div class="relation-ad-table-tip">
      <InfoCircleOutlined class="relation-ad-table-tip-icon" />
      <span class="relation-ad-table-tip-text">1. {{ t('cmdb.ciType.relationADTip') }}</span>
      <span class="relation-ad-table-tip-text">2. {{ t('cmdb.ciType.relationADTip2') }}</span>
      <span class="relation-ad-table-tip-text">3. {{ t('cmdb.ciType.relationADTip3') }}</span>
    </div>
    <div class="relation-ad-header">
      <div class="relation-ad-header-left">{{ t('cmdb.ciType.relationADHeader1') }}</div>
      <div class="relation-ad-header-left">{{ t('cmdb.ciType.relationADHeader2') }}</div>
    </div>
    <div class="relation-ad-main">
      <div class="relation-ad-item" v-for="item in relationList" :key="item.id">
        <treeselect
          class="custom-treeselect"
          :style="{ width: '230px', '--custom-height': '32px' }"
          v-model="item.ad_key"
          :multiple="false"
          :clearable="true"
          searchable
          :options="ciTypeADTAttributes"
          value-consists-of="LEAF_PRIORITY"
          :placeholder="t('cmdb.ciType.relationADSelectAttr')"
          :normalizer="ciTypeADTNormalizer"
        >
          <template #option-label="{ node }">
            <div :title="node.label">
              <div>{{ node.label }}</div>
            </div>
          </template>
        </treeselect>
        <div class="relation-ad-item-link">
          <div class="relation-ad-item-link-left"></div>
          <div class="relation-ad-item-link-right"></div>
        </div>
        <treeselect
          class="custom-treeselect"
          :style="{ width: '230px', marginRight: '10px', '--custom-height': '32px' }"
          v-model="item.peer_type_id"
          :multiple="false"
          :clearable="true"
          searchable
          :options="relationOptions"
          value-consists-of="LEAF_PRIORITY"
          :placeholder="t('cmdb.ciType.relationADSelectCIType')"
          :disable-branch-nodes="true"
          @select="changeType(item)"
          :normalizer="relationNormalizer"
        >
          <template #option-label="{ node }">
            <div
              :title="node.label"
              :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }"
            >
              {{ node.label }}
            </div>
          </template>
        </treeselect>
        <treeselect
          class="custom-treeselect"
          :style="{ width: '230px', marginRight: '18px', '--custom-height': '32px' }"
          v-model="item.peer_attr_id"
          :multiple="false"
          :clearable="true"
          searchable
          :options="item.attributes"
          value-consists-of="LEAF_PRIORITY"
          :placeholder="t('cmdb.ciType.relationADSelectModelAttr')"
          :normalizer="attrNormalizer"
        >
          <template #option-label="{ node }">
            <div
              :title="node.label"
              :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }"
            >
              {{ node.label }}
            </div>
          </template>
        </treeselect>
        <div class="relation-ad-item-action">
          <a @click="copyRelation(item)"><CopyOutlined /></a>
          <a @click="deleteRelation(item)"><MinusCircleOutlined /></a>
          <a @click="addRelation"><PlusCircleOutlined /></a>
        </div>
      </div>
      <div class="relation-ad-footer">
        <a-button type="primary" @click="handleSave">{{ t('save') }}</a-button>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.relation-ad {
  overflow: auto;
  padding: 0 20px;

  &-tip {
    color: @text-color_4;
    font-size: 12px;
    font-weight: 400;
    line-height: 22px;
  }

  &-header {
    margin-top: 20px;
    display: flex;
    align-items: center;
    font-size: 14px;
    font-weight: 700;
    line-height: 22px;

    &-left {
      width: 230px;
      margin-right: 63px;
    }
  }

  &-main {
    display: inline-block;
  }

  .relation-ad-item {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    margin-top: 10px;

    &-link {
      position: relative;
      height: 1px;
      width: 63px;
      background-color: @border-color-base;

      &-left {
        position: absolute;
        top: -6px;
        left: -6px;
        z-index: 10;
        width: 12px;
        height: 12px;
        background-color: @primary-color;
        border: solid 3px @primary-color_4;
        border-radius: 50%;
      }

      &-right {
        position: absolute;
        z-index: 10;
        top: -5px;
        right: 0px;
        width: 2px;
        height: 10px;
        border-radius: 1px 0px 0px 1px;
        background-color: @primary-color;
      }
    }

    &-action {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }

  &-table-tip {
    display: inline-flex;
    align-items: center;
    padding: 3px 16px;
    color: @text-color_2;
    font-size: 14px;
    font-weight: 400;
    border: solid 1px @primary-color_8;
    background-color: @primary-color_5;
    border-radius: 2px;

    &-icon {
      font-size: 16px;
      color: @primary-color;
      margin-right: 8px;
    }

    &-text {
      &:not(:last-child) {
        padding-right: 10px;
        margin-right: 10px;
        border-right: solid 1px @primary-color_8;
      }
    }
  }

  &-footer {
    text-align: right;
    margin: 10px 0;
  }
}
</style>
