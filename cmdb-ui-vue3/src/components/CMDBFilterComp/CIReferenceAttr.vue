<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import request from '@/utils/request'

// Minimal local equivalent of the legacy `ciReferenceAttr` component. It lets a
// filter rule pick a referenced CI by searching the referenced CI type.
interface SelectOption {
  key: string | number
  title: string
}

const props = withDefaults(
  defineProps<{
    value?: string | number | null | Array<string | number>
    isList?: boolean
    referenceShowAttrName?: string
    referenceTypeId?: string | number
    initSelectOption?: SelectOption[]
  }>(),
  {
    value: '',
    isList: false,
    referenceShowAttrName: '',
    referenceTypeId: '',
    initSelectOption: () => [],
  }
)

const emit = defineEmits<{
  (e: 'change', v: string | number | null | Array<string | number>): void
}>()

const isInit = ref(false)
const options = ref<SelectOption[]>([])
const innerReferenceShowAttrName = ref('')

watch(
  () => props.referenceTypeId,
  () => {
    isInit.value = false
  },
  { immediate: true }
)

const selectCIIds = computed<string | number | Array<string | number>>({
  get() {
    if (props.isList) {
      return props.value || []
    }
    return props.value ? Number(props.value) : ''
  },
  set(val) {
    emit('change', val ?? (props.isList ? [] : null))
  },
})

async function handleDropdownVisibleChange(open: boolean) {
  if (!isInit.value && open && props.referenceTypeId) {
    isInit.value = true

    if (!props.referenceShowAttrName) {
      const res = (await request.get(`/v0.1/ci_types/${props.referenceTypeId}`)) as any
      const ciType = res?.ci_types?.[0]
      innerReferenceShowAttrName.value = ciType?.show_name || ciType?.unique_name || ''
    }

    const attrName = props.referenceShowAttrName || innerReferenceShowAttrName.value || ''
    if (!attrName) {
      return
    }

    const res = (await request.get('/v0.1/ci/s', {
      params: { q: `_type:${props.referenceTypeId}`, fl: attrName, count: 25 },
    })) as any

    let next = (res?.result ?? []).map((item: Record<string, any>) => ({
      key: item._id,
      title: String(item?.[attrName] ?? ''),
    }))

    next = uniqByKey([...props.initSelectOption, ...next])
    options.value = next
  }
}

async function handleSearch(v: string) {
  const attrName = props.referenceShowAttrName || innerReferenceShowAttrName.value || ''
  if (!attrName || !props.referenceTypeId) {
    return
  }

  const res = (await request.get('/v0.1/ci/s', {
    params: {
      q: `_type:${props.referenceTypeId}${v ? ',*' + v + '*' : ''}`,
      fl: attrName,
      count: v ? 100 : 25,
    },
  })) as any

  options.value = (res?.result ?? []).map((item: Record<string, any>) => ({
    key: item._id,
    title: String(item?.[attrName] ?? ''),
  }))
}

function handleChange(v: string | number | Array<string | number>) {
  if (Array.isArray(v) ? !v.length : !v) {
    handleSearch('')
  }
}

// Debounce wrapper matching the legacy lodash debounce(300) behavior.
let searchTimer: ReturnType<typeof setTimeout> | null = null
function onSearch(v: string) {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => handleSearch(v), 300)
}

function uniqByKey(list: SelectOption[]): SelectOption[] {
  const seen = new Set<string | number>()
  return list.filter((item) => {
    const key = item.key
    if (seen.has(key)) {
      return false
    }
    seen.add(key)
    return true
  })
}

function getPopupContainer(trigger: HTMLElement) {
  return trigger.parentElement
}
</script>

<template>
  <div class="reference-attr-select-wrap">
    <a-select
      v-model:value="selectCIIds"
      option-filter-prop="title"
      :mode="isList ? 'multiple' : undefined"
      show-search
      allow-clear
      :get-popup-container="getPopupContainer"
      class="reference-attr-select"
      :max-tag-count="2"
      @dropdown-visible-change="handleDropdownVisibleChange"
      @search="onSearch"
      @change="handleChange"
    >
      <template v-if="!isInit">
        <a-select-option v-for="item in initSelectOption" :key="item.key" :title="item.title">
          {{ item.title }}
        </a-select-option>
      </template>
      <a-select-option v-for="item in options" :key="item.key" :title="item.title">
        {{ item.title }}
      </a-select-option>
    </a-select>
  </div>
</template>

<style scoped>
.reference-attr-select-wrap {
  width: 100%;
}
.reference-attr-select {
  width: 100%;
}
</style>
