<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { LeftOutlined } from '@ant-design/icons-vue'
import ADPreviewTable from './adPreviewTable.vue'

interface Category {
  category: string
  items: string[]
}

const props = withDefaults(
  defineProps<{
    categories?: Category[]
    currentCate?: string
    tableData?: Record<string, any>[]
    ruleType?: string
  }>(),
  {
    categories: () => [],
    currentCate: '',
    tableData: () => [],
    ruleType: 'http',
  }
)

const emit = defineEmits<{
  (e: 'clickCategory', item: string): void
}>()

const { t } = useI18n()

const searchValue = ref('')
const isPreviewDetail = ref(false)

const filterCategories = computed<Category[]>(() => {
  const categories: Category[] = JSON.parse(JSON.stringify(props.categories))
  return categories.filter((category) => {
    category.items = category.items.filter((item) => item?.indexOf(searchValue.value) !== -1)
    return category?.items?.length > 0
  })
})

function onSearchHttp(v: string) {
  searchValue.value = v
}

function clickCategory(item: string) {
  emit('clickCategory', item)
  isPreviewDetail.value = true
}

function clickBack() {
  isPreviewDetail.value = false
}
</script>

<template>
  <div class="http-ad-category">
    <div v-if="currentCate && isPreviewDetail" class="http-ad-category-preview">
      <div class="category-side">
        <div v-for="(category, categoryIndex) in categories" :key="category.category" class="category-side-item">
          <div class="category-side-title">
            <div class="category-side-title">
              <LeftOutlined v-if="categoryIndex === 0" @click="clickBack" />
              {{ category.category }}
            </div>
          </div>
          <div class="category-side-children">
            <div
              v-for="(item, itemIndex) in category.items"
              :key="item"
              :class="['category-side-children-item', item === currentCate ? 'category-side-children-item_active' : '']"
              @click="clickCategory(item)"
            >
              {{ item }}
              <span
                v-if="ruleType === 'private_cloud' || (ruleType === 'http' && (categoryIndex !== 0 || itemIndex !== 0))"
                class="category-side-children-item-corporate"
              >
                {{ t('cmdb.enterpriseVersionFlag') }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div class="category-table">
        <ADPreviewTable :table-data="tableData" />
      </div>
    </div>

    <template v-else>
      <a-input-search
        class="category-search"
        :placeholder="t('cmdb.ad.httpSearchPlaceHolder')"
        @search="onSearchHttp"
      />
      <div class="category-main">
        <div v-for="(category, categoryIndex) in filterCategories" :key="category.category" class="category-item">
          <div class="category-title">{{ category.category }}</div>
          <div class="category-children">
            <div
              v-for="(item, itemIndex) in category.items"
              :key="item"
              :class="['category-children-item', item === currentCate ? 'category-children-item_active' : '']"
              @click="clickCategory(item)"
            >
              {{ item }}
              <div
                v-if="ruleType === 'private_cloud' || (ruleType === 'http' && (categoryIndex !== 0 || itemIndex !== 0))"
                class="corporate-flag"
              >
                <span class="corporate-flag-text">{{ t('cmdb.enterpriseVersionFlag') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="corporate-tip">
        {{ t('cmdb.ad.corporateTip') }} <a href="mailto:bd@veops.cn">bd@veops.cn</a>
      </div>
    </template>
  </div>
</template>

<style scoped>
.http-ad-category-preview {
  display: flex;
  width: 100%;
  height: calc(100vh - 156px);
  justify-content: space-between;
}
.category-side {
  flex-shrink: 0;
  width: 150px;
  height: 100%;
  border-right: solid 1px #e4e7ed;
  padding-right: 10px;
}
.category-side-item:not(:last-child) {
  margin-bottom: 24px;
}
.category-side-title {
  font-size: 12px;
  font-weight: 400;
  color: #a5a9bc;
}
.category-side-children {
  margin-top: 5px;
}
.category-side-children-item {
  padding: 7px 10px;
  background-color: #f7f8fa;
  border-radius: 2px;
  color: #4e5969;
  font-size: 12px;
  font-weight: 400;
  cursor: pointer;
  position: relative;
  margin-top: 5px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.category-side-children-item:hover {
  background-color: #f0f5ff;
  color: #2f54eb;
}
.category-side-children-item_active {
  background-color: #f0f5ff;
  color: #2f54eb;
}
.category-side-children-item-corporate {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  background-color: #e1efff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #2f54eb;
  font-size: 12px;
}
.category-table {
  width: calc(100% - 150px - 10px - 16px);
  flex-shrink: 0;
  height: 100%;
}
.category-search {
  width: 254px;
}
.category-item {
  margin-top: 24px;
}
.category-title {
  font-size: 14px;
  font-weight: 700;
}
.category-children {
  margin-top: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 19px;
}
.category-children-item {
  padding: 18px 19px;
  background-color: #f7f8fa;
  border-radius: 2px;
  color: #4e5969;
  font-size: 14px;
  font-weight: 400;
  cursor: pointer;
  position: relative;
  min-width: 100px;
  text-align: center;
}
.category-children-item:hover {
  background-color: #f0f5ff;
  color: #2f54eb;
}
.category-children-item_active {
  background-color: #f0f5ff;
  color: #2f54eb;
}
.corporate-tip {
  margin-top: 20px;
}
.corporate-flag {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 4;
  width: 38px;
  height: 28px;
  border-left: 38px solid transparent;
  border-top: 28px solid #e1efff;
}
.corporate-flag-text {
  width: 37px;
  position: absolute;
  top: -28px;
  right: 3px;
  text-align: right;
  color: #2f54eb;
  font-size: 10px;
  font-weight: 400;
}
</style>
