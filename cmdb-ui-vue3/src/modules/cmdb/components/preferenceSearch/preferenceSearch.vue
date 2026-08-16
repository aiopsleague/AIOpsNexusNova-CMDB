<script setup lang="ts">
import { inject, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { DownOutlined, CloseOutlined } from '@ant-design/icons-vue'
import {
  getPreferenceSearch,
  savePreferenceSearch,
  deletePreferenceSearch as deletePreferenceSearchApi,
} from '@/modules/cmdb/api/preference'

/**
 * Saved-search chips shown inside the CI search bar. `savePreference` is exposed
 * so the parent can persist the current query state.
 */
interface PreferenceSearchItem {
  id: string | number
  name: string
  [key: string]: any
}

const emit = defineEmits<{
  (e: 'getQAndSort'): void
  (e: 'setParamsFromPreferenceSearch', item: PreferenceSearchItem): void
}>()

const { t } = useI18n()

const filterCompPreferenceSearch = inject<() => Record<string, unknown>>(
  'filterCompPreferenceSearch',
  () => ({})
)

const inputValue = ref('')
const inputVisible = ref(false)
const input = ref<{ focus: () => void }>()
const preferenceSearchList = ref<PreferenceSearchItem[]>([])
const currentPreferenceSearch = ref<string | number | null>(null)

watch(
  () => filterCompPreferenceSearch(),
  () => {
    getPreferenceSearchList()
  },
  { immediate: true, deep: true }
)

function getPreferenceSearchList() {
  const params = filterCompPreferenceSearch()
  getPreferenceSearch({ ...params }).then((res: any[]) => {
    if (!params) {
      preferenceSearchList.value = res.filter(
        (item) => !item.type_id && !item.ptv_id && !item.prv_id
      )
    } else {
      preferenceSearchList.value = res
    }
  })
}

function showInput() {
  inputVisible.value = true
  nextTick(() => {
    setTimeout(() => {
      input.value?.focus()
    }, 100)
  })
}

function handleInputConfirm() {
  emit('getQAndSort')
}

function savePreference({
  fuzzySearch,
  expression,
  currenCiType = undefined,
}: {
  fuzzySearch: string
  expression: string
  currenCiType?: unknown
}) {
  if (inputValue.value) {
    savePreferenceSearch({
      ...filterCompPreferenceSearch(),
      name: inputValue.value,
      option: { fuzzySearch, expression, currenCiType },
    }).then(() => {
      getPreferenceSearchList()
    })
  }
  inputValue.value = ''
  inputVisible.value = false
}

function deletePreferenceSearch(item: PreferenceSearchItem) {
  deletePreferenceSearchApi(item.id).then(() => {
    getPreferenceSearchList()
  })
}

function clickPreferenceSearch(item: PreferenceSearchItem, index?: number, isGotoFirst = false) {
  if (isGotoFirst && typeof index === 'number') {
    const cloned = JSON.parse(JSON.stringify(preferenceSearchList.value))
    const spliced = cloned.splice(index + 3, 1)
    cloned.unshift(JSON.parse(JSON.stringify(spliced[0])))
    preferenceSearchList.value = cloned
  }
  currentPreferenceSearch.value = item.id
  emit('setParamsFromPreferenceSearch', item)
}

defineExpose({ savePreference, currentPreferenceSearch })
</script>

<template>
  <div>
    <span :style="{ marginRight: '10px' }">
      <a-input
        v-if="inputVisible"
        ref="input"
        v-model:value="inputValue"
        type="text"
        size="small"
        :style="{ width: '78px' }"
        @blur="handleInputConfirm"
        @keyup.enter="handleInputConfirm"
      />
      <a v-else @click="showInput">{{ t('cmdb.components.saveQuery') }}</a>
    </span>
    <template v-for="(item, index) in preferenceSearchList.slice(0, 3)" :key="`${item.id}_${index}`">
      <span
        v-if="item.name.length > 6"
        :class="[
          'preference-search-tag',
          item.id === currentPreferenceSearch ? 'preference-search-tag-focus' : '',
        ]"
      >
        <a-tooltip :title="item.name">
          <span @click="clickPreferenceSearch(item)">{{ `${item.name.slice(0, 6)}...` }}</span>
        </a-tooltip>
        <a-popconfirm :title="t('cmdb.ciType.confirmDelete2')" @confirm="deletePreferenceSearch(item)">
          <CloseOutlined />
        </a-popconfirm>
      </span>
      <span
        v-else
        :class="[
          'preference-search-tag',
          item.id === currentPreferenceSearch ? 'preference-search-tag-focus' : '',
        ]"
      >
        <span @click="clickPreferenceSearch(item)">{{ item.name }}</span>
        <a-popconfirm :title="t('cmdb.ciType.confirmDelete2')" @confirm="deletePreferenceSearch(item)">
          <CloseOutlined />
        </a-popconfirm>
      </span>
    </template>
    <a-dropdown v-if="preferenceSearchList.length > 3">
      <a @click="(e: MouseEvent) => e.preventDefault()"><DownOutlined /></a>
      <template #overlay>
        <a-menu>
          <a-menu-item
            v-for="(item, index) in preferenceSearchList.slice(3)"
            :key="`${item.id}_${index}`"
            :style="{
              display: 'flex',
              flexDirection: 'row',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '12px',
            }"
          >
            <div
              :style="{
                display: 'inline-block',
                width: '120px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }"
              :title="item.name"
              @click="clickPreferenceSearch(item, index, true)"
            >
              {{ item.name }}
            </div>
            <a-popconfirm
              :title="t('cmdb.ciType.confirmDelete2')"
              :get-popup-container="(trigger: HTMLElement) => trigger.parentElement as HTMLElement"
              placement="left"
              @confirm="
                (e: MouseEvent) => {
                  e.preventDefault()
                  e.stopPropagation()
                  deletePreferenceSearch(item)
                }
              "
            >
              <CloseOutlined class="preference-search-delete" />
            </a-popconfirm>
          </a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>
  </div>
</template>

<style lang="less" scoped>
.preference-search-tag {
  cursor: pointer;
  border-radius: 2px;
  border: 1px solid #d9d9d9;
  display: inline-block;
  padding: 2px 7px;
  margin-right: 8px;
  > span {
    margin-right: 4px;
  }
  > i {
    font-size: 12px;
  }

  &:hover {
    color: @primary-color;
  }

  &-focus {
    background-color: @primary-color;
    color: #ffffff !important;
  }
}
.preference-search-delete {
  color: #a9a9a9;
  &:hover {
    color: #626262;
  }
}
</style>
