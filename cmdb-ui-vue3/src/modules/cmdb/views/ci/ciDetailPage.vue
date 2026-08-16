<script setup lang="ts">
import { computed, nextTick, onMounted, provide, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { getCIType } from '@/modules/cmdb/api/CIType'
import CiDetailTab from './modules/ciDetailTab.vue'

const route = useRoute()
const router = useRouter()

const typeId = ref(Number(route.params.typeId))
const type = ref<Record<string, any>>({})
const attrList = ref<any[]>([])
const attributes = ref<Record<string, any>>({})

const ciDetailTabRef = ref<InstanceType<typeof CiDetailTab>>()

const windowHeight = computed(() => window.innerHeight)

provide('attrList', () => attrList.value)
provide('attributes', () => attributes.value)

function loadByRoute() {
  typeId.value = Number(route.params.typeId)
  const ciId = route.params.ciId as string | undefined
  const tab = (route.query.tab as string) || 'tab_1'
  if (ciId) {
    nextTick(() => {
      ciDetailTabRef.value?.create(Number(ciId), tab)
    })
  }
  getCIType(typeId.value).then((res) => {
    type.value = res.ci_types[0]
  })
  getAttributeList()
}

function handleNavigateToCi({ typeId: toTypeId, ciId }: { typeId: number; ciId: number }) {
  if (Number(route.params.typeId) === toTypeId && Number(route.params.ciId) === ciId) {
    return
  }
  router
    .push({
      name: 'cmdb_ci_detail',
      params: { typeId: toTypeId, ciId },
      query: { tab: 'tab_2' },
    })
    .catch((err: any) => {
      if (err?.name !== 'NavigationDuplicated') throw err
    })
}

async function getAttributeList() {
  await getCITypeAttributesById(typeId.value).then((res) => {
    attrList.value = res.attributes
    attributes.value = res
  })
}

onMounted(() => {
  loadByRoute()
})

// Reuse the component instance when only the route params change (e.g. double-clicking a
// topology node): mounted won't fire again, so watch the route and reload.
watch(
  () => route.fullPath,
  () => {
    if (route.name === 'cmdb_ci_detail') {
      loadByRoute()
    }
  }
)
</script>

<template>
  <div>
    <div class="ci-detail-header">{{ type.alias }}</div>
    <div class="ci-detail-page">
      <CiDetailTab
        ref="ciDetailTabRef"
        :type-id="typeId"
        :attribute-history-table-height="windowHeight - 250"
        @navigate-to-ci="handleNavigateToCi"
      />
    </div>
  </div>
</template>

<style lang="less" scoped>
.ci-detail-header {
  border-left: 3px solid @primary-color;
  padding-left: 10px;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 10px;
}
.ci-detail-page {
  background-color: #fff;
  height: calc(100vh - 122px);
}
</style>
