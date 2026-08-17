<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import { SearchOutlined, DownloadOutlined, RedoOutlined, UpOutlined, DownOutlined } from '@ant-design/icons-vue'
import { DATE_FORMAT, TIME_DEFAULT_VALUE } from '../constants'

defineProps<{
  attrList: Array<Record<string, any>>
}>()

const emit = defineEmits<{
  (e: 'search', params: Record<string, any>): void
  (e: 'export', params: Record<string, any>): void
  (e: 'searchFormReset'): void
  (e: 'expandChange', expand: boolean): void
  (e: 'searchFormChange', params: Record<string, any>): void
}>()

const { t } = useI18n()

const expand = ref(false)
const queryParams = reactive<Record<string, any>>({
  page: 1,
  page_size: 50,
})
const date = ref<any>(undefined)

let searchDebounced: { (val: Record<string, any>): void; cancel?: () => void } | null = null

const timeConfig = computed(() => ({
  hideDisabledOptions: TIME_DEFAULT_VALUE.hideDisabledOptions,
  defaultValue: [
    dayjs(TIME_DEFAULT_VALUE.defaultValue[0], 'HH:mm:ss'),
    dayjs(TIME_DEFAULT_VALUE.defaultValue[1], 'HH:mm:ss'),
  ],
}))

function preProcessData() {
  Object.keys(queryParams).forEach((item) => {
    if (queryParams[item] === '' || queryParams[item] === undefined) {
      delete queryParams[item]
    }
  })
  return queryParams
}

function debounce<T extends (...args: any[]) => void>(fn: T, wait: number) {
  let timer: ReturnType<typeof setTimeout> | null = null
  const debounced = (...args: any[]) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), wait)
  }
  debounced.cancel = () => {
    if (timer) clearTimeout(timer)
    timer = null
  }
  return debounced
}

watch(
  queryParams,
  (val) => {
    if (searchDebounced) {
      searchDebounced(val)
    }
  },
  { deep: true }
)

onMounted(() => {
  searchDebounced = debounce((val: Record<string, any>) => {
    preProcessData()
    emit('searchFormChange', val)
  }, 300)
})

onBeforeUnmount(() => {
  if (searchDebounced?.cancel) {
    searchDebounced.cancel()
  }
})

function handleSearch() {
  queryParams.page = 1
  emit('search', queryParams)
}

function handleExport() {
  const params = { ...queryParams }
  emit('export', params)
}

function handleReset() {
  Object.keys(queryParams).forEach((key) => delete queryParams[key])
  Object.assign(queryParams, { page: 1, page_size: 50 })
  date.value = undefined
  emit('searchFormReset')
}

function toggle() {
  expand.value = !expand.value
  emit('expandChange', expand.value)
}

function onChange(_dates: any, dateString: [string, string]) {
  queryParams.start = dateString[0]
  queryParams.end = dateString[1]
}

defineExpose({ queryParams })
</script>

<template>
  <div class="search-form-wrapper">
    <a-form class="search-form" :colon="false" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }" label-align="left">
      <a-row :gutter="24">
        <a-col v-for="attr in attrList.slice(0, 3)" :key="attr.name" :sm="24" :md="12" :lg="12" :xl="8">
          <a-form-item :label="attr.alias || attr.name">
            <a-select
              v-if="attr.is_choice"
              v-model:value="queryParams[attr.name]"
              :placeholder="t('cmdb.history.pleaseSelect')"
              show-search
              option-filter-prop="label"
              allow-clear
            >
              <a-select-option
                v-for="(choice, index) in attr.choice_value"
                :key="'Search_' + attr.name + Object.values(choice)[0] + index"
                :value="Object.values(choice)[0]"
                :label="Object.keys(choice)[0]"
              >
                {{ Object.keys(choice)[0] }}
              </a-select-option>
            </a-select>
            <a-range-picker
              v-else-if="attr.value_type === '3'"
              v-model:value="date"
              :style="{ width: '100%' }"
              :format="DATE_FORMAT"
              :placeholder="[t('cmdb.history.startTime'), t('cmdb.history.endTime')]"
              :show-time="timeConfig"
              @change="onChange"
            />
            <a-input v-else v-model:value="queryParams[attr.name]" style="width: 100%" allow-clear />
          </a-form-item>
        </a-col>

        <template v-if="expand && attrList.length >= 4">
          <a-col
            v-for="item in attrList.slice(3)"
            :key="'expand_' + item.name"
            :sm="24"
            :md="12"
            :lg="8"
            :xl="8"
          >
            <a-form-item :label="item.alias || item.name">
              <a-select
                v-if="item.is_choice"
                v-model:value="queryParams[item.name]"
                :placeholder="t('cmdb.history.pleaseSelect')"
                show-search
                option-filter-prop="label"
                allow-clear
              >
                <a-select-option
                  v-for="(choice, index) in item.choice_value"
                  :key="'Search_' + item.name + index"
                  :value="Object.values(choice)[0]"
                  :label="Object.keys(choice)[0]"
                >
                  {{ Object.keys(choice)[0] }}
                </a-select-option>
              </a-select>
              <a-range-picker
                v-else-if="item.value_type === '3'"
                :style="{ width: '100%' }"
                :format="DATE_FORMAT"
                :placeholder="[t('cmdb.history.startTime'), t('cmdb.history.endTime')]"
                :show-time="timeConfig"
                @change="onChange"
              />
              <a-input v-else v-model:value="queryParams[item.name]" style="width: 100%" allow-clear />
            </a-form-item>
          </a-col>
        </template>
      </a-row>
      <a-row>
        <a-col :span="24" class="search-form-actions">
          <a-space :size="8">
            <a-button type="primary" html-type="submit" @click="handleSearch">
              <template #icon><SearchOutlined /></template>
              {{ t('query') }}
            </a-button>
            <a-button @click="handleExport">
              <template #icon><DownloadOutlined /></template>
              {{ t('export') }}
            </a-button>
            <a-button @click="handleReset">
              <template #icon><RedoOutlined /></template>
              {{ t('reset') }}
            </a-button>
            <a v-if="attrList.length >= 4" class="expand-link" @click="toggle">
              {{ expand ? t('hide') : t('expand') }}
              <component :is="expand ? UpOutlined : DownOutlined" />
            </a>
          </a-space>
        </a-col>
      </a-row>
    </a-form>
  </div>
</template>

<style lang="less" scoped>
.search-form-wrapper {
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 2px;
  padding: 16px;
  margin-bottom: 16px;
}

.search-form {
  :deep(.ant-form-item) {
    margin-bottom: 16px;
  }

  :deep(.ant-form-item-label) {
    line-height: 32px;

    > label {
      color: rgba(0, 0, 0, 0.85);
      font-weight: 500;
    }
  }

  :deep(.ant-input),
  :deep(.ant-select-selection),
  :deep(.ant-calendar-picker-input) {
    border-radius: 2px;

    &:hover {
      border-color: @primary-color;
    }

    &:focus,
    &.ant-select-focused .ant-select-selection {
      border-color: @primary-color;
      box-shadow: 0 0 0 2px fade(@primary-color, 20%);
    }
  }
}

.search-form-actions {
  text-align: right;
  padding-top: 16px;
  border-top: 1px solid #e8e8e8;

  :deep(.ant-space) {
    margin-top: 16px;
  }

  :deep(.ant-btn) {
    border-radius: 2px;
    font-weight: 400;
    box-shadow: 0 2px 0 rgba(0, 0, 0, 0.015);

    &.ant-btn-primary {
      &:hover {
        background-color: @primary-color;
        border-color: @primary-color;
      }
    }

    &:not(.ant-btn-primary) {
      &:hover {
        color: @primary-color;
        border-color: @primary-color;
      }
    }
  }

  .expand-link {
    font-size: 12px;
    color: @primary-color;
    cursor: pointer;
    transition: color 0.3s;
    user-select: none;

    &:hover {
      color: @primary-color;
    }

    .anticon {
      margin-left: 4px;
      font-size: 12px;
      transition: transform 0.3s;
    }
  }
}
</style>
