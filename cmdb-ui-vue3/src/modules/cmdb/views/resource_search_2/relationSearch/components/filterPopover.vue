<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { FilterOutlined } from '@ant-design/icons-vue'
import ConditionFilter from '@/modules/cmdb/components/conditionFilter/index.vue'

const props = withDefaults(
  defineProps<{
    allAttributesList?: any[]
    selectCITypeIds?: Array<string | number>
    expression?: string
  }>(),
  {
    allAttributesList: () => [],
    selectCITypeIds: () => [],
    expression: '',
  }
)

const emit = defineEmits<{
  (e: 'changeExpression', expression: string): void
}>()

const { t } = useI18n()

const visible = ref(false)
const conditionFilterRef = ref<InstanceType<typeof ConditionFilter>>()

function handleVisibleChange(open: boolean) {
  if (open) {
    nextTick(() => {
      conditionFilterRef.value?.init(true, false)
    })
  }
}

function clickSubmit() {
  conditionFilterRef.value?.handleSubmit()
  visible.value = false
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

  emit('changeExpression', expression)
}
</script>

<template>
  <a-popover v-model:open="visible" trigger="click" placement="bottomRight" @open-change="handleVisibleChange">
    <div class="search-condition-filter">
      <FilterOutlined class="search-condition-filter-icon" />

      <div v-if="expression" class="search-condition-filter-flag"></div>
    </div>
    <template #content>
      <div class="search-condition-content">
        <div class="search-condition-content-title">
          {{ t('cmdb.relationSearch.conditionFilter') }}:
        </div>

        <ConditionFilter
          ref="conditionFilterRef"
          :can-search-preference-attr-list="allAttributesList"
          :expression="expression"
          :c-i-type-ids="selectCITypeIds"
          :is-dropdown="false"
          @set-exp-from-filter="setExpFromFilter"
        />

        <div class="search-condition-filter-submit">
          <a-button type="primary" size="small" @click="clickSubmit()">
            {{ t('confirm') }}
          </a-button>
        </div>
      </div>
    </template>
  </a-popover>
</template>

<style lang="less" scoped>
.search-condition-filter {
  height: 32px;
  width: 32px;
  background-color: #ffffff;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;

  &-flag {
    position: absolute;
    right: -5px;
    bottom: -5px;
    width: 10px;
    height: 10px;
    border-radius: 10px;
    background-color: #00b42a22;
    display: flex;
    align-items: center;
    justify-content: center;

    &::after {
      content: '';
      width: 5px;
      height: 5px;
      border-radius: 5px;
      background-color: #00b42a;
    }
  }

  &-icon {
    font-size: 12px;
    color: #a5a9bc;
  }

  &:hover {
    .search-condition-filter-icon {
      color: #2f54eb;
    }
  }
}

.search-condition-content {
  min-width: 500px;

  &-title {
    font-size: 14px;
    font-weight: 400;
    color: #4e5969;
  }
}

.search-condition-filter-submit {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
