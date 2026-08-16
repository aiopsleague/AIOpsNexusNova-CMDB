// src/__tests__/request.spec.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { extractErrorMessage, getAccessToken, TOKEN_KEY } from '@/utils/request'

describe('getAccessToken', () => {
  beforeEach(() => localStorage.clear())

  it('returns token from localStorage', () => {
    localStorage.setItem(TOKEN_KEY, 'abc123')
    expect(getAccessToken()).toBe('abc123')
  })

  it('returns null when absent', () => {
    expect(getAccessToken()).toBeNull()
  })
})

describe('extractErrorMessage', () => {
  it('prefers server-provided message', () => {
    const err = { response: { data: { message: 'server said no' } } }
    expect(extractErrorMessage(err, 'fallback')).toBe('server said no')
  })

  it('falls back when no message', () => {
    const err = { response: { data: {} } }
    expect(extractErrorMessage(err, 'fallback')).toBe('fallback')
  })
})
