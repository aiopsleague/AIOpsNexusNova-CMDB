/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent
  export default component
}

// vue3-treeselect ships no TypeScript types.
declare module 'vue3-treeselect' {
  import type { DefineComponent } from 'vue'
  const Treeselect: DefineComponent
  export default Treeselect
  export { Treeselect }
}

// @wangeditor/editor-for-vue publishes types but its package.json "exports"
// map does not expose them, so TS cannot resolve them via module resolution.
declare module '@wangeditor/editor-for-vue' {
  import type { DefineComponent } from 'vue'
  export const Editor: DefineComponent
  export const Toolbar: DefineComponent
}
