<script setup lang="ts">
import { computed, nextTick, onMounted, onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { AppstoreOutlined, CloseOutlined, PlusOutlined } from '@ant-design/icons-vue'
import dataEmptyImg from '@/assets/data_empty.png'
import { postImageFile, getFileData as fetchFileData, addFileData, deleteFileData } from '@/api/file'
import {
  iconTypeList,
  linearIconList,
  fillIconList,
  multicolorIconList,
  extendIconList,
  type IconCategory,
} from './constants'

interface IconValue {
  name?: string
  color?: string
  id?: string | number
  url?: string
}

interface CustomIcon {
  id: string | number
  data: { name: string; url?: string }
}

const props = withDefaults(
  defineProps<{
    value?: IconValue
    iconType?: string
  }>(),
  {
    value: () => ({ name: '', color: '' }),
    iconType: 'cmdb',
  }
)

const emit = defineEmits<{ (e: 'change', v: IconValue): void }>()
const { t } = useI18n()

const visible = ref(false)
const currentIconType = ref('3')
const customIconList = ref<CustomIcon[]>([])
const formVisible = ref(false)
const formImg = ref<string | null>(null)
const nameValue = ref('')
const uploadFile = ref<File | null>(null)
const uuid = uuidv4()

const iconTypeOptions = computed(() => iconTypeList(t))

const iconCategories = computed<IconCategory[]>(() => {
  switch (currentIconType.value) {
    case '0':
      // Common icons (`changyong-*`) are deprecated.
      return []
    case '1':
      return linearIconList
    case '2':
      return fillIconList
    case '3':
      return multicolorIconList
    case '5':
      return extendIconList
    default:
      return linearIconList
  }
})

const valueColor = computed<string>({
  get: () => props.value.color || '#000000',
  set: (color: string) => emit('change', { ...props.value, color }),
})

function uuidv4(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

function loadCustomIcons() {
  fetchFileData('ops-custom-icon').then((res: CustomIcon[]) => {
    customIconList.value = res
  })
}

function eventListener(e: MouseEvent) {
  if (!visible.value) {
    return
  }
  const dom = document.getElementById('custom-icon-select-popover')
  const domIcon = document.getElementById(`custom-icon-select-block-${uuid}`)
  e.stopPropagation()
  e.preventDefault()
  if (dom) {
    const isSelf = dom.contains(e.target as Node) || domIcon?.contains(e.target as Node)
    if (!isSelf) {
      visible.value = false
    }
  }
}

function clickIcon(name: string) {
  if (name === props.value.name) {
    emit('change', { name: '', color: '' })
  } else {
    emit('change', {
      name,
      color: props.value.name && props.value.name.startsWith('icon-') ? props.value.color || '' : '',
    })
  }
}

function clickCustomIcon(icon: CustomIcon) {
  if (icon.id === props.value.id) {
    emit('change', { name: '', color: '' })
  } else {
    emit('change', { name: icon.data.name, id: icon.id, url: icon?.data?.url })
  }
}

function showSelect() {
  visible.value = true
  if (!props.value.name) {
    currentIconType.value = '3'
    return
  }
  if (props.value.name.startsWith('changyong-')) {
    currentIconType.value = '0'
  } else if (props.value.name.startsWith('icon-xianxing')) {
    currentIconType.value = '1'
  } else if (props.value.name.startsWith('icon-shidi')) {
    currentIconType.value = '2'
  } else if (props.value.name.startsWith('caise')) {
    currentIconType.value = '3'
  } else if (props.value.name.startsWith('icon-')) {
    currentIconType.value = '5'
  } else {
    currentIconType.value = '4'
  }
}

function handleChangeIconType(value: string) {
  currentIconType.value = value
}

function fileName(file: File): string {
  const parts = file.name.split('.')
  return parts.splice(0, parts.length - 1).join('')
}

function beforeUpload(file: File): boolean {
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    message.error(t('customIconSelect.sizeLimit'))
    return false
  }
  const reader = new FileReader()
  reader.readAsDataURL(file)
  reader.onload = () => {
    formVisible.value = true
    nextTick(() => {
      uploadFile.value = file
      formImg.value = reader.result as string
      nameValue.value = fileName(file)
    })
  }
  return false
}

function handleCancel() {
  formVisible.value = false
  nameValue.value = ''
  formImg.value = null
}

function handleOk() {
  if (!nameValue.value) {
    message.error(t('placeholder1'))
    return
  }
  if (!uploadFile.value) {
    return
  }
  const fm = new FormData()
  fm.append('file', uploadFile.value)
  postImageFile(fm).then((res: { file_name: string }) => {
    addFileData('ops-custom-icon', { data: { name: nameValue.value, url: res.file_name } }).then(() => {
      message.success(t('uploadSuccess'))
      handleCancel()
      loadCustomIcons()
    })
  })
}

function deleteIcon(e: Event, icon: CustomIcon) {
  e.stopPropagation()
  e.preventDefault()
  deleteFileData('ops-custom-icon', icon.id).then(() => {
    message.success(t('deleteSuccess'))
    handleCancel()
    loadCustomIcons()
  })
}

function getPopupContainer(trigger: HTMLElement): HTMLElement {
  return trigger.parentNode as HTMLElement
}

onMounted(() => {
  document.addEventListener('click', eventListener)
  loadCustomIcons()
})

onBeforeUnmount(() => {
  document.removeEventListener('click', eventListener)
})
</script>

<template>
  <a-popover :open="visible" overlay-class-name="custom-icon-select-popover" placement="bottom">
    <template #content>
      <div id="custom-icon-select-popover">
        <div class="custom-icon-select-popover-icon-type">
          <div
            v-for="item in iconTypeOptions"
            :key="item.value"
            :class="currentIconType === item.value ? 'selected' : ''"
            @click="handleChangeIconType(item.value)"
          >
            {{ item.label }}
          </div>
          <div :class="currentIconType === '4' ? 'selected' : ''" @click="handleChangeIconType('4')">
            {{ t('customIconSelect.custom') }}
          </div>
          <a-upload
            v-if="currentIconType === '4'"
            name="avatar"
            :before-upload="beforeUpload"
            :show-upload-list="false"
            accept=".svg,.png,.jpg,.jpeg"
          >
            <a-button size="small" type="primary">
              <template #icon><PlusOutlined /></template>{{ t('add') }}
            </a-button>
          </a-upload>
        </div>
        <div class="custom-icon-select-popover-content">
          <template v-if="currentIconType === '4'">
            <div
              v-if="customIconList.length"
              class="custom-icon-select-popover-content-wrapper"
              :style="{ marginTop: '10px' }"
            >
              <div
                v-for="icon in customIconList"
                :key="icon.id"
                :class="`custom-icon-select-popover-item ${value.id === icon.id ? 'selected' : ''}`"
                @click="clickCustomIcon(icon)"
              >
                <div class="custom-icon-select-popover-content-img-box">
                  <img v-if="icon.data && icon.data.url" :src="`/api/common-setting/v1/file/${icon.data.url}`" />
                  <a-popconfirm
                    overlay-class-name="custom-icon-select-confirm-popover"
                    :get-popup-container="getPopupContainer"
                    :title="t('confirmDelete')"
                    @confirm="(e: any) => deleteIcon(e, icon)"
                    @cancel="(e: any) => { e.stopPropagation(); e.preventDefault() }"
                  >
                    <CloseOutlined
                      @click="
                        (e: MouseEvent) => {
                          e.stopPropagation()
                          e.preventDefault()
                        }
                      "
                    />
                  </a-popconfirm>
                </div>
                <span class="custom-icon-select-popover-item-label" :title="icon.data.name">{{ icon.data.name }}</span>
              </div>
            </div>
            <a-empty v-else :style="{ marginTop: '15%' }">
              <template #image><img :src="dataEmptyImg" /></template>
              <template #description>
                <a-upload
                  name="avatar"
                  :before-upload="beforeUpload"
                  :show-upload-list="false"
                  accept=".svg,.png,.jpg,.jpeg"
                >
                  <a>{{ t('customIconSelect.nodata') }}</a>
                </a-upload>
              </template>
            </a-empty>
          </template>
          <template v-else>
            <div v-for="category in iconCategories" :key="category.value">
              <h4 class="category">{{ t(category.label) }}</h4>
              <div class="custom-icon-select-popover-content-wrapper">
                <div
                  v-for="name in category.list"
                  :key="name.value"
                  :class="`custom-icon-select-popover-item ${value.name === name.value ? 'selected' : ''}`"
                  @click="clickIcon(name.value)"
                >
                  <AppstoreOutlined />
                  <span class="custom-icon-select-popover-item-label">{{ name.label }}</span>
                </div>
              </div>
            </div>
          </template>
        </div>
        <template v-if="!['0', '3', '4'].includes(currentIconType)">
          <a-divider :style="{ margin: '5px 0' }" />
          <input v-model="valueColor" type="color" />
        </template>
        <a-form
          v-show="currentIconType === '4' && formVisible"
          class="custom-icon-select-form"
          :label-col="{ span: 4 }"
          :wrapper-col="{ span: 16 }"
        >
          <a-form-item :label="t('name')">
            <a-input v-model:value="nameValue" />
          </a-form-item>
          <a-form-item :label="t('customIconSelect.preview')">
            <div class="custom-icon-select-form-img">
              <img :src="formImg || undefined" />
            </div>
          </a-form-item>
          <a-form-item label=" " :colon="false" :wrapper-col="{ span: 16 }">
            <a-space>
              <a-button size="small" @click="handleCancel">{{ t('cancel') }}</a-button>
              <a-button size="small" type="primary" @click="handleOk">{{ t('confirm') }}</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </div>
    </template>

    <div :id="`custom-icon-select-block-${uuid}`" class="custom-icon-select-block" @click="showSelect">
      <img v-if="value.id && value.url" :src="`/api/common-setting/v1/file/${value.url}`" />
      <AppstoreOutlined
        v-else
        :style="{ color: value.name && value.name.startsWith('icon-') ? value.color || '' : '' }"
      />
    </div>
  </a-popover>
</template>

<style lang="less">
.custom-icon-select-popover.ant-popover-placement-top .ant-popover-content {
  margin-bottom: -10px;
}
.custom-icon-select-popover {
  width: 650px;
  overflow: auto;
  padding-top: 0;
  box-shadow: 0px 2px 12px rgba(0, 0, 0, 0.1);
  .ant-popover-arrow {
    display: none;
  }
  .ant-popover-inner-content {
    padding: 4px 6px;
  }
  .custom-icon-select-popover-content {
    height: 400px;
    overflow: auto;
    .category {
      font-size: 14px;
    }
    .custom-icon-select-popover-content-wrapper {
      font-size: 24px;
      display: flex;
      flex-direction: row;
      flex-wrap: wrap;
      margin-left: 10px;
      .custom-icon-select-popover-item {
        width: 60px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        padding: 5px 5px 2px 5px;
        margin: 0 2px 6px;
        color: #666;
        position: relative;
        .custom-icon-select-popover-item-label {
          margin-top: 6px;
          font-size: 11px;
          width: 100%;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          text-align: center;
        }
        &:hover {
          background-color: #eeeeee;
          .custom-icon-select-popover-content-img-box > i {
            display: inline;
          }
        }
        .custom-icon-select-popover-content-img-box {
          width: 26px;
          height: 26px;
          display: flex;
          align-items: center;
          justify-content: center;
          > img {
            max-width: 26px;
            max-height: 26px;
          }
          > i {
            display: none;
            position: absolute;
            top: 2px;
            right: 2px;
            font-size: 12px;
            &:hover {
              color: #2f54eb;
            }
          }
        }
      }
      .selected {
        background-color: #eeeeee;
      }
    }
  }
  .custom-icon-select-popover-icon-type {
    display: inline-block;
    width: 100%;
    position: relative;
    > div {
      cursor: pointer;
      display: inline-block;
      padding: 2px 8px;
      border: 1px solid #eeeeee;
      &:hover {
        color: #2f54eb;
      }
    }
    .selected {
      border-color: #2f54eb;
    }
    .ant-btn {
      position: absolute;
      right: 0;
      top: 50%;
      transform: translateY(-50%);
    }
  }

  .custom-icon-select-confirm-popover .ant-popover-inner-content {
    width: 150px;
  }
}
</style>

<style lang="less" scoped>
.custom-icon-select-block {
  position: relative;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: 1px solid #d9d9d9;
  display: inline-block;
  cursor: pointer;
  > i,
  > img {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
  > img {
    max-width: 26px;
    max-height: 26px;
  }
  > i {
    font-size: 18px;
  }
}
.custom-icon-select-form {
  .custom-icon-select-form-img {
    width: 28px;
    height: 28px;
    border-radius: 4px;
    border: 1px solid #d9d9d9;
    display: inline-flex;
    margin-top: 5px;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    img {
      max-width: 26px;
      max-height: 26px;
    }
  }
}
</style>
