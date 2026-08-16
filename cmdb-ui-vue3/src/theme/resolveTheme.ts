// src/theme/resolveTheme.ts
export type ThemeMode = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

/** 当前系统是否偏好深色。 */
export function getSystemDark(): boolean {
  return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)
}

/**
 * 将用户选择的 themeMode 解析为实际主题：
 * - 'system' → 跟随系统偏好
 * - 'light' → 'light'
 * - 其余（含旧 'liquid-glass' 等）→ 'dark'
 */
export function resolveTheme(mode: ThemeMode): ResolvedTheme {
  if (mode === 'system') return getSystemDark() ? 'dark' : 'light'
  if (mode === 'light') return 'light'
  return 'dark'
}
