// src/stores/routes.ts
import { defineStore } from 'pinia'
import { filterAsyncRoutes, type AppRouteRecord } from './routeFilter'
import { loadModuleRoutes, resolveRouteComponents } from '@/modules'

interface RoutesState {
  appRoutes: AppRouteRecord[]
}

export const useRoutesStore = defineStore('routes', {
  state: (): RoutesState => ({
    appRoutes: [],
  }),
  actions: {
    async generateRoutes(permissions: string[]) {
      const moduleRoutes = resolveRouteComponents(await loadModuleRoutes()) as AppRouteRecord[]
      this.appRoutes = filterAsyncRoutes(moduleRoutes, permissions)
      return this.appRoutes
    },
    reset() {
      this.appRoutes = []
    },
  },
})
