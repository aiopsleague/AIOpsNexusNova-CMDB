// src/stores/app.ts
import { defineStore } from 'pinia'
import { resolveTheme, type ThemeMode, type ResolvedTheme } from '@/theme/resolveTheme'
import setting from '@/config/setting'

interface AppState {
  themeMode: ThemeMode
  sidebar: boolean
  layout: 'sidemenu' | 'topmenu'
  fixedHeader: boolean
  fixSiderbar: boolean
  contentWidth: 'Fluid' | 'Fixed'
  colorWeak: boolean
  multiTab: boolean
}

export const useAppStore = defineStore('app', {
  state: (): AppState => ({
    themeMode: setting.themeMode,
    sidebar: true,
    layout: setting.layout,
    fixedHeader: setting.fixedHeader,
    fixSiderbar: setting.fixSiderbar,
    contentWidth: setting.contentWidth,
    colorWeak: setting.colorWeak,
    multiTab: setting.multiTab,
  }),
  getters: {
    resolvedTheme(state): ResolvedTheme {
      return resolveTheme(state.themeMode)
    },
  },
  actions: {
    setThemeMode(mode: ThemeMode) {
      this.themeMode = mode
    },
    toggleSidebar() {
      this.sidebar = !this.sidebar
    },
  },
  persist: {
    key: 'pro__app',
    pick: ['themeMode', 'sidebar', 'layout', 'fixedHeader', 'fixSiderbar', 'contentWidth', 'colorWeak', 'multiTab'],
  },
})
