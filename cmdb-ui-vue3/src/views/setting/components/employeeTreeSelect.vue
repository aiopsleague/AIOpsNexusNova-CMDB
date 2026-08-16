<script setup lang="ts">
import { computed, inject, useAttrs } from 'vue'
import { useI18n } from 'vue-i18n'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import { formatOption } from '@/utils/employeeTree'

const props = withDefaults(
  defineProps<{
    value?: string | number | Array<string | number> | null
    multiple?: boolean
    className?: string
    placeholder?: string
    idType?: number
    departmentKey?: string
    employeeKey?: string
    limit?: number
    flat?: boolean
    otherOptions?: any[]
  }>(),
  {
    value: null,
    multiple: false,
    className: 'ops-setting-treeselect',
    placeholder: '',
    idType: 1,
    departmentKey: 'department_id',
    employeeKey: 'employee_id',
    limit: 20,
    flat: false,
    otherOptions: () => [],
  }
)

const emit = defineEmits<{
  (e: 'change', v: unknown): void
  (e: 'update:value', v: unknown): void
}>()

const { t } = useI18n()
const attrs = useAttrs()

const provideAllTreeDepAndEmp = inject<() => any[]>('provide_allTreeDepAndEmp', () => [])
const readOnly = inject<boolean>('readOnly', false)

const treeValue = computed({
  get() {
    return props.value
  },
  set(val) {
    emit('change', val)
    emit('update:value', val)
  },
})

const allTreeDepAndEmp = computed(() => provideAllTreeDepAndEmp())

const employeeTreeSelectOption = computed(() => {
  return formatOption(
    [...structuredCloneSafe(Array.isArray(allTreeDepAndEmp.value) ? allTreeDepAndEmp.value : []), ...structuredCloneSafe(props.otherOptions)],
    props.idType,
    false,
    props.departmentKey,
    props.employeeKey
  )
})

function structuredCloneSafe(list: any[]): any[] {
  return JSON.parse(JSON.stringify(list))
}
</script>

<template>
  <Treeselect
    v-model="treeValue"
    :disable-branch-nodes="multiple ? false : true"
    :multiple="multiple"
    :options="employeeTreeSelectOption"
    :placeholder="readOnly ? '' : placeholder || t('cs.components.selectEmployee')"
    :max-height="200"
    :no-children-text="t('cs.components.empty')"
    :no-options-text="t('cs.components.empty')"
    :class="className ? className : 'ops-setting-treeselect'"
    value-consists-of="LEAF_PRIORITY"
    :limit="limit"
    :limit-text="(count: number) => `+ ${count}`"
    v-bind="attrs"
    append-to-body
    :z-index="1050"
    :flat="flat"
  />
</template>
