<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { CopyOutlined, MinusCircleOutlined, PlusCircleOutlined, PlusOutlined } from '@ant-design/icons-vue'
import EmployeeTreeSelect from '@/views/setting/components/employeeTreeSelect.vue'
import { ruleTypeList, expList, compareTypeList } from './constants'
import { USER_FILTER_SELECT } from '../constants'

interface UserFilterRule {
  id: string
  relation: string
  column: string | null
  operator: number
  value: any
}

const { t } = useI18n()

const ruleList = ref<UserFilterRule[]>([])
const userFilterSelect = ref<any[]>(USER_FILTER_SELECT)

function genId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function setRuleList(list?: UserFilterRule[]) {
  ruleList.value = list?.length ? list : []
}

function handleAddRule() {
  ruleList.value = [
    ...ruleList.value,
    {
      id: genId(),
      relation: '&',
      column: userFilterSelect.value?.[0]?.value ?? null,
      operator: 1,
      value: null,
    },
  ]
}

function handleCopyRule(item: UserFilterRule) {
  ruleList.value = [...ruleList.value, { ...item, id: genId() }]
}

function handleDeleteRule(item: UserFilterRule) {
  ruleList.value = ruleList.value.filter((r) => r.id !== item.id)
}

function getRuleList(): any[] {
  if (!ruleList.value.length) {
    return []
  }
  const list = cloneDeep(ruleList.value)
  list.forEach((item, index) => {
    if (item.column === 'direct_supervisor_id') {
      list[index].value = item.value ? (String(item.value).includes('-') ? +String(item.value).split('-')[1] : +item.value) : 0
    }
  })
  if (list.length > 0) {
    list[0].relation = '&'
  }
  return list.map((rule) => {
    const copy: Partial<UserFilterRule> = { ...rule }
    delete copy.id
    return copy
  })
}

function handleChangeExp(node: { value: number }, index: number) {
  const value = node.value
  const list = cloneDeep(ruleList.value)
  if (value === 7 || value === 8) {
    list[index] = { ...list[index], value: null, operator: value }
  } else {
    list[index] = { ...list[index], operator: value }
  }
  ruleList.value = list
}

function isChoiceByProperty(column: string | null): boolean {
  const found = userFilterSelect.value.find((item) => item.value === column)
  return found ? Boolean(found.is_choice) : false
}

function getChoiceValueByProperty(column: string | null): any[] {
  const found = userFilterSelect.value.find((item) => item.value === column)
  return found ? found.choice_value || [] : []
}

defineExpose({ setRuleList, getRuleList })
</script>

<template>
  <div class="user-filter">
    <a-button v-if="!ruleList.length" type="primary" ghost size="small" class="add-btn" @click="handleAddRule">
      <template #icon><PlusOutlined /></template>
      {{ t('add') }}
    </a-button>
    <template v-else>
      <a-space v-for="(item, index) in ruleList" :key="item.id" :style="{ display: 'flex', marginBottom: '10px' }">
        <div :style="{ width: '50px', height: '24px', position: 'relative' }">
          <treeselect
            v-if="index"
            v-model="item.relation"
            class="custom-treeselect"
            :style="{ width: '50px', '--custom-height': '36px', position: 'absolute', top: '-30px', left: 0 }"
            :multiple="false"
            :clearable="false"
            searchable
            :options="ruleTypeList"
            :normalizer="
              (node: any) => ({ id: node.value, label: t(node.label), children: node.children })
            "
          />
        </div>
        <treeselect
          v-model="item.column"
          class="custom-treeselect"
          :style="{ width: '140px', '--custom-height': '36px' }"
          :multiple="false"
          :clearable="false"
          searchable
          :options="userFilterSelect"
          :max-height="150"
          :normalizer="
            (node: any) => ({ id: node.value, label: t(node.label), children: node.children })
          "
        >
          <template #option-label="{ node }">
            <div :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }">
              <a-tooltip :title="t(node.label)">
                {{ t(node.label) }}
              </a-tooltip>
            </div>
          </template>
          <template #value-label="{ node }">
            <div :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }">
              <a-tooltip :title="t(node.label)">
                {{ t(node.label) }}
              </a-tooltip>
            </div>
          </template>
        </treeselect>
        <treeselect
          v-model="item.operator"
          class="custom-treeselect"
          :style="{ width: '90px', '--custom-height': '36px' }"
          :multiple="false"
          :clearable="false"
          searchable
          :options="[...expList, ...compareTypeList]"
          :max-height="150"
          :normalizer="
            (node: any) => ({ id: node.value, label: t(node.label), children: node.children })
          "
          @select="(node: any) => handleChangeExp(node, index)"
        >
          <template #option-label="{ node }">
            <div :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }">
              <a-tooltip :title="t(node.label)">
                {{ t(node.label) }}
              </a-tooltip>
            </div>
          </template>
          <template #value-label="{ node }">
            <div :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }">
              <a-tooltip :title="t(node.label)">
                {{ t(node.label) }}
              </a-tooltip>
            </div>
          </template>
        </treeselect>
        <treeselect
          v-if="isChoiceByProperty(item.column) && (item.operator === 1 || item.operator === 2)"
          v-model="item.value"
          class="custom-treeselect"
          :style="{ width: '100px', '--custom-height': '36px' }"
          :multiple="false"
          :clearable="false"
          searchable
          :options="getChoiceValueByProperty(item.column)"
          :placeholder="t('cs.components.selectPlaceholder')"
          :normalizer="
            (node: any) => ({ id: node.value, label: t(node.label), children: node.children })
          "
        >
          <template #option-label="{ node }">
            <div :title="t(node.label)" :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }">
              {{ t(node.label) }}
            </div>
          </template>
        </treeselect>
        <EmployeeTreeSelect
          v-else-if="item.column === 'direct_supervisor_id' && (item.operator === 1 || item.operator === 2)"
          v-model:value="item.value"
          :id-type="3"
          class-name="custom-treeselect"
        />
        <a-input
          v-else-if="item.operator !== 7 && item.operator !== 8"
          v-model:value="item.value"
          size="small"
          class="ops-input"
        />
        <a-tooltip :title="t('cs.components.copy')">
          <a class="operation" @click="handleCopyRule(item)"><CopyOutlined /></a>
        </a-tooltip>
        <a-tooltip :title="t('delete')">
          <a class="operation" @click="handleDeleteRule(item)"><MinusCircleOutlined /></a>
        </a-tooltip>
        <a-tooltip :title="t('add')">
          <a class="operation" @click="handleAddRule"><PlusCircleOutlined /></a>
        </a-tooltip>
      </a-space>
    </template>
  </div>
</template>

<style lang="less" scoped>
.user-filter {
  display: flex;
  flex-direction: column;
  line-height: 36px;

  .ops-input {
    height: 36px;
    width: 100px;
  }
}

.add-btn {
  font-size: 12px;
  width: 80px;
  margin-top: 10px;
}
</style>
