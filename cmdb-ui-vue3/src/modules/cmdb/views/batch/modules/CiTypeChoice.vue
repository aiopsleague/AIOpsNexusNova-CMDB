<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { DownloadOutlined } from '@ant-design/icons-vue'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import { getCITypeGroupsConfig } from '@/modules/cmdb/api/ciTypeGroup'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { getCITypeParent, getCanEditByParentIdChildId } from '@/modules/cmdb/api/CITypeRelation'
import { searchPermResourceByRoleId } from '@/modules/acl/api/permission'
import { useUserStore } from '@/stores/user'
import CMDBTypeSelectAntd from '@/modules/cmdb/components/cmdbTypeSelect/cmdbTypeSelectAntd.vue'

const emit = defineEmits<{
  (e: 'getCiTypeAttr', value: any): void
  (e: 'stepChange', step: number): void
}>()

const { t } = useI18n()
const userStore = useUserStore()

const CITypeGroup = ref<any[]>([])
const ciTypeName = ref('')
const selectNum = ref<number | undefined>(undefined)
const selectCiTypeAttrList = ref<Record<string, any>>({})
const visible = ref(false)
const checkedAttrs = ref<string[]>([])
const indeterminate = ref(false)
const checkAll = ref(true)
const parentsType = ref<any[]>([])
const parentsForm = ref<Record<string, any>>({})
const checkedParents = ref<string[]>([])
const canEdit = ref<Record<number, any>>({})

onMounted(async () => {
  const { resources } = (await searchPermResourceByRoleId(userStore.rid, {
    resource_type_id: 'CIType',
    app_id: 'cmdb',
  })) as unknown as { resources: any[] }

  getCITypeGroupsConfig({ need_other: true }).then((res) => {
    const groups = res || []
    groups.forEach((group: any) => {
      group.ci_types = (group.ci_types || []).filter((type: any) => {
        const _find = resources.find((resource: any) => resource.name === type.name)
        return _find?.permissions?.includes?.('create') ?? false
      })
    })
    CITypeGroup.value = groups.filter((group: any) => group?.ci_types?.length)
  })
})

watch(checkedAttrs, () => {
  if (checkedAttrs.value.length < selectCiTypeAttrList.value.attributes.length) {
    indeterminate.value = true
    checkAll.value = false
  }
  if (checkedAttrs.value.length === selectCiTypeAttrList.value.attributes.length) {
    indeterminate.value = false
    checkAll.value = true
  }
})

function selectCiType(id: number) {
  getCITypeAttributesById(id).then((res: any) => {
    emit('getCiTypeAttr', res)
    selectCiTypeAttrList.value = res
    emit('stepChange', 1)
  })

  let name = ''
  CITypeGroup.value.forEach((group: any) => {
    if (group?.ci_types?.length) {
      group.ci_types.forEach((type: any) => {
        if (type?.id === id) {
          name = type.alias || type.name
        }
      })
    }
  })
  ciTypeName.value = name
}

function openModal() {
  emit('stepChange', 1)
  getCITypeParent(selectNum.value!).then(async (res: any) => {
    for (let i = 0; i < res.parents.length; i++) {
      const p_res = await getCanEditByParentIdChildId(res.parents[i].id, selectNum.value!)
      canEdit.value = {
        ...cloneDeep(canEdit.value),
        [res.parents[i].id]: p_res.result,
      }
    }
    parentsType.value = res.parents.filter((parent: any) => canEdit.value[parent.id])
    const _parentsForm: Record<string, any> = {}
    res.parents.forEach((item: any) => {
      const _find = item.attributes.find((attr: any) => attr.id === item.unique_id)
      _parentsForm[item.alias || item.name] = { ...item, selectedParentAttr: _find?.alias || _find?.name }
    })
    parentsForm.value = _parentsForm
    checkedParents.value = []
    visible.value = true
    checkedAttrs.value = selectCiTypeAttrList.value.attributes.map((item: any) => item.alias || item.name)
  })
}

function handleCancel() {
  visible.value = false
}

function handleOk() {
  // TODO: template download (ExcelJS + FileSaver) is not yet available in the Vue 3
  // app. Reintroduce once `exceljs` and `file-saver` are added to dependencies. The
  // legacy implementation built a .xlsx template from the checked attributes/parents
  // (with data-validation dropdowns) and saved it via FileSaver.saveAs.
  message.info(t('cmdb.batch.requestFailedTips'))
  handleCancel()
}

function changeCheckAll(e: any) {
  if (e.target.checked) {
    checkedAttrs.value = selectCiTypeAttrList.value.attributes.map((item: any) => item.alias || item.name)
  } else {
    const _find = selectCiTypeAttrList.value.attributes.find(
      (item: any) => item.name === selectCiTypeAttrList.value.unique
    )
    checkedAttrs.value = [_find?.alias || _find?.name]
  }
}

function clickParent(item: any) {
  const key = item.alias || item.name
  const _idx = checkedParents.value.findIndex((p) => p === key)
  if (_idx > -1) {
    checkedParents.value.splice(_idx, 1)
  } else {
    checkedParents.value.push(key)
  }
}

function clearSelectNum() {
  selectNum.value = undefined
}

defineExpose({ clearSelectNum })
</script>

<template>
  <div class="ci-type-choice-container">
    <div class="ci-type-choice-row">
      <div class="ci-type-choice-label">
        <span class="required-mark">*</span>
        <span>{{ t('cmdb.batch.selectCIType') }}</span>
      </div>
      <CMDBTypeSelectAntd
        v-model="selectNum"
        :placeholder="t('cmdb.batch.selectCITypeTips')"
        class="ci-type-choice-select"
        :ci-type-group="CITypeGroup"
        @change="selectCiType"
      />
    </div>
    <div class="ci-type-choice-row">
      <div class="ci-type-choice-label">
        <span>{{ t('cmdb.batch.downloadTemplate') }}</span>
      </div>
      <a-button :disabled="!selectNum" type="primary" ghost class="ops-button-ghost" @click="openModal">
        <template #icon><DownloadOutlined /></template>
        {{ t('cmdb.batch.clickDownload') }}
      </a-button>
    </div>
    <a-modal
      :body-style="{ paddingTop: '0px' }"
      width="800px"
      :title="ciTypeName"
      :open="visible"
      wrap-class-name="ci-type-choice-modal"
      @cancel="handleCancel"
      @ok="handleOk"
    >
      <a-divider orientation="left">{{ t('cmdb.ciType.attributes') }}</a-divider>
      <a-checkbox
        :style="{ marginBottom: '20px' }"
        :indeterminate="indeterminate"
        :checked="checkAll"
        @change="changeCheckAll"
      >
        {{ t('checkAll') }}
      </a-checkbox>
      <br />
      <a-checkbox-group v-model:value="checkedAttrs" style="width: 100%">
        <a-row>
          <a-col v-for="item in selectCiTypeAttrList.attributes" :key="item.alias || item.name" :span="6">
            <a-checkbox :disabled="item.name === selectCiTypeAttrList.unique" :value="item.alias || item.name">
              {{ item.alias || item.name }}
              <span v-if="item.name === selectCiTypeAttrList.unique" style="color: red">*</span>
            </a-checkbox>
          </a-col>
        </a-row>
      </a-checkbox-group>
      <template v-if="parentsType && parentsType.length">
        <a-divider orientation="left">{{ t('cmdb.ciType.relation') }}</a-divider>
        <a-row :gutter="[24, 24]" align="top">
          <a-col v-for="item in parentsType" :key="item.id" :style="{ display: 'inline-flex' }" :span="12">
            <a-checkbox :checked="checkedParents.includes(item.alias || item.name)" @click="clickParent(item)">
            </a-checkbox>
            <span
              :style="{
                display: 'inline-block',
                overflow: 'hidden',
                whiteSpace: 'nowrap',
                textOverflow: 'ellipsis',
                width: '80px',
                margin: '0 5px',
                textAlign: 'right',
              }"
              :title="item.alias || item.name"
              >{{ item.alias || item.name }}</span
            >
            <a-select
              v-model:value="parentsForm[item.alias || item.name].selectedParentAttr"
              :style="{ flex: 1 }"
              size="small"
            >
              <a-select-option
                v-for="attr in item.attributes"
                :key="attr.alias || attr.name"
                :title="attr.alias || attr.name"
                :value="attr.alias || attr.name"
              >
                {{ attr.alias || attr.name }}
              </a-select-option>
            </a-select>
          </a-col>
        </a-row>
      </template>
    </a-modal>
  </div>
</template>

<style lang="less" scoped>
.ci-type-choice-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ci-type-choice-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.ci-type-choice-label {
  min-width: 140px;
  font-size: 14px;
  font-weight: 500;
  color: @text-color_1;

  .required-mark {
    color: #ff4d4f;
    margin-right: 4px;
  }
}

.ci-type-choice-select {
  flex: 1;
  max-width: 500px;
}
</style>

<style lang="less">
.ci-type-choice-modal {
  .ant-checkbox-disabled .ant-checkbox-inner {
    border-color: @primary-color !important;
    background-color: @primary-color;
  }
  .ant-checkbox-disabled.ant-checkbox-checked .ant-checkbox-inner::after {
    border-color: #fff;
  }
}
</style>
