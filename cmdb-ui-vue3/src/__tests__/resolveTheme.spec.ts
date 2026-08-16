// src/__tests__/resolveTheme.spec.ts
import { describe, it, expect, vi, afterEach } from 'vitest'
import { resolveTheme, getSystemDark } from '@/theme/resolveTheme'

describe('resolveTheme', () => {
  it("resolves 'system' to OS preference", () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true }))
    expect(resolveTheme('system')).toBe('dark')
    vi.stubGlobal('matchMedia', () => ({ matches: false }))
    expect(resolveTheme('system')).toBe('light')
  })

  it("resolves 'light' and 'dark' literally", () => {
    expect(resolveTheme('light')).toBe('light')
    expect(resolveTheme('dark')).toBe('dark')
  })

  it('maps unknown/legacy values to dark', () => {
    expect(resolveTheme('liquid-glass')).toBe('dark')
  })
})

describe('getSystemDark', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('returns true when prefers-color-scheme is dark', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true }))
    expect(getSystemDark()).toBe(true)
  })
})
