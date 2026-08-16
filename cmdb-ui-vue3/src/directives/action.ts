// src/directives/action.ts
import type { App, Directive } from 'vue'
import pinia from '@/stores'
import { useUserStore } from '@/stores/user'

function hasAction(value: unknown): boolean {
  if (value === undefined || value === null || value === '') return true
  const userStore = useUserStore(pinia)
  const permissions = userStore.roles.permissions?.map((p) => p.name) ?? []
  const required = Array.isArray(value) ? value : [value]
  return required.some((p) => permissions.includes(String(p)))
}

const actionDirective: Directive = {
  mounted(el, binding) {
    if (!hasAction(binding.value)) {
      el.parentNode?.removeChild(el)
    }
  },
}

export function setupActionDirective(app: App) {
  app.directive('action', actionDirective)
}
