// src/modules/index.ts
import type { Router } from 'vue-router'
import type { I18n } from 'vue-i18n'

export interface ModuleManifest {
  name: string
  routes: unknown[]
  locales?: Record<string, unknown>
}

/**
 * 加载业务模块清单并装配路由与 i18n。
 * shell 阶段清单为空；acl/cmdb 迁移时在此追加注册。
 */
export async function loadModules(_router: Router, _i18n: I18n) {
  // TODO(acl): register module manifests here
}
