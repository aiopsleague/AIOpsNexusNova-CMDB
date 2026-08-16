// src/__tests__/userStore.spec.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'
import { TOKEN_KEY } from '@/utils/request'

vi.mock('@/api/login', () => ({
  login: vi.fn(async () => ({ token: 'tok-1' })),
  getInfo: vi.fn(async () => ({ result: { name: 'Alice', uid: 1, rid: 1, username: 'alice', role: {} } })),
  logout: vi.fn(async () => undefined),
  getAllUsers: vi.fn(async () => ({ users: [] })),
}))

describe('useUserStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('login stores token to state and localStorage', async () => {
    const store = useUserStore()
    await store.login({ username: 'alice', password: 'x' })
    expect(store.token).toBe('tok-1')
    expect(localStorage.getItem(TOKEN_KEY)).toBe('tok-1')
  })

  it('logout clears token', async () => {
    const store = useUserStore()
    await store.login({ username: 'alice', password: 'x' })
    await store.logout()
    expect(store.token).toBe('')
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
  })
})
