/**
 * Generate dark overrides for cmdb/acl business module scoped light backgrounds.
 * Scans src/modules/{cmdb,acl}/views/*.vue scoped styles, expands less nesting,
 * maps common light colors to the dark palette, and writes
 * src/style/themes/dark-business.less (consumed by dark.less).
 * Usage: node scripts/gen-dark-business.js
 */
const fs = require('fs')
const path = require('path')

const CWD = path.resolve(__dirname, '..')
const OUT = path.join(CWD, 'src/style/themes/dark-business.less')

const COLOR_MAP = {
  '#ffffff': '#1f1f1f',
  '#f7f8fa': '#1f1f1f',
  '#fafafa': '#1f1f1f',
  '#f9fbff': '#14181f',
  '#f5f5f5': '#262626',
  '#f5f7fa': '#262626',
  '#f0f0f0': '#262626',
  '#f0f2f5': '#141414',
  '#f0f1f5': '#1f1f1f',
  '#ebeff8': '#1a1f2e',
  '#f0f5ff': '#171e2e',
  '#f4f9ff': '#1a1f2e',
  '#e8eaed': '#303030',
  '#e4e7ed': '#303030',
  '#e9e9e9': '#303030',
  '#e1efff': '#1f2738',
  '#eeeeee': '#262626',
  '#f6f6f6': '#262626',
  '#f2f3f5': '#262626',
  '#f5f8fe': '#1a1f2e',
  '#e5e7eb': '#303030',
  '#f8f9fd': '#1f1f1f',
  '#f2f6fc': '#1a1f2e',
  '#fff1f0': '#2a1215',
  '#e6f7ff': '#111d2c',
  '#f0f7ff': '#1a1f2e',
  '#eff3fa': '#1f1f1f',
}

function mapColor (hex) {
  if (COLOR_MAP[hex]) return COLOR_MAP[hex]
  if (hex.length === 9) return '#1f1f1f' // rgba 浅色：直接暗色化（丢弃 alpha 近似）
  return '#1f1f1f'
}

function extract (file) {
  const s = fs.readFileSync(file, 'utf8')
  const isLess = file.endsWith('.less')
  // Scan ALL style blocks. Non-scoped pages (e.g. tree_views uses plain
  // <style lang="less">) keep light backgrounds there; a scoped-only scan
  // silently misses them and leaves those containers bright in dark mode.
  // Standalone .less files (component-imported) are parsed as-is.
  const blocks = isLess ? [s] : (s.match(/<style[^>]*>([\s\S]*?)<\/style>/g) || [])
  if (!blocks.length) return []
  const out = []
  for (const block of blocks) {
    const lines = block.replace(/^<style[^>]*>\s*/, '').split('\n')
    const stack = []
    for (const line of lines) {
    const t = line.trim()
    if (!t || t.startsWith('//') || t.startsWith('/*')) continue
    if (t.endsWith('{')) {
      let sel = t.slice(0, -1).trim()
      // 仍 push 以保持嵌套栈平衡（/deep/ 规则在生成时过滤）
      const p = stack[stack.length - 1] || ''
      if (p) sel = sel.includes('&') ? sel.replace(/\&/g, p) : p + ' ' + sel
      stack.push(sel.split(',').pop().trim())
    } else if (t === '}') {
      stack.pop()
    } else {
      const m = t.match(/background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,8})/)
      if (m) {
        const hex = m[1].toLowerCase()
        // expand 3-digit hex (#fff -> #ffffff) before judging brightness
        const full = hex.length === 4 ? `#${hex[1]}${hex[1]}${hex[2]}${hex[2]}${hex[3]}${hex[3]}` : hex
        if (parseInt(full.slice(1, 7), 16) >= 0xe0e0e0) {
          out.push({ sel: stack[stack.length - 1] || '', color: full })
        }
      }
    }
  }
  }
  return out
}

function walk (d, files = []) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name)
    if (e.isDirectory()) walk(p, files)
    // .vue: <style> blocks; .less: standalone style files that components
    // @import (e.g. ciDetailRelationTopo/index.less) - their light bgs would
    // otherwise be missed
    else if (/\.(vue|less)$/.test(e.name)) files.push(p)
  }
  return files
}

const scanDirs = [
  'src/modules/cmdb/views',
  'src/modules/acl/views',
  'src/modules/cmdb/components',
  'src/modules/acl/components',
]
const files = scanDirs
  .filter((d) => fs.existsSync(path.join(CWD, d)))
  .flatMap((d) => walk(path.join(CWD, d)))
const seen = new Set()
const groups = []

for (const f of files) {
  const hits = extract(f)
  if (!hits.length) continue
  const rel = path.relative(CWD, f)
  const rules = []
  for (const h of hits) {
    if (!h.sel || /:global|^\s*&-/.test(h.sel)) continue
    // /deep/ compiles to [data-v] on the parent (higher specificity), so use
    // !important for those; plain selectors rely on html[data-theme='dark'] prefix
    const isDeep = /\/deep\/|>>>|::v-deep/.test(h.sel)
    const sel = h.sel.replace(/\/deep\/|>>>|::v-deep/g, ' ').replace(/\s+/g, ' ').trim()
    if (!sel) continue
    const key = sel + '|' + h.color
    if (seen.has(key)) continue
    seen.add(key)
    rules.push(`  ${sel} { background-color: ${mapColor(h.color)}${isDeep ? ' !important' : ''}; }`)
  }
  if (rules.length) groups.push(`\n/* ${rel} */\n${rules.join('\n')}`)
}

let out = `/**
 * Business module scoped light-background overrides (auto-generated).
 * Scoped under html[data-theme='dark'] to beat scoped [data-v] specificity.
 * Regenerate: node scripts/gen-dark-business.js
 */
html[data-theme='dark'] {
${groups.join('\n')}
}
`
fs.writeFileSync(OUT, out)
console.log('generated', seen.size, 'rules ->', path.relative(CWD, OUT))
