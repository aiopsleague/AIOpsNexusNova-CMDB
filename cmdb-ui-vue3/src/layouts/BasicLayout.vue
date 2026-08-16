<script setup lang="ts">
import { h, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Layout, Menu, Dropdown, Avatar } from 'ant-design-vue'
import { LogoutOutlined, UserOutlined } from '@ant-design/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { useRoutesStore } from '@/stores/routes'

const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()
const routesStore = useRoutesStore()

const menuItems = computed(() =>
  routesStore.appRoutes
    .filter((r) => r.children && r.children.length)
    .map((r) => ({
      key: r.path,
      label: (r.meta?.title as string) || r.name,
      children: (r.children || [])
        .filter((c) => !c.meta?.hidden)
        .map((c) => ({ key: c.path, label: (c.meta?.title as string) || c.name })),
    }))
)

const themeLabel = computed(() => {
  if (appStore.themeMode === 'system') return 'System'
  return appStore.themeMode === 'dark' ? 'Dark' : 'Light'
})

function onMenuClick({ key }: { key: string }) {
  router.push(key)
}

function cycleTheme() {
  const order = ['light', 'dark', 'system'] as const
  const idx = order.indexOf(appStore.themeMode)
  appStore.setThemeMode(order[(idx + 1) % order.length])
}

function onLogout() {
  router.push('/user/logout')
}
</script>

<template>
  <Layout class="basic-layout">
    <Layout.Sider :theme="appStore.themeMode === 'dark' ? 'dark' : 'light'" width="220">
      <div class="logo">CMDB</div>
      <Menu
        theme="dark"
        mode="inline"
        :selected-keys="[router.currentRoute.value.path]"
        :items="menuItems"
        @click="onMenuClick"
      />
    </Layout.Sider>
    <Layout>
      <Layout.Header class="header">
        <button class="theme-toggle" @click="cycleTheme">{{ themeLabel }}</button>
        <Dropdown>
          <span class="user">
            <Avatar size="small" :icon="h(UserOutlined)" />
            <span class="name">{{ userStore.name || userStore.username }}</span>
          </span>
          <template #overlay>
            <Menu @click="onLogout">
              <Menu.Item key="logout">
                <LogoutOutlined /> Logout
              </Menu.Item>
            </Menu>
          </template>
        </Dropdown>
      </Layout.Header>
      <Layout.Content class="content">
        <router-view />
      </Layout.Content>
    </Layout>
  </Layout>
</template>

<style scoped>
.basic-layout {
  min-height: 100vh;
}
.logo {
  height: 32px;
  margin: 16px;
  color: #fff;
  font-weight: 600;
  text-align: center;
  line-height: 32px;
}
.header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  background: #fff;
  padding: 0 16px;
}
.theme-toggle {
  cursor: pointer;
}
.user {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.content {
  padding: 16px;
}
</style>
