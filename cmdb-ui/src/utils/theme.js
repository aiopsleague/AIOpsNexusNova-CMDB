/**
 * Runtime theme system: resolve light/dark/system and apply the dark css link.
 * See docs/superpowers/specs/2026-08-12-theme-settings-design.md
 */

// dark css is served from public/ at dev/build time (see scripts/build-theme.js)
const DARK_CSS_PATH = `${process.env.BASE_URL || '/'}themes/dark.css`

export function getSystemDark () {
  return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)
}

export function resolveTheme (mode) {
  if (mode === 'system') {
    return getSystemDark() ? 'dark' : 'light'
  }
  return mode === 'dark' ? 'dark' : 'light'
}

function syncDarkCss (dark) {
  const link = document.getElementById('theme-style')
  if (dark) {
    if (!link) {
      const el = document.createElement('link')
      el.id = 'theme-style'
      el.rel = 'stylesheet'
      el.href = DARK_CSS_PATH
      document.head.appendChild(el)
    }
  } else if (link) {
    link.remove()
  }
}

export function applyTheme (resolved) {
  const dark = resolved === 'dark'
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
  syncDarkCss(dark)
  // keep body background in sync to avoid white flash between route transitions
  if (document.body) {
    document.body.style.backgroundColor = dark ? '#141414' : ''
  }
}

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
