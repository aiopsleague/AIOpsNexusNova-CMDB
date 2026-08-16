<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import itsmUninstalledImg from '@/assets/itsm_uninstalled.png'

const { t } = useI18n()
</script>

<template>
  <a-empty
    :image="itsmUninstalledImg"
    :image-style="{
      height: '200px',
    }"
    :style="{ paddingTop: '10%' }"
  >
    <template #description> {{ t('cmdb.history.itsmUninstalled') }} </template>
    <a-button href="https://veops.cn/apply" target="_blank" type="primary">
      {{ t('cmdb.history.applyItsm') }}
    </a-button>
  </a-empty>
</template>
