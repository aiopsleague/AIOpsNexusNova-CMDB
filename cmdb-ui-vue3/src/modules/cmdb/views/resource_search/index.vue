<script setup lang="ts">
import { computed, nextTick, onMounted, provide, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { AppstoreOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import SearchForm from '@/modules/cmdb/components/searchForm/SearchForm.vue'
import { searchCI } from '@/modules/cmdb/api/ci'
import { searchAttributes, getCITypeAttributesByTypeIds, getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { getCITypes, getCIType } from '@/modules/cmdb/api/CIType'
import { getSubscribeAttributes } from '@/modules/cmdb/api/preference'
import { getCITableColumns } from '@/modules/cmdb/utils/helper'
import EditAttrsPopover from '@/modules/cmdb/views/ci/modules/editAttrsPopover.vue'
import PasswordField from '@/modules/cmdb/components/passwordField/index.vue'
import CiFileField from '@/modules/cmdb/components/CiFileField.vue'
import BatchDownload from '@/modules/cmdb/components/batchDownload/batchDownload.vue'
import PreferenceSearch from '@/modules/cmdb/components/preferenceSearch/preferenceSearch.vue'
import dataEmptyImg from '@/assets/data_empty.png'

const props = withDefaults(
  defineProps<{
    fromCronJob?: boolean
    typeId?: number | null
    type?: string
  }>(),
  {
    fromCronJob: false,
    typeId: null,
    type: 'resourceSearch',
  }
)

const emit = defineEmits<{
  (e: 'copySuccess', text: string): void
}>()

const { t } = useI18n()

const searchRef = ref<any>()
const xTableRef = ref<any>()
const preferenceSearchRef = ref<any>()
const batchDownloadRef = ref<any>()

const ciTypes = ref<any[]>([])
const originAllAttributesList = ref<any[]>([])
const allAttributesList = ref<any[]>([])
const currentPage = ref(1)
const pageSizeOptions = ref(['50', '100', '200', '100000'])
const pageSize = ref(50)
const totalNumber = ref(0)
const instanceList = ref<any[]>([])
const sortByTable = ref<string | undefined>(undefined)
const loading = ref(false)
const columnsGroup = ref<any[]>([])
const referenceShowAttrNameMap = ref<Record<string, string>>({})
const referenceCIIdMap = ref<Record<string, Record<string, any>>>({})

const windowHeight = computed(() => window.innerHeight)

function setPreferenceSearchCurrent(id: number | null = null) {
  if (preferenceSearchRef.value) {
    preferenceSearchRef.value.currentPreferenceSearch = id
  }
}

provide('setPreferenceSearchCurrent', setPreferenceSearchCurrent)
provide('filterCompPreferenceSearch', () => ({}))

onMounted(() => {
  if (props.typeId) {
    getCITypeData(props.typeId)
    getAttrsByType(props.typeId)
    loadInstance()
  } else {
    getAllAttr()
    getAllCiTypes()
  }
})

function getAllCiTypes() {
  getCITypes().then((res) => {
    ciTypes.value = res.ci_types
  })
}

async function getCITypeData(typeId: number) {
  await getCIType(typeId).then((res) => {
    ciTypes.value = res.ci_types
  })
}

async function getAttrsByType(typeId: number) {
  await getCITypeAttributesById(typeId).then((res) => {
    allAttributesList.value = res.attributes
    originAllAttributesList.value = res.attributes
  })
}

async function getAllAttr() {
  await searchAttributes({ page_size: 9999 }).then((res) => {
    allAttributesList.value = res.attributes
    originAllAttributesList.value = res.attributes
  })
}

async function updateAllAttributesList(value: unknown) {
  const ids = value as Array<string | number>
  if (ids && ids.length) {
    await getCITypeAttributesByTypeIds({ type_ids: ids.join(',') }).then((res) => {
      allAttributesList.value = res.attributes
    })
  } else {
    allAttributesList.value = originAllAttributesList.value
  }
}

async function loadInstance(sortBy?: string) {
  loading.value = true
  const fuzzySearch = searchRef.value?.fuzzySearch
  const expression = searchRef.value?.expression || ''
  const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
  const regSort = /(?<=sort=).+/g

  const exp = expression.match(regQ) ? expression.match(regQ)![0] : null
  let sort
  if (sortBy) {
    sort = sortBy
  } else {
    sort = expression.match(regSort) ? expression.match(regSort)![0] : undefined
  }
  if (!sort) {
    sort = '_type'
  }
  let currenCiType = searchRef.value?.currenCiType || []
  if (!currenCiType.length) {
    const _currenCiType: Array<string | number> = []
    ;(searchRef.value?.ciTypeGroup || []).forEach((item: any) => {
      _currenCiType.push(...item.ci_types.map((type: any) => type.id))
    })
    currenCiType = _currenCiType
  }
  searchCI({
    q: `${currenCiType && currenCiType.length ? `_type:(${currenCiType.join(';')})` : ''}${exp ? `,${exp}` : ''}${
      fuzzySearch ? `,*${fuzzySearch}*` : ''
    }`,
    count: pageSize.value,
    page: currentPage.value,
    sort,
  })
    .then(async (res) => {
      columnsGroup.value = []
      instanceList.value = []
      totalNumber.value = res['numfound']
      if (!res['numfound']) {
        return
      }
      const { attributes: resAllAttributes } = await getCITypeAttributesByTypeIds({
        type_ids: Object.keys(res.counter).join(','),
      })
      const _columnsGroup: any[] = Object.keys(res.counter).map((key) => {
        const _find = ciTypes.value.find((item) => item.name === key)
        return {
          id: `parent-${_find.id}`,
          value: key,
          label: _find?.alias || _find?.name,
          isCiType: true,
        }
      })
      const ciTypeAttribute: Record<string, any> = {}
      const promises = _columnsGroup.map((item) => {
        return getCITypeAttributesById(item.id.split('-')[1]).then((res) => {
          ciTypeAttribute[item.label] = res.attributes
        })
      })
      await Promise.all(promises)

      const outputKeys: Record<string, string> = {}
      resAllAttributes.forEach((attr: any) => {
        outputKeys[attr.name] = ''
      })

      const common: Record<string, Record<string, string>> = {}
      Object.keys(outputKeys).forEach((key) => {
        Object.entries(ciTypeAttribute).forEach(([type, attrs]) => {
          if ((attrs as any[]).find((a) => a.name === key)) {
            if (key in common) {
              common[key][type] = ''
            } else {
              common[key] = { [type]: '' }
            }
          }
        })
      })

      const commonObject: Record<string, string[]> = {}
      const commonKeys: string[] = []
      Object.keys(common).forEach((key) => {
        if (Object.keys(common[key]).length > 1) {
          commonKeys.push(key)
          const reverseKey = Object.keys(common[key]).join('&')
          if (!commonObject[reverseKey]) {
            commonObject[reverseKey] = [key]
          } else {
            commonObject[reverseKey].push(key)
          }
        }
      })
      const _commonColumnsGroup = Object.keys(commonObject).map((key) => {
        return {
          id: `parent-${key}`,
          value: key,
          label: key,
          children: getColumns(
            res.result,
            commonObject[key].map((item) => {
              const _find = allAttributesList.value.find((attr) => attr.name === item)
              return _find
            })
          ),
        }
      })

      const promises1 = _columnsGroup.map((item) => {
        return getSubscribeAttributes(item.id.split('-')[1]).then((res1) => {
          item.children = getColumns(res.result, res1.attributes).filter((col) => !commonKeys.includes(col.field))
        })
      })
      await Promise.all(promises1).then(() => {
        columnsGroup.value = [..._commonColumnsGroup, ..._columnsGroup]
        instanceList.value = res['result']
        handlePerference()
      })
    })
    .finally(() => {
      loading.value = false
    })
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

function handlePerference() {
  let needRequiredCIType: any[] = []
  columnsGroup.value.forEach((group) => {
    ;(group.children || []).forEach((col: any) => {
      if (col?.is_reference && col?.reference_type_id) {
        needRequiredCIType.push(col)
      }
    })
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
  instanceList.value.forEach((row) => {
    needRequiredCIType.forEach((col) => {
      const ids = Array.isArray(row[col.field]) ? row[col.field] : row[col.field] ? [row[col.field]] : []
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

  allRes.forEach((res) => {
    res.result.forEach((item: any) => {
      if (map?.[item._type]?.[item._id]) {
        map[item._type][item._id] = item
      }
    })
  })

  referenceCIIdMap.value = map
}

function getReferenceAttrValue(id: any, col: Record<string, any>): string {
  const ci = referenceCIIdMap.value?.[col?.reference_type_id]?.[id]
  if (!ci) {
    return id
  }

  const attrName = referenceShowAttrNameMap.value?.[col.reference_type_id]
  return ci?.[attrName] || id
}

function getColumns(data: any[], attrList: any[]) {
  const el = document.getElementById('resource_search')
  const width = el ? el.clientWidth - 50 : 1600
  return getCITableColumns(data, attrList, width).map((item) => {
    return { ...item, id: item.field, label: item.title }
  })
}

async function handleSearch() {
  currentPage.value = 1
  loadInstance()
}

function onShowSizeChange(_current: number, nextPageSize: number) {
  pageSize.value = nextPageSize
  currentPage.value = 1
  loadInstance()
}

function handleSortCol() {}

function getCellStyle({ row, column }: { row: Record<string, any>; column: Record<string, any> }) {
  const { property } = column
  const _find = allAttributesList.value.find((attr) => attr.name === property)
  if (_find && _find.option && _find.option.fontOptions && row[`${property}`] !== undefined && row[`${property}`] !== null) {
    return { ..._find.option.fontOptions }
  }
  return undefined
}

function getChoiceValueStyle(col: Record<string, any>, colValue: any): Record<string, any> {
  const _find = col.filters?.find((item: any[]) => String(item[0]) === String(colValue))
  if (_find) {
    return _find[1]?.style || {}
  }
  return {}
}

function getChoiceValueIcon(col: Record<string, any>, colValue: any): Record<string, any> {
  const _find = col.filters?.find((item: any[]) => String(item[0]) === String(colValue))
  if (_find) {
    return _find[1]?.icon || {}
  }
  return {}
}

function getChoiceValueLabel(col: Record<string, any>, colValue: any): string {
  const _find = col?.filters?.find((item: any[]) => String(item[0]) === String(colValue))
  if (_find) {
    return _find[1]?.label || ''
  }
  return ''
}

function handleExport() {
  const preferenceAttrList = [
    { id: `ci_type_alias`, value: 'ci_type_alias', label: t('cmdb.ciType.ciType') },
    ...columnsGroup.value,
  ]

  preferenceAttrList.forEach((attr) => {
    if (Array.isArray(attr?.children) && attr?.children?.length) {
      attr.children = attr.children.filter((child: any) => {
        return !child?.is_reference
      })
    }
  })

  batchDownloadRef.value?.open({
    preferenceAttrList,
  })
}

function batchDownload(payload: Record<string, unknown>) {
  // TODO: restore the vxe-table export (the export-xlsx plugin is not available
  // in the Vue3 shell yet).
  void payload

  xTableRef.value?.clearCheckboxRow()
  xTableRef.value?.clearCheckboxReserve()
}

function getQAndSort() {
  const fuzzySearch = searchRef.value?.fuzzySearch || ''
  const expression = searchRef.value?.expression || ''
  const currenCiType = searchRef.value?.currenCiType || undefined
  preferenceSearchRef.value?.savePreference({ fuzzySearch, expression, currenCiType })
}

function setParamsFromPreferenceSearch(item: any) {
  const { fuzzySearch, expression, currenCiType } = item.option
  if (searchRef.value) {
    searchRef.value.fuzzySearch = fuzzySearch
    searchRef.value.expression = expression
    searchRef.value.currenCiType = currenCiType
  }
  currentPage.value = 1
  nextTick(() => {
    loadInstance()
  })
}

function copyExpression() {
  const expression = searchRef.value?.expression || ''
  const fuzzySearch = searchRef.value?.fuzzySearch

  const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g

  const exp = expression.match(regQ) ? expression.match(regQ)![0] : null
  let currenCiType = searchRef.value?.currenCiType || []
  if (!currenCiType.length) {
    const _currenCiType: Array<string | number> = []
    ;(searchRef.value?.ciTypeGroup || []).forEach((item: any) => {
      _currenCiType.push(...item.ci_types.map((type: any) => type.id))
    })
    currenCiType = _currenCiType
  }
  const text = `q=${currenCiType && currenCiType.length ? `_type:(${currenCiType.join(';')})` : ''}${
    exp ? `,${exp}` : ''
  }${fuzzySearch ? `,*${fuzzySearch}*` : ''}`
  navigator.clipboard
    .writeText(text)
    .then(() => {
      message.success(t('copySuccess'))
      emit('copySuccess', text)
    })
    .catch(() => {
      message.error(t('cmdb.ci.copyFailed'))
    })
}
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <div
    id="resource_search"
    class="resource-search"
    :style="{ height: fromCronJob ? `${windowHeight - 48}px` : `${windowHeight - 64}px` }"
  >
    <div class="cmdb-views-header">
      <span>
        <span class="cmdb-views-header-title">{{ t('cmdb.menu.ciSearch') }}</span>
      </span>
      <a-button v-if="!fromCronJob" type="primary" class="ops-button-ghost" ghost @click="handleExport">
        <template #icon><DownloadOutlined /></template>{{ t('download') }}
      </a-button>
    </div>
    <div v-if="fromCronJob" class="resource-search-tip">
      <div class="resource-search-tip-item">{{ t('cmdb.ciType.resourceSearchTip1') }}</div>
      <div class="resource-search-tip-item">{{ t('cmdb.ciType.resourceSearchTip2') }}</div>
      <div class="resource-search-tip-item">{{ t('cmdb.ciType.resourceSearchTip3') }}</div>
    </div>
    <SearchForm
      ref="searchRef"
      :type="type"
      :type-id="typeId"
      :preference-attr-list="allAttributesList"
      @refresh="handleSearch"
      @update-all-attributes-list="updateAllAttributesList"
      @copy-expression="copyExpression"
    >
      <PreferenceSearch
        v-if="!fromCronJob"
        ref="preferenceSearchRef"
        @get-q-and-sort="getQAndSort"
        @set-params-from-preference-search="setParamsFromPreferenceSearch"
      />
    </SearchForm>
    <vxe-table
      :id="`cmdb-resource`"
      border
      keep-source
      show-overflow
      resizable
      ref="xTableRef"
      size="small"
      :loading="loading"
      :height="fromCronJob ? windowHeight - 280 : windowHeight - 240"
      show-header-overflow
      highlight-hover-row
      :data="instanceList"
      :row-config="{ useKey: true, keyField: '_id' }"
      :column-config="{ useKey: true }"
      :sort-config="{ remote: true, trigger: 'cell' }"
      @sort-change="handleSortCol"
      :cell-style="getCellStyle"
      :scroll-y="{ enabled: true, gt: 20 }"
      :scroll-x="{ enabled: true, gt: 0 }"
      class="ops-unstripe-table"
      :custom-config="{ storage: true }"
    >
      <vxe-column
        v-if="instanceList.length"
        :title="t('cmdb.ciType.ciType')"
        field="ci_type_alias"
        :width="100"
        fixed="left"
      ></vxe-column>
      <vxe-colgroup v-for="colGroup in columnsGroup" :key="colGroup.value" :title="colGroup.label">
        <template #header>
          <span :style="{ display: 'inline-flex', alignItems: 'center' }">
            {{ colGroup.label }}
            <EditAttrsPopover
              v-if="colGroup.isCiType"
              :style="{ borderLeft: 'none', width: '30px', height: '38px', cursor: 'pointer' }"
              :type-id="Number(colGroup.id.split('-')[1])"
              @refresh="loadInstance"
            />
          </span>
        </template>
        <vxe-column
          v-for="(col, index) in colGroup.children"
          :key="`${col.field}_${index}`"
          :title="col.title"
          :field="col.field"
          :width="col.width"
          :min-width="100"
          :cell-type="col.value_type === '2' ? 'string' : 'auto'"
        >
          <template v-if="col.value_type === '6' || col.is_link || col.is_password || col.is_choice || col.is_reference || col.is_file" #default="{ row }">
            <template v-if="col.is_reference && row[col.field]">
              <a
                v-for="ciId in (col.is_list ? row[col.field] : [row[col.field]])"
                :key="ciId"
                :href="`/cmdb/cidetail/${col.reference_type_id}/${ciId}`"
                target="_blank"
              >
                {{ getReferenceAttrValue(ciId, col) }}
              </a>
            </template>
            <span v-else-if="col.value_type === '6' && row[col.field]">{{ JSON.stringify(row[col.field]) }}</span>
            <template v-else-if="col.is_link && row[col.field]">
              <a
                v-for="(item, linkIndex) in (col.is_list ? row[col.field] : [row[col.field]])"
                :key="linkIndex"
                :href="
                  item.startsWith('http') || item.startsWith('https')
                    ? `${item}`
                    : `http://${item}`
                "
                target="_blank"
              >
                {{ getChoiceValueLabel(col, item) || item }}
              </a>
            </template>
            <PasswordField v-else-if="col.is_password && row[col.field]" :ci_id="row._id" :attr_id="col.attr_id" />
            <CiFileField
              v-else-if="col.is_file"
              :value="row[col.field]"
              :is-list="col.is_list"
              :is-edit="false"
              :attr-id="col.attr_id"
              :ci-id="row._id"
              :attr-name="col.field"
              @input="(val: string) => { row[col.field] = val }"
            />
            <template v-else-if="col.is_choice">
              <template v-if="col.is_list">
                <span
                  v-for="value in row[col.field]"
                  :key="value"
                  :style="{
                    borderRadius: '4px',
                    padding: '1px 5px',
                    margin: '2px',
                    ...getChoiceValueStyle(col, value),
                  }"
                >
                  <img
                    v-if="getChoiceValueIcon(col, value).id && getChoiceValueIcon(col, value).url"
                    :src="`/api/common-setting/v1/file/${getChoiceValueIcon(col, value).url}`"
                    :style="{ maxHeight: '13px', maxWidth: '13px', marginRight: '5px' }"
                  />
                  <AppstoreOutlined
                    v-else-if="getChoiceValueIcon(col, value).name"
                    :style="{ color: getChoiceValueIcon(col, value).color, marginRight: '5px' }"
                  />
                  {{ getChoiceValueLabel(col, value) || value }}
                </span>
              </template>
              <span
                v-else
                :style="{
                  borderRadius: '4px',
                  padding: '1px 5px',
                  margin: '2px 0',
                  ...getChoiceValueStyle(col, row[col.field]),
                }"
              >
                <img
                  v-if="getChoiceValueIcon(col, row[col.field]).id && getChoiceValueIcon(col, row[col.field]).url"
                  :src="`/api/common-setting/v1/file/${getChoiceValueIcon(col, row[col.field]).url}`"
                  :style="{ maxHeight: '13px', maxWidth: '13px', marginRight: '5px' }"
                />
                <AppstoreOutlined
                  v-else-if="getChoiceValueIcon(col, row[col.field]).name"
                  :style="{ color: getChoiceValueIcon(col, row[col.field]).color, marginRight: '5px' }"
                />
                {{ getChoiceValueLabel(col, row[col.field]) || row[col.field] }}
              </span>
            </template>
          </template>
        </vxe-column>
      </vxe-colgroup>

      <template #empty>
        <div>
          <img :style="{ width: '140px' }" :src="dataEmptyImg" />
          <div>{{ t('noData') }}</div>
        </div>
      </template>
      <template #loading>
        <div style="height: 200px; line-height: 200px">{{ t('loading') }}</div>
      </template>
    </vxe-table>
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
        @change="(page: number) => { currentPage = page; loadInstance(sortByTable) }"
      >
        <template #buildOptionText="{ value }">
          <span v-if="value !== '100000'">{{ value }}{{ t('itemsPerPage') }}</span>
          <span v-if="value === '100000'">{{ t('all') }}</span>
        </template>
      </a-pagination>
    </div>

    <BatchDownload
      :replace-fields="{ children: 'children', title: 'label', key: 'id' }"
      ref="batchDownloadRef"
      tree-type="tree"
      @batch-download="batchDownload"
    />
  </div>
</template>

<style lang="less" scoped>
.resource-search {
  margin-bottom: -24px;
  background-color: #fff;
  padding: 20px;
  border-radius: @border-radius-box;

  &-tip {
    margin-bottom: 16px;

    &-item {
      font-size: 12px;
      color: @text-color_4;
    }
  }
}
</style>
