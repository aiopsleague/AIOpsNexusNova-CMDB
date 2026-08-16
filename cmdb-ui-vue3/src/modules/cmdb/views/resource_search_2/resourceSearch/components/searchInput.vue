<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { CheckCircleOutlined, InfoCircleOutlined, SearchOutlined } from '@ant-design/icons-vue'
import { SEARCH_MODE } from '../constants'
import FilterPopover from './filterPopover.vue'

const props = withDefaults(
  defineProps<{
    searchValue?: string
    expression?: string
    selectCITypeIds?: Array<string | number>
    CITypeGroup?: any[]
    allAttributesList?: any[]
    classType?: string
    searchMode?: string
  }>(),
  {
    searchValue: '',
    expression: '',
    selectCITypeIds: () => [],
    CITypeGroup: () => [],
    allAttributesList: () => [],
    classType: '',
    searchMode: SEARCH_MODE.NORMAL,
  }
)

const emit = defineEmits<{
  (e: 'changeFilter', data: { name: string; value: any }): void
  (e: 'updateAllAttributesList', value: Array<string | number>): void
  (e: 'saveCondition', isSubmit: boolean): void
  (e: 'updateSearchMode', mode: string): void
}>()

const { t, locale } = useI18n()

const searchModeList = [
  {
    value: SEARCH_MODE.NORMAL,
    label: 'cmdb.ciType.rowSearchMode',
  },
  {
    value: SEARCH_MODE.COLUMN,
    label: 'cmdb.ciType.columnSearchMode',
  },
]

const isZh = computed(() => locale.value === 'zh')

// Display text shown under the input; unlike the actual copied text, it does not
// include the full CI-type list when no model is selected.
const copyText = computed(() => {
  const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
  const exp = props.expression.match(regQ) ? props.expression.match(regQ)![0] : null

  const textArray: string[] = []
  if (props.selectCITypeIds?.length) {
    textArray.push(`_type:(${props.selectCITypeIds.join(';')})`)
  }
  if (exp) {
    textArray.push(exp)
  }
  if (props.searchValue) {
    if (props.searchMode === SEARCH_MODE.COLUMN && props.searchValue.includes('\n')) {
      const values = props.searchValue.split('\n').filter((v) => v.trim())
      textArray.push(`(${values.join(';')})`)
    } else {
      textArray.push(`*${props.searchValue}*`)
    }
  }

  return textArray.length ? `q=${textArray.join(',')}` : ''
})

function updateAllAttributesList(value: Array<string | number>) {
  emit('updateAllAttributesList', value)
}

function saveCondition(isSubmit: boolean) {
  emit('saveCondition', isSubmit)
}

function handleChangeSearchValue(e: Event) {
  const value = (e.target as HTMLInputElement).value
  changeFilter({
    name: 'searchValue',
    value,
  })
}

function changeFilter(data: { name: string; value: any }) {
  emit('changeFilter', data)
}

function handleCopyExpression() {
  const { selectCITypeIds, expression, searchValue } = props
  const regQ = /(?<=q=).+(?=&)|(?<=q=).+$/g
  const exp = expression.match(regQ) ? expression.match(regQ)![0] : null

  const ciTypeIds = [...selectCITypeIds]
  if (!ciTypeIds.length) {
    props.CITypeGroup.forEach((item: any) => {
      const ids = item.ci_types.map((ci_type: any) => ci_type.id)
      ciTypeIds.push(...ids)
    })
  }

  let copySearchValue = ''
  if (searchValue) {
    if (props.searchMode === SEARCH_MODE.COLUMN && props.searchValue.includes('\n')) {
      const values = searchValue.split('\n').filter((v) => v.trim())
      copySearchValue = `,(${values.join(';')})`
    } else {
      copySearchValue = `,*${searchValue}*`
    }
  }

  const text = `${ciTypeIds?.length ? `_type:(${ciTypeIds.join(';')})` : ''}${exp ? `,${exp}` : ''}${copySearchValue}`

  navigator.clipboard
    .writeText(text)
    .then(() => {
      message.success(t('copySuccess'))
    })
    .catch(() => {
      message.error(t('cmdb.ci.copyFailed'))
    })
}

function updateSearchMode(mode: string) {
  emit('updateSearchMode', mode)
}
</script>

<template>
  <div :class="['search-input', classType ? 'search-input-' + classType : '']">
    <div class="search-area">
      <a-input
        v-show="searchMode === SEARCH_MODE.NORMAL"
        :value="searchValue"
        class="search-input-component"
        :placeholder="t('cmdb.ciType.searchInputTip')"
        @change="handleChangeSearchValue"
        @press-enter="saveCondition(true)"
      >
        <template #prefix>
          <SearchOutlined class="search-icon" @click="saveCondition(true)" />
        </template>
      </a-input>

      <div v-show="searchMode === SEARCH_MODE.COLUMN" class="search-textarea-component">
        <a-textarea
          :value="searchValue"
          :autosize="{
            minRows: 3,
            maxRows: 3,
          }"
          :placeholder="t('cmdb.ciType.columnSearchInputTip')"
          @change="handleChangeSearchValue"
        />
        <div class="search-textarea-icon-wrap">
          <SearchOutlined class="search-icon" @click="saveCondition(true)" />

          <a-tooltip :title="t('cmdb.ciType.columnSearchTip')">
            <InfoCircleOutlined class="search-icon" />
          </a-tooltip>
        </div>
      </div>

      <div class="operation-area">
        <FilterPopover
          :c-i-type-group="CITypeGroup"
          :all-attributes-list="allAttributesList"
          :expression="expression"
          :select-c-i-type-ids="selectCITypeIds"
          @change-filter="changeFilter"
          @update-all-attributes-list="updateAllAttributesList"
          @save-condition="saveCondition"
        />

        <div class="search-mode-switch">
          <span
            v-for="item in searchModeList"
            :key="item.value"
            :class="['search-mode-switch-item', searchMode === item.value ? 'search-mode-switch-item-active' : '']"
            :style="{
              width: isZh ? '40px' : '65px',
            }"
            @click="updateSearchMode(item.value)"
          >
            {{ t(item.label) }}
          </span>

          <span
            class="search-mode-switch-slide"
            :style="{
              left: searchMode === SEARCH_MODE.COLUMN ? (isZh ? '44px' : '69px') : '4px',
              width: isZh ? '40px' : '65px',
            }"
          ></span>
        </div>
      </div>
    </div>

    <div v-if="copyText" class="expression-display">
      <span class="expression-display-text">{{ copyText }}</span>
      <CheckCircleOutlined class="expression-display-icon" @click="handleCopyExpression" />
    </div>
  </div>
</template>

<style lang="less" scoped>
.search-input {
  width: 100%;
  margin-bottom: 16px;

  .search-area {
    width: 100%;
    position: relative;

    .search-input-component {
      height: 48px;
      line-height: 48px;
      border-radius: 48px;
      width: 100%;
      background-color: #ffffff;
      font-size: 14px;

      &:hover {
        :deep(.ant-input) {
          background-color: @primary-color_5;
        }
      }

      :deep(.ant-input) {
        border: none;
        height: 48px;
        line-height: 48px;
        border-radius: 48px;

        &:focus {
          border: solid 1px @primary-color;
          background-color: #ffffff !important;
        }
      }
    }

    .search-textarea-component {
      position: relative;

      .search-textarea-icon-wrap {
        position: absolute;
        top: 10px;
        left: 12px;
        display: flex;
        flex-direction: column;
        row-gap: 6px;
      }

      &:hover {
        :deep(.ant-input) {
          background-color: @primary-color_5;
        }
      }

      :deep(.ant-input) {
        border: none;
        padding-left: 36px;
        resize: none;

        &:focus {
          border: solid 1px @primary-color;
          background-color: #ffffff !important;
        }
      }
    }

    .search-icon {
      color: @primary-color;
      font-size: 14px;
      cursor: pointer;
    }
  }

  .operation-area {
    position: absolute;
    display: flex;
    align-items: center;
    right: 0px;
    top: 0px;
    height: 48px;
    transform: translateX(100%);

    .search-mode-switch {
      display: flex;
      align-items: center;
      height: 32px;
      background-color: @primary-color_3;
      border-radius: 32px;
      position: relative;
      padding: 0 4px;
      margin-left: 14px;
      cursor: pointer;

      &-item {
        height: 24px;
        width: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 400;
        color: @text-color_2;
        z-index: 1;
        position: relative;

        &-active {
          color: @primary-color;
        }
      }

      &-slide {
        position: absolute;
        transition: left 0.2s;
        border-radius: 24px;
        background-color: #ffffff;
        height: 24px;
        top: 4px;
        width: 40px;
        z-index: 0;
      }
    }
  }

  .expression-display {
    display: flex;
    align-items: center;
    max-width: 100%;
    width: fit-content;
    margin-top: 8px;

    &-text {
      width: 100%;
      text-overflow: ellipsis;
      overflow: hidden;
      text-wrap: nowrap;
    }

    &-icon {
      margin-left: 8px;
      color: #00b42a;
      cursor: pointer;
    }
  }

  &-after {
    .search-area {
      max-width: 420px;
    }
  }
}
</style>
