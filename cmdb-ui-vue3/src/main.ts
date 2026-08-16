// src/main.ts
import { createApp } from 'vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import App from './App.vue'
import pinia from '@/stores'
import { router } from '@/router'
import i18n from '@/lang'
import { setupRouterGuard } from '@/router/guard'
import { setupActionDirective } from '@/directives/action'
import { initThemeSystem } from '@/theme/system'
import { setupVxe } from '@/plugins/vxe'
import { setupTreeselect } from '@/plugins/treeselect'
import { loadModules } from '@/modules'

async function bootstrap() {
  const app = createApp(App)

  app.use(pinia)
  app.use(router)
  app.use(i18n)
  app.use(Antd)

  setupVxe(app)
  setupTreeselect(app)

  setupActionDirective(app)

  initThemeSystem()

  await loadModules(router, i18n)
  setupRouterGuard(router)

  app.mount('#app')
}

bootstrap()
