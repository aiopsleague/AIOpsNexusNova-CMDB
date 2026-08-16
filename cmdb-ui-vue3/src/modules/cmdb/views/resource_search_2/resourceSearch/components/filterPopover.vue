<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { FilterOutlined } from '@ant-design/icons-vue'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import ConditionFilter from '@/modules/cmdb/components/conditionFilter/index.vue'
import { cloneDeep } from '@/modules/cmdb/utils/helper'

const props = withDefaults(
  defineProps<{
    expression?: string
    selectCITypeIds?: Array<string | number>
    CITypeGroup?: any[]
    allAttributesList?: any[]
  }>(),
  {
    expression: '',
    selectCITypeIds: () => [],
    CITypeGroup: () => [],
    allAttributesList: () => [],
  }
)

const emit = defineEmits<{
  (e: 'changeFilter', data: { name: string; value: any }): void
  (e: 'updateAllAttributesList', value: Array<string | number>): void
  (e: 'saveCondition', isSubmit: boolean): void
}>()

const { t } = useI18n()

const visible = ref(false)
const conditionFilterRef = ref<InstanceType<typeof ConditionFilter>>()
const formLayout = {
  labelCol: { span: 3 },
  wrapperCol: { span: 15 },
}
const lastCiType = ref<Array<string | number>>([])

function handleVisibleChange(open: boolean) {
  if (open) {
    nextTick(() => {
      conditionFilterRef.value?.init(true, false)
    })
  }
}

function normalizer(node: any) {
  return {
    id: node.id || -1,
    label: node.alias || node.name || t('cmdb.common.other'),
    title: node.alias || node.name || t('cmdb.common.other'),
    children: node.ci_types,
  }
}

function openCiTypeGroup() {
  lastCiType.value = cloneDeep(props.selectCITypeIds)
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
  emit('changeFilter', {
    name: 'selectCITypeIds',
    value,
  })
}

function setExpFromFilter(filterExp: string) {
  const regSort = /(?<=sort=).+/g
  const expSort = props.expression.match(regSort) ? props.expression.match(regSort)![0] : undefined
  let expression = ''
  if (filterExp) {
    expression = `q=${filterExp}`
  }
  if (expSort) {
    expression += `&sort=${expSort}`
  }
  emit('changeFilter', {
    name: 'expression',
    value: expression,
  })
}

function saveCondition(isSubmit: boolean) {
  conditionFilterRef.value?.handleSubmit()
  nextTick(() => {
    emit('saveCondition', isSubmit)
    visible.value = false
  })
}
</script>

<template>
  <a-popover v-model:open="visible" trigger="click" placement="bottom" @open-change="handleVisibleChange">
    <div class="filter-btn">
      <FilterOutlined class="filter-btn-icon" />
      <span class="filter-btn-title">{{ t('cmdb.ciType.advancedFilter') }}</span>
    </div>
    <template #content>
      <div class="filter-content">
        <a-form>
          <a-form-item
            :label="t('cmdb.ciType.ciType')"
            :label-col="formLayout.labelCol"
            :wrapper-col="formLayout.wrapperCol"
          >
            <Treeselect
              :model-value="selectCITypeIds"
              class="custom-treeselect custom-treeselect-bgcAndBorder filter-content-ciTypes"
              :style="{
                width: '400px',
                zIndex: '1000',
                '--custom-height': '32px',
                '--custom-bg-color': '#FFF',
                '--custom-border': '1px solid #d9d9d9',
                '--custom-multiple-lineHeight': '32px',
              }"
              :multiple="true"
              :clearable="true"
              searchable
              :options="CITypeGroup"
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
          </a-form-item>

          <a-form-item
            :label="t('cmdb.ciType.filterPopoverLabel')"
            :label-col="formLayout.labelCol"
            :wrapper-col="formLayout.wrapperCol"
            class="filter-content-condition-filter"
          >
            <ConditionFilter
              ref="conditionFilterRef"
              :can-search-preference-attr-list="allAttributesList"
              :expression="expression"
              :c-i-type-ids="selectCITypeIds"
              :is-dropdown="false"
              @set-exp-from-filter="setExpFromFilter"
            />
          </a-form-item>
        </a-form>

        <div class="filter-content-action">
          <a-button size="small" @click="saveCondition(false)">
            {{ t('cmdb.ciType.saveCondition') }}
          </a-button>
          <a-button type="primary" size="small" @click="saveCondition(true)">
            {{ t('confirm') }}
          </a-button>
        </div>
      </div>
    </template>
  </a-popover>
</template>

<style lang="less" scoped>
.filter-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  margin-left: 13px;
  cursor: pointer;

  &-icon {
    color: #2f54eb;
    font-size: 12px;
  }

  &-title {
    font-size: 14px;
    font-weight: 400;
    color: #2f54eb;
    margin-left: 3px;
  }
}

.filter-content {
  width: 600px;

  &-ciTypes {
    :deep(.vue-treeselect__value-container) {
      line-height: 32px;
    }
  }

  &-condition-filter {
    max-height: 250px;
    margin-bottom: 0px;
  }

  &-action {
    width: 100%;
    margin-top: 12px;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    column-gap: 21px;
  }
}
</style>
