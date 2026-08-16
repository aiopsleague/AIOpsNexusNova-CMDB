<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { DatabaseOutlined } from '@ant-design/icons-vue'
import { getPreferenceSearch, savePreferenceSearch, getSubscribeAttributes, deletePreferenceSearch } from '@/modules/cmdb/api/preference'
import { searchAttributes, getCITypeAttributesByTypeIds } from '@/modules/cmdb/api/CITypeAttr'
import { searchCI } from '@/modules/cmdb/api/ci'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { SEARCH_MODE } from './constants'

import SearchInput from './components/searchInput.vue'
import HistoryList from './components/historyList.vue'
import InstanceList from './components/instanceList.vue'
import InstanceDetail from './components/instanceDetail.vue'
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

// Filter conditions.
const searchValue = ref('')
const selectCITypeIds = ref<Array<string | number>>([])
const expression = ref('')
const currentSearchValue = ref('')

const recentList = ref<any[]>([])
const favorList = ref<any[]>([])
const allAttributesList = ref<any[]>([])
const originAllAttributesList = ref<any[]>([])

const isSearch = ref(false)
const currentPage = ref(1)
const pageSizeOptions = ref(['50', '100', '200', '100000'])
const pageSize = ref(50)
const totalNumber = ref(0)
const ciTabList = ref<any[]>([])
const instanceList = ref<any[]>([])
const referenceShowAttrNameMap = ref<Record<string, string>>({})
const referenceCIIdMap = ref<Record<string, Record<string, any>>>({})

const showInstanceDetail = ref(false)
const detailCIId = ref<number>(-1)
const detailCITypeId = ref<number>(-1)
const currentSearchMode = ref<string>(SEARCH_MODE.NORMAL)

// The legacy Vue2 shell carried a global search value via `app.cmdbSearchValue`.
// No equivalent store field exists in the Vue3 shell yet.
const cmdbSearchValue = ref('')

const windowHeight = computed(() => window.innerHeight)

watch(cmdbSearchValue, (value) => {
  searchValue.value = value
  saveCondition(true)
})

function isEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
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

onMounted(() => {
  initData()
})

async function initData() {
  await getFavorList()

  nextTick(async () => {
    if (cmdbSearchValue.value) {
      searchValue.value = cmdbSearchValue.value
      saveCondition(true)
    } else {
      await getRecentList()
    }
  })

  await getAllAttr()
}

async function getRecentList() {
  const list = await getPreferenceSearch({
    name: '__recent__',
  })
  list.sort((a: any, b: any) => b.id - a.id)
  recentList.value = list
}

async function getFavorList() {
  const list = await getPreferenceSearch({
    name: '__favor__',
  })
  list.sort((a: any, b: any) => b.id - a.id)
  favorList.value = list
}

async function getAllAttr() {
  const res = await searchAttributes({ page_size: 9999 })
  allAttributesList.value = res.attributes
  originAllAttributesList.value = res.attributes
}

async function updateAllAttributesList(value: Array<string | number>) {
  if (value && value.length) {
    const res = await getCITypeAttributesByTypeIds({ type_ids: value.join(',') })
    allAttributesList.value = res.attributes
  } else {
    allAttributesList.value = originAllAttributesList.value
  }
}

async function saveCondition(isSubmit: boolean) {
  if (searchValue.value || expression.value || selectCITypeIds.value.length) {
    const needDeleteList: Array<string | number> = []
    const differentList: Array<string | number> = []
    recentList.value.forEach((item) => {
      const option = item.option
      if (
        option.searchValue === searchValue.value &&
        option.expression === expression.value &&
        isEqual(option.ciTypeIds, selectCITypeIds.value) &&
        option.searchMode === currentSearchMode.value
      ) {
        needDeleteList.push(item.id)
      } else {
        differentList.push(item.id)
      }
    })
    if (differentList.length >= 10) {
      needDeleteList.push(...differentList.slice(9))
    }
    if (needDeleteList.length) {
      await Promise.all(needDeleteList.map((id) => deletePreferenceSearch(id)))
    }

    const ciTypeNames = selectCITypeIds.value.map((id) => {
      const ciType = props.allCITypes.find((item: any) => item.id === id)
      return ciType?.alias || ciType?.name || id
    })

    await savePreferenceSearch({
      option: {
        searchValue: searchValue.value,
        expression: expression.value,
        ciTypeIds: selectCITypeIds.value,
        ciTypeNames,
        searchMode: currentSearchMode.value,
      },
      name: '__recent__',
    })
    getRecentList()
  }

  if (isSubmit) {
    isSearch.value = true
    currentPage.value = 1
    hideDetail()
    loadInstance()
  }
}

async function deleteRecent(id: string | number) {
  await deletePreferenceSearch(id)
  getRecentList()
}

async function clearRecent() {
  const deletePromises = recentList.value.map((item) => {
    return deletePreferenceSearch(item.id)
  })
  await Promise.all(deletePromises)
  getRecentList()
}

async function loadInstance() {
  const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
  const exp = expression.value.match(regQ) ? expression.value.match(regQ)![0] : null

  const ciTypeIds = [...selectCITypeIds.value]
  if (!ciTypeIds.length) {
    props.CITypeGroup.forEach((item: any) => {
      const ids = item.ci_types.map((ci_type: any) => ci_type.id)
      ciTypeIds.push(...ids)
    })
  }

  let querySearchValue = ''
  if (searchValue.value) {
    if (currentSearchMode.value === SEARCH_MODE.COLUMN && searchValue.value.includes('\n')) {
      const values = searchValue.value.split('\n').filter((v) => v.trim())
      querySearchValue = `,(${values.join(';')})`
    } else {
      querySearchValue = `,*${searchValue.value}*`
    }
  }

  const res = await searchCI({
    q: `${ciTypeIds?.length ? `_type:(${ciTypeIds.join(';')})` : ''}${exp ? `,${exp}` : ''}${querySearchValue}`,
    count: pageSize.value,
    page: currentPage.value,
    sort: '_type',
  })
  currentSearchValue.value = searchValue.value

  totalNumber.value = res?.numfound ?? 0
  if (!res?.result?.length) {
    ciTabList.value = []
    instanceList.value = []
  }

  const ciTabMap = new Map()

  let list = res.result
  list.forEach((item: any) => {
    const ciType = props.allCITypes.find((type: any) => type.id === item._type)
    if (ciTabMap.has(item._type)) {
      ciTabMap.get(item._type).count++
    } else {
      ciTabMap.set(item._type, {
        id: item._type,
        count: 1,
        title: ciType?.alias || ciType?.name || '',
      })
    }
  })

  const mapEntries = [...ciTabMap.entries()]
  const subscribedPromises = mapEntries.map((item: any) => {
    return getSubscribeAttributes(item[0])
  })
  const subscribedRes = await Promise.all(subscribedPromises)
  list = list.map((item: any) => {
    const subscribedIndex = mapEntries.findIndex((mapValue: any) => mapValue[0] === item._type)
    const subscribedAttr = subscribedRes?.[subscribedIndex]?.attributes || []
    const obj: Record<string, any> = {
      ci: item,
      ciTypeObj: {},
      attributes: subscribedAttr,
    }

    const ciType = props.allCITypes.find((type: any) => type.id === item._type)
    obj.ciTypeObj = {
      showAttrName: ciType?.show_name || ciType?.unique_key || '',
      icon: ciType?.icon || '',
      title: ciType?.alias || ciType?.name || '',
      name: ciType?.name || '',
      id: ciType.id,
    }

    return obj
  })

  instanceList.value = list
  const newCiTabList = [...ciTabMap.values()]
  if (list?.length) {
    newCiTabList.unshift({
      id: -1,
      title: t('all'),
      count: list?.length,
    })
  }
  ciTabList.value = newCiTabList

  // Resolve reference attributes.
  const allAttr: any[] = []
  subscribedRes.map((item: any) => {
    allAttr.push(...item.attributes)
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
  instanceList.value.forEach(({ ci }) => {
    needRequiredCIType.forEach((col) => {
      const ids = Array.isArray(ci[col.name]) ? ci[col.name] : ci[col.name] ? [ci[col.name]] : []
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

  allRes.forEach((res: any) => {
    res.result.forEach((item: any) => {
      if (map?.[item._type]?.[item._id]) {
        map[item._type][item._id] = item
      }
    })
  })

  referenceCIIdMap.value = map
}

function clickRecent(data: any) {
  updateAllAttributesList(data.ciTypeIds || [])
  isSearch.value = true
  currentPage.value = 1
  searchValue.value = data?.searchValue || ''
  expression.value = data?.expression || ''
  selectCITypeIds.value = data?.ciTypeIds || []
  currentSearchMode.value = data?.searchMode || 'normal'

  hideDetail()
  loadInstance()
}

function handlePageSizeChange(_: number, nextPageSize: number) {
  pageSize.value = nextPageSize
  currentPage.value = 1
  loadInstance()
}

function changePage(page: number) {
  currentPage.value = page
  loadInstance()
}

function changeFilter(data: { name: string; value: any }) {
  if (data.name === 'searchValue') {
    searchValue.value = data.value
  } else if (data.name === 'selectCITypeIds') {
    selectCITypeIds.value = data.value
  } else if (data.name === 'expression') {
    expression.value = data.value
  }
}

function showDetail(data: { id: string | number; ciTypeId: string | number }) {
  detailCIId.value = Number(data.id)
  detailCITypeId.value = Number(data.ciTypeId)
  showInstanceDetail.value = true
}

function hideDetail() {
  detailCIId.value = -1
  detailCITypeId.value = -1
  showInstanceDetail.value = false
}

async function addCollect(data: Record<string, any>) {
  if (favorList.value.length >= 10) {
    const deletePromises = favorList.value.slice(9).map((item) => {
      return deletePreferenceSearch(item.id)
    })
    await Promise.all(deletePromises)
  }
  await savePreferenceSearch({
    option: {
      ...data,
    },
    name: '__favor__',
  })
  getFavorList()
}

async function deleteCollect(id: string | number) {
  await deletePreferenceSearch(id)
  getFavorList()
}

function clickFavor(data: any) {
  isSearch.value = true
  showDetail(data)
}

function updateSearchMode(mode: string) {
  currentSearchMode.value = mode
}
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <div class="resource-search" :style="{ height: `${windowHeight - 131}px` }">
    <div v-if="!isSearch" class="resource-search-before">
      <div class="resource-search-title">
        <DatabaseOutlined class="resource-search-title-icon" />
        <span class="resource-search-title-text">{{ t('cmdb.ciType.resourceSearch') }}</span>
      </div>
      <SearchInput
        :c-i-type-group="CITypeGroup"
        :all-attributes-list="allAttributesList"
        :search-value="searchValue"
        :select-c-i-type-ids="selectCITypeIds"
        :expression="expression"
        :search-mode="currentSearchMode"
        @change-filter="changeFilter"
        @update-all-attributes-list="updateAllAttributesList"
        @save-condition="saveCondition"
        @update-search-mode="updateSearchMode"
      />
      <HistoryList
        :recent-list="recentList"
        :favor-list="favorList"
        :detail-c-i-id="detailCIId"
        @click-recent="clickRecent"
        @delete-recent="deleteRecent"
        @clear-recent="clearRecent"
        @delete-collect="deleteCollect"
        @show-detail="clickFavor"
      />

      <img class="resource-search-before-bg" :src="resourceSearchBg1" />
    </div>

    <div v-else class="resource-search-after">
      <div class="resource-search-after-left" :style="{ width: showInstanceDetail ? '70%' : '100%' }">
        <SearchInput
          class-type="after"
          :c-i-type-group="CITypeGroup"
          :all-attributes-list="allAttributesList"
          :search-value="searchValue"
          :select-c-i-type-ids="selectCITypeIds"
          :expression="expression"
          :search-mode="currentSearchMode"
          @change-filter="changeFilter"
          @update-all-attributes-list="updateAllAttributesList"
          @save-condition="saveCondition"
          @update-search-mode="updateSearchMode"
        />
        <HistoryList
          :recent-list="recentList"
          :favor-list="favorList"
          :detail-c-i-id="detailCIId"
          @click-recent="clickRecent"
          @delete-recent="deleteRecent"
          @clear-recent="clearRecent"
          @delete-collect="deleteCollect"
          @show-detail="clickFavor"
        />
        <div class="resource-search-divider"></div>
        <InstanceList
          :list="instanceList"
          :tab-list="ciTabList"
          :reference-show-attr-name-map="referenceShowAttrNameMap"
          :reference-c-i-id-map="referenceCIIdMap"
          :favor-list="favorList"
          :detail-c-i-id="detailCIId"
          :search-value="currentSearchValue"
          @show-detail="showDetail"
          @add-collect="addCollect"
          @delete-collect="deleteCollect"
        />

        <div class="resource-search-pagination">
          <a-pagination
            show-size-changer
            :current="currentPage"
            size="small"
            :total="totalNumber"
            show-quick-jumper
            :page-size="pageSize"
            :page-size-options="pageSizeOptions"
            @show-size-change="handlePageSizeChange"
            :show-total="(total: number, range: number[]) => t('pagination.total', { range0: range[0], range1: range[1], total })"
            @change="changePage"
          >
            <template #buildOptionText="{ value }">
              <span v-if="value !== '100000'">{{ value }}{{ t('itemsPerPage') }}</span>
              <span v-if="value === '100000'">{{ t('all') }}</span>
            </template>
          </a-pagination>
        </div>
      </div>

      <div v-if="showInstanceDetail" class="resource-search-after-right">
        <InstanceDetail
          :c-i-id="detailCIId"
          :c-i-type-id="detailCITypeId"
          :favor-list="favorList"
          @add-collect="addCollect"
          @delete-collect="deleteCollect"
          @hide-detail="hideDetail"
        />
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.resource-search {
  width: 100%;
  height: 100%;
  position: relative;

  &-before {
    width: 100%;
    max-width: 718px;
    height: 100%;
    margin: 0 auto;
    padding-top: 100px;
    display: flex;
    flex-direction: column;
    align-items: center;

    & > div {
      position: relative;
      z-index: 1;
    }

    &-bg {
      position: absolute;
      left: -24px;
      bottom: -24px;
      width: calc(100% + 48px);
      z-index: 0;
    }
  }

  &-title {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 25px;

    &-icon {
      font-size: 28px;
    }

    &-text {
      margin-left: 10px;
      font-size: 20px;
      font-weight: 700;
      color: #1d2129;
    }
  }

  &-after {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: space-between;

    &-left {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;

      & > div {
        flex-shrink: 0;
      }
    }

    &-right {
      margin-left: 20px;
      width: calc(30% - 20px);
      flex-shrink: 0;
    }
  }

  &-divider {
    width: 100%;
    height: 1px;
    background-color: #e4e7ed;
    margin: 20px 0;
  }

  &-pagination {
    text-align: right;
    margin: 12px 0px;
  }
}
</style>
