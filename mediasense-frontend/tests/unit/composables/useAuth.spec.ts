import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { useAuthStore } from '@/stores/auth'
import { useAuth } from '@/composables/useAuth'
import { setActivePinia } from 'pinia'
import { ref } from 'vue'

describe('useAuth', () => {
  let store: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        auth: {
          user: null,
          token: null,
          loading: false,
          error: null
        }
      }
    })
    setActivePinia(pinia)
    store = useAuthStore()

    // 模拟 store 方法
    store.login = vi.fn().mockResolvedValue({ token: 'test-token', user: { id: 1, username: 'test' } })
    store.register = vi.fn().mockResolvedValue({ token: 'test-token', user: { id: 1, username: 'test' } })
    store.logout = vi.fn()
    store.fetchUserInfo = vi.fn().mockResolvedValue(true)
  })

  it('应该提供默认状态', () => {
    const { user, token, loading, error } = useAuth()
    expect(user.value).toBeNull()
    expect(token.value).toBeNull()
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('应该能够登录', async () => {
    const { login, user, token, loading, error } = useAuth()
    const credentials = { username: 'test', password: 'password' }
    
    await login(credentials)
    
    expect(store.login).toHaveBeenCalledWith(credentials.username, credentials.password)
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('应该能够注册', async () => {
    const { register, user, token, loading, error } = useAuth()
    const userData = { username: 'test', password: 'password', email: 'test@example.com' }
    
    await register(userData)
    
    expect(store.register).toHaveBeenCalledWith(userData.username, userData.password, userData.email)
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('应该能够登出', async () => {
    const { logout, user, token } = useAuth()
    await logout()
    
    expect(store.logout).toHaveBeenCalled()
  })

  it('应该能够检查认证状态', async () => {
    const { checkAuth, loading, error } = useAuth()
    const result = await checkAuth()
    
    expect(store.fetchUserInfo).toHaveBeenCalled()
    expect(result).toBe(true)
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('应该正确处理错误', async () => {
    const error = new Error('登录失败')
    store.login.mockRejectedValueOnce(error)
    
    const { login, loading, error: errorState } = useAuth()
    await login({ username: 'test', password: 'wrong' }).catch(() => {})
    
    expect(loading.value).toBe(false)
    expect(errorState.value).toBe('登录失败')
  })
})
