// src/theme/system.ts
import pinia from '@/stores'
import { useAppStore } from '@/stores/app'

/** 订阅系统 prefers-color-scheme 变化，使 system 主题模式在运行时即时跟随。 */
export function initThemeSystem() {
  if (!window.matchMedia) return
  const appStore = useAppStore(pinia)
  const media = window.matchMedia('(prefers-color-scheme: dark)')
  const handler = (e: MediaQueryListEvent) => appStore.setSystemDark(e.matches)
  media.addEventListener('change', handler)
}
