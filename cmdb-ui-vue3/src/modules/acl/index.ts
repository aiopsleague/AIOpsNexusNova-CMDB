// src/modules/acl/index.ts
import { genAclRoutes } from './router'
import zh from './lang/zh'
import en from './lang/en'

export const aclManifest = {
  name: 'acl',
  routes: genAclRoutes,
  locales: { zh, en },
}

export default aclManifest
