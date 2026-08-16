<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getCITypeGroupById, getCITypes } from '@/modules/cmdb/api/CIType'
import { searchCI } from '@/modules/cmdb/api/ci'
import { cloneDeep } from '@/modules/cmdb/utils/helper'
import CiDetailAttrContent from '@/modules/cmdb/views/ci/modules/ciDetailAttrContent.vue'

const props = withDefaults(
  defineProps<{
    ci?: Record<string, any>
    rackCITYpeId?: number
  }>(),
  {
    ci: () => ({}),
    rackCITYpeId: 0,
  }
)

const { t } = useI18n()

const attributeGroups = ref<any[]>([])

onMounted(() => {
  getAttributes()
})

function getAttributes() {
  getCITypeGroupById(props.rackCITYpeId, { need_other: 1 })
    .then((res) => {
      attributeGroups.value = res

      handleReferenceAttr()
    })
    .catch(() => {})
}

async function handleReferenceAttr() {
  const map: Record<string, Record<string, Record<string, any>>> = {}
  attributeGroups.value.forEach((group) => {
    group.attributes.forEach((attr: any) => {
      if (attr?.is_reference && attr?.reference_type_id && props.ci[attr.name]) {
        const ids = Array.isArray(props.ci[attr.name]) ? props.ci[attr.name] : props.ci[attr.name] ? [props.ci[attr.name]] : []
        if (ids.length) {
          if (!map?.[attr.reference_type_id]) {
            map[attr.reference_type_id] = {}
          }
          ids.forEach((id: any) => {
            map[attr.reference_type_id][id] = {}
          })
        }
      }
    })
  })

  if (!Object.keys(map).length) {
    return
  }

  const ciTypesRes = await getCITypes({
    type_ids: Object.keys(map).join(','),
  })
  const showAttrNameMap: Record<string, string> = {}
  ciTypesRes.ci_types.forEach((ciType: any) => {
    showAttrNameMap[ciType.id] = ciType?.show_name || ciType?.unique_name || ''
  })

  const allRes = await Promise.all(
    Object.keys(map).map((key) => {
      return searchCI({
        q: `_type:${key},_id:(${Object.keys(map[key]).join(';')})`,
        count: 9999,
      })
    })
  )

  const ciNameMap: Record<string, any> = {}
  allRes.forEach((res) => {
    res.result.forEach((item: any) => {
      ciNameMap[item._id] = item
    })
  })

  const newAttrGroups = cloneDeep(attributeGroups.value)

  newAttrGroups.forEach((group) => {
    group.attributes.forEach((attr: any) => {
      if (attr?.is_reference && attr?.reference_type_id) {
        attr.showAttrName = showAttrNameMap?.[attr?.reference_type_id] || ''

        const referenceShowAttrNameMap: Record<string, any> = {}
        const referenceCIIds = props.ci[attr.name]
        ;(Array.isArray(referenceCIIds) ? referenceCIIds : referenceCIIds ? [referenceCIIds] : []).forEach((id: any) => {
          referenceShowAttrNameMap[id] = ciNameMap?.[id]?.[attr.showAttrName] ?? id
        })
        attr.referenceShowAttrNameMap = referenceShowAttrNameMap
      }
    })
  })

  attributeGroups.value = newAttrGroups
}
</script>

<template>
  <div class="rack-group-attr">
    <a-descriptions
      v-for="group in attributeGroups"
      :key="group.name"
      class="rack-group-attr-desc"
      :title="group.name || t('cmdb.common.other')"
      bordered
      :column="3"
    >
      <a-descriptions-item v-for="attr in group.attributes" :key="attr.name" :label="`${attr.alias || attr.name}`">
        <CiDetailAttrContent :ci="ci" :attr="attr" :show-edit="false" />
      </a-descriptions-item>
    </a-descriptions>
  </div>
</template>

<style lang="less" scoped>
.rack-group-attr {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;

  &-desc {
    margin-bottom: 25px;
  }
}
</style>
