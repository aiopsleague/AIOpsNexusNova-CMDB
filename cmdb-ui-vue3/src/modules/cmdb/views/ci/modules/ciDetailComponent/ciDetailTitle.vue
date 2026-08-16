<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CI_DEFAULT_ATTR } from '@/modules/cmdb/constants'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    ci?: Record<string, any>
    ci_types?: Record<string, any>[]
  }>(),
  {
    ci: () => ({}),
    ci_types: () => [],
  }
)

const findCIType = computed<Record<string, any>>(
  () => props.ci_types?.find?.((item) => item?.id === props.ci?._type) || {}
)

const title = computed(() => props.ci?.[findCIType.value?.show_name] || props.ci?.[findCIType.value?.unique_key] || '')

const icon = computed(() => findCIType.value?.icon || '')

// icon string format: `name$$color$$id$$url`
const iconImgSrc = computed(() => {
  const parts = icon.value ? icon.value.split('$$') : []
  return parts[2] && parts[3] ? `/api/common-setting/v1/file/${parts[3]}` : ''
})
</script>

<template>
  <!-- eslint-disable vue/attributes-order -->
  <div class="ci-detail-title-card">
    <div class="ci-detail-title-main">
      <span class="ci-icon" :style="{ width: '24px', height: '24px' }">
        <img v-if="iconImgSrc" :src="iconImgSrc" />
        <span v-else class="ci-icon-letter">{{ title ? title[0].toUpperCase() : '' }}</span>
      </span>
      <span class="ci-detail-title-text">{{ title }}</span>
    </div>
    <div class="ci-detail-title-meta">
      <div class="ci-detail-title-meta-item" v-if="ci._id">
        <span class="meta-label">CI ID:</span>
        <span class="meta-value">{{ ci._id }}</span>
      </div>
      <div class="ci-detail-title-meta-item" v-if="ci[CI_DEFAULT_ATTR.UPDATE_TIME]">
        <span class="meta-label">{{ t('cmdb.components.updateTime') }}:</span>
        <span class="meta-value">{{ ci[CI_DEFAULT_ATTR.UPDATE_TIME] }}</span>
      </div>
      <div class="ci-detail-title-meta-item" v-if="ci[CI_DEFAULT_ATTR.UPDATE_USER]">
        <span class="meta-label">{{ t('cmdb.components.updater') }}:</span>
        <span class="meta-value">{{ ci[CI_DEFAULT_ATTR.UPDATE_USER] }}</span>
      </div>
      <div class="ci-detail-title-meta-item ci-detail-title-meta-item-citype" v-if="findCIType.alias">
        <span class="meta-label">{{ t('cmdb.ciType.ciType') }}:</span>
        <a-tag color="blue">
          {{ findCIType.alias }}
        </a-tag>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.ci-detail-title-card {
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  border: 1px solid #e8eaed;
}

.ci-detail-title-main {
  display: flex;
  align-items: center;
  column-gap: 12px;
  flex-shrink: 0;
  min-width: 0;
}

.ci-detail-title-text {
  font-size: 18px;
  font-weight: 600;
  color: @text-color_1;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ci-detail-title-meta {
  display: flex;
  align-items: center;
  column-gap: 20px;
  row-gap: 6px;
  flex-wrap: nowrap;
  max-width: 100%;
  overflow: hidden;
}

.ci-detail-title-meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  flex-shrink: 0;

  &-citype {
    flex-shrink: 1;

    .ant-tag {
      border-radius: 4px;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      text-wrap-mode: nowrap;
    }
  }

  .meta-label {
    font-size: 12px;
    color: @text-color_3;
    font-weight: 500;
    flex-shrink: 0;
  }

  .meta-value {
    font-size: 12px;
    color: @text-color_2;
    background: #f5f7fa;
    padding: 2px 8px;
    border-radius: 4px;
  }
}

.ci-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  img {
    width: 100%;
    height: 100%;
  }

  .ci-icon-letter {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #ffffff;
    color: @primary-color;
    border-radius: 4px;
    box-shadow: 0 1px 2px rgba(47, 84, 235, 0.2);
    font-size: 14px;
    font-weight: 600;
  }
}
</style>
