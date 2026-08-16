<script setup lang="ts">
import { computed } from 'vue'
import { ConfigProvider } from 'ant-design-vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import enUS from 'ant-design-vue/es/locale/en_US'
import { useI18n } from 'vue-i18n'
import { useTheme } from '@/theme/useTheme'

const { locale } = useI18n()
const { themeConfig } = useTheme()

const antdLocale = computed(() => (locale.value === 'en' ? enUS : zhCN))
</script>

<template>
  <ConfigProvider :theme="themeConfig" :locale="antdLocale">
    <router-view />
  </ConfigProvider>
</template>
