/**
 * Runtime theme system: resolve light/dark/system and apply the appropriate
 * theme css link. The dark theme carries the liquid-glass visual.
 * See docs/superpowers/specs/2026-08-12-theme-settings-design.md
 *     docs/superpowers/specs/2026-08-12-dark-theme-design.md
 */

// Theme css is served from public/ at dev/build time (see scripts/build-theme.js).
// It is injected as a dynamic <link> with no content hash, so browsers may
// aggressively cache it; add a query param to bypass that cache.
// - dev: Date.now() so every reload refetches the freshly regenerated css
// - prod: fixed version, bump on release to invalidate stale cached css
const THEME_CSS_VERSION = process.env.NODE_ENV === 'development' ? Date.now() : '20260813'
const BASE = process.env.BASE_URL || '/'

// Map resolved theme → CSS path (light has no CSS file)
const THEME_CSS_MAP = {
  dark: `${BASE}themes/dark.css?v=${THEME_CSS_VERSION}`
}

// Body backgrounds per theme (set to match base bg, prevents white flash)
const THEME_BODY_BG = {
  dark: '#080a10'
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
  if (theme === 'dark') return '#080a10'
  return '#FFFFFF'
}

export function getSystemDark () {
  return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)
}

/**
 * Resolve a user-chosen themeMode to the actual theme value.
 * 'system' follows OS preference → 'dark' | 'light'
 * 'light' → 'light'
 * everything else (incl. legacy persisted 'liquid-glass') → 'dark'
 */
export function resolveTheme (mode) {
  if (mode === 'system') {
    return getSystemDark() ? 'dark' : 'light'
  }
  if (mode === 'light') {
    return 'light'
  }
  // 'dark' resolves to itself; the legacy 'liquid-glass' value also maps here
  return 'dark'
}

/**
 * Sync the <link id="theme-style"> element to load the correct CSS file.
 * - dark → injects the <link>
 * - light → removes the <link>
 */
function syncThemeCss (theme) {
  const link = document.getElementById('theme-style')
  const cssPath = THEME_CSS_MAP[theme] // undefined for 'light'

  if (cssPath) {
    if (!link) {
      const el = document.createElement('link')
      el.id = 'theme-style'
      el.rel = 'stylesheet'
      el.href = cssPath
      document.head.appendChild(el)
    } else if (link.getAttribute('href') !== cssPath) {
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

  document.documentElement.setAttribute('data-theme', resolved)
  syncThemeCss(resolved)

  // Sync body background to avoid white flash between route transitions
  if (document.body) {
    document.body.style.backgroundColor = isDark ? THEME_BODY_BG['dark'] : ''
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
