<script setup lang="ts">
import { computed, inject, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { SearchOutlined, QuestionCircleOutlined, FilterOutlined, DownOutlined, CheckCircleOutlined } from '@ant-design/icons-vue'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import FilterComp from '@/components/CMDBFilterComp/index.vue'
import { getCITypeGroups } from '@/modules/cmdb/api/ciTypeGroup'
import { CI_DEFAULT_ATTR } from '@/modules/cmdb/constants'

/**
 * Shared CI search bar. Supports fuzzy search, CI type group selection and the
 * expression-based condition filter. The expression / fuzzySearch refs are
 * exposed so the parent list can read the current query state.
 */
const props = withDefaults(
  defineProps<{
    preferenceAttrList: Array<Record<string, any>>
    isShowExpression?: boolean
    typeId?: number | null
    type?: string
    selectedRowKeys?: Array<string | number>
  }>(),
  {
    isShowExpression: true,
    typeId: null,
    type: '',
    selectedRowKeys: () => [],
  }
)

const emit = defineEmits<{
  (e: 'updateAllAttributesList', value: unknown): void
  (e: 'refresh', value: boolean): void
  (e: 'copyExpression'): void
}>()

const { t } = useI18n()
const route = useRoute()

const filterComp = ref<InstanceType<typeof FilterComp>>()

const setPreferenceSearchCurrent = inject<((id: number | null) => void) | null>(
  'setPreferenceSearchCurrent',
  null
)

const isFocusExpression = ref(false)
const expression = ref('')
const fuzzySearch = ref('')
const currenCiType = ref<Array<string | number>>([])
const ciTypeGroup = ref<any[]>([])
const lastCiType = ref<Array<string | number>>([])

const placeholder = computed(() =>
  isFocusExpression.value ? t('cmdb.components.ciSearchTips2') : t('cmdb.ciType.expr')
)
const width = computed(() => '200px')
const canSearchPreferenceAttrList = computed(() =>
  props.preferenceAttrList.filter(
    (item) =>
      item.value_type !== '6' &&
      ![CI_DEFAULT_ATTR.UPDATE_USER, CI_DEFAULT_ATTR.UPDATE_TIME].includes(item.name)
  )
)

watch(
  () => route.path,
  () => {
    expression.value = ''
    fuzzySearch.value = ''
  }
)

function normalizer(node: any) {
  return {
    id: node.id || -1,
    label: node.alias || node.name || t('cmdb.common.other'),
    title: node.alias || node.name || t('cmdb.common.other'),
    children: node.ci_types,
  }
}

function loadCITypeGroups() {
  getCITypeGroups({ need_other: true }).then((res: any[]) => {
    ciTypeGroup.value = res
      .filter((item) => item.ci_types && item.ci_types.length)
      .map((item) => {
        item.id = `parent_${item.id || -1}`
        return JSON.parse(JSON.stringify(item))
      })
  })
}

function reset() {
  expression.value = ''
  fuzzySearch.value = ''
  if (props.type !== 'resourceView') {
    currenCiType.value = []
  }
  emitRefresh()
}

function setExpFromFilter(filterExp: string) {
  const regSort = /(?<=sort=).+/g
  const expSort = expression.value.match(regSort) ? expression.value.match(regSort)![0] : undefined
  let next = ''
  if (filterExp) {
    next = `q=${filterExp}`
  }
  if (expSort) {
    next += `&sort=${expSort}`
  }
  expression.value = next
  emitRefresh()
}

function handleSubmit() {
  filterComp.value?.handleSubmit()
}

function openCiTypeGroup() {
  lastCiType.value = JSON.parse(JSON.stringify(currenCiType.value))
}

function closeCiTypeGroup(value: Array<string | number>) {
  if (JSON.stringify(value) !== JSON.stringify(lastCiType.value)) {
    emit('updateAllAttributesList', value)
  }
}

function inputCiTypeGroup(value: Array<string | number>) {
  if (!value || !value.length) {
    emit('updateAllAttributesList', value)
  }
}

function emitRefresh() {
  setPreferenceSearchCurrent?.(null)
  nextTick(() => {
    emit('refresh', true)
  })
}

function handleCopyExpression() {
  emit('copyExpression')
}

onMounted(() => {
  if (props.type === 'resourceSearch') {
    loadCITypeGroups()
  }
  if (props.typeId) {
    currenCiType.value = [props.typeId]
  }
})

defineExpose({ fuzzySearch, expression, handleSubmit })
</script>

<template>
  <div>
    <div id="search-form-bar" class="search-form-bar">
      <div :style="{ display: 'inline-flex', alignItems: 'center' }">
        <a-space>
          <Treeselect
            v-if="type === 'resourceSearch'"
            v-model="currenCiType"
            class="custom-treeselect"
            :style="{
              width: '200px',
              marginRight: '10px',
              '--custom-height': '32px',
              '--custom-multiple-lineHeight': '16px',
            }"
            :multiple="true"
            :clearable="true"
            searchable
            :options="ciTypeGroup"
            :limit="1"
            :limit-text="(count: number) => `+ ${count}`"
            value-consists-of="LEAF_PRIORITY"
            :placeholder="t('cmdb.ciType.ciType')"
            :normalizer="normalizer"
            @close="closeCiTypeGroup"
            @open="openCiTypeGroup"
            @update:model-value="inputCiTypeGroup"
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
          <a-input
            v-model:value="fuzzySearch"
            :style="{ display: 'inline-block', width: '200px' }"
            :placeholder="t('cmdb.components.pleaseSearch')"
            @press-enter="emitRefresh"
          >
            <template #suffix>
              <SearchOutlined
                :class="['search-form-bar-input-icon', fuzzySearch ? 'search-form-bar-input-icon-focus' : '']"
                @click="emitRefresh"
              />
            </template>
            <template #prefix>
              <a-tooltip placement="bottom" :overlay-style="{ maxWidth: '550px', whiteSpace: 'pre-line' }">
                <template #title>
                  {{ t('cmdb.components.ciSearchTips') }}
                </template>
                <a><QuestionCircleOutlined /></a>
              </a-tooltip>
            </template>
          </a-input>
          <a-button @click="reset">{{ t('reset') }}</a-button>
          <FilterComp
            ref="filterComp"
            :can-search-preference-attr-list="canSearchPreferenceAttrList"
            :expression="expression"
            placement="bottomLeft"
            @set-exp-from-filter="setExpFromFilter"
          >
            <template #popover_item>
              <div class="search-form-bar-filter">
                <FilterOutlined class="search-form-bar-filter-icon" />
                {{ t('cmdb.components.conditionFilter') }}
                <DownOutlined class="search-form-bar-filter-icon" :style="{ color: '#d9d9d9' }" />
              </div>
            </template>
          </FilterComp>
          <a-input
            v-if="isShowExpression"
            v-show="!selectedRowKeys.length"
            v-model:value="expression"
            :class="{ 'ci-searchform-expression': true, 'ci-searchform-expression-has-value': expression }"
            :style="{ width }"
            :placeholder="placeholder"
            @focus="isFocusExpression = true"
            @blur="isFocusExpression = false"
            @keyup.enter="emitRefresh"
          >
            <template #suffix>
              <CheckCircleOutlined @click="handleCopyExpression" />
            </template>
          </a-input>
          <slot></slot>
        </a-space>
      </div>
      <a-space>
        <slot name="extraContent"></slot>
        <!-- TODO: wire up MetadataDrawer for the relationView attribute description trigger -->
      </a-space>
    </div>
  </div>
</template>

<style lang="less">
.ci-searchform-expression {
  > input {
    border-bottom: 2px solid #d9d9d9;
    border-top: none;
    border-left: none;
    border-right: none;
    &:hover,
    &:focus {
      border-bottom: 2px solid @primary-color;
    }
    &:focus {
      box-shadow: 0 2px 2px -2px #1f78d133;
    }
  }
  .ant-input-suffix {
    color: #d9d9d9;
    cursor: pointer;
  }
}
.ci-searchform-expression-has-value .ant-input-suffix {
  color: @func-color_3;
}
.cmdb-search-form {
  .ant-form-item-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>

<style lang="less" scoped>
.search-form-bar {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 32px;

  &-input-icon {
    cursor: pointer;
    color: #d9d9d9;

    &-focus {
      color: @primary-color;
    }
  }

  .search-form-bar-filter {
    .ops_display_wrapper(transparent);

    &:hover {
      color: @primary-color;
    }

    .search-form-bar-filter-icon {
      color: @primary-color;
      font-size: 12px;
    }
  }
}
</style>
