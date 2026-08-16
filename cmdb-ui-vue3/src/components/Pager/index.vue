<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { DownOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons-vue'
import { useI18n } from 'vue-i18n'

const props = withDefaults(
  defineProps<{
    currentPage: number
    pageSize: number
    pageSizes: number[]
    total: number
    isLoading?: boolean
  }>(),
  { isLoading: false }
)

const emit = defineEmits<{ (e: 'change', page: number): void; (e: 'showSizeChange', size: number): void }>()
const { t } = useI18n()

const dropdownIsDisabled = ref(false)
const prevIsDisabled = ref(true)

const nextIsDisabled = computed(() => props.isLoading || props.total < props.pageSize)

watch(
  () => props.isLoading,
  (val) => {
    if (val) {
      dropdownIsDisabled.value = true
      prevIsDisabled.value = true
    } else {
      dropdownIsDisabled.value = false
      prevIsDisabled.value = props.currentPage === 1
    }
  },
  { immediate: true }
)

watch(
  () => props.currentPage,
  (val) => {
    if (val === 1) prevIsDisabled.value = true
  },
  { immediate: true }
)

function handleItemClick(size: number) {
  emit('showSizeChange', size)
}
function nextPage() {
  emit('change', props.currentPage + 1)
}
function prevPage() {
  emit('change', props.currentPage - 1)
}
</script>

<template>
  <div>
    <a-row class="row" justify="end">
      <a-col>
        <a-space>
          <a-button class="left-button" size="small" :disabled="prevIsDisabled" @click="prevPage">
            <LeftOutlined />
          </a-button>
          <a-button class="page-button" size="small">{{ currentPage }}</a-button>
          <a-button class="right-button" size="small" :disabled="nextIsDisabled" @click="nextPage">
            <RightOutlined />
          </a-button>
          <a-dropdown placement="topCenter" :trigger="['click']" :disabled="dropdownIsDisabled">
            <a-button size="small">
              {{ pageSize }}{{ t('itemsPerPage') }}<DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item v-for="(size, index) in pageSizes" :key="index" @click="handleItemClick(size)">
                  {{ size }}{{ t('itemsPerPage') }}
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </a-space>
      </a-col>
    </a-row>
  </div>
</template>

<style scoped>
.row {
  margin-top: 5px;
}
.left-button,
.right-button,
.page-button {
  padding: 0;
  width: 24px;
}
</style>
