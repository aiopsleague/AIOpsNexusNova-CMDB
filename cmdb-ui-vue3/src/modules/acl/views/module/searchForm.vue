<script setup lang="ts">
import { ref, watch } from 'vue'
import dayjs, { type Dayjs } from 'dayjs'
import { useI18n } from 'vue-i18n'
import { DownOutlined, UpOutlined } from '@ant-design/icons-vue'
import { valueTypeMap } from '@/modules/acl/constants'

interface ChoiceOption {
  [key: string]: unknown
}

interface AttrItem {
  name: string
  alias?: string
  is_choice?: boolean
  choice_value?: ChoiceOption[]
  value_type?: string
}

interface SelectOption {
  value?: unknown
  label?: string
}

const { t } = useI18n()

defineProps<{
  attrList: AttrItem[]
  hasSwitch?: boolean
  switchValue?: string
}>()

const emit = defineEmits<{
  (e: 'search', v: Record<string, unknown>): void
  (e: 'searchFormChange', v: Record<string, unknown>): void
  (e: 'searchFormReset'): void
  (e: 'resourceClear'): void
  (e: 'expandChange', v: boolean): void
  (e: 'onSwitchChange', v: boolean): void
  (e: 'loadMoreData', name: string, value?: string): void
  (e: 'fetchData', value: string): void
}>()

const expand = ref(false)
const queryParams = ref<Record<string, unknown>>({ page: 1 })
const date = ref<[Dayjs, Dayjs] | undefined>(undefined)
const checked = ref(false)
const searchValue = ref<string | undefined>(undefined)

const defaultTimeValue = [dayjs('00:00:00', 'HH:mm:ss'), dayjs('23:59:59', 'HH:mm:ss')]

function choiceOptions(attr: AttrItem): SelectOption[] {
  return (attr.choice_value || []).map((choice) => ({
    value: Object.values(choice)[0],
    label: Object.keys(choice)[0],
  }))
}

function isDateType(attr: AttrItem): boolean {
  const vt = valueTypeMap[attr.value_type || ''] || ''
  return vt === 'date' || vt === 'datetime'
}

function preProcessData() {
  Object.keys(queryParams.value).forEach((item) => {
    if (queryParams.value[item] === '' || queryParams.value[item] === undefined) {
      delete queryParams.value[item]
    }
  })
}

watch(
  queryParams,
  (val) => {
    preProcessData()
    emit('searchFormChange', val)
  },
  { deep: true }
)

watch(
  () => queryParams.value.resource_id,
  (val) => {
    if (val === undefined) emit('resourceClear')
  }
)

watch(
  () => queryParams.value.link_id,
  (val) => {
    if (val === undefined) emit('resourceClear')
  }
)

function handleSearch() {
  queryParams.value.page = 1
  emit('search', queryParams.value)
}

function handleReset() {
  queryParams.value = { page: 1 }
  date.value = undefined
  checked.value = false
  emit('searchFormReset')
}

function toggle() {
  expand.value = !expand.value
  emit('expandChange', expand.value)
}

function onChange(_dates: [Dayjs, Dayjs] | null, dateString: [string, string]) {
  queryParams.value.start = dateString[0]
  queryParams.value.end = dateString[1]
}

function onSwitchChange(val: boolean) {
  emit('onSwitchChange', val)
}

function filterOption(input: string, option: SelectOption) {
  const label = String(option?.label ?? option?.value ?? '')
  return label.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

function loadMoreData(name: string, e: Event) {
  const target = e.target as HTMLElement
  if (target.scrollTop + target.clientHeight === target.scrollHeight) {
    emit('loadMoreData', name, searchValue.value)
  }
}

function fetchData(value: string, name: string) {
  searchValue.value = value
  if (name === 'link_id' || name === 'resource_id') {
    emit('fetchData', value)
  }
}

// Expose the query params so parent tables can clear stale filter fields when
// the selected app changes (rid / resource_type_id / resource_id / link_id / trigger_id).
defineExpose({ queryParams })
</script>

<template>
  <div>
    <a-form :colon="false">
      <a-row :gutter="24">
        <a-col
          v-for="attr in attrList.slice(0, 4)"
          :key="attr.name"
          :sm="24"
          :md="12"
          :lg="12"
          :xl="6"
        >
          <a-form-item
            :label="attr.alias || attr.name"
            :label-col="{ span: 4 }"
            :wrapper-col="{ span: 20 }"
            label-align="right"
          >
            <a-select
              v-if="attr.is_choice"
              v-model:value="queryParams[attr.name]"
              :options="choiceOptions(attr)"
              :placeholder="t('placeholder2')"
              show-search
              :filter-option="filterOption"
              allow-clear
              @popup-scroll="(e: Event) => loadMoreData(attr.name, e)"
              @search="(value: string) => fetchData(value, attr.name)"
            />
            <a-range-picker
              v-else-if="isDateType(attr)"
              v-model:value="date"
              style="width: 100%"
              format="YYYY-MM-DD HH:mm:ss"
              :show-time="{ hideDisabledOptions: true, defaultValue: defaultTimeValue }"
              @change="onChange"
            />
            <a-input v-else v-model:value="queryParams[attr.name]" style="width: 100%" allow-clear />
          </a-form-item>
        </a-col>

        <template v-if="expand && attrList.length >= 4">
          <a-col
            v-for="item in attrList.slice(4)"
            :key="'expand_' + item.name"
            :sm="24"
            :md="12"
            :lg="8"
            :xl="6"
          >
            <a-form-item
              :label="item.alias || item.name"
              :label-col="{ span: 4 }"
              :wrapper-col="{ span: 20 }"
              label-align="right"
            >
              <a-select
                v-if="item.is_choice"
                v-model:value="queryParams[item.name]"
                :options="choiceOptions(item)"
                :placeholder="t('placeholder2')"
                show-search
                :filter-option="filterOption"
                allow-clear
                @popup-scroll="(e: Event) => loadMoreData(item.name, e)"
                @search="(value: string) => fetchData(value, item.name)"
              />
              <a-range-picker
                v-else-if="isDateType(item)"
                v-model:value="date"
                style="width: 100%"
                format="YYYY-MM-DD HH:mm"
                :placeholder="[t('acl.startAt'), t('acl.endAt')]"
                :show-time="{ hideDisabledOptions: true, defaultValue: defaultTimeValue }"
                @change="onChange"
              />
              <a-input v-else v-model:value="queryParams[item.name]" style="width: 100%" allow-clear />
            </a-form-item>
          </a-col>
        </template>
      </a-row>

      <a-row>
        <a-col :span="24" :style="{ textAlign: 'right', marginBottom: '10px' }">
          <a-switch
            v-if="hasSwitch"
            v-model:checked="checked"
            :un-checked-children="switchValue"
            @change="onSwitchChange"
          />
          <a-button :style="{ marginLeft: '8px' }" type="primary" html-type="submit" @click="handleSearch">
            {{ t('query') }}
          </a-button>
          <a-button :style="{ marginLeft: '8px' }" @click="handleReset">
            {{ t('reset') }}
          </a-button>
          <a v-if="attrList.length >= 5" :style="{ marginLeft: '8px', fontSize: '12px' }" @click="toggle">
            {{ t('expand') }} <UpOutlined v-if="expand" /><DownOutlined v-else />
          </a>
        </a-col>
      </a-row>
    </a-form>
  </div>
</template>
