// src/theme/useTheme.ts
import { computed } from 'vue'
import { theme as antdTheme } from 'ant-design-vue'
import { useAppStore } from '@/stores/app'
import { COLOR_PRIMARY } from './tokens'

/** 提供响应式的 antd 主题配置（明/暗算法 + 主题色 token）。 */
export function useTheme() {
  const appStore = useAppStore()
  const themeConfig = computed(() => ({
    algorithm: appStore.resolvedTheme === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
    token: { colorPrimary: COLOR_PRIMARY },
  }))
  return { themeConfig }
}
