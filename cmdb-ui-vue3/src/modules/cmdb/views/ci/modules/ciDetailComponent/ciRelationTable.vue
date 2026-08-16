<script setup lang="ts">
import { computed, inject, ref, watch } from 'vue'
import { DeleteOutlined, PlusOutlined, UnorderedListOutlined } from '@ant-design/icons-vue'
import { useI18n } from 'vue-i18n'
import { getCanEditByParentIdChildId } from '@/modules/cmdb/api/CITypeRelation'
import { deleteCIRelationView } from '@/modules/cmdb/api/CIRelation'
import { searchCI } from '@/modules/cmdb/api/ci'
import { getSubscribeAttributes } from '@/modules/cmdb/api/preference'
import { cloneDeep } from '../../../../utils/helper'
import CIDetailTableTitle from './ciDetailTableTitle.vue'

const { t } = useI18n()

const PARENT_KEY = 'parents'
const CHILDREN_KEY = 'children'

const props = withDefaults(
  defineProps<{
    ciId?: number | null
    typeId?: number
    ci?: Record<string, any>
    relationData?: Record<string, any>
  }>(),
  {
    ciId: null,
    typeId: 0,
    ci: () => ({}),
    relationData: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'refreshRelationCI'): void
}>()

const ciTypesProvider = inject<() => any[]>('ci_types', () => [])
const relationViewRefreshNumber = inject<(() => void) | null>('relationViewRefreshNumber', null)

const tabList = ref<any[]>([])
const currentTab = ref('all')
const allCITypes = ref<any[]>([])
const allColumns = ref<Record<string, any[]>>({})
const allJSONAttr = ref<Record<string, string[]>>({})
const allCIList = ref<Record<string, any[]>>({})
const allCanEdit = ref<Record<string, boolean>>({})
const referenceCINameMap = ref<Record<string, Record<string, string>>>({})

function uniqBy<T>(list: T[], key: string): T[] {
  const seen = new Set<unknown>()
  return list.filter((item) => {
    const value = (item as Record<string, any>)?.[key]
    if (seen.has(value)) return false
    seen.add(value)
    return true
  })
}

const tabListFlat = computed(() => tabList.value.reduce((list: any[], group) => list.concat(group.list), []))

const tableIDList = computed(() => {
  const baseKeys =
    currentTab.value === 'all'
      ? tabListFlat.value.filter((item: any) => item.value !== 'all').map((item: any) => item.key)
      : [currentTab.value]

  return baseKeys
    .filter((key) => allCIList.value?.[key]?.length)
    .map((key) => {
      const findTab = tabListFlat.value.find((item: any) => item.key === key) || {}

      let name = findTab?.name || ''
      if (name && findTab?.value === props.ci._type) {
        name = `${findTab?.isParent ? t('cmdb.ci.upstream') : t('cmdb.ci.downstream')} - ${name}`
      }

      return {
        key,
        value: findTab?.value || '',
        name,
        count: findTab?.count || '',
      }
    })
})

watch(
  () => props.relationData,
  (val) => {
    init(val)
  },
  { immediate: true, deep: true }
)

async function init(relationData: Record<string, any>) {
  const ciTypesList = ciTypesProvider()
  const _findCiType = ciTypesList.find((item) => item.id === props.typeId)
  if (!_findCiType) {
    return
  }

  const cloneRelationData = cloneDeep(relationData)

  const ciTypes = uniqBy<any>(
    [...cloneRelationData.parentCITypeList, ...cloneRelationData.childCITypeList],
    'id'
  )
  await handleSubscribeAttributes(ciTypes)

  const { columns: parentColumns, jsonAttr: parentJSONAttr } = handleCITypeList(
    cloneRelationData.parentCITypeList,
    true
  )
  const { columns: childColumns, jsonAttr: childJSONAttr } = handleCITypeList(
    cloneRelationData.childCITypeList,
    false
  )

  allCITypes.value = ciTypes
  allColumns.value = { ...parentColumns, ...childColumns }
  allJSONAttr.value = { ...parentJSONAttr, ...childJSONAttr }

  await getCanEditList(allCITypes.value)

  const [parentCIs, childCIs] = await Promise.all([
    handleCIList(cloneRelationData.parentCIList, true),
    handleCIList(cloneRelationData.childCIList, false),
  ])
  allCIList.value = { ...parentCIs, ...childCIs }

  const list: any[] = []
  list[0] = {
    name: '',
    key: 'all',
    list: [
      {
        name: t('all'),
        key: 'all',
        value: 'all',
        count: Object.values(allCIList.value).reduce((acc, cur) => acc + (cur?.length || 0), 0),
        showAdd: false,
      },
    ],
  }
  list[1] = {
    name: t('cmdb.ci.upstream'),
    key: PARENT_KEY,
    list: buildTabList(cloneRelationData.parentCITypeList, PARENT_KEY, true),
  }
  list[2] = {
    name: t('cmdb.ci.downstream'),
    key: CHILDREN_KEY,
    list: buildTabList(cloneRelationData.childCITypeList, CHILDREN_KEY, false),
  }
  tabList.value = list

  handleReferenceCINameMap()
}

function buildTabList(list: any[], keyPrefix: string, isParent: boolean): any[] {
  return list.map((item) => {
    const key = `${keyPrefix}-${item.id}`
    return {
      name: item?.alias ?? item?.name ?? '',
      key,
      isParent,
      value: item.id,
      count: allCIList.value?.[key]?.length || 0,
      showAdd: allCanEdit.value?.[item.id] ?? false,
    }
  })
}

function handleCITypeList(list: any[], isParent: boolean) {
  const CIColumns: Record<string, any[]> = {}
  const CIJSONAttr: Record<string, string[]> = {}

  list.forEach((item) => {
    const columns: any[] = []
    const jsonAttr: string[] = []

    item.isParent = isParent
    item.attributes.forEach((attr: any) => {
      const column: Record<string, any> = {
        key: 'p_' + attr.id,
        field: attr.name,
        title: attr.alias,
        minWidth: '100px',
        params: { attr },
      }
      if (attr.is_reference) {
        column.slots = { default: 'reference_default' }
      }
      columns.push(column)

      if (attr.value_type === '6') {
        jsonAttr.push(attr.name)
      }
    })
    CIJSONAttr[item.id] = jsonAttr
    CIColumns[item.id] = columns
    CIColumns[item.id].push({
      key: 'p_operation',
      field: 'operation',
      title: t('operation'),
      width: '80px',
      fixed: 'right',
      slots: { default: 'operation_default' },
      align: 'center',
    })
  })

  return { columns: CIColumns, jsonAttr: CIJSONAttr }
}

async function getCanEditList(ciTypes: any[]) {
  const promises = ciTypes.map((ciType) => {
    let parentId = ciType.id
    let childId = props.typeId

    if (!ciType.isParent) {
      parentId = props.typeId
      childId = ciType.id
    }

    return getCanEditByParentIdChildId(parentId, childId).then((res) => {
      return { id: ciType.id, canEdit: res.result }
    })
  })

  const result: Record<string, boolean> = {}
  const res = await Promise.all(promises)
  if (res?.length) {
    res.forEach((item) => {
      result[item.id] = item.canEdit
    })
  }
  allCanEdit.value = result
}

async function handleSubscribeAttributes(ciTypes: any[]) {
  const promises = ciTypes.map((ciType, index) => {
    return getSubscribeAttributes(ciType.id).then((res) => {
      return { ...(res || {}), id: ciType.id, indexInAll: index }
    })
  })
  const res = await Promise.all(promises)

  if (res?.length) {
    res.forEach((item) => {
      if (ciTypes?.[item.indexInAll]?.attributes && item?.is_subscribed) {
        ciTypes[item.indexInAll].attributes = item.attributes
      }
    })
  }

  return ciTypes
}

async function handleCIList(ciList: any[], isParent: boolean) {
  const cis: Record<string, any[]> = {}
  ciList.forEach((item) => {
    allJSONAttr.value[item._type].forEach((attr) => {
      item[`${attr}`] = item[`${attr}`] ? JSON.stringify(item[`${attr}`]) : ''
    })
    formatCI(item)
    item.isParent = isParent
    const CIKey = `${isParent ? PARENT_KEY : CHILDREN_KEY}-${item._type}`

    if (CIKey in cis) {
      cis[CIKey].push(item)
    } else {
      cis[CIKey] = [item]
    }
  })

  return cis
}

function formatCI(ci: any) {
  Object.keys(ci).forEach((key) => {
    const attr = allColumns.value?.[ci?._type]?.find(
      (item: any) => item?.params?.attr?.name === key
    )?.params?.attr
    if (attr?.is_choice && attr?.choice_value?.length) {
      if (attr?.is_list) {
        ci[key] = ci[key].map((value: any) => {
          const label = attr?.choice_value?.find((choice: any) => choice?.[0] === value)?.[1]?.label
          return label || ci[key]
        })
      } else {
        const label = attr?.choice_value?.find((choice: any) => choice?.[0] === ci[key])?.[1]?.label
        ci[key] = label || ci[key]
      }
    }
  })

  return ci
}

async function handleReferenceCINameMap() {
  const map: Record<string, Record<string, string>> = {}
  allCITypes.value.forEach((CIType: any) => {
    const CIKey = `${CIType.isParent ? PARENT_KEY : CHILDREN_KEY}-${CIType.id}`

    CIType.attributes.forEach((attr: any) => {
      if (attr?.is_reference && attr?.reference_type_id) {
        const currentCIList = allCIList.value[CIKey]
        if (currentCIList?.length) {
          currentCIList.forEach((ci: any) => {
            const ids = Array.isArray(ci[attr.name]) ? ci[attr.name] : ci[attr.name] ? [ci[attr.name]] : []

            if (ids.length) {
              if (!map?.[attr.reference_type_id]) {
                map[attr.reference_type_id] = {}
              }
              ids.forEach((id: any) => {
                map[attr.reference_type_id][id] = ''
              })
            }
          })
        }
      }
    })
  })

  if (!Object.keys(map).length) {
    return
  }

  const allRes = await Promise.all(
    Object.keys(map).map((key) => {
      return searchCI({
        q: `_type:${key},_id:(${Object.keys(map[key]).join(';')})`,
        count: 9999,
      })
    })
  )
  const CITypeList = ciTypesProvider()
  const showNameMap: Record<string, any> = {}

  Object.keys(map).forEach((id) => {
    const CIType = CITypeList.find((item) => Number(item.id) === Number(id))
    showNameMap[id] = {
      show_name: CIType?.show_name,
      unique_key: CIType?.unique_key,
    }
  })

  allRes.forEach((res) => {
    res.result.forEach((item: any) => {
      if (map?.[item._type]?.[item._id] === '') {
        const showName = showNameMap?.[item._type]
        map[item._type][item._id] = item?.[showName?.show_name] ?? item?.[showName?.unique_key] ?? ''
      }
    })
  })

  referenceCINameMap.value = map
}

function getReferenceName(id: any, column: any): string {
  const typeId = column?.params?.attr?.reference_type_id
  return referenceCINameMap.value?.[typeId]?.[id] || id
}

function clickTab(key: string) {
  currentTab.value = key
}

function deleteRelation(row: any) {
  const first_ci_id = row?.isParent ? row?._id : props.ciId
  const second_ci_id = row?.isParent ? props.ciId : row?._id

  deleteCIRelationView(first_ci_id, second_ci_id, {}).then(() => {
    refreshTableData()
    if (relationViewRefreshNumber) {
      relationViewRefreshNumber()
    }
  })
}

function openAddModal(tabData: any) {
  // TODO: wire up AddTableModal (relation add modal not yet ported)
  void tabData
}

async function refreshTableData() {
  emit('refreshRelationCI')
}
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <div v-if="allCITypes.length" class="ci-relation-table">
    <CIDetailTableTitle :title="t('cmdb.relation')" />

    <div class="ci-relation-table-wrap">
      <div class="ci-relation-table-tab">
        <div v-for="(group) in tabList" :key="group.key" class="tab-group">
          <div v-if="group.name" class="tab-group-name">
            {{ group.name }}
          </div>
          <div
            v-for="(item) in group.list"
            :key="item.key"
            :class="`tab-item ${item.key === currentTab ? 'tab-item-active' : ''}`"
            :style="{ paddingLeft: item.key === 'all' ? '8px' : '16px' }"
            @click="clickTab(item.key)"
          >
            <span class="tab-item-name">
              <a-tooltip :title="item.name">
                <span class="tab-item-name-text">{{ item.name }}</span>
              </a-tooltip>
              <span v-if="item.count" class="tab-item-name-count">
                ({{ item.count }})
              </span>
            </span>
            <span v-if="item.key === currentTab && item.showAdd" class="tab-item-add" @click="openAddModal(item)">
              <PlusOutlined />
            </span>
          </div>
        </div>
      </div>

      <div class="ci-relation-table-container" v-if="tableIDList.length">
        <div v-for="(item) in tableIDList" :key="item.key" class="ci-relation-table-item">
          <div v-if="currentTab === 'all'" class="ci-relation-table-item-name">
            <span class="ci-relation-table-item-name-text">{{ item.name }}</span>
            <span class="ci-relation-table-item-name-count">({{ item.count }})</span>
          </div>

          <vxe-grid
            bordered
            size="mini"
            :columns="allColumns[item.value]"
            :data="allCIList[item.key]"
            overflow
            show-overflow="tooltip"
            show-header-overflow="tooltip"
            resizable
            class="ops-stripe-table"
            max-height="300px"
          >
            <template #reference_default="{ row, column }">
              <a
                v-for="(id) in (column.params.attr.is_list ? row[column.field] : [row[column.field]])"
                :key="id"
                :href="`/cmdb/cidetail/${column.params.attr.reference_type_id}/${id}`"
                target="_blank"
              >
                {{ getReferenceName(id, column) }}
              </a>
            </template>
            <template #operation_default="{ row }">
              <a-tooltip :title="t('cmdb.ci.detail')">
                <a
                  :href="`/cmdb/cidetail/${item.value}/${row._id}`"
                  target="_blank"
                  :style="{ marginRight: '12px' }"
                >
                  <UnorderedListOutlined />
                </a>
              </a-tooltip>
              <a-popconfirm arrow-point-at-center :title="t('cmdb.ci.confirmDeleteRelation')" @confirm="deleteRelation(row)">
                <a
                  :disabled="!allCanEdit[item.value]"
                  :style="{ color: !allCanEdit[item.value] ? 'rgba(0, 0, 0, 0.25)' : 'red' }"
                >
                  <DeleteOutlined />
                </a>
              </a-popconfirm>
            </template>
          </vxe-grid>
        </div>
      </div>
    </div>

    <!-- TODO: wire up AddTableModal @reload="refreshTableData" -->
  </div>
</template>

<style lang="less" scoped>
.ci-relation-table {
  width: 100%;
  margin-top: 16px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  overflow: hidden;

  &-wrap {
    border: none;
    display: flex;
    width: 100%;
  }

  &-tab {
    flex-shrink: 0;
    width: 180px;
    min-height: 300px;
    max-height: 600px;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 8px 0px;
    border-right: solid 1px #e8eaed;
    background: #f8f9fb;

    .tab-group {
      width: 100%;

      &-name {
        padding-left: 12px;
        height: 32px;
        line-height: 32px;
        width: 100%;
        font-weight: 600;
        font-size: 12px;
        color: @text-color_3;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
    }

    .tab-item {
      height: 36px;
      width: calc(100% - 16px);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-left: 16px;
      padding-right: 10px;
      margin: 2px 8px;
      border-radius: 4px;
      background-color: transparent;
      cursor: pointer;
      transition: all 0.2s ease;
      column-gap: 6px;

      &-name {
        font-size: 13px;
        color: @text-color_1;
        display: flex;
        align-items: baseline;
        max-width: calc(100% - 28px);

        &-text {
          text-overflow: ellipsis;
          text-wrap: nowrap;
          overflow: hidden;
          color: @text-color_2;
        }

        &-count {
          color: @text-color_3;
          font-size: 12px;
          margin-left: 4px;
        }
      }

      &-add {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        background-color: @primary-color;
        display: none;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 12px;
        flex-shrink: 0;
      }

      &-active {
        background-color: @primary-color_6;
        border-left: 3px solid @primary-color;
        padding-left: 13px;

        .tab-item-name-text {
          color: @text-color_1;
          font-weight: 500;
        }
      }

      &:hover {
        background-color: @primary-color_7;

        .tab-item-name-text {
          color: @text-color_1;
        }

        .tab-item-add {
          display: flex;
        }
      }
    }
  }

  &-container {
    width: 100%;
    padding: 20px;
    min-height: 300px;
    background: #ffffff;
    max-height: 600px;
    overflow-y: auto;
    overflow-x: hidden;
  }

  &-item {
    margin-bottom: 20px;

    &:last-child {
      margin-bottom: 0;
    }

    &-name {
      margin-bottom: 12px;
      font-size: 14px;
      font-weight: 600;
      color: @text-color_1;
      display: flex;
      align-items: baseline;
      padding-left: 12px;
      position: relative;

      &::before {
        content: "";
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 14px;
        background: @primary-color;
        border-radius: 2px;
      }

      &-text {
        flex: 1;
      }

      &-count {
        font-size: 12px;
        color: @text-color_3;
        margin-left: 6px;
      }
    }
  }
}
</style>
