<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { SearchOutlined } from '@ant-design/icons-vue'
import dataEmptyImg from '@/assets/data_empty.png'
import { searchAttributes } from '@/modules/cmdb/api/CITypeAttr'
import AttributeCard from './attributeCard.vue'

const { t } = useI18n()

const visible = ref(false)
const loading = ref(false)
const attrList = ref<any[]>([])
const searchKey = ref<'alias' | 'name'>('alias')
const searchValue = ref('')
const tablePage = ref({
  currentPage: 1,
  pageSize: 50,
  totalResult: 0,
})

function open() {
  visible.value = true
  searchAttributesReq()
}

function handleCancel() {
  visible.value = false
}

async function searchAttributesReq(currentPage = 1, pageSize = tablePage.value.pageSize) {
  loading.value = true
  const params: Record<string, unknown> = {
    page: currentPage,
    page_size: pageSize,
  }
  if (searchKey.value && searchValue.value) {
    params[searchKey.value] = searchValue.value
  }
  searchAttributes(params)
    .then((res) => {
      attrList.value = res.attributes
      tablePage.value = {
        ...tablePage.value,
        currentPage: res.page,
        pageSize: res.page_size,
        totalResult: res.numfound,
      }
    })
    .finally(() => {
      loading.value = false
    })
}

function pageOrSizeChange(currentPage: number, pageSize: number) {
  searchAttributesReq(currentPage, pageSize)
}

function pressEnter() {
  searchAttributesReq(1)
}

function handleInput(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.value) {
    pressEnter()
  }
}

function showTotal(total: number, range: [number, number]) {
  return t('pagination.total', { total, range0: range[0], range1: range[1] })
}

defineExpose({ open })
</script>

<template>
  <a-modal
    wrap-class-name="attrbute-store-wrapper"
    width="80%"
    :open="visible"
    @cancel="handleCancel"
  >
    <template #title>
      <div class="attrbute-store-header">
        <span>{{ t('cmdb.ciType.attributeLibray') }}</span>
        <div class="attrbute-store-search">
          <a-input-group compact>
            <a-select v-model:value="searchKey" class="attrbute-store-search-select">
              <a-select-option value="alias">{{ t('cmdb.common.alias') }}</a-select-option>
              <a-select-option value="name">{{ t('name') }}</a-select-option>
            </a-select>
            <a-input
              v-model:value="searchValue"
              class="attrbute-store-search-input"
              allow-clear
              @press-enter="pressEnter"
              @change="handleInput"
            >
              <template #suffix>
                <SearchOutlined :style="{ cursor: 'pointer' }" @click="pressEnter" />
              </template>
            </a-input>
          </a-input-group>
        </div>
      </div>
    </template>
    <a-spin :spinning="loading" :style="{ height: '100%' }">
      <a-row v-if="attrList.length">
        <a-col
          v-for="item in attrList"
          :key="item.id"
          class="attrbute-store-col"
          :xxl="4"
          :xl="6"
          :lg="8"
          :md="12"
          :sm="24"
        >
          <AttributeCard :is-store="true" :property="item" @ok="searchAttributesReq()" />
        </a-col>
      </a-row>
      <a-empty v-else>
        <template #image><img :src="dataEmptyImg" /></template>
        <template #description><span>{{ t('noData') }}</span></template>
      </a-empty>
    </a-spin>
    <template #footer>
      <a-pagination
        size="small"
        show-size-changer
        show-quick-jumper
        :current="tablePage.currentPage"
        :total="tablePage.totalResult"
        :show-total="showTotal"
        :page-size="tablePage.pageSize"
        :page-size-options="['20', '50', '100', '200']"
        @change="pageOrSizeChange"
        @show-size-change="pageOrSizeChange"
      />
    </template>
  </a-modal>
</template>

<style lang="less" scoped>
.attrbute-store-wrapper {
  .attrbute-store-col {
    display: flex;
    justify-content: center;
  }
}
</style>

<style lang="less">
.attrbute-store-wrapper {
  .ant-modal-body {
    height: 70vh;
    overflow: auto;
  }
  .attrbute-store-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
}

.attrbute-store-search {
  width: 300px;
  display: inline-block;
  margin-right: 60px;
  .ant-input-group.ant-input-group-compact > *:first-child,
  .ant-input-group.ant-input-group-compact > .ant-select:first-child > .ant-select-selection {
    background-color: @primary-color;
    color: #fff;
    border: none;
  }
  .ant-select-focused .ant-select-selection,
  .ant-select-selection:focus {
    box-shadow: none;
  }
  .ant-select-selection__rendered {
    margin-right: 12px;
  }
  .ant-select-arrow {
    color: #fff;
    font-size: 10px;
    right: 8px;
  }
  .attrbute-store-search-select {
    width: 65px;
    .ant-select-selection-selected-value {
      font-size: 12px;
    }
  }
  .attrbute-store-search-input {
    display: inline-block;
    width: calc(100% - 65px);
    .ant-input {
      background-color: #f0f5ff;
      border: none;
      &:focus {
        box-shadow: none;
      }
    }
  }
}
</style>
