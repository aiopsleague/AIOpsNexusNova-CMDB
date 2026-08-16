// src/modules/cmdb/store.ts
import { defineStore } from 'pinia'

export const useCmdbStore = defineStore('cmdb', {
  state: () => ({
    isTableLoading: false,
  }),
  actions: {
    setIsTableLoading(payload: boolean) {
      this.isTableLoading = payload
    },
  },
})
