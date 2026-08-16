// src/plugins/treeselect.ts
import type { App } from 'vue'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'

/**
 * Register vue3-treeselect (the Vue 3 port of @riophae/vue-treeselect).
 * The package ships a single component and has no `install` method,
 * so it is registered globally by name.
 */
export function setupTreeselect(app: App) {
  app.component('Treeselect', Treeselect)
}
