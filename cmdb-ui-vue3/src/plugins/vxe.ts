// src/plugins/vxe.ts
import type { App } from 'vue'
import VxeUI from 'vxe-pc-ui'
import 'vxe-pc-ui/lib/style.css'
import VXETable from 'vxe-table'
import 'vxe-table/lib/style.css'

/**
 * Register vxe-table 4 (vxe-pc-ui base library + vxe-table components).
 * v4 splits the UI into `vxe-pc-ui` (VxeUI) and `vxe-table` (VXETable);
 * both expose an `install` method so they are registered via `app.use`.
 */
export function setupVxe(app: App) {
  app.use(VxeUI)
  app.use(VXETable)
}
