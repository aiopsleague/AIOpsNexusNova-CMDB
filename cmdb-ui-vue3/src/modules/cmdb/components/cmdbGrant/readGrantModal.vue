<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, inject, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'ant-design-vue'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import { grantCiType, revokeCiType } from '@/modules/cmdb/api/CIType'
import { getCITypeAttributesByTypeIds } from '@/modules/cmdb/api/CITypeAttr'
import FilterComp from '@/components/CMDBFilterComp/index.vue'

const props = withDefaults(
  defineProps<{
    CITypeId?: number | null
  }>(),
  {
    CITypeId: null,
  }
)

const emit = defineEmits<{
  (e: 'updateTableDataRead', row: Record<string, any>, hasRead: boolean): void
}>()

const { t } = useI18n()

// Injected by GrantComp: () => attribute groups / filter permissions.
const provideAttrGroup = inject<() => any[]>('attrGroup', () => [])
const provideFilerPerimissions = inject<() => Record<string, any>>('filerPerimissions', () => ({}))

const visible = ref(false)
const colType = ref('')
const row = ref<Record<string, any>>({})
const radioValue = ref(1)
const selectedAttr = ref<any[]>([])
const canSearchPreferenceAttrList = ref<any[]>([])
const expression = ref('')
const form = ref<{ name: string }>({ name: '' })
const rules = {
  name: [{ required: true, message: t('cmdb.components.customizeFilterName') }],
}

const filterCompRef = ref<InstanceType<typeof FilterComp>>()
const formRef = ref<FormInstance>()

const title = computed(() => {
  if (colType.value === 'read_attr') {
    return t('cmdb.components.attributeGrant')
  }
  return t('cmdb.components.ciGrant')
})

const modalDesc = computed(() => {
  if (colType.value === 'read_attr') {
    return t('cmdb.components.readAttrModalDesc')
  }
  return t('cmdb.components.readCIModalDesc')
})

const attrGroup = computed(() => {
  const group = provideAttrGroup() || []
  return group.filter((g) => g?.attributes?.length)
})

const filerPerimissions = computed(() => provideFilerPerimissions())

const filterKey = computed(() => {
  if (colType.value === 'read_attr') {
    return 'attr_filter'
  }
  return 'ci_filter'
})

function normalizer(node: any) {
  return {
    id: node.name || -1,
    label: node.alias || node.name || t('other'),
    title: node.alias || node.name || t('other'),
    children: node.attributes,
  }
}

async function open(colTypeParam: string, rowParam: Record<string, any>) {
  visible.value = true
  colType.value = colTypeParam
  row.value = rowParam
  form.value = { name: '' }

  if (colType.value === 'read_ci') {
    const res = await getCITypeAttributesByTypeIds({ type_ids: props.CITypeId })
    canSearchPreferenceAttrList.value = (res?.attributes ?? []).filter(
      (item: any) => item.value_type !== '6'
    )
  }

  if (filerPerimissions.value[rowParam.rid]) {
    const tempValue = filerPerimissions.value[rowParam.rid][filterKey.value]
    if (tempValue && tempValue.length) {
      radioValue.value = 2
      if (colType.value === 'read_attr') {
        selectedAttr.value = tempValue
      } else {
        expression.value = `q=${tempValue}`
        form.value = { name: filerPerimissions.value[rowParam.rid].name || '' }
        nextTick(() => {
          filterCompRef.value?.visibleChange(true)
        })
      }
    }
  }
}

async function handleOk() {
  if (radioValue.value === 1) {
    await grantCiType(props.CITypeId as number, row.value.rid, {
      perms: ['read'],
      attr_filter: colType.value === 'read_attr' ? [] : undefined,
      ci_filter: colType.value === 'read_ci' ? '' : undefined,
    })
  } else if (radioValue.value === 2) {
    if (colType.value === 'read_ci') {
      filterCompRef.value?.handleSubmit()
    }
    await grantCiType(props.CITypeId as number, row.value.rid, {
      perms: ['read'],
      attr_filter: colType.value === 'read_attr' ? selectedAttr.value : undefined,
      ci_filter: colType.value === 'read_ci' ? expression.value.slice(2) : undefined,
      name: colType.value === 'read_ci' ? form.value.name : undefined,
    })
  } else {
    const tempValue = filerPerimissions.value?.[row.value.rid]?.[filterKey.value]
    await revokeCiType(props.CITypeId as number, row.value.rid, {
      perms: ['read'],
      attr_filter: colType.value === 'read_attr' ? tempValue : undefined,
      ci_filter: colType.value === 'read_ci' ? tempValue : undefined,
    })
  }
  emit('updateTableDataRead', row.value, radioValue.value === 1 || radioValue.value === 2)
  handleCancel()
}

function handleCancel() {
  radioValue.value = 1
  selectedAttr.value = []
  formRef.value?.resetFields()
  visible.value = false
}

function setExpFromFilter(filterExp: string) {
  expression.value = filterExp ? `q=${filterExp}` : ''
}

function changeRadioValue(value: number) {
  radioValue.value = value
}

defineExpose({ open })
</script>

<template>
  <a-modal :width="680" :title="title" :open="visible" @ok="handleOk" @cancel="handleCancel">
    <div class="read-grant-modal-desc">{{ modalDesc }}</div>
    <a-radio-group v-model:value="radioValue" style="width: 100%" @change="(e: any) => changeRadioValue(e.target.value)">
      <div class="radio-option">
        <a-radio :value="1">{{ t('cmdb.components.all') }}</a-radio>
        <span class="radio-desc">{{ t('cmdb.components.allDesc') }}</span>
      </div>
      <div class="radio-option">
        <a-radio :value="2">{{ t('cmdb.components.customize') }}</a-radio>
        <span class="radio-desc">{{ t('cmdb.components.customizeDesc') }}</span>
      </div>
      <div v-if="radioValue === 2" style="margin-left: 24px; margin-top: 12px; margin-bottom: 12px">
        <Treeselect
          v-if="colType === 'read_attr'"
          v-model="selectedAttr"
          :multiple="true"
          :clearable="true"
          searchable
          :options="attrGroup"
          :placeholder="t('cmdb.ciType.selectAttributes')"
          value-consists-of="LEAF_PRIORITY"
          :limit="10"
          :limit-text="(count: number) => `+ ${count}`"
          :normalizer="normalizer"
          append-to-body
          :z-index="1050"
        />
        <a-form
          v-if="colType === 'read_ci'"
          ref="formRef"
          :model="form"
          :rules="rules"
          :label-col="{ span: 2 }"
          :wrapper-col="{ span: 10 }"
        >
          <a-form-item :label="t('name')" name="name">
            <a-input v-model:value="form.name" />
          </a-form-item>
          <FilterComp
            ref="filterCompRef"
            :is-dropdown="false"
            :can-search-preference-attr-list="canSearchPreferenceAttrList"
            :expression="expression"
            @set-exp-from-filter="setExpFromFilter"
          />
          <div class="read-ci-tip">{{ t('cmdb.ciType.ciGrantTip') }}</div>
        </a-form>
      </div>
      <div class="radio-option">
        <a-radio :value="3">{{ t('cmdb.components.none') }}</a-radio>
        <span class="radio-desc">{{ t('cmdb.components.noneDesc') }}</span>
      </div>
    </a-radio-group>
  </a-modal>
</template>

<style scoped>
.read-grant-modal-desc {
  color: #999;
  font-size: 12px;
  margin-bottom: 16px;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border-left: 3px solid #2f54eb;
}
.radio-option {
  margin-bottom: 12px;
  display: flex;
  align-items: baseline;
}
.radio-option .radio-desc {
  color: #999;
  font-size: 12px;
  margin-left: 8px;
}
.read-ci-tip {
  font-size: 12px;
  line-height: 22px;
  color: #a5a9bc;
}
</style>
