<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useRoutesStore } from '@/stores/routes'

const router = useRouter()
const userStore = useUserStore()
const routesStore = useRoutesStore()

onMounted(async () => {
  await userStore.logout()
  // 清理动态注册的模块路由，避免下次登录重复 addRoute 或残留旧用户权限路由
  routesStore.addedRouteNames.forEach((name) => {
    if (router.hasRoute(name)) router.removeRoute(name)
  })
  routesStore.reset()
  router.replace('/user/login')
})
</script>

<template>
  <div />
</template>
