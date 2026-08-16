<script setup lang="ts">
import { computed, inject, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RightOutlined, LeftOutlined } from '@ant-design/icons-vue'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import { getAllDepAndEmployee, getAllDepartmentList } from '@/api/company'
import { getEmployeeList } from '@/api/employee'
import { formatOption } from '@/utils/employeeTree'

const props = withDefaults(
  defineProps<{
    height?: number
    disableBranchNodes?: boolean
    uniqueKey?: string
    readOnly?: boolean
    isDisabledAllCompany?: boolean
    showInternship?: boolean
  }>(),
  {
    height: 260,
    disableBranchNodes: false,
    uniqueKey: '',
    readOnly: false,
    isDisabledAllCompany: false,
    showInternship: false,
  }
)

const { t } = useI18n()

const getDataBySelf = inject<boolean>('getDataBySelf', true)
const provideAllTreeDepAndEmp = inject<() => any[] | null>('provide_allTreeDepAndEmp', () => null)
const provideAllFlatDepartments = inject<() => any[] | null>('provide_allFlatDepartments', () => null)
const provideAllFlatEmployees = inject<() => any[] | null>('provide_allFlatEmployees', () => null)

const defaultAllTreeDepAndEmp = ref<any[]>([])
const treeValue = ref<any[]>([])
const inputValue = ref('')
const rightData = ref<any[]>([])
const selectedRight = ref<any[]>([])
const defaultAllFlatDepartments = ref<any[]>([])
const defaultAllFlatEmployees = ref<any[]>([])

const employeeTreeSelectOption = computed(() => {
  const formatOptions = formatOption(
    allTreeDepAndEmp.value,
    2,
    props.isDisabledAllCompany,
    props.uniqueKey || 'department_id',
    props.uniqueKey || 'employee_id'
  )
  if (props.showInternship) {
    formatOptions.push({ id: -2, label: '全职' }, { id: -3, label: '实习生' })
  }
  return formatOptions
})

const allTreeDepAndEmp = computed<any[]>(() => {
  if (getDataBySelf) {
    return defaultAllTreeDepAndEmp.value
  }
  return provideAllTreeDepAndEmp() ?? []
})

const allFlatDepartments = computed<any[]>(() => {
  if (getDataBySelf) {
    return defaultAllFlatDepartments.value
  }
  return provideAllFlatDepartments() ?? []
})

const allFlatEmployees = computed<any[]>(() => {
  if (getDataBySelf) {
    return defaultAllFlatEmployees.value
  }
  return provideAllFlatEmployees() ?? []
})

onMounted(() => {
  if (getDataBySelf) {
    getAllDepAndEmployee({ block: 0 }).then((res) => {
      defaultAllTreeDepAndEmp.value = res
    })
    getEmployeeList({ block_status: 0, page_size: 99999 }).then((res: any) => {
      defaultAllFlatEmployees.value = res.data_list
    })
    getAllDepartmentList({ is_tree: 0 }).then((res) => {
      defaultAllFlatDepartments.value = res as any[]
    })
  }
})

function setValues({ rightData: value }: { rightData: any[] }) {
  rightData.value = value
}

function getValues() {
  const department: number[] = []
  const user: number[] = []
  rightData.value.forEach((item: any) => {
    if (item === -2 || item === -3) {
      department.push(item)
    } else {
      const split = String(item).split('-')
      if (split[0] === 'department') {
        department.push(Number(split[1]))
      } else {
        user.push(Number(split[1]))
      }
    }
  })
  const idx = department.findIndex((item) => item === 0)
  if (idx > -1) {
    department.splice(idx, 1)
    department.unshift(-1)
  }
  return { department, user }
}

function changeInputValue(value: string) {
  inputValue.value = value
}

function handleRight() {
  rightData.value = [...new Set([...treeValue.value, ...rightData.value])]
  treeValue.value = []
  selectedRight.value = []
}

function handleLeft() {
  selectedRight.value.forEach((id) => {
    const idx = rightData.value.findIndex((item) => item === id)
    if (idx > -1) {
      rightData.value.splice(idx, 1)
    }
  })
  selectedRight.value = []
}

function handleSelectedRight(id: any) {
  const idx = selectedRight.value.findIndex((item) => item === id)
  if (idx > -1) {
    selectedRight.value.splice(idx, 1)
  } else {
    selectedRight.value.push(id)
  }
}

function getLabel(id: any): string {
  if (id === -2) {
    return '全职'
  }
  if (id === -3) {
    return '实习生'
  }
  const split = String(id).split('-')
  const type = split[0]
  const valueId = Number(split[1])
  if (type === 'department') {
    const found = allFlatDepartments.value.find(
      (item: any) => item[props.uniqueKey || 'department_id'] === valueId
    )
    return found?.department_name ?? ''
  }
  const found = allFlatEmployees.value.find(
    (item: any) => item[props.uniqueKey || 'employee_id'] === valueId
  )
  return found?.nickname ?? ''
}

defineExpose({ setValues, getValues })
</script>

<template>
  <div class="employee-transfer" :style="{ '--custom-height': `${height}px` }">
    <div v-if="!readOnly" class="employee-transfer-left">
      <Treeselect
        v-model="treeValue"
        :disable-branch-nodes="disableBranchNodes"
        :flat="true"
        :multiple="true"
        :options="employeeTreeSelectOption"
        :placeholder="t('placeholderSearch')"
        :max-height="height - 50"
        no-children-text="空"
        no-options-text="空"
        :clearable="false"
        :always-open="true"
        :default-expand-level="showInternship ? 0 : 1"
        :class="{ 'employee-transfer': true, 'employee-transfer-has-input': !!inputValue }"
        :no-results-text="t('noData')"
        open-direction="below"
        @search-change="changeInputValue"
      />
    </div>
    <div v-if="!readOnly" class="employee-transfer-operation">
      <div class="operation-right" @click="handleRight"><RightOutlined /></div>
      <br />
      <div class="operation-left" @click="handleLeft"><LeftOutlined /></div>
    </div>
    <div class="employee-transfer-right">
      <div
        v-for="right in rightData"
        :key="right"
        :class="{
          'employee-transfer-right-item': true,
          'employee-transfer-right-selected': !readOnly && selectedRight.includes(right),
        }"
        @click="handleSelectedRight(right)"
      >
        {{ getLabel(right) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.employee-transfer {
  display: flex;
  justify-content: space-between;
}
.employee-transfer .employee-transfer-left,
.employee-transfer .employee-transfer-right {
  width: 40%;
  background-color: #f9fbff;
  padding-top: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  height: var(--custom-height);
}
.employee-transfer .employee-transfer-right {
  padding-top: 12px;
  overflow: auto;
}
.employee-transfer-right-item {
  cursor: pointer;
  padding: 2px 12px;
  margin: 2px 0;
}
.employee-transfer-right-selected {
  background-color: #f0f5ff;
}
.employee-transfer .employee-transfer-operation {
  width: 10%;
  height: var(--custom-height);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.employee-transfer .operation-left,
.employee-transfer .operation-right {
  width: 20px;
  height: 20px;
  border-radius: 2px;
  background-color: #f0f5ff;
  color: #2f54eb;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}
.employee-transfer .operation-left:hover,
.employee-transfer .operation-right:hover {
  background-color: #2f54eb;
  color: #fff;
}
</style>
