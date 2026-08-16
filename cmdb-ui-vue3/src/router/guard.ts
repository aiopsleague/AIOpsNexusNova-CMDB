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
    const routesStore = useRoutesStore()
    const token = localStorage.getItem(TOKEN_KEY)

    if (whiteList.includes(to.path)) {
      return next()
    }

    if (!token) {
      return next({ path: '/user/login', query: { redirect: to.fullPath } })
    }

    // 重新水合用户信息（uid 已持久化时跳过，避免每次刷新重复拉取）
    if (!userStore.uid) {
      try {
        await userStore.getInfo()
      } catch {
        await userStore.logout()
        return next({ path: '/user/login', query: { redirect: to.fullPath } })
      }
      // 非关键：鉴权方式列表，失败不阻断登录态
      userStore.fetchAuthDataEnable().catch(() => {})
    }

    // 动态路由尚未生成时构建并注册（刷新后 appRoutes 为空，会重新生成）
    if (routesStore.appRoutes.length === 0) {
      try {
        const permissions = userStore.roles.permissions?.map((p) => p.name) ?? []
        const dynamic = await routesStore.generateRoutes(permissions)
        dynamic.forEach((r) => router.addRoute(r as never))
        return next({ ...to, replace: true })
      } catch {
        // 模块路由构建失败不阻断导航
      }
    }

    next()
  })

  router.afterEach(() => NProgress.done())
}
