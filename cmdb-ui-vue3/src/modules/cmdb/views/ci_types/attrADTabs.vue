<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { AppstoreOutlined, EditOutlined, DeleteOutlined, PlusCircleOutlined } from '@ant-design/icons-vue'

withDefaults(
  defineProps<{
    currentTab?: string | number
    adCITypeList?: any[]
    getADCITypeParam?: (adr_id: number | string, params?: string, isAll?: boolean) => any
  }>(),
  {
    currentTab: '',
    adCITypeList: () => [],
    getADCITypeParam: () => () => '',
  }
)

const emit = defineEmits<{
  (e: 'changeTab', id: string | number): void
  (e: 'changeAlias', payload: { id: string | number; value: string; isClient: boolean }): void
  (e: 'deleteADT', item: any): void
  (e: 'clickAdd'): void
}>()

const nameEditId = ref<string | number>('')
const nameEditValue = ref('')

function changeTab(id: string | number) {
  emit('changeTab', id)
}

function openNameEdit(e: Event, item: any) {
  e.preventDefault()
  e.stopPropagation()
  nameEditId.value = item.id
  if (item?.extra_option?.alias) {
    nameEditValue.value = item.extra_option.alias
  }
}

function changeAlias(isClient: boolean) {
  emit('changeAlias', {
    id: nameEditId.value,
    value: nameEditValue.value,
    isClient,
  })
  nextTick(() => {
    nameEditId.value = ''
    nameEditValue.value = ''
  })
}

function deleteADT(e: Event, item: any) {
  e.preventDefault()
  e.stopPropagation()
  emit('deleteADT', item)
}

function clickAdd() {
  emit('clickAdd')
}
</script>

<template>
  <div class="attr-ad-tabs">
    <div
      v-for="item in adCITypeList"
      :key="item.id"
      :class="['attr-ad-tab', currentTab === item.id ? 'attr-ad-tab_active' : '']"
      @click="changeTab(item.id)"
    >
      <img
        v-if="item.icon.id && item.icon.url"
        :src="`/api/common-setting/v1/file/${item.icon.url}`"
        class="attr-ad-tab-icon"
      />
      <AppstoreOutlined
        v-else
        :style="{ color: item.icon.color }"
        class="attr-ad-tab-icon"
      />
      <a-input
        v-if="nameEditId === item.id"
        v-model:value="nameEditValue"
        size="small"
        :autofocus="true"
        @blur="changeAlias(item.isClient || false)"
      />
      <span v-else class="attr-ad-tab-name">
        {{ item.extra_option && item.extra_option.alias ? item.extra_option.alias : getADCITypeParam(item.adr_id) }}
      </span>
      <EditOutlined class="attr-ad-tab-edit" @click="(e) => openNameEdit(e, item)" />
      <DeleteOutlined class="attr-ad-tab-delete" @click="(e) => deleteADT(e, item)" />
    </div>
    <PlusCircleOutlined class="attr-ad-tabs-add" @click="clickAdd" />
  </div>
</template>

<style lang="less" scoped>
.attr-ad-tabs {
  display: flex;
  align-items: center;
  width: 100%;
  overflow-x: auto;
  padding-bottom: 10px;

  .attr-ad-tab {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px 24px;
    margin-right: 12px;
    background-color: @primary-color_7;
    cursor: pointer;
    flex-shrink: 0;

    &-name {
      font-weight: 400;
      font-size: 12px;
    }

    &-icon {
      font-size: 12px;
      width: 12px;
      height: 12px;
      margin-right: 4px;
    }

    &-edit {
      display: none;
      font-size: 10px;
      color: @text-color_4;
      margin-left: 4px;
    }

    &-delete {
      display: none;
      font-size: 10px;
      color: @func-color_1;
      margin-left: 6px;
    }

    &:hover {
      background-color: @primary-color_5;

      .attr-ad-tab-edit {
        display: inline-block;
      }
      .attr-ad-tab-delete {
        display: inline-block;
      }
    }

    &_active {
      border: solid 1px @primary-color_8;
      background-color: @primary-color_6;

      .attr-ad-tab-name {
        color: @primary-color;
      }

      &:hover {
        background-color: @primary-color_6;
      }
    }
  }

  &-add {
    padding: 11px;
    background-color: @primary-color_7;
    font-size: 12px;
    color: @text-color_4;

    &:hover {
      background-color: @primary-color_5;
      color: @primary-color;
    }
  }
}
</style>
