// src/config/app.ts
export interface AppConfig {
  /** 需要编译/加载的业务模块（shell 阶段为空，后续加 'acl'）。 */
  buildModules: string[]
  /** 首页重定向路径。 */
  redirectTo: string
}

const appConfig: AppConfig = {
  buildModules: [],
  redirectTo: '/home',
}

export default appConfig
