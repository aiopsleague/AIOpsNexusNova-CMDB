<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ApartmentOutlined, DownOutlined } from '@ant-design/icons-vue'
import { getCITypeAttributesByTypeIds } from '@/modules/cmdb/api/CITypeAttr'
import { getRecursive_level2children, getCITypeRelationPath } from '@/modules/cmdb/api/CITypeRelation'
import { searchCIRelationPath } from '@/modules/cmdb/api/CIRelation'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { getSubscribeAttributes } from '@/modules/cmdb/api/preference'
import { searchCI } from '@/modules/cmdb/api/ci'

import SearchCondition from './components/searchCondition.vue'
import CITable from './components/ciTable.vue'
import resourceSearchBg1 from '@/modules/cmdb/assets/resourceSearch/resource_search_bg_1.png'

const props = withDefaults(
  defineProps<{
    CITypeGroup?: any[]
    allCITypes?: any[]
  }>(),
  {
    CITypeGroup: () => [],
    allCITypes: () => [],
  }
)

const { t } = useI18n()

const relationSearchRef = ref<HTMLElement>()

const isSearch = ref(false)
const isHideSearchCondition = ref(false)
const isWatchData = ref(true)
const isSearchLoading = ref(false)

const sourceCIType = ref<number | undefined>(undefined)
const sourceCITypeSearchValue = ref('')
const sourceAllAttributesList = ref<any[]>([])
const sourceExpression = ref('')

const targetCITypes = ref<Array<string | number>>([])
const targetCITypeGroup = ref<Record<string, any>>({})
const targetAllAttributesList = ref<any[]>([])
const targetExpression = ref('')

const returnPath = ref(true)
const allPath = ref<any[]>([])
const selectedPath = ref<string[]>([])

// Table state.
const page = ref(1)
const pageSize = ref(50)
const pageSizeOptions = ref(['50', '100', '200'])
const allTableData = ref<Record<string, any>>({})
const totalNumber = ref(0)
const tableTabActive = ref('')
const referenceShowAttrNameMap = ref<Record<string, string>>({})
const referenceCIIdMap = ref<Record<string, Record<string, any>>>({})

const windowHeight = computed(() => window.innerHeight)

const watchParams = computed(() => ({
  sourceCIType: sourceCIType.value,
  targetCITypes: targetCITypes.value,
}))

function uniq<T>(arr: T[]): T[] {
  return Array.from(new Set(arr))
}

function uniqBy(arr: any[], key: string): any[] {
  const seen = new Set()
  return arr.filter((item) => {
    const k = item?.[key]
    if (seen.has(k)) {
      return false
    }
    seen.add(k)
    return true
  })
}

/** Compute a rough pixel width for a value (mirrors the legacy helper `strLength`). */
function strLength(fData: any): number {
  if (!fData) {
    return 0
  }
  if (fData.length && typeof fData === 'object') {
    fData = fData.join(' ')
  }
  let intLength = 0
  for (let i = 0; i < fData.length; i++) {
    if (fData.charCodeAt(i) < 0 || fData.charCodeAt(i) > 255) {
      intLength += 2
    } else {
      intLength += 1
    }
  }
  return Math.floor(intLength * 7)
}

watch(
  () => sourceCIType.value,
  (id) => {
    if (isWatchData.value) {
      sourceExpression.value = ''

      targetCITypes.value = []
      targetAllAttributesList.value = []
      targetExpression.value = ''

      selectedPath.value = []

      getTargetCITypeGroup(id)
      updateSourceAllAttributesList(id)
    }
  },
  { immediate: true, deep: true }
)

watch(
  () => targetCITypes.value,
  (ids) => {
    if (isWatchData.value) {
      selectedPath.value = []
      targetExpression.value = ''
      updateTargetAllAttributesList(ids)
    }
  },
  { immediate: true, deep: true }
)

watch(
  watchParams,
  (data) => {
    if (isWatchData.value) {
      updateAllPath(data)
    }
  },
  { immediate: true, deep: true }
)

function changeData(data: { name: string; value: any }) {
  switch (data.name) {
    case 'sourceCIType':
      sourceCIType.value = data.value
      break
    case 'sourceCITypeSearchValue':
      sourceCITypeSearchValue.value = data.value
      break
    case 'sourceExpression':
      sourceExpression.value = data.value
      break
    case 'targetCITypes':
      targetCITypes.value = data.value
      break
    case 'targetExpression':
      targetExpression.value = data.value
      break
    case 'selectedPath':
      selectedPath.value = data.value
      break
    case 'returnPath':
      returnPath.value = data.value
      break
  }
}

async function updateSourceAllAttributesList(id: number | undefined) {
  if (id) {
    const res = await getCITypeAttributesByTypeIds({ type_ids: id })
    sourceAllAttributesList.value = res.attributes
  } else {
    sourceAllAttributesList.value = []
  }
}

async function getTargetCITypeGroup(id: number | undefined) {
  let targetGroup: Record<string, any> = {}
  if (id) {
    const res = await getRecursive_level2children(id)
    targetGroup = res
  }
  targetCITypeGroup.value = targetGroup
}

async function updateTargetAllAttributesList(ids: Array<string | number>) {
  if (ids?.length) {
    const res = await getCITypeAttributesByTypeIds({ type_ids: ids.join(',') })
    targetAllAttributesList.value = res.attributes
  } else {
    targetAllAttributesList.value = []
  }
}

async function updateAllPath(data: { sourceCIType: number | undefined; targetCITypes: Array<string | number> }) {
  let pathList: any[] = []
  if (data.sourceCIType && data?.targetCITypes?.length) {
    const params = {
      source_type_id: data.sourceCIType,
      target_type_ids: data.targetCITypes.join(','),
    }

    const res = await getCITypeRelationPath(params)

    if (res?.paths?.length) {
      const sourceCITypeItem = props.allCITypes.find((ciType: any) => ciType.id === data.sourceCIType)
      const sourceCITypeName = sourceCITypeItem?.alias || sourceCITypeItem?.name || ''
      const targetCITypeList = Object.values(targetCITypeGroup.value).reduce(
        (acc: any[], cur: any) => acc.concat(cur),
        []
      )

      pathList = res.paths.map((ids: any[]) => {
        const [sourceId, ...targetIds] = ids
        const pathNames = [sourceCITypeName]

        targetIds.forEach((id: any) => {
          const ciType = targetCITypeList.find((item: any) => item.id === id)
          if (ciType) {
            pathNames.push(ciType.alias || ciType.name)
          }
        })

        return {
          value: ids.join(','),
          sourceId,
          targetIds,
          pathNames: pathNames.join('-'),
        }
      })
    }
  }

  allPath.value = pathList
}

async function loadCI() {
  isSearchLoading.value = true

  const path = selectedPath.value.map((item) => {
    return item?.split(',')?.map((id) => Number(id)) || []
  })

  const params: Record<string, any> = {
    page: page.value,
    page_size: pageSize.value,
    source: {
      type_id: sourceCIType.value,
    },
    target: {
      type_ids: targetCITypes.value,
    },
    path,
  }

  const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
  const sourceExp = sourceExpression.value.match(regQ) ? sourceExpression.value.match(regQ)![0] : null
  const targetExp = targetExpression.value.match(regQ) ? targetExpression.value.match(regQ)![0] : null
  const sourceSearch = `${sourceExp ? `${sourceExp}` : ''}${sourceCITypeSearchValue.value ? `,*${sourceCITypeSearchValue.value}*` : ''}`

  if (sourceSearch) {
    params.source.q = sourceSearch
  }
  if (targetExp) {
    params.target.q = targetExp
  }

  let res: Record<string, any> = {}
  const tableData: Record<string, any> = {}
  const typeId2Attr: Record<string, any> = {}
  let pathKeyList: string[] = []

  try {
    res = await searchCIRelationPath(params)

    pathKeyList = Object.keys(res.paths)
    const filterAllPath = allPath.value.filter((pathItem: any) => pathKeyList.includes(pathItem.pathNames))
    const typeIds = uniq(
      filterAllPath.map((item: any) => item?.targetIds?.[item?.targetIds?.length - 1])
    )

    const promises = typeIds.map((id) => {
      return getSubscribeAttributes(id)
    })
    const subscribedRes = await Promise.all(promises)
    typeIds.forEach((id, index) => {
      const attrList = subscribedRes?.[index]?.attributes || []
      typeId2Attr[id] = attrList
    })
  } catch {
    isSearchLoading.value = false
    allTableData.value = {}
    totalNumber.value = 0
    tableTabActive.value = ''
    return
  }

  pathKeyList.forEach((key) => {
    const pathObj = allPath.value.find((pathItem: any) => pathItem.pathNames === key)

    const pathIdList = pathObj?.value?.split(',') || []
    const pathNameList = key?.split('-') || []

    const pathList = pathNameList.map((name, index) => {
      let relation = ''
      if (index < pathNameList.length - 1) {
        const targetName = pathNameList[index + 1]
        const sourceRelation = res?.relation_types?.[name]

        if (sourceRelation) {
          if (Object.keys(sourceRelation)?.includes?.(targetName)) {
            relation = sourceRelation?.[targetName] || ''
          }
        }
      }

      return {
        id: pathIdList?.[index] || '',
        name,
        relation,
      }
    })

    tableData[key] = {
      key,
      count: res.paths?.[key]?.length || 0,
      pathList,
      ciAttr: [],
      ciList: [],
    }

    if (pathObj) {
      const firstIds = res?.paths?.[key]?.[0]
      const targetId = firstIds[firstIds.length - 1]
      const ciTypeId = (res?.id2ci?.[targetId] || {})?._type
      if (ciTypeId) {
        tableData[key].ciAttr = typeId2Attr[ciTypeId]
      }

      tableData[key].ciList = res.paths[key].map((ids: any[]) => {
        const pathCI: Record<string, any> = {}
        ids.map((id) => {
          const ci = res?.id2ci?.[id] || {}
          const showAttr = res?.type2show_key?.[ci._type] || ''
          pathCI[ci._type] = ci?.[showAttr] ?? ''
        })

        const targetId = ids[ids.length - 1]
        const targetCI = res?.id2ci?.[targetId] || {}

        return {
          pathCI,
          targetCI,
        }
      })

      let totalWidth = 0
      tableData[key].ciAttr.forEach((attr: any) => {
        const lengthList = tableData[key].ciList.map(({ targetCI }: any) => {
          return strLength(targetCI[attr.name])
        })

        attr.width = Math.round(Math.min(Math.max(100, ...lengthList), 350))
        totalWidth += attr.width
      })

      // CI table width = container width - path column width - checkbox width.
      const wrapWidth =
        (relationSearchRef.value?.clientWidth ?? 0) - (tableData?.[key]?.pathList.length || 0) * 160 - 60

      if (wrapWidth && totalWidth < wrapWidth) {
        tableData[key].ciAttr.forEach((attr: any) => {
          delete attr.width
        })
      }
    }
  })

  allTableData.value = tableData
  totalNumber.value = res?.numfound ?? 0
  tableTabActive.value = Object.keys(tableData)?.[0] || ''
  isSearch.value = true
  isSearchLoading.value = false

  const allAttr: any[] = []
  Object.values(typeId2Attr).map((attrList: any) => {
    allAttr.push(...attrList)
  })
  handlePerference(uniqBy(allAttr, 'id'))
}

function handlePerference(allAttr: any[]) {
  let needRequiredCIType: any[] = []
  allAttr.forEach((attr) => {
    if (attr?.is_reference && attr?.reference_type_id) {
      needRequiredCIType.push(attr)
    }
  })
  needRequiredCIType = uniqBy(needRequiredCIType, 'id')

  if (!needRequiredCIType.length) {
    referenceShowAttrNameMap.value = {}
    referenceCIIdMap.value = {}
    return
  }

  handleReferenceShowAttrName(needRequiredCIType)
  handleReferenceCIIdMap(needRequiredCIType)
}

async function handleReferenceShowAttrName(needRequiredCIType: any[]) {
  const res = await getCITypes({
    type_ids: needRequiredCIType.map((col) => col.reference_type_id).join(','),
  })

  const map: Record<string, string> = {}
  res.ci_types.forEach((ciType: any) => {
    map[ciType.id] = ciType?.show_name || ciType?.unique_name || ''
  })

  referenceShowAttrNameMap.value = map
}

async function handleReferenceCIIdMap(needRequiredCIType: any[]) {
  const map: Record<string, Record<string, any>> = {}

  Object.values(allTableData.value).forEach((item: any) => {
    const ciList = item?.ciList || []
    ciList.forEach(({ targetCI }: any) => {
      needRequiredCIType.forEach((col) => {
        const ids = Array.isArray(targetCI[col.name])
          ? targetCI[col.name]
          : targetCI[col.name]
            ? [targetCI[col.name]]
            : []
        if (ids.length) {
          if (!map?.[col.reference_type_id]) {
            map[col.reference_type_id] = {}
          }
          ids.forEach((id: any) => {
            map[col.reference_type_id][id] = {}
          })
        }
      })
    })
  })

  if (!Object.keys(map).length) {
    referenceCIIdMap.value = {}
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

  allRes.forEach((resItem: any) => {
    resItem.result.forEach((item: any) => {
      if (map?.[item._type]?.[item._id]) {
        map[item._type][item._id] = item
      }
    })
  })

  referenceCIIdMap.value = map
}

function handlePageSizeChange(_: number, nextPageSize: number) {
  pageSize.value = nextPageSize
  page.value = 1
  loadCI()
}

function changePage(nextPage: number) {
  page.value = nextPage
  loadCI()
}

function handleSearch() {
  page.value = 1
  loadCI()
}

function clickFavor(option: Record<string, any>) {
  isWatchData.value = false

  nextTick(async () => {
    sourceCIType.value = option?.sourceCIType || undefined
    sourceCITypeSearchValue.value = option?.searchValue || ''
    sourceExpression.value = option?.sourceExpression || ''
    targetCITypes.value = option?.targetCITypes || []
    targetExpression.value = option?.targetExpression || ''
    selectedPath.value = option?.selectedPath || []

    await Promise.all([
      getTargetCITypeGroup(sourceCIType.value),
      updateSourceAllAttributesList(sourceCIType.value),
      updateTargetAllAttributesList(targetCITypes.value),
    ])
    await updateAllPath({
      sourceCIType: sourceCIType.value,
      targetCITypes: targetCITypes.value,
    })

    isWatchData.value = true
    page.value = 1

    loadCI()
  })
}
</script>

<template>
  <div ref="relationSearchRef" class="relation-search" :style="{ height: `${windowHeight - 131}px` }">
    <div class="relation-search-wrap">
      <div v-if="!isSearch" class="relation-search-title">
        <ApartmentOutlined class="relation-search-title-icon" />
        <div class="relation-search-title-text">{{ t('cmdb.relationSearch.relationSearch') }}</div>
      </div>

      <div v-if="isHideSearchCondition" class="relation-search-expand">
        <div class="relation-search-expand-line"></div>

        <div class="relation-search-expand-right">
          <div class="relation-search-expand-handle" @click="isHideSearchCondition = false">
            <DownOutlined class="relation-search-expand-icon" />
          </div>
          <div class="relation-search-expand-text" @click="isHideSearchCondition = false">
            {{ t('cmdb.relationSearch.expandCondition') }}
          </div>
        </div>
      </div>

      <SearchCondition
        v-else
        :c-i-type-group="CITypeGroup"
        :source-c-i-type="sourceCIType"
        :source-c-i-type-search-value="sourceCITypeSearchValue"
        :source-all-attributes-list="sourceAllAttributesList"
        :source-expression="sourceExpression"
        :target-c-i-types="targetCITypes"
        :target-c-i-type-group="targetCITypeGroup"
        :target-all-attributes-list="targetAllAttributesList"
        :target-expression="targetExpression"
        :return-path="returnPath"
        :all-path="allPath"
        :selected-path="selectedPath"
        :is-search="isSearch"
        :is-search-loading="isSearchLoading"
        @change-data="changeData"
        @search="handleSearch"
        @hide-search-condition="isHideSearchCondition = true"
        @click-favor="clickFavor"
      />

      <div v-if="isSearch" class="relation-search-main">
        <CITable
          :all-table-data="allTableData"
          :tab-active="tableTabActive"
          :return-path="returnPath"
          :is-hide-search-condition="isHideSearchCondition"
          :reference-show-attr-name-map="referenceShowAttrNameMap"
          :reference-c-i-id-map="referenceCIIdMap"
          :search-value="sourceCITypeSearchValue"
          :is-search-loading="isSearchLoading"
          @update-tab="(tab: string) => (tableTabActive = tab)"
        />

        <div class="relation-search-pagination">
          <a-pagination
            show-size-changer
            :current="page"
            size="small"
            :total="totalNumber"
            show-quick-jumper
            :page-size="pageSize"
            :page-size-options="pageSizeOptions"
            :show-total="(total: number, range: number[]) => t('pagination.total', { range0: range[0], range1: range[1], total })"
            @show-size-change="handlePageSizeChange"
            @change="changePage"
          >
            <template #buildOptionText="{ value }">
              <span v-if="value !== '100000'">{{ value }}{{ t('itemsPerPage') }}</span>
              <span v-if="value === '100000'">{{ t('all') }}</span>
            </template>
          </a-pagination>
        </div>
      </div>
    </div>

    <img v-if="!isSearch" class="relation-search-bg" :src="resourceSearchBg1" />
  </div>
</template>

<style lang="less" scoped>
.relation-search {
  width: 100%;
  height: 100%;
  position: relative;

  &-wrap {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    z-index: 1;
  }

  &-title {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 30px;
    margin-top: 100px;

    &-icon {
      font-size: 28px;
      margin-right: 10px;
    }

    &-text {
      font-size: 20px;
      font-weight: 700;
      color: #1d2129;
    }
  }

  &-expand {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;

    &-line {
      width: 650px;
      height: 1px;
      background-color: #e4e7ed;
    }

    &-icon {
      font-size: 12px;
      color: #86909c;
    }

    &-text {
      margin-left: 5px;
      font-size: 12px;
      font-weight: 400;
      color: #a5a9bc;
    }

    &-handle {
      width: 14px;
      height: 14px;
      background-color: #ebeff8;
      border-radius: 1px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    &-right {
      flex-shrink: 0;
      display: flex;
      align-items: center;
      cursor: pointer;

      &:hover {
        .relation-search-expand-handle {
          background-color: @primary-color_4;
        }

        .relation-search-expand-icon {
          color: @primary-color;
        }

        .relation-search-expand-text {
          color: @primary-color;
        }
      }
    }
  }

  &-bg {
    position: absolute;
    left: -24px;
    bottom: -24px;
    width: calc(100% + 48px);
    z-index: 0;
  }

  &-main {
    width: calc(100% + 48px);
    background-color: #ffffff;
    padding: 24px;
  }

  &-pagination {
    text-align: right;
    margin-top: 12px;
  }
}
</style>
