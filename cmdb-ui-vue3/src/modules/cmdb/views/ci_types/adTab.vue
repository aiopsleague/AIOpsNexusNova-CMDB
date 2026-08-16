<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AttrAD from './attrAD.vue'
import RelationAD from './relationAD.vue'

const AD_TAB_KEY = {
  ATTR: '1',
  RELATION: '2',
} as const

withDefaults(defineProps<{ CITypeId?: number | null }>(), { CITypeId: null })

const { t } = useI18n()

const activeKey = ref<string>(AD_TAB_KEY.ATTR)
const windowHeight = computed(() => window.innerHeight)

const tabs = [
  {
    key: AD_TAB_KEY.ATTR,
    label: 'cmdb.ciType.attributeAD',
  },
  {
    key: AD_TAB_KEY.RELATION,
    label: 'cmdb.ciType.relationAD',
  },
]

function changeTab(key: string) {
  activeKey.value = key
}
</script>

<template>
  <!-- eslint-disable vue/attribute-hyphenation, vue/attributes-order -->
  <div class="ad-container" :style="{ height: `${windowHeight - 130}px` }">
    <div class="ad-btns">
      <div
        :class="['ad-btns-item', activeKey === item.key ? 'ad-btns-item_active' : '']"
        v-for="item in tabs"
        :key="item.key"
        @click="changeTab(item.key)"
      >
        {{ t(item.label) }}
      </div>
    </div>
    <AttrAD
      v-if="activeKey === AD_TAB_KEY.ATTR"
      :CITypeId="CITypeId"
    ></AttrAD>
    <RelationAD
      v-else-if="activeKey === AD_TAB_KEY.RELATION"
      :CITypeId="CITypeId"
    ></RelationAD>
  </div>
</template>

<style lang="less" scoped>
.ad-btns {
  display: inline-flex;
  align-items: center;
  border: solid 1px @border-color-base;
  margin-left: 17px;
  margin-bottom: 15px;

  &-item {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 6px 20px;
    background-color: #ffffff;
    cursor: pointer;

    color: @text-color_2;
    font-size: 14px;
    font-weight: 400;

    &:hover {
      color: @primary-color;
    }

    &:not(:first-child) {
      border-left: solid 1px @border-color-base;
    }

    &_active {
      background-color: @primary-color;
      color: #ffffff;

      &:hover {
        color: #ffffff;
      }
    }
  }
}
</style>
