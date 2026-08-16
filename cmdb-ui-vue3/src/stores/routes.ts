// src/stores/routes.ts
import { defineStore } from 'pinia'
import { filterAsyncRoutes, type AppRouteRecord } from './routeFilter'
import { loadModuleRoutes, resolveRouteComponents } from '@/modules'

interface RoutesState {
  appRoutes: AppRouteRecord[]
  /** 已通过 router.addRoute 注册的顶层路由名，登出时用于 removeRoute 清理。 */
  addedRouteNames: string[]
}

export const useRoutesStore = defineStore('routes', {
  state: (): RoutesState => ({
    appRoutes: [],
    addedRouteNames: [],
  }),
  actions: {
    async generateRoutes(permissions: string[]) {
      const moduleRoutes = resolveRouteComponents(await loadModuleRoutes()) as AppRouteRecord[]
      this.appRoutes = filterAsyncRoutes(moduleRoutes, permissions)
      this.addedRouteNames = this.appRoutes
        .map((r) => r.name)
        .filter((n): n is string => !!n)
      return this.appRoutes
    },
    reset() {
      this.appRoutes = []
      this.addedRouteNames = []
    },
  },
})
