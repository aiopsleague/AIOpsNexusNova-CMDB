// src/modules/acl/store.ts
import { defineStore } from 'pinia'

export const useAclStore = defineStore('acl', {
  state: () => ({
    currentApp: 'acl',
  }),
  actions: {
    setCurrentApp(app: string) {
      this.currentApp = app
    },
  },
})
