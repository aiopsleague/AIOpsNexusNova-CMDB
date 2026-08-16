<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import { getCITypeGroupsConfig } from '@/modules/cmdb/api/ciTypeGroup'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'

 
const props = withDefaults(
  defineProps<{
    value?: string | number | Array<string | number> | null
    selectType?: string
    attrIdkey?: string
    disabled?: boolean
    multiple?: boolean
    placeholder?: string
  }>(),
  {
    value: null,
    selectType: 'attributes',
    attrIdkey: 'id',
    disabled: false,
    multiple: false,
    placeholder: '',
  }
)

const emit = defineEmits<{
  (e: 'change', v: unknown): void
  (e: 'select', node: any, instanceId: any): void
  (e: 'deselect', node: any, instanceId: any): void
}>()

const { t } = useI18n()

const ciTypeGroup = ref<any[]>([])
const childrenOptions = ref<any[]>([])

const currenCiType = computed<unknown>({
  get() {
    return props.value
  },
  set(val) {
    emit('change', val)
  },
})

function getAllParentNodesLabel(node: any, label: string): string {
  if (node.parentNode) {
    return getAllParentNodesLabel(node.parentNode, `${node.parentNode.label}-${label}`)
  }
  return label
}

function getTreeSelectLabel(node: any): string {
  return getAllParentNodesLabel(node, node.label)
}

function normalizer(node: any) {
  return {
    id: node.id || -1,
    label: node.alias || node.name || '其他',
    title: node.alias || node.name || '其他',
  }
}

function loadOptions({ parentNode, callback }: any) {
  getCITypeAttributesById(parentNode.id).then((res: any) => {
    parentNode.children = res.attributes.map((item: any) => ({
      ...item,
      id: `${parentNode.id}-${item[props.attrIdkey]}`,
    }))
    callback()
  })
}

function getCITypeGroups() {
  getCITypeGroupsConfig({ need_other: true }).then((res: any[]) => {
    ciTypeGroup.value = res
      .filter((item) => item.ci_types && item.ci_types.length)
      .map((item) => {
        const selectedTypeId = typeof props.value === 'string' ? Number(props.value.split('-')[0]) : NaN
        const children = item.ci_types.map((type: any) => {
          const obj = { ...type }
          if (props.selectType === 'attributes') {
            obj.children =
              typeof props.value === 'string' && props.value && type.id === selectedTypeId ? childrenOptions.value : null
          }
          return obj
        })
        return { ...item, id: `type_${item.id || -1}`, children }
      })
  })
}

onMounted(async () => {
  if (typeof props.value === 'string' && props.value) {
    const typeId = props.value.split('-')[0]
    const res = await getCITypeAttributesById(typeId)
    childrenOptions.value = res.attributes.map((item: any) => ({
      ...item,
      id: `${typeId}-${item[props.attrIdkey]}`,
    }))
  }
  getCITypeGroups()
})
 
</script>

<template>
  <Treeselect
    ref="cmdb_type_select"
    v-model="currenCiType"
    :disabled="disabled"
    :disable-branch-nodes="true"
    class="custom-treeselect custom-treeselect-white"
    :style="{ '--custom-height': '30px', lineHeight: '30px' }"
    :multiple="multiple"
    :clearable="true"
    searchable
    :options="ciTypeGroup"
    value-consists-of="LEAF_PRIORITY"
    :placeholder="placeholder || t('placeholder2')"
    :load-options="loadOptions"
    :normalizer="normalizer"
    @select="(node, instanceId) => emit('select', node, instanceId)"
    @deselect="(node, instanceId) => emit('deselect', node, instanceId)"
  >
    <template #option-label="{ node }">
      <div
        :title="node.label"
        :style="{ width: '100%', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }"
      >
        {{ node.label }}
      </div>
    </template>
    <template #value-label="{ node }">{{ getTreeSelectLabel(node) }}</template>
  </Treeselect>
</template>

<style></style>
