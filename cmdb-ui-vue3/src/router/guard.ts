// src/router/guard.ts
import type { Router } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { useUserStore } from '@/stores/user'
import { useRoutesStore } from '@/stores/routes'
import { TOKEN_KEY } from '@/utils/request'
import { setDocumentTitle } from '@/utils/dom'

NProgress.configure({ showSpinner: false })

const whiteList = ['/user/login', '/user/logout', '/user/register']

export function setupRouterGuard(router: Router) {
  router.beforeEach(async (to, _from, next) => {
    NProgress.start()
    if (to.meta?.title) {
      setDocumentTitle(to.meta.title as string)
    }

    const userStore = useUserStore()
    const token = localStorage.getItem(TOKEN_KEY)

    if (whiteList.includes(to.path)) {
      return next()
    }

    if (token && !userStore.uid) {
      try {
        await userStore.getInfo()
      } catch {
        await userStore.logout()
        return next({ path: '/user/login', query: { redirect: to.fullPath } })
      }
      // 非关键：鉴权方式列表，失败不阻断登录态
      userStore.fetchAuthDataEnable().catch(() => {})
      try {
        const permissions = userStore.roles.permissions?.map((p) => p.name) ?? []
        const dynamic = await useRoutesStore().generateRoutes(permissions)
        dynamic.forEach((r) => router.addRoute(r as never))
      } catch {
        // 模块路由构建失败不阻断导航
      }
      return next({ ...to, replace: true })
    }

    if (!token) {
      return next({ path: '/user/login', query: { redirect: to.fullPath } })
    }

    next()
  })

  router.afterEach(() => NProgress.done())
}
