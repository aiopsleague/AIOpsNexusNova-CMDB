/**
 * Build theme css files.
 * Compile src/style/themes/{name}.less → public/themes/{name}.css using less
 * directly.
 *
 * Usage:
 *   node scripts/build-theme.js                  # builds all themes
 *   node scripts/build-theme.js liquid-glass     # builds liquid-glass.css only
 *
 * ant-design-vue 1.x has no built-in dark theme, so we compile each separately.
 */
const fs = require('fs')
const path = require('path')
const less = require('less')

const projectRoot = path.resolve(__dirname, '..')
const themesDir = path.join(projectRoot, 'src/style/themes')

// All known theme entry files
const ALL_THEMES = ['liquid-glass']

function buildTargets() {
  const arg = process.argv[2]
  if (arg) {
    // Single theme mode
    if (!ALL_THEMES.includes(arg)) {
      console.error(`[build-theme] Unknown theme: "${arg}". Known: ${ALL_THEMES.join(', ')}`)
      process.exit(1)
    }
    return [arg]
  }
  // Build all themes
  return ALL_THEMES
}

async function compileTheme(name) {
  const entryFile = path.join(themesDir, `${name}.less`)
  const outputFile = path.join(projectRoot, 'public', 'themes', `${name}.css`)

  if (!fs.existsSync(entryFile)) {
    console.error(`[build-theme] Entry file not found: ${entryFile}`)
    return false
  }

  let source = fs.readFileSync(entryFile, 'utf8')

  // Inline ../global.less so project styles are compiled with theme variables.
  // Bare less does not understand webpack's `~` alias, and its relative import
  // './static.less' would otherwise resolve from the wrong directory.
  source = source.replace(/@import\s+['"]\.\.\/global\.less['"];\s*/, () => {
    let globalLess = fs.readFileSync(path.join(projectRoot, 'src/style/global.less'), 'utf8')
    // antd full less is already imported by the theme entry via bare module path
    globalLess = globalLess.replace(/@import\s+['"]~ant-design-vue\/dist\/antd\.less['"];\s*/g, '')
    // inline static.less (variables + mixins) so it resolves correctly
    const staticLess = fs.readFileSync(path.join(projectRoot, 'src/style/static.less'), 'utf8')
    return globalLess.replace(/@import\s+['"]\.\/static\.less['"];\s*/g, () => staticLess + '\n')
  })

  const result = await less.render(source, {
    filename: entryFile,
    paths: [path.join(projectRoot, 'node_modules')],
    javascriptEnabled: true,
    compress: true
  })
  fs.mkdirSync(path.dirname(outputFile), { recursive: true })
  fs.writeFileSync(outputFile, result.css)
  console.log(`[build-theme] ${path.relative(projectRoot, outputFile)} generated (${(result.css.length / 1024).toFixed(1)} KB)`)
  return true
}

async function main() {
  const targets = buildTargets()
  let ok = 0
  for (const name of targets) {
    const success = await compileTheme(name)
    if (success) ok++
  }
  if (ok < targets.length) {
    process.exit(1)
  }
}

main().catch(err => {
  console.error('[build-theme] failed:', err)
  process.exit(1)
})
