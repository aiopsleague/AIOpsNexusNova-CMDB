// src/modules/cmdb/index.ts
import { buildCmdbRoutes } from './router'
import zh from './lang/zh'
import en from './lang/en'

export const cmdbManifest = {
  name: 'cmdb',
  routes: () => Promise.resolve(buildCmdbRoutes()),
  locales: { zh, en },
}

export default cmdbManifest
