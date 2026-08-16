<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { searchCI } from '@/modules/cmdb/api/ci'
import dataEmptyImg from '@/assets/data_empty.png'

const props = withDefaults(
  defineProps<{
    currentSelect?: number | undefined
    CITypeId?: number | undefined
    currentCITYpe?: Record<string, any>
  }>(),
  {
    currentSelect: undefined,
    CITypeId: undefined,
    currentCITYpe: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'change', ci: any): void
}>()

const { t } = useI18n()

const page = ref(1)
const pageSize = ref(20)
const pageSizeOptions = ['20', '50', '100']
const totalNumber = ref(0)
const CIList = ref<any[]>([])

const searchValue = ref('')

watch(
  () => props.CITypeId,
  (newVal, oldVal) => {
    page.value = 1
    searchValue.value = ''

    if (newVal && newVal !== oldVal) {
      getCIList()
    } else {
      CIList.value = []
      totalNumber.value = 0
    }
  },
  { immediate: true, deep: true }
)

async function getCIList() {
  const res = await searchCI({
    q: `_type:${props.CITypeId}${searchValue.value ? `,*${searchValue.value}*` : ''}`,
    count: pageSize.value,
    page: page.value,
  })
  let list = res?.result || []

  const { show_key = '', unique_id = '', attributes = [] } = props?.currentCITYpe || {}
  const unique_key = attributes?.find((attr: any) => attr?.id === unique_id)?.name || ''

  if (list.length) {
    list = list.map((item: any) => {
      return {
        value: item?._id,
        name: item?.[show_key] || item?.[unique_key] || item?._id || '',
        unitCount: item?.u_count ?? 0,
      }
    })
  }

  CIList.value = list
  totalNumber.value = res?.numfound || 0
}

function handleSearch(value: string) {
  searchValue.value = value
  page.value = 1
  getCIList()
}

function handleChangePage(newPage: number) {
  page.value = newPage
  getCIList()
}

function onShowSizeChange(_: number, newPageSize: number) {
  page.value = 1
  pageSize.value = newPageSize
  getCIList()
}

function handleCIChange(e: any) {
  const value = e.target.value
  const findCI = CIList.value.find((item) => item.value === value)

  emit('change', findCI)
}
</script>

<template>
  <div class="device-select">
    <a-input-search @search="handleSearch" />

    <a-radio-group v-if="CIList.length" :value="currentSelect" class="device-select-group" @change="handleCIChange">
      <a-radio v-for="item in CIList" :key="item.value" :value="item.value" class="device-select-item">
        <a-tooltip :title="item.name" placement="topLeft">
          {{ item.name }}
        </a-tooltip>
      </a-radio>
    </a-radio-group>

    <div v-else class="device-select-null">
      <img class="device-select-null-img" :src="dataEmptyImg" />
      <div class="device-select-null-text">{{ t('noData') }}</div>
    </div>

    <div class="device-select-pagination">
      <a-pagination
        show-size-changer
        :current="page"
        size="small"
        :total="totalNumber"
        show-quick-jumper
        :page-size="pageSize"
        :page-size-options="pageSizeOptions"
        :show-total="(total: number, range: number[]) => t('pagination.total', { range0: range[0], range1: range[1], total })"
        @change="handleChangePage"
        @show-size-change="onShowSizeChange"
      />
    </div>
  </div>
</template>

<style lang="less" scoped>
.device-select {
  width: 650px;

  &-group {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    row-gap: 20px;
    margin: 12px 0px;
    max-height: 40vh;
    overflow-y: auto;
    overflow-x: hidden;
  }

  &-item {
    width: 48%;
    flex-shrink: 0;

    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &-null {
    margin: 30px 0px;
    text-align: center;
    width: 100%;

    &-img {
      width: 130px;
    }

    &-text {
      margin-top: 12px;
    }
  }

  &-pagination {
    text-align: right;
    margin-top: 4px;
  }
}
</style>
