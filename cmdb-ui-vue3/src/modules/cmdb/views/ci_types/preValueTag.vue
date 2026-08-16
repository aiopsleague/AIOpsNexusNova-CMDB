<script setup lang="ts">
import { onBeforeUnmount, onMounted, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  AppstoreOutlined,
  BoldOutlined,
  ItalicOutlined,
  UnderlineOutlined,
  FontColorsOutlined,
  BgColorsOutlined,
  DeleteOutlined,
  CheckOutlined,
  CloseOutlined,
  DownOutlined,
} from '@ant-design/icons-vue'
import IconArea from './iconArea.vue'

const props = withDefaults(
  defineProps<{
    item?: any[]
    type?: string
    disabled?: boolean
  }>(),
  { item: () => [], type: 'edit', disabled: false }
)

const emit = defineEmits<{
  (e: 'deleteValue', item: any[]): void
  (e: 'editValue', item: any[], value: string, style: Record<string, any>, icon: any): void
  (e: 'add', value: string, style: Record<string, any>, icon: any): void
}>()

const { t } = useI18n()

const inputVisible = ref(false)
const inputValue = ref('')
const style = ref<Record<string, any>>({})
const icon = ref<Record<string, any>>({})

const inputRef = ref()
const preValueEditRef = ref<HTMLElement>()
const iconAreaRef = ref<InstanceType<typeof IconArea>>()

function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function eventListener(e: MouseEvent) {
  if (!inputVisible.value) {
    return
  }
  const dom = preValueEditRef.value
  const domInput = inputRef.value?.$el as HTMLElement | undefined
  const domIcon = document.getElementById('custom-icon-select-popover')
  e.stopPropagation()
  e.preventDefault()
  if (dom) {
    const target = e.target as Node
    const isSelf = dom.contains(target) || (domInput && domInput.contains(target)) || (domIcon && domIcon.contains(target))
    if (!isSelf) {
      inputVisible.value = false
    }
  }
}

function handleDelete() {
  emit('deleteValue', props.item)
  inputVisible.value = false
}

function handleEdit() {
  style.value = cloneDeep(props.item[1]?.style || {})
  icon.value = cloneDeep(props.item[1]?.icon || {})
  setTimeout(() => {
    inputVisible.value = true
    inputValue.value = props.item[0]
    nextTick(() => {
      inputRef.value?.focus()
      nextTick(() => {
        iconAreaRef.value?.setIcon(icon.value)
      })
    })
  }, 100)
}

function handleEditOk() {
  const iconVal = iconAreaRef.value?.getIcon()
  if (props.type === 'edit') {
    icon.value = {
      ...iconVal,
      color: iconVal && iconVal.name && iconVal.name.startsWith('icon-') ? iconVal.color || '' : '',
    }
    emit('editValue', props.item, inputValue.value, style.value, icon.value)
  } else {
    emit('add', inputValue.value, style.value, iconVal)
  }
  inputVisible.value = false
}

function changeFontStyle(key: string, value: string) {
  style.value = {
    ...cloneDeep(style.value),
    [key]: style.value[key] === value ? 'initial' : value,
  }
}

onMounted(() => {
  document.addEventListener('click', eventListener)
  style.value = cloneDeep(props.item[1]?.style || {})
  icon.value = cloneDeep(props.item[1]?.icon || {})
})

onBeforeUnmount(() => {
  document.removeEventListener('click', eventListener)
})
</script>

<template>
  <div style="display: inline; position: relative">
    <a-popover v-if="inputVisible" :open="true" placement="bottom" overlay-class-name="pre-value-edit-popover">
      <a-input
        ref="inputRef"
        v-model:value="inputValue"
        type="text"
        size="small"
        :style="{ width: '150px', marginBottom: type === 'add' ? '10px' : '5px' }"
        class="pre-value-tag-input"
      />
      <template #content>
        <div ref="preValueEditRef">
          <a-divider orientation="left" style="margin: 8px 0; color: gray; font-size: 10px">
            {{ t('cmdb.common.icon') }}
          </a-divider>
          <IconArea ref="iconAreaRef" />
          <a-divider orientation="left" style="margin: 8px 0; color: gray; font-size: 10px">
            {{ t('cmdb.ciType.font') }}
          </a-divider>
          <div :style="{ display: 'flex', justifyContent: 'space-around' }">
            <div
              class="attributes-font-icon"
              :class="{ 'attributes-font-icon-selected': style.fontWeight === 'bold' }"
              @click="changeFontStyle('fontWeight', 'bold')"
            >
              <BoldOutlined />
            </div>
            <div
              class="attributes-font-icon"
              :class="{ 'attributes-font-icon-selected': style.fontStyle === 'italic' }"
              @click="changeFontStyle('fontStyle', 'italic')"
            >
              <ItalicOutlined />
            </div>
            <div
              class="attributes-font-icon"
              :class="{ 'attributes-font-icon-selected': style.textDecoration === 'underline' }"
              @click="changeFontStyle('textDecoration', 'underline')"
            >
              <UnderlineOutlined />
            </div>
          </div>

          <a-divider orientation="left" style="margin: 8px 0; color: gray; font-size: 10px">
            {{ t('cmdb.ciType.color') }}
          </a-divider>
          <div :style="{ display: 'flex', justifyContent: 'space-around' }">
            <div class="attributes-font-color">
              <FontColorsOutlined />
              <input v-model="style.color" type="color" />
            </div>
            <div class="attributes-font-color">
              <BgColorsOutlined />
              <input v-model="style.backgroundColor" type="color" />
            </div>
          </div>
          <a-divider orientation="left" style="margin: 8px 0; color: gray; font-size: 10px">
            {{ t('operation') }}
          </a-divider>
          <div style="text-align: right">
            <a-tooltip v-if="type !== 'add'" :title="t('delete')">
              <a><DeleteOutlined v-if="type !== 'add'" style="margin-right: 10px; color: red" @click="handleDelete" /></a>
            </a-tooltip>
            <a-tooltip :title="t('confirm')">
              <a><CheckOutlined style="margin-right: 10px; color: green" @click="handleEditOk" /></a>
            </a-tooltip>
            <a-tooltip :title="t('cancel')">
              <a><CloseOutlined style="color: gray" @click="inputVisible = false" /></a>
            </a-tooltip>
          </div>
        </div>
      </template>
    </a-popover>
    <div
      v-else
      ref="valueTag"
      :class="`handle ${type === 'edit' ? 'pre-value-tag' : ''}`"
      :style="type === 'edit' && item[1] && item[1].style ? item[1].style : {}"
      @click="
        (e) => {
          if (!disabled) {
            e.preventDefault()
            handleEdit()
          }
        }
      "
    >
      <span :style="{ cursor: disabled ? 'default' : 'move' }">
        <img
          v-if="icon.id && icon.url"
          :src="`/api/common-setting/v1/file/${icon.url}`"
          :style="{ maxHeight: '12px', maxWidth: '12px', marginRight: '5px' }"
        />
        <AppstoreOutlined v-else-if="icon.name" :style="{ marginRight: '5px', color: icon.color || '#595959' }" />
        <span>{{ item[0] }}</span>
      </span>
      <a
        class="pre-value-tag-dropdown"
        @click="
          (e) => {
            if (!disabled) {
              e.preventDefault()
              handleEdit()
            }
          }
        "
      >
        <DownOutlined v-if="type === 'edit' && !disabled" class="pre-value-tag-dropdown-icon" />
        <slot v-else></slot>
      </a>
    </div>
  </div>
</template>

<style lang="less" scoped>
.pre-value-tag {
  display: inline-block;
  margin: 5px 15px 5px 0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  position: relative;
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
