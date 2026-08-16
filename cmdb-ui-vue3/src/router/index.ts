// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { constantRouterMap } from './constant'

function createAppRouter() {
  return createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    scrollBehavior: () => ({ top: 0 }),
    routes: constantRouterMap as never,
  })
}

export const router = createAppRouter()

export function resetRouter() {
  const fresh = createAppRouter()
  router.options.routes = fresh.options.routes
}
