/**
 * Build dark theme css.
 * Compile src/style/themes/dark.less -> public/themes/dark.css using less directly.
 * ant-design-vue 1.x has no built-in dark theme, so we compile it separately
 * (see docs/superpowers/specs/2026-08-12-theme-settings-design.md).
 */
const fs = require('fs')
const path = require('path')
const less = require('less')

const projectRoot = path.resolve(__dirname, '..')
const entryFile = path.join(projectRoot, 'src/style/themes/dark.less')
const outputFile = path.join(projectRoot, 'public/themes/dark.css')

async function main() {
  let source = fs.readFileSync(entryFile, 'utf8')

  // Inline ../global.less so project styles are compiled with dark variables.
  // Bare less does not understand webpack's `~` alias, and its relative import
  // './static.less' would otherwise resolve from the wrong directory.
  source = source.replace(/@import\s+['"]\.\.\/global\.less['"];\s*/, () => {
    let globalLess = fs.readFileSync(path.join(projectRoot, 'src/style/global.less'), 'utf8')
    // antd full less is already imported by dark.less via bare module path
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
}

main().catch(err => {
  console.error('[build-theme] failed:', err)
  process.exit(1)
})
