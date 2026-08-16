<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { getHttpCategories, getHttpAttributes, getSnmpAttributes, getHttpAttrMapping } from '@/modules/cmdb/api/discovery'
import { DISCOVERY_CATEGORY_TYPE } from '@/modules/cmdb/constants'
import AttrMapTable from '@/modules/cmdb/components/attrMapTable/index.vue'
import ADPreviewTable from './adPreviewTable.vue'
import HttpADCategory from './httpADCategory.vue'

const props = withDefaults(
  defineProps<{
    ruleName?: string
    ruleType?: string
    isEdit?: boolean
    ciTypeAttributes?: Record<string, any>[]
    adCITypeList?: Record<string, any>[]
    currentTab?: number
    uniqueKey?: string
    currentAdt?: Record<string, any>
  }>(),
  {
    ruleName: '',
    ruleType: 'http',
    isEdit: false,
    ciTypeAttributes: () => [],
    adCITypeList: () => [],
    currentTab: 0,
    uniqueKey: '',
    currentAdt: () => ({}),
  }
)

const categories = ref<any[]>([])
const categoriesSelect = ref<string[]>([])
const currentCate = ref('')
const tableData = ref<Record<string, any>[]>([])
const httpAttrMap = ref<Record<string, string>>({})

const attrMapTableRef = ref<InstanceType<typeof AttrMapTable>>()

const isCloud = computed(() =>
  [DISCOVERY_CATEGORY_TYPE.HTTP, DISCOVERY_CATEGORY_TYPE.PRIVATE_CLOUD].includes(props.ruleType)
)

function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function formatTableData(list: any[]) {
  const findADT = props.adCITypeList.find((item) => Number(item.adr_id) === Number(props.currentTab))
  tableData.value = (list || []).map((val) => {
    const item = cloneDeep(val)

    if (findADT?.attributes?.[item.name]) {
      item.attr = findADT.attributes[item.name]
    }

    const attrMapName = httpAttrMap.value?.[item?.name]

    if (
      props.isEdit &&
      !item.attr &&
      attrMapName &&
      props.ciTypeAttributes.some((ele) => ele.name === attrMapName)
    ) {
      item.attr = attrMapName
    }

    if (!item.attr) {
      const find = props.ciTypeAttributes.find((ele) => ele.name === item.name)
      if (find) {
        item.attr = find.name
      }
    }

    return item
  })
}

async function getHttpAttrMappingLocal(name: string, resource: string) {
  const res = await getHttpAttrMapping(name, resource)
  httpAttrMap.value = res || {}
}

async function getHttpAttr(val: string) {
  await getHttpAttrMappingLocal(props.ruleName, val)
  getHttpAttributes(props.ruleName, { resource: val }).then((res: any) => {
    if (props.isEdit) {
      formatTableData(res)
    } else {
      tableData.value = res
    }
  })
}

function getTableData() {
  const table = attrMapTableRef.value
  const { fullData } = table?.getTableData() ?? { fullData: [] }
  return fullData || []
}

function setCurrentCate(cate: string) {
  if (cate) {
    currentCate.value = cate
  }
}

watch(
  () => currentCate.value,
  (newVal) => {
    if (newVal) {
      getHttpAttr(newVal)
    }
  },
  { immediate: true }
)

watch(
  () => [props.ruleType, props.ruleName],
  ([ruleType, ruleName]) => {
    currentCate.value = ''
    nextTick(() => {
      if ([DISCOVERY_CATEGORY_TYPE.SNMP, DISCOVERY_CATEGORY_TYPE.COMPONENT].includes(ruleType) && ruleName) {
        getSnmpAttributes(ruleType, ruleName).then((res: any) => {
          if (props.isEdit) {
            formatTableData(res)
          } else {
            tableData.value = res
          }
        })
      }

      if (isCloud.value && ruleName) {
        getHttpCategories(ruleName).then((res: any) => {
          categories.value = res
          const selectOptions: string[] = []
          res.forEach((category: any) => {
            if (category?.items?.length) {
              selectOptions.push(...category.items)
            }
          })
          categoriesSelect.value = selectOptions
          if (props.isEdit && selectOptions?.length) {
            currentCate.value = props?.currentAdt?.extra_option?.category || selectOptions[0]
          }
        })
      }
    })
  },
  { immediate: true }
)

defineExpose({ getTableData })
</script>

<template>
  <div class="http-snmp-ad">
    <HttpADCategory
      v-if="!isEdit && isCloud"
      :categories="categories"
      :current-cate="currentCate"
      :table-data="tableData"
      :rule-type="ruleType"
      @click-category="setCurrentCate"
    />
    <template v-else>
      <a-select v-if="isCloud" v-model:value="currentCate" style="margin-bottom: 10px; min-width: 200px">
        <a-select-option v-for="cate in categoriesSelect" :key="cate" :value="cate">{{ cate }}</a-select-option>
      </a-select>
      <AttrMapTable
        v-if="isEdit"
        ref="attrMapTableRef"
        :rule-type="ruleType"
        :table-data="tableData"
        :ci-type-attributes="ciTypeAttributes"
        :unique-key="uniqueKey"
      />
      <ADPreviewTable v-else :table-data="tableData" />
    </template>
  </div>
</template>

<style scoped>
.http-snmp-ad {
  height: 100%;
}
</style>
