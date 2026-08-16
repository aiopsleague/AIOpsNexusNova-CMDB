<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { DISCOVERY_CATEGORY_TYPE } from '@/modules/cmdb/constants'

const props = withDefaults(
  defineProps<{
    tableData?: Record<string, any>[]
    ciTypeAttributes?: Record<string, any>[]
    ruleType?: string
    uniqueKey?: string
  }>(),
  {
    tableData: () => [],
    ciTypeAttributes: () => [],
    ruleType: '',
    uniqueKey: '',
  }
)

const { t } = useI18n()

const leftTableRef = ref()
const rightTableRef = ref()

const ciTypeAttrOptions = computed(() =>
  props.ciTypeAttributes.map((attr) => ({
    value: attr.name,
    label: attr.alias || attr.name,
  }))
)

function getTableData() {
  const leftTable = leftTableRef.value
  const rightTable = rightTableRef.value
  const { fullData: leftFullData } = leftTable.getTableData()
  const { fullData: rightFullData } = rightTable.getTableData()
  const fullData = leftFullData.map((item: any, index: number) => ({
    ...(rightFullData?.[index] || {}),
    ...(item || {}),
  }))
  return { fullData }
}

defineExpose({ getTableData })
</script>

<template>
  <div class="attr-map-table">
    <div class="attr-map-table-left">
      <div class="attr-map-table-title">{{ t('cmdb.ciType.attributes') }}</div>
      <vxe-table
        ref="leftTableRef"
        size="mini"
        :data="tableData"
        :scroll-y="{ enabled: true }"
        :min-height="78"
      >
        <vxe-column field="attr" :title="t('name')">
          <template #default="{ row }">
            <div class="attr-select">
              <span
                v-if="uniqueKey"
                :style="{ opacity: uniqueKey === row.name ? 1 : 0 }"
                class="attr-select-unique"
              >
                *
              </span>
              <a-select
                v-model:value="row.attr"
                :placeholder="t('cmdb.ciType.attrMapTableAttrPlaceholder')"
                show-search
                allow-clear
                :options="ciTypeAttrOptions"
                style="width: 100%; height: 28px; line-height: 28px"
                class="attr-map-table-left-select"
              />
            </div>
          </template>
        </vxe-column>
      </vxe-table>
    </div>
    <div class="attr-map-table-right">
      <div class="attr-map-table-title">{{ t('cmdb.ciType.autoDiscovery') }}</div>
      <vxe-table
        ref="rightTableRef"
        size="mini"
        show-overflow
        show-header-overflow
        :data="tableData"
        :scroll-y="{ enabled: true }"
        :row-config="{ height: 42 }"
        :min-height="78"
      >
        <vxe-column field="name" :title="t('name')"></vxe-column>
        <vxe-column field="type" :title="t('type')"></vxe-column>
        <vxe-column v-if="ruleType !== DISCOVERY_CATEGORY_TYPE.AGENT" field="example" :title="t('cmdb.components.example')">
          <template #default="{ row }">
            <span v-if="row.type === 'json'">{{ JSON.stringify(row.example) }}</span>
            <span v-else>{{ row.example }}</span>
          </template>
        </vxe-column>
        <vxe-column field="desc" :title="t('desc')"></vxe-column>
      </vxe-table>
    </div>
    <div class="attr-map-table-link">
      <div v-for="item in tableData" :key="item._X_ROW_KEY" class="attr-map-table-link-item">
        <div class="attr-map-table-link-left"></div>
        <div class="attr-map-table-link-right"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.attr-map-table {
  display: flex;
  justify-content: space-between;
  position: relative;
}
.attr-map-table-left {
  width: 30%;
}
.attr-map-table-right {
  width: calc(70% - 60px);
}
.attr-map-table-title {
  font-size: 14px;
  font-weight: 700;
  line-height: 22px;
  margin-bottom: 12px;
}
.attr-map-table-link {
  position: absolute;
  z-index: 10;
  bottom: 0;
  left: calc(30% - 6px);
  width: 66px;
}
.attr-map-table-link-item {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: calc(42px - 12px);
  width: 100%;
}
.attr-map-table-link-item:last-child {
  margin-bottom: calc(21px - 6px);
}
.attr-map-table-link-item::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  height: 1px;
  background-color: #e4e7ed;
  z-index: -1;
}
.attr-map-table-link-left {
  width: 12px;
  height: 12px;
  background-color: #2f54eb;
  border: solid 3px #e1efff;
  border-radius: 50%;
}
.attr-map-table-link-right {
  width: 2px;
  height: 10px;
  border-radius: 1px 0 0 1px;
  background-color: #2f54eb;
}
.attr-select {
  display: flex;
  align-items: center;
  gap: 10px;
}
.attr-select-unique {
  color: #fd4c6a;
}
</style>
