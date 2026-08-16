// src/stores/routes.ts
import { defineStore } from 'pinia'
import { constantRouterMap } from '@/router/constant'
import { filterAsyncRoutes, type AppRouteRecord } from './routeFilter'

interface RoutesState {
  appRoutes: AppRouteRecord[]
}

export const useRoutesStore = defineStore('routes', {
  state: (): RoutesState => ({
    appRoutes: [],
  }),
  actions: {
    /** 由登录用户的权限动态生成可访问路由。 */
    generateRoutes(permissions: string[]) {
      const dynamic = filterAsyncRoutes([...constantRouterMap], permissions)
      this.appRoutes = dynamic
      return dynamic
    },
    reset() {
      this.appRoutes = []
    },
  },
})
