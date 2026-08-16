// src/__tests__/app.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { createRouter, createMemoryHistory } from 'vue-router'
import App from '@/App.vue'

describe('App', () => {
  it('mounts without error', () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [] })
    const i18n = createI18n({ legacy: false, messages: { zh: {}, en: {} } })
    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), router, i18n],
      },
    })
    expect(wrapper.exists()).toBe(true)
  })
})
