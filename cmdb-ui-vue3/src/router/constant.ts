// src/router/constant.ts
import type { AppRouteRecord } from '@/stores/routeFilter'

export const constantRouterMap: AppRouteRecord[] = [
  { path: '/', redirect: '/home' },
  {
    path: '/user/login',
    name: 'login',
    component: () => import('@/views/user/Login.vue'),
    meta: { hidden: true },
  },
  {
    path: '/user/logout',
    name: 'logout',
    component: () => import('@/views/user/Logout.vue'),
    meta: { hidden: true },
  },
  {
    path: '/home',
    name: 'home',
    component: () => import('@/layouts/BasicLayout.vue'),
    children: [
      {
        path: '',
        name: 'home_index',
        component: () => import('@/views/home/index.vue'),
        meta: { title: 'Home' },
      },
    ],
  },
  {
    path: '/404',
    name: 'not_found',
    component: () => import('@/views/exception/404.vue'),
    meta: { hidden: true },
  },
  { path: '/:pathMatch(.*)*', redirect: '/404', meta: { hidden: true } },
]
