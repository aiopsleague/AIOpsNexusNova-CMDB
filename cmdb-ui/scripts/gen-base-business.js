/**
 * Generate the dark theme base business overrides for cmdb/acl business module
 * scoped light backgrounds AND dark text colors.
 * Scans src/modules/{cmdb,acl}/views/*.vue and standalone .less scoped styles,
 * expands less nesting, maps common light bg colors to the dark palette and
 * dark text colors to light equivalents, and writes
 * src/style/themes/base-business.less (consumed by dark.less).
 * Usage: node scripts/gen-base-business.js
 */
const fs = require('fs')
const path = require('path')

const CWD = path.resolve(__dirname, '..')
const OUT = path.join(CWD, 'src/style/themes/base-business.less')

// Light backgrounds → dark surface equivalents
const COLOR_MAP = {
  '#ffffff': '#1e1e24',
  '#f7f8fa': '#1e1e24',
  '#fafafa': '#1e1e24',
  '#f9fbff': '#2e2a4b',
  '#f5f5f5': '#2c2c31',
  '#f5f7fa': '#2c2c31',
  '#f0f0f0': '#2c2c31',
  '#f0f2f5': '#2c2c31',
  '#f0f1f5': '#1e1e24',
  '#ebeff8': '#282544',
  '#f0f5ff': '#282544',
  '#f4f9ff': '#282544',
  '#e8eaed': '#2c2c31',
  '#e4e7ed': '#2c2c31',
  '#e9e9e9': '#2c2c31',
  '#e1efff': '#2a2748',
  '#eeeeee': '#2c2c31',
  '#f6f6f6': '#2c2c31',
  '#f2f3f5': '#2c2c31',
  '#f5f8fe': '#282544',
  '#e7ecf3': '#2e2e38',
  '#e5e7eb': '#2c2c31',
  '#f8f9fd': '#1e1e24',
  '#f2f6fc': '#282544',
  '#fff1f0': '#2a1215',
  '#e6f7ff': '#111d2c',
  '#f0f7ff': '#1f1b3d',
  '#eff3fa': '#1e1e24',
}

// Dark text colors (designed for light backgrounds) → light text equivalents for dark mode
// Brightness thresholds: < #555 → primary (#f0f0f3), #555–#999 → secondary (#9999a6)
const TEXT_COLOR_MAP = {
  '#000': '#f0f0f3',
  '#000000': '#f0f0f3',
  '#111': '#f0f0f3',
  '#111111': '#f0f0f3',
  '#222': '#f0f0f3',
  '#222222': '#f0f0f3',
  '#333': '#f0f0f3',
  '#333333': '#f0f0f3',
  '#444': '#f0f0f3',
  '#444444': '#f0f0f3',
  '#555': '#9999a6',
  '#555555': '#9999a6',
  '#666': '#9999a6',
  '#666666': '#9999a6',
  '#777': '#9999a6',
  '#777777': '#9999a6',
  '#888': '#8f959e',
  '#888888': '#8f959e',
  '#999': '#9999a6',
  '#999999': '#9999a6',
}

// Less variable names used for text color → dark mode value
// Scoped styles compile these variables at webpack build time with light values
// (e.g. @text-color_1 → #1d2129), which become invisible on dark backgrounds.
// These overrides remap them to their dark equivalents.
const VAR_COLOR_MAP = {
  '@text-color': '#f0f0f3',
  '@text-color_1': '#f0f0f3',
  '@text-color_2': '#9999a6',
  '@text-color_3': '#8f959e',
  '@text-color_4': '#555562',
  '@text-color_5': '#2e2e38',
  '@text-color_6': '#282830',
  '@heading-color': '#f0f0f3',
  '@text-color-secondary': '#9999a6',
  '@disabled-color': '#555562',
}

// Less variable names used for background-color → dark mode hex values.
// Scoped styles use @primary-color_5/6/7 for hover/selected/active backgrounds.
const VAR_BG_MAP = {
  '@primary-color_3': '#262442',
  '@primary-color_4': '#2a2748',
  '@primary-color_5': '#282544',
  '@primary-color_6': '#2e2a4b',
  '@primary-color_7': '#2c2c31',
}

// When @primary-color is used as text color inside an active/selected parent,
// the dark purple (#6c5ce7) has poor contrast on dark selected backgrounds.
// Remap to the lighter accent (#a29bfe) matching sidebar menu selected text.
const PRIMARY_IN_ACTIVE = '#a29bfe'
const ACTIVE_SEL_RE = /(^|[_-])active|\.active|(^|[_-])selected|\.selected|&\.selected|^selected$/i

function isActiveContext (stack) {
  for (const sel of stack) {
    if (ACTIVE_SEL_RE.test(sel)) return true
  }
  return false
}

function mapBgColor (hex) {
  if (COLOR_MAP[hex]) return COLOR_MAP[hex]
  if (hex.length === 9) return '#1e1e24' // rgba light color → dark surface
  return '#1e1e24'
}

function mapTextColor (hex) {
  if (TEXT_COLOR_MAP[hex]) return TEXT_COLOR_MAP[hex]
  // For 6-digit hex: if brightness < 0x55 → primary text, < 0x99 → secondary
  if (hex.length === 6 || hex.length === 7) {
    const val = parseInt(hex.slice(-6), 16)
    const r = (val >> 16) & 0xff
    const g = (val >> 8) & 0xff
    const b = val & 0xff
    const avg = (r + g + b) / 3
    if (avg < 0x55) return '#f0f0f3'
    if (avg < 0x99) return '#9999a6'
    if (avg < 0xaa) return '#8f959e'
  }
  return null // too bright to remap — likely a colored icon/badge, leave alone
}

/**
 * Parse a style block and extract background-color + color overrides.
 * Returns { bg: [...], text: [...] }
 */
function extract (file) {
  const s = fs.readFileSync(file, 'utf8')
  const isLess = file.endsWith('.less')
  const blocks = isLess ? [s] : (s.match(/<style[^>]*>([\s\S]*?)<\/style>/g) || [])
  if (!blocks.length) return { bg: [], text: [] }
  const bgOut = []
  const textOut = []
  for (const block of blocks) {
    const lines = block.replace(/^<style[^>]*>\s*/, '').split('\n')
    const stack = []
    for (const line of lines) {
      const t = line.trim()
      if (!t || t.startsWith('//') || t.startsWith('/*')) continue
      if (t.endsWith('{')) {
        let sel = t.slice(0, -1).trim()
        const p = stack[stack.length - 1] || ''
        if (p) sel = sel.includes('&') ? sel.replace(/&/g, p) : p + ' ' + sel
        stack.push(sel.split(',').pop().trim())
      } else if (t === '}') {
        stack.pop()
      } else {
        const bgM = t.match(/background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,8})/)
        if (bgM) {
          const hex = bgM[1].toLowerCase()
          const full = hex.length === 4 ? `#${hex[1]}${hex[1]}${hex[2]}${hex[2]}${hex[3]}${hex[3]}` : hex
          if (parseInt(full.slice(1, 7), 16) >= 0xe0e0e0) {
            bgOut.push({ sel: stack[stack.length - 1] || '', color: full, prop: 'background-color' })
          }
        }
        // Also catch background-color: @variable (Less vars resolve to light values in scoped styles)
        const varBgM = t.match(/background(?:-color)?\s*:\s*(@[\w-]+)/)
        if (varBgM) {
          const varName = varBgM[1]
          const mapped = VAR_BG_MAP[varName]
          if (mapped) {
            bgOut.push({ sel: stack[stack.length - 1] || '', color: varName, mapped, prop: 'background-color' })
          }
        }
        // Also extract color: properties with dark values (brightness < 0xaa)
        const colorM = t.match(/(?<!\w)color\s*:\s*(#[0-9a-fA-F]{3,8})/)
        if (colorM) {
          const hex = colorM[1].toLowerCase()
          const full = hex.length === 4 ? `#${hex[1]}${hex[1]}${hex[2]}${hex[2]}${hex[3]}${hex[3]}` : hex
          const mapped = mapTextColor(full)
          if (mapped) {
            textOut.push({ sel: stack[stack.length - 1] || '', color: full, mapped, prop: 'color' })
          }
        }
        // Also extract color: @variable (Less variables resolve to light values in scoped styles)
        const varColorM = t.match(/(?<!\w)color\s*:\s*(@[\w-]+)/)
        if (varColorM) {
          const varName = varColorM[1]
          let mapped = VAR_COLOR_MAP[varName]
          // @primary-color in active/selected contexts → lighter accent for readability
          if (!mapped && varName === '@primary-color' && isActiveContext(stack)) {
            mapped = PRIMARY_IN_ACTIVE
          }
          if (mapped) {
            textOut.push({ sel: stack[stack.length - 1] || '', color: varName, mapped, prop: 'color' })
          }
        }
      }
    }
  }
  return { bg: bgOut, text: textOut }
}

function walk (d, files = []) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name)
    if (e.isDirectory()) walk(p, files)
    else if (/\.(vue|less)$/.test(e.name)) files.push(p)
  }
  return files
}

const scanDirs = [
  'src/modules/cmdb/views',
  'src/modules/acl/views',
  'src/modules/cmdb/components',
  'src/modules/acl/components',
  'src/components',
  'src/views',
]
const files = scanDirs
  .filter((d) => fs.existsSync(path.join(CWD, d)))
  .flatMap((d) => walk(path.join(CWD, d)))
const seen = new Set()
const groups = []

for (const f of files) {
  const { bg, text } = extract(f)
  if (!bg.length && !text.length) continue
  const rel = path.relative(CWD, f)
  const rules = []
  for (const h of bg) {
    if (!h.sel || /:global|^\s*&-|@/.test(h.sel)) continue
    const isDeep = /\/deep\/|>>>|::v-deep/.test(h.sel)
    const sel = h.sel.replace(/\/deep\/|>>>|::v-deep/g, ' ').replace(/\s+/g, ' ').trim()
    if (!sel) continue
    const key = sel + '|bg|' + h.color
    if (seen.has(key)) continue
    seen.add(key)
    const bgVal = h.mapped || mapBgColor(h.color)
    rules.push(`  ${sel} { background-color: ${bgVal}${isDeep ? ' !important' : ''}; }`)
  }
  for (const h of text) {
    if (!h.sel || /:global|^\s*&-|@/.test(h.sel)) continue
    const isDeep = /\/deep\/|>>>|::v-deep/.test(h.sel)
    const sel = h.sel.replace(/\/deep\/|>>>|::v-deep/g, ' ').replace(/\s+/g, ' ').trim()
    if (!sel) continue
    const key = sel + '|color|' + h.color
    if (seen.has(key)) continue
    seen.add(key)
    rules.push(`  ${sel} { color: ${h.mapped}${isDeep ? ' !important' : ''}; }`)
  }
  if (rules.length) groups.push(`\n/* ${rel} */\n${rules.join('\n')}`)
}

const out = `/**
 * Business module scoped light-background and dark-text overrides (auto-generated),
 * forming the dark theme base layer.
 * Scoped under html[data-theme='dark'] to beat scoped [data-v] specificity.
 * Regenerate: node scripts/gen-base-business.js
 */
html[data-theme='dark'] {
${groups.join('\n')}
}
`
fs.writeFileSync(OUT, out)
console.log('generated', seen.size, 'rules ->', path.relative(CWD, OUT))
