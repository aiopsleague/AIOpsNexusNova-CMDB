<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  AppstoreOutlined,
  BgColorsOutlined,
  BoldOutlined,
  CheckOutlined,
  DeleteOutlined,
  FontColorsOutlined,
  ItalicOutlined,
  UnderlineOutlined,
} from '@ant-design/icons-vue'
import CustomIconSelect from '@/components/CustomIconSelect/index.vue'

interface IconValue {
  name?: string
  color?: string
  id?: string | number
  url?: string
}

const props = withDefaults(
  defineProps<{
    labelData?: Record<string, any>
  }>(),
  { labelData: () => ({}) }
)

const emit = defineEmits<{
  (e: 'change', key: string, value: any): void
  (e: 'deleteData'): void
}>()

const { t } = useI18n()

const popoverVisible = ref(false)
const popoverLabelRef = ref<HTMLElement>()
const preValueEditRef = ref<HTMLElement>()

function eventListener(e: MouseEvent) {
  if (!popoverVisible.value) {
    return
  }
  const dom = preValueEditRef.value
  const domLabel = popoverLabelRef.value
  const domIcon = document.getElementById('custom-icon-select-popover')
  e.stopPropagation()
  e.preventDefault()
  if (dom) {
    const target = e.target as Node
    const isSelf = dom.contains(target) || (domLabel && domLabel.contains(target)) || (domIcon && domIcon.contains(target))
    if (!isSelf) {
      popoverVisible.value = false
    }
  }
}

function handleDelete() {
  popoverVisible.value = false
  emit('deleteData')
}

function changeFontStyle(key: string, value: string) {
  const style = {
    ...(props.labelData.style || {}),
    [key]: props.labelData.style[key] === value ? 'initial' : value,
  }
  emit('change', 'style', style)
}

function changeLabel(e: Event) {
  const value = (e.target as HTMLInputElement).value
  emit('change', 'label', value)
}

function changeIcon(value: IconValue) {
  emit('change', 'icon', value)
}

onMounted(() => {
  document.addEventListener('click', eventListener)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', eventListener)
})
</script>

<template>
  <div>
    <a-popover :open="popoverVisible" placement="bottom" overlay-class-name="pre-value-edit-popover">
      <div ref="popoverLabelRef" @click="popoverVisible = true">
        <a-input
          v-show="!labelData.label || popoverVisible"
          type="text"
          :style="{ width: '210px' }"
          :value="labelData.label"
          @change="changeLabel"
        />

        <div
          v-show="!popoverVisible && labelData.label"
          class="pre-value-tag"
          :style="labelData.style ? labelData.style : {}"
        >
          <span>
            <img
              v-if="labelData.icon.id && labelData.icon.url"
              :src="`/api/common-setting/v1/file/${labelData.icon.url}`"
              :style="{ maxHeight: '12px', maxWidth: '12px', marginRight: '5px' }"
            />
            <AppstoreOutlined
              v-else-if="labelData.icon.name"
              :style="{ marginRight: '5px', color: labelData.icon.color || '#595959' }"
            />
            <a-tooltip :title="labelData.label">
              <span class="pre-value-tag-text">{{ labelData.label }}</span>
            </a-tooltip>
          </span>
        </div>
      </div>

      <template #content>
        <div ref="preValueEditRef">
          <a-divider orientation="left" style="margin: 8px 0; color: gray; font-size: 10px">{{ t('icon') }}</a-divider>
          <CustomIconSelect :style="{ marginLeft: '10px' }" :value="labelData.icon" @change="changeIcon" />
          <a-divider orientation="left" style="margin: 8px 0; color: gray; font-size: 10px">{{ t('cmdb.ciType.font') }}</a-divider>
          <div :style="{ display: 'flex', justifyContent: 'space-around' }">
            <div
              class="attributes-font-icon"
              :class="{ 'attributes-font-icon-selected': labelData.style.fontWeight === 'bold' }"
              @click="changeFontStyle('fontWeight', 'bold')"
            >
              <BoldOutlined />
            </div>
            <div
              class="attributes-font-icon"
              :class="{ 'attributes-font-icon-selected': labelData.style.fontStyle === 'italic' }"
              @click="changeFontStyle('fontStyle', 'italic')"
            >
              <ItalicOutlined />
            </div>
            <div
              class="attributes-font-icon"
              :class="{ 'attributes-font-icon-selected': labelData.style.textDecoration === 'underline' }"
              @click="changeFontStyle('textDecoration', 'underline')"
            >
              <UnderlineOutlined />
            </div>
          </div>

          <a-divider orientation="left" style="margin: 8px 0; color: gray; font-size: 10px">{{ t('cmdb.ciType.color') }}</a-divider>
          <div :style="{ display: 'flex', justifyContent: 'space-around' }">
            <div class="attributes-font-color">
              <FontColorsOutlined />
              <input type="color" :value="labelData.style.color" @change="(e: any) => changeFontStyle('color', e.target.value)" />
            </div>
            <div class="attributes-font-color">
              <BgColorsOutlined />
              <input
                type="color"
                :value="labelData.style.backgroundColor"
                @change="(e: any) => changeFontStyle('backgroundColor', e.target.value)"
              />
            </div>
          </div>
          <a-divider orientation="left" style="margin: 8px 0; color: gray; font-size: 10px">{{ t('operation') }}</a-divider>
          <div style="text-align: right">
            <a-tooltip :title="t('delete')">
              <a>
                <DeleteOutlined style="margin-right: 10px; color: red" @click="handleDelete" />
              </a>
            </a-tooltip>
            <a-tooltip :title="t('confirm')">
              <a>
                <CheckOutlined style="margin-right: 10px; color: green" @click="popoverVisible = false" />
              </a>
            </a-tooltip>
          </div>
        </div>
      </template>
    </a-popover>
  </div>
</template>

<style lang="less" scoped>
.pre-value-edit-color {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  flex-wrap: wrap;
  .pre-value-edit-color-item {
    cursor: pointer;
    display: inline-block;
    width: 25px;
    height: 20px;
    margin: 5px;
  }
}
.pre-value-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  position: relative;
  cursor: pointer;
  max-width: 100%;

  &-text {
    overflow: hidden;
    text-wrap: nowrap;
    text-overflow: ellipsis;
    max-width: 100%;
  }

  > span {
    display: flex;
    align-items: center;
  }

  &:hover .pre-value-tag-dropdown-icon {
    display: inline !important;
  }

  .pre-value-tag-dropdown {
    font-size: 10px;
    color: #999999;
    &:hover {
      color: #2f54eb;
    }
    .pre-value-tag-dropdown-icon {
      display: none;
      position: absolute;
      right: -10px;
      top: 8px;
    }
  }
}
</style>

<style lang="less">
.pre-value-tag-input {
  border: none;
  border-bottom: 1px solid #d9d9d9;
  font-size: 12px;
  &:focus {
    box-shadow: none;
  }
}
.pre-value-edit-popover.ant-popover-placement-top .ant-popover-content {
  margin-bottom: -10px;
}
.pre-value-edit-popover.ant-popover-placement-bottom .ant-popover-content {
  margin-top: -10px;
}
.pre-value-edit-popover {
  .ant-popover-content {
    width: 150px;
    .ant-popover-arrow {
      display: none;
    }
    .ant-popover-inner-content {
      padding: 3px 4px;
    }
  }
  .attributes-font-icon {
    cursor: pointer;
    display: inline-block;
    width: 30px;
    height: 30px;
    position: relative;
    border: 1px solid #fff;
    &:hover {
      background-color: #eeeeee;
      border-color: #606266;
    }
    > i {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
    }
  }
  .attributes-font-icon-selected {
    background-color: #eeeeee;
  }
  .attributes-font-color {
    display: inline-flex;
    align-items: center;
    width: 50%;
    justify-content: center;
  }
}
</style>
