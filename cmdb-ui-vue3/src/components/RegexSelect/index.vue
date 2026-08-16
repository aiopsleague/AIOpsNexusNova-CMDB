<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { COLOR_PRIMARY } from '@/theme/tokens'
import { getRegList, type RegexPreset } from './constants'

const props = withDefaults(
  defineProps<{
    value?: Partial<RegexPreset>
    isShowErrorMsg?: boolean
    limitedFormat?: string[]
    disabled?: boolean
  }>(),
  {
    value: () => ({}),
    isShowErrorMsg: true,
    limitedFormat: () => [],
    disabled: false,
  }
)

const emit = defineEmits<{ (e: 'change', v: Partial<RegexPreset>): void }>()
const { t, locale } = useI18n()

const showMessage = ref(false)
const width = ref(370)
const testInput = ref('')
const regInputRef = ref<HTMLElement | null>(null)

const regList = computed<RegexPreset[]>(() => {
  const all = getRegList(t)
  if (props.limitedFormat.length) {
    return all.filter((item) => props.limitedFormat.includes(item.id))
  }
  return all
})

const current = computed<Partial<RegexPreset>>({
  get() {
    const value = props.value
    if (value?.value && !value?.label) {
      const found = regList.value.find((reg) => reg.value === value.value)
      return { ...value, label: found?.label ?? t('regexSelect.custom') }
    }
    return value ?? {}
  },
  set(val) {
    showMessage.value = false
    emit('change', val)
  },
})

function onCustomValueChange(e: Event) {
  const value = (e.target as HTMLInputElement).value
  current.value = { ...current.value, value }
}

function onMessageChange(e: Event) {
  const message = (e.target as HTMLInputElement).value
  current.value = { ...current.value, message }
}

function validate(e: Event) {
  const reg = new RegExp(current.value.value || '', 'g')
  showMessage.value = !reg.test((e.target as HTMLInputElement).value)
}

function changeLabel() {
  current.value = {}
}

function visibleChange(visible: boolean) {
  if (visible) {
    nextTick(() => {
      testInput.value = ''
      showMessage.value = false
    })
  }
}

onMounted(() => {
  nextTick(() => {
    const el = regInputRef.value?.querySelector('input') ?? regInputRef.value
    width.value = el?.offsetWidth || 370
  })
})
</script>

<template>
  <a-popover
    trigger="click"
    placement="bottom"
    overlay-class-name="regex-select-wrapper"
    :overlay-style="{ '--overlay-width': `${width}px` }"
    @open-change="visibleChange"
  >
    <template #content>
      <div class="regex-select">
        <div class="regex-select-left">
          <div class="regex-select-left-header">{{ t('regexSelect.limitedFormat') }}</div>
          <div
            v-for="(reg, index) in regList"
            :key="reg.label"
            class="regex-select-left-reg"
            :class="{ 'regex-select-left-reg-selected': current && current.label === reg.label }"
            @click="
              () => {
                current = reg
                testInput = ''
                showMessage = false
              }
            "
          >
            <a-divider
              v-if="index === regList.length - 1"
              :style="{ margin: '2px -12px', width: 'calc(100% + 24px)' }"
            />
            {{ reg.label }}
          </div>
        </div>
        <div class="regex-select-right">
          <template v-if="current">
            <div class="regex-select-right-header">{{ t('regexSelect.regExp') }}</div>
            <div
              v-if="current.label !== t('regexSelect.custom')"
              :style="{ color: '#000', fontSize: '12px', margin: '12px 0' }"
            >
              {{ current.value }}
            </div>
            <a-input
              v-else
              :style="{ margin: '12px 0' }"
              size="small"
              :value="current.value"
              @change="onCustomValueChange"
            />
            <template v-if="isShowErrorMsg">
              <div class="regex-select-right-header">{{ t('regexSelect.errMsg') }}</div>
              <a-input
                :style="{ margin: '12px 0' }"
                size="small"
                :value="current.message"
                @change="onMessageChange"
              />
            </template>
            <div class="regex-select-right-header">{{ t('regexSelect.test') }}</div>
            <a-input v-model="testInput" :style="{ margin: '12px 0 4px' }" size="small" @change="validate" />
            <span v-if="showMessage" :style="{ color: 'red', fontSize: '12px' }">
              {{ locale === 'zh' ? current.message || '错误' : t('regexSelect.error') }}
            </span>
          </template>
        </div>
      </div>
    </template>
    <a-input
      ref="regInputRef"
      :placeholder="t('regexSelect.placeholder')"
      :value="current.label"
      :disabled="disabled"
      @change="changeLabel"
    />
  </a-popover>
</template>

<style scoped>
.regex-select {
  width: 100%;
  height: 300px;
  display: flex;
}
.regex-select-left {
  width: 40%;
  height: 100%;
  border: 1px solid #cacdd9;
  border-radius: 4px;
  padding: 12px;
}
.regex-select-left-reg {
  padding-left: 2px;
  cursor: pointer;
}
.regex-select-left-reg-selected,
.regex-select-left-reg:hover {
  color: v-bind(COLOR_PRIMARY);
}
.regex-select-right {
  flex: 1;
  height: 100%;
  border: 1px solid #cacdd9;
  border-radius: 4px;
  margin-left: 8px;
  padding: 12px;
}
.regex-select-left-header,
.regex-select-right-header {
  font-weight: 400;
  font-size: 14px;
  color: #000000;
  border-left: 2px solid v-bind(COLOR_PRIMARY);
  padding-left: 6px;
  margin-left: -6px;
}
</style>

<style>
.regex-select-wrapper .ant-popover-arrow {
  display: none;
}
.regex-select-wrapper .ant-popover-inner-content {
  padding: 0;
  min-width: 370px;
  width: var(--overlay-width);
}
.regex-select-wrapper.ant-popover-placement-bottom .ant-popover-content {
  margin-top: -8px;
}
.regex-select-wrapper.ant-popover-placement-top .ant-popover-content {
  margin-bottom: -8px;
}
</style>
