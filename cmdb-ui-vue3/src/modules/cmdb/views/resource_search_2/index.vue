<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getCITypeGroups } from '@/modules/cmdb/api/ciTypeGroup'
import { getCITypes } from '@/modules/cmdb/api/CIType'

import ResourceSearchCom from './resourceSearch/index.vue'
import RelationSearch from './relationSearch/index.vue'

const { t } = useI18n()

const tabActive = ref('resourceSearch')
const tabList = [
  {
    lable: 'cmdb.ciType.resourceSearch',
    value: 'resourceSearch',
  },
  {
    lable: 'cmdb.relationSearch.relationSearch',
    value: 'relationSearch',
  },
]
const CITypeGroup = ref<any[]>([])
const allCITypes = ref<any[]>([])
const isInit = ref(false)

// The legacy Vue2 shell carried a global search value via `app.cmdbSearchValue`.
// No equivalent store field exists in the Vue3 shell yet.
const cmdbSearchValue = ref('')

watch(
  cmdbSearchValue,
  () => {
    tabActive.value = 'resourceSearch'
  },
  { immediate: true, deep: true }
)

onMounted(async () => {
  try {
    await Promise.all([getCITypeGroupsData(), getAllCITypes()])
  } catch (error) {
    console.log('resource search mounted fail', error)
  }

  isInit.value = true
})

async function getCITypeGroupsData() {
  const res = await getCITypeGroups({ need_other: true })

  CITypeGroup.value = res
    .filter((item: any) => item?.ci_types?.length)
    .map((item: any) => {
      item.id = `parent_${item.id || -1}`
      return item
    })
}

async function getAllCITypes() {
  const res = await getCITypes()
  allCITypes.value = res?.ci_types
}
</script>

<template>
  <div class="resource-search">
    <div class="resource-search-tab">
      <div
        v-for="tab in tabList"
        :key="tab.value"
        :class="['resource-search-tab-item', tabActive === tab.value ? 'resource-search-tab-item_active' : '']"
        @click="tabActive = tab.value"
      >
        {{ t(tab.lable) }}
      </div>
    </div>

    <template v-if="isInit">
      <ResourceSearchCom
        v-show="tabActive === 'resourceSearch'"
        :c-i-type-group="CITypeGroup"
        :all-c-i-types="allCITypes"
      />
      <RelationSearch
        v-show="tabActive === 'relationSearch'"
        :c-i-type-group="CITypeGroup"
        :all-c-i-types="allCITypes"
      />
    </template>
  </div>
</template>

<style lang="less" scoped>
.resource-search {
  width: 100%;
  height: 100%;

  &-tab {
    display: flex;
    align-items: center;
    margin-bottom: 12px;

    &-item {
      padding-right: 8px;
      margin-right: 8px;
      font-size: 14px;
      font-weight: 400;
      color: #86909c;
      cursor: pointer;

      &:not(:last-child) {
        border-right: solid 1px #e4e7ed;
      }

      &:hover {
        color: #2f54eb;
      }

      &_active {
        color: #2f54eb;
      }
    }
  }
}
</style>
