// src/router/guard.ts
import type { Router } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { useUserStore } from '@/stores/user'
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
        await userStore.fetchAuthDataEnable()
        // TODO(acl): register module routes via routesStore.generateRoutes + router.addRoute
        return next({ ...to, replace: true })
      } catch {
        await userStore.logout()
        return next({ path: '/user/login', query: { redirect: to.fullPath } })
      }
    }

    if (!token) {
      return next({ path: '/user/login', query: { redirect: to.fullPath } })
    }

    next()
  })

  router.afterEach(() => NProgress.done())
}
