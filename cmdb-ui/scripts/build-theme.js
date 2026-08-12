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
  const source = fs.readFileSync(entryFile, 'utf8')
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
