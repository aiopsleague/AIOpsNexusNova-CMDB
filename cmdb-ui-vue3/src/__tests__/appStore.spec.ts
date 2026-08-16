// src/__tests__/appStore.spec.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from '@/stores/app'

describe('useAppStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('defaults themeMode to system', () => {
    const store = useAppStore()
    expect(store.themeMode).toBe('system')
  })

  it('setThemeMode updates themeMode and resolvedTheme', () => {
    const store = useAppStore()
    store.setThemeMode('dark')
    expect(store.themeMode).toBe('dark')
    expect(store.resolvedTheme).toBe('dark')
  })
})
