<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  CloseOutlined,
  DownOutlined,
  LoadingOutlined,
  SaveOutlined,
  SearchOutlined,
  UpOutlined,
} from '@ant-design/icons-vue'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import { getPreferenceSearch, savePreferenceSearch, deletePreferenceSearch } from '@/modules/cmdb/api/preference'

import FilterPopover from './filterPopover.vue'
import SaveConditionModal from './saveConditionModal.vue'
import dataEmptyImg from '@/assets/data_empty.png'

const props = withDefaults(
  defineProps<{
    CITypeGroup?: any[]
    sourceCIType?: number | undefined
    sourceCITypeSearchValue?: string
    sourceAllAttributesList?: any[]
    sourceExpression?: string
    targetCITypes?: Array<string | number>
    targetCITypeGroup?: Record<string, any>
    targetAllAttributesList?: any[]
    targetExpression?: string
    returnPath?: boolean
    allPath?: any[]
    selectedPath?: string[]
    isSearch?: boolean
    isSearchLoading?: boolean
  }>(),
  {
    CITypeGroup: () => [],
    sourceCIType: undefined,
    sourceCITypeSearchValue: '',
    sourceAllAttributesList: () => [],
    sourceExpression: '',
    targetCITypes: () => [],
    targetCITypeGroup: () => ({}),
    targetAllAttributesList: () => [],
    targetExpression: '',
    returnPath: false,
    allPath: () => [],
    selectedPath: () => [],
    isSearch: false,
    isSearchLoading: false,
  }
)

const emit = defineEmits<{
  (e: 'changeData', data: { name: string; value: any }): void
  (e: 'search'): void
  (e: 'hideSearchCondition'): void
  (e: 'clickFavor', option: Record<string, any>): void
}>()

const { t, locale } = useI18n()

const saveConditionVisible = ref(false)
const pathSelectVisible = ref(false)

const favorList = ref<any[]>([])
const relationSearchFavorKey = '__relation_favor__'

const pathDisplay = computed(() => {
  return (
    props.allPath
      ?.filter((path: any) => props.selectedPath?.includes?.(path?.value))
      ?.map((path: any) => path?.pathNames)
      ?.join(', ') || ''
  )
})

onMounted(() => {
  getFavorList()
})

async function getFavorList() {
  const list = await getPreferenceSearch({
    name: relationSearchFavorKey,
  })
  list.sort((a: any, b: any) => b.id - a.id)
  favorList.value = list
}

function normalizer(node: any) {
  return {
    id: node.id || -1,
    label: node.alias || node.name || t('cmdb.common.other'),
    title: node.alias || node.name || t('cmdb.common.other'),
    children: node.ci_types,
  }
}

function updateSourceCIType(value: number) {
  emit('changeData', {
    name: 'sourceCIType',
    value,
  })
}

function handleSourceCITypeSearchValueChange(e: Event) {
  const value = (e.target as HTMLInputElement).value
  emit('changeData', {
    name: 'sourceCITypeSearchValue',
    value,
  })
}

function changeSourceExpression(expression: string) {
  emit('changeData', {
    name: 'sourceExpression',
    value: expression,
  })
}

function handleTargetCITypeChange(value: Array<string | number>) {
  emit('changeData', {
    name: 'targetCITypes',
    value,
  })
}

function changeTargetExpression(expression: string) {
  emit('changeData', {
    name: 'targetExpression',
    value: expression,
  })
}

function handlePathChange(value: string[]) {
  emit('changeData', {
    name: 'selectedPath',
    value,
  })
}

function handleReturnPathChange(checked: boolean) {
  emit('changeData', {
    name: 'returnPath',
    value: checked,
  })
}

function clickSubmit() {
  if (props.isSearchLoading) {
    return
  }

  if (validateControl()) {
    return
  }

  emit('search')
}

function validateControl(): boolean {
  if (!props.sourceCIType) {
    message.warning(`${t('placeholder2')} ${t('cmdb.relationSearch.sourceCIType')}`)
    return true
  }

  if (!props.targetCITypes.length) {
    message.warning(`${t('placeholder2')} ${t('cmdb.relationSearch.targetCIType')}`)
    return true
  }

  if (!props.selectedPath.length) {
    message.warning(`${t('placeholder2')} ${t('cmdb.relationSearch.path')}`)
    return true
  }

  return false
}

function saveCondition() {
  if (validateControl()) {
    return
  }

  saveConditionVisible.value = true
}

async function handleSaveConditionOk({ name }: { name: string }) {
  if (favorList.value.length >= 10) {
    const deletePromises = favorList.value.slice(9).map((item) => {
      return deletePreferenceSearch(item.id)
    })
    await Promise.all(deletePromises)
  }

  const option = {
    name,
    sourceCIType: props.sourceCIType,
    searchValue: props.sourceCITypeSearchValue,
    sourceExpression: props.sourceExpression,
    targetCITypes: props.targetCITypes,
    targetExpression: props.targetExpression,
    selectedPath: props.selectedPath,
  }

  savePreferenceSearch({
    option: {
      ...option,
    },
    name: relationSearchFavorKey,
  }).then(() => {
    message.success(t('saveSuccess'))
    getFavorList()
  })
}

function deleteFavor(id: string | number) {
  deletePreferenceSearch(id).then(() => {
    message.success(t('deleteSuccess'))
    getFavorList()
  })
}

function hideSearchCondition() {
  emit('hideSearchCondition')
}

function clickPathSelectDropdown() {
  // Kept for parity with the legacy implementation; normal clicks do not close
  // the dropdown (only the source-CI-type re-open does).
}

function clickFavor(data: any) {
  if (data?.option) {
    emit('clickFavor', data.option)
  }
}

function handleSourceCITypeOpen() {
  pathSelectVisible.value = false
}
</script>

<template>
  <div
    class="search-condition"
    :style="{
      '--label-width': locale === 'en' ? '90px' : '60px',
    }"
  >
    <div class="search-condition-row">
      <div class="search-condition-label">
        {{ t('cmdb.relationSearch.sourceCIType') }}
      </div>

      <div class="search-condition-control">
        <Treeselect
          :model-value="sourceCIType"
          class="custom-treeselect custom-treeselect-white filter-content-ciTypes"
          :style="{
            width: '100%',
            zIndex: '1000',
            '--custom-height': '32px',
            '--custom-multiple-lineHeight': '32px',
          }"
          :multiple="false"
          :clearable="true"
          searchable
          :options="CITypeGroup"
          :limit="1"
          :limit-text="(count: number) => `+ ${count}`"
          :disable-branch-nodes="true"
          :placeholder="t('cmdb.relationSearch.sourceCITypeTip')"
          :normalizer="normalizer"
          @update:model-value="updateSourceCIType"
          @open="handleSourceCITypeOpen"
        >
          <template #option-label="{ node }">
            <div
              :title="node.label"
              :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }"
            >
              {{ node.label }}
            </div>
          </template>
        </Treeselect>

        <a-input-search
          class="search-condition-input"
          :placeholder="t('cmdb.relationSearch.sourceCITYpeInput')"
          :value="sourceCITypeSearchValue"
          @change="handleSourceCITypeSearchValueChange"
        />
      </div>

      <FilterPopover
        :all-attributes-list="sourceAllAttributesList"
        :select-c-i-type-ids="sourceCIType ? [sourceCIType] : []"
        :expression="sourceExpression"
        @change-expression="changeSourceExpression"
      />
    </div>

    <div class="search-condition-row">
      <div class="search-condition-label">
        {{ t('cmdb.relationSearch.targetCIType') }}
      </div>

      <div class="search-condition-control">
        <a-select
          :value="targetCITypes"
          show-search
          option-filter-prop="children"
          mode="multiple"
          :placeholder="t('cmdb.relationSearch.targetCITypeTip')"
          class="search-condition-select"
          @change="handleTargetCITypeChange"
        >
          <a-select-opt-group
            v-for="(group, index) in Object.keys(targetCITypeGroup)"
            :key="group"
            :label="t('cmdb.relationSearch.level') + `${index + 1}`"
          >
            <a-select-option
              v-for="citype in targetCITypeGroup[group]"
              :key="citype.id"
              :value="citype.id"
            >
              {{ citype.alias || citype.name }}
            </a-select-option>
          </a-select-opt-group>
        </a-select>
      </div>

      <FilterPopover
        :all-attributes-list="targetAllAttributesList"
        :select-c-i-type-ids="targetCITypes"
        :expression="targetExpression"
        @change-expression="changeTargetExpression"
      />
    </div>

    <div class="search-condition-row">
      <div class="search-condition-label">
        {{ t('cmdb.relationSearch.pathSelect') }}
      </div>

      <div class="search-condition-control">
        <a-dropdown v-model:open="pathSelectVisible" :trigger="['click']" :get-popup-container="(trigger: HTMLElement) => trigger.parentElement">
          <a-input
            :value="pathDisplay"
            read-only
            :placeholder="t('cmdb.relationSearch.pathSelectTip')"
            class="search-condition-input"
            @click="(e: MouseEvent) => e.preventDefault()"
          >
            <template #suffix>
              <DownOutlined class="search-condition-input-suffix" />
            </template>
          </a-input>
          <template #overlay>
            <div @click="clickPathSelectDropdown">
              <template v-if="allPath.length">
                <a-checkbox-group
                  :value="selectedPath"
                  class="search-condition-checkbox"
                  @change="handlePathChange"
                >
                  <a-checkbox
                    v-for="path in allPath"
                    :key="path.value"
                    :value="path.value"
                    class="search-condition-checkbox-item"
                  >
                    <a-tooltip :title="path.pathNames">
                      <span class="search-condition-checkbox-item-name">
                        {{ path.pathNames }}
                      </span>
                    </a-tooltip>
                  </a-checkbox>
                </a-checkbox-group>

                <div class="search-condition-path-divider"></div>

                <div class="search-condition-path-switch">
                  <span>{{ t('cmdb.relationSearch.returnPath') }}</span>
                  <a-switch :checked="returnPath" @change="handleReturnPathChange" />
                </div>
              </template>

              <div v-else class="search-condition-path-null">
                <img :src="dataEmptyImg" class="search-condition-path-null-img" />
                <div class="search-condition-path-null-text">{{ t('noData') }}</div>
              </div>
            </div>
          </template>
        </a-dropdown>
      </div>

      <div
        :class="['search-condition-submit', isSearchLoading ? 'search-condition-submit-loading' : '']"
        @click="clickSubmit"
      >
        <LoadingOutlined v-if="isSearchLoading" class="search-condition-submit-icon" />
        <SearchOutlined v-else class="search-condition-submit-icon" />
      </div>
    </div>
    <div class="search-condition-favor">
      <div class="search-condition-favor-list">
        <div
          v-for="item in favorList"
          :key="item.id"
          class="search-condition-favor-item"
          @click="clickFavor(item)"
        >
          <div class="search-condition-favor-name">
            {{ item.option.name }}
          </div>
          <CloseOutlined class="search-condition-favor-close" @click.stop="deleteFavor(item.id)" />
        </div>
      </div>
      <div class="search-condition-favor-right">
        <a class="search-condition-save" @click="saveCondition">
          <SaveOutlined class="search-condition-save-icon" />
          <span class="search-condition-save-text">
            {{ t('cmdb.relationSearch.saveCondition') }}
          </span>
        </a>

        <div v-if="isSearch" class="search-condition-hide" @click="hideSearchCondition">
          <UpOutlined class="search-condition-hide-icon" />
        </div>
      </div>
    </div>

    <SaveConditionModal
      :visible="saveConditionVisible"
      @ok="handleSaveConditionOk"
      @cancel="saveConditionVisible = false"
    />
  </div>
</template>

<style lang="less" scoped>
.search-condition {
  &-row {
    display: flex;
    align-items: center;
    margin-bottom: 24px;
    column-gap: 15px;
  }

  &-label {
    font-size: 14px;
    font-weight: 400;
    color: #000000;
    width: var(--label-width);
  }

  &-control {
    display: flex;
    align-items: center;
    column-gap: 12px;
    width: 500px;

    :deep(.ant-dropdown-content) {
      background-color: #ffffff;
      padding: 14px 18px;
      width: 500px;
    }

    :deep(.filter-content-ciTypes) {
      &:not(.vue-treeselect--disabled):not(.vue-treeselect--focused) {
        .vue-treeselect__control {
          border: solid 1px transparent;

          &:hover {
            border-color: @primary-color;
          }
        }
      }
    }
  }

  &-input {
    width: 100%;

    :deep(.ant-input) {
      border: solid 1px transparent;
      box-shadow: none;
      cursor: pointer;

      &:hover {
        border-color: @primary-color;
      }
    }

    &-suffix {
      color: #cacdd9;
    }
  }

  &-select {
    width: 100%;

    :deep(.ant-select-selector) {
      border: solid 1px transparent;
      box-shadow: none;

      &:hover {
        border-color: @primary-color;
      }
    }
  }

  &-path {
    &-divider {
      width: 100%;
      margin: 20px 0;
      height: 1px;
      background-color: #e4e7ed;
    }

    &-switch {
      display: flex;
      align-items: center;
      column-gap: 16px;
    }
  }

  &-checkbox {
    display: flex;
    flex-direction: column;
    max-height: 300px;
    overflow-y: auto;
    overflow-x: hidden;

    &-item {
      margin: 0px;
      display: flex;
      align-items: center;

      :deep(& > span:first-child) {
        flex-shrink: 0;
      }

      :deep(& > span:last-child) {
        width: 100%;
      }

      &-name {
        overflow: hidden;
        text-wrap: nowrap;
        text-overflow: ellipsis;
        display: inline-block;
        max-width: 100%;
      }

      &:not(:last-child) {
        margin-bottom: 16px;
      }
    }
  }

  &-path-null {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;

    &-img {
      width: 100px;
    }

    &-text {
      margin-top: 12px;
      color: #a5a9bc;
    }
  }

  &-submit {
    width: 32px;
    height: 32px;
    cursor: pointer;
    border-radius: 2px;
    background-color: #2f54eb;
    display: flex;
    align-items: center;
    justify-content: center;

    &-icon {
      font-size: 12px;
      color: #ffffff;
    }

    &-loading {
      background-color: #2f54eb90;
    }

    &:hover {
      background-color: #2f54eb90;
    }
  }

  &-favor {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 24px;
    column-gap: 15px;

    &-list {
      max-width: 500px;
      display: flex;
      align-items: center;
      column-gap: 14px;
      overflow-x: auto;
      overflow-y: hidden;
      padding-bottom: 4px;
    }

    &-name {
      font-size: 12px;
      font-weight: 400;
      color: #4e5969;
      overflow: hidden;
      text-overflow: ellipsis;
      text-wrap: nowrap;
    }

    &-close {
      font-size: 12px;
      color: #4e5969;
      flex-shrink: 0;

      &:hover {
        color: #4e596980;
      }
    }

    &-right {
      display: flex;
      align-items: center;
      flex-shrink: 0;
    }

    &-item {
      display: flex;
      align-items: center;
      max-width: 150px;
      background-color: #ebeff8;
      border-radius: 28px;
      padding: 2px 12px;
      column-gap: 3px;
      cursor: pointer;

      &:hover {
        background-color: @primary-color_4;

        .search-condition-favor-name {
          color: @primary-color;
        }

        .search-condition-favor-close {
          color: @primary-color;
        }
      }
    }
  }

  &-save {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    font-size: 12px;
    column-gap: 7px;
  }

  &-hide {
    width: 18px;
    height: 18px;
    background-color: #ebeff8;
    border-radius: 1px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    margin-left: 22px;

    &-icon {
      font-size: 12px;
      color: #86909c;
    }

    &:hover {
      background-color: @primary-color_4;

      .search-condition-hide-icon {
        color: @primary-color;
      }
    }
  }
}
</style>
