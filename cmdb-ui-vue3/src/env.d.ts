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
