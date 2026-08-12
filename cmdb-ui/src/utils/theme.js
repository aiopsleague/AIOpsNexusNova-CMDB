/**
 * Runtime theme system: resolve light/dark/liquid-glass/system and apply the
 * appropriate theme css link.
 * See docs/superpowers/specs/2026-08-12-theme-settings-design.md
 *     docs/superpowers/specs/2026-08-12-liquid-glass-theme-design.md
 */

// Theme css is served from public/ at dev/build time (see scripts/build-theme.js).
// It is injected as a dynamic <link> with no content hash, so browsers may
// aggressively cache it; add a query param to bypass that cache.
// - dev: Date.now() so every reload refetches the freshly regenerated css
// - prod: fixed version, bump on release to invalidate stale cached css
const DARK_CSS_VERSION = process.env.NODE_ENV === 'development' ? Date.now() : '20260812'
const BASE = process.env.BASE_URL || '/'

// Map resolved theme → CSS path (light has no CSS file)
const THEME_CSS_MAP = {
  dark: `${BASE}themes/dark.css?v=${DARK_CSS_VERSION}`,
  'liquid-glass': `${BASE}themes/liquid-glass.css?v=${DARK_CSS_VERSION}`
}

// Body backgrounds per theme (set to match base bg, prevents white flash)
const THEME_BODY_BG = {
  dark: '#121216',
  'liquid-glass': '#080a10'
}

/**
 * Get the topology canvas background color for the current theme.
 * Used by topology_view/index.vue and other relation-graph consumers.
 * Exported so components can import it directly.
 */
export function getTopoCanvasBg() {
  if (typeof window !== 'undefined' && window.getComputedStyle) {
    const v = window.getComputedStyle(document.documentElement).getPropertyValue('--ops-topo-canvas-bg').trim()
    if (v) return v
  }
  const theme = document.documentElement.getAttribute('data-theme')
  if (theme === 'dark') return '#121216'
  if (theme === 'liquid-glass') return '#080a10'
  return '#FFFFFF'
}

export function getSystemDark () {
  return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)
}

/**
 * Resolve a user-chosen themeMode to the actual theme value.
 * 'system' follows OS preference → 'dark' | 'light'
 * 'liquid-glass' → 'liquid-glass'
 * everything else → 'dark' | 'light'
 */
export function resolveTheme (mode) {
  if (mode === 'system') {
    return getSystemDark() ? 'dark' : 'light'
  }
  if (mode === 'liquid-glass') {
    return 'liquid-glass'
  }
  return mode === 'dark' ? 'dark' : 'light'
}

/**
 * Sync the <link id="theme-style"> element to load the correct CSS file.
 * - dark / liquid-glass → injects the corresponding <link>
 * - light → removes the <link>
 * Switches href when moving between dark ↔ liquid-glass.
 */
function syncThemeCss (theme) {
  const link = document.getElementById('theme-style')
  const cssPath = THEME_CSS_MAP[theme]  // undefined for 'light'

  if (cssPath) {
    if (!link) {
      const el = document.createElement('link')
      el.id = 'theme-style'
      el.rel = 'stylesheet'
      el.href = cssPath
      document.head.appendChild(el)
    } else if (link.getAttribute('href') !== cssPath) {
      // Switching between dark ↔ liquid-glass: update href
      link.setAttribute('href', cssPath)
    }
  } else if (link) {
    // Light mode: remove any theme CSS
    link.remove()
  }
}

/**
 * Apply the resolved theme:
 * 1. Set data-theme attribute on <html>
 * 2. Load/unload the theme CSS file
 * 3. Sync body background to prevent flash during route transitions
 * 4. Dispatch ops:theme-change event for charts/components
 */
export function applyTheme (resolved) {
  const isDark = resolved === 'dark'
  const isLiquid = resolved === 'liquid-glass'

  document.documentElement.setAttribute('data-theme', resolved)
  syncThemeCss(resolved)

  // Sync body background to avoid white flash between route transitions
  if (document.body) {
    if (isLiquid) {
      document.body.style.backgroundColor = THEME_BODY_BG['liquid-glass']
    } else if (isDark) {
      document.body.style.backgroundColor = THEME_BODY_BG['dark']
    } else {
      document.body.style.backgroundColor = ''
    }
  }

  // Notify charts/components that need to re-render on theme change
  if (typeof window !== 'undefined' && typeof window.CustomEvent === 'function') {
    window.dispatchEvent(new CustomEvent('ops:theme-change', { detail: { theme: resolved } }))
  }
}

/**
 * Initialize the theme system.
 * - Apply the current theme immediately
 * - Subscribe to Vuex mutations for TOGGLE_THEME / TOGGLE_THEME_MODE
 * - Listen for OS prefers-color-scheme changes (for system mode)
 */
export function initThemeSystem (store) {
  applyTheme(store.state.app.theme)

  store.subscribe((mutation) => {
    if (mutation.type === 'TOGGLE_THEME' || mutation.type === 'TOGGLE_THEME_MODE') {
      applyTheme(store.state.app.theme)
    }
  })

  if (window.matchMedia) {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      if (store.state.app.themeMode === 'system') {
        store.commit('TOGGLE_THEME', resolveTheme('system'))
      }
    }
    if (media.addEventListener) {
      media.addEventListener('change', handler)
    } else if (media.addListener) {
      media.addListener(handler)
    }
  }
}
