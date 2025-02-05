import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import * as authApi from '@/api/auth'
import { ElMessage } from 'element-plus'

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  getUserInfo: vi.fn()
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const store = useAuthStore()
      expect(store.token).toBe('')
      expect(store.user).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.isAuthenticated).toBe(false)
      expect(store.isAdmin).toBe(false)
    })

    it('应该从 localStorage 加载 token', () => {
      const mockToken = 'test-token'
      localStorage.setItem('token', mockToken)
      const store = useAuthStore()
      expect(store.token).toBe(mockToken)
    })
  })

  describe('登录功能', () => {
    it('应该成功登录并更新状态', async () => {
      const mockResponse = {
        token: 'test-token',
        user: { id: 1, username: 'test', role: 'user' }
      }
      vi.mocked(authApi.login).mockResolvedValue(mockResponse)

      const store = useAuthStore()
      await store.login('test', 'password')

      expect(store.token).toBe(mockResponse.token)
      expect(store.user).toEqual(mockResponse.user)
      expect(store.loading).toBe(false)
      expect(store.isAuthenticated).toBe(true)
      expect(localStorage.getItem('token')).toBe(mockResponse.token)
      expect(ElMessage.success).toHaveBeenCalledWith('登录成功')
    })

    it('应该处理登录失败', async () => {
      const error = new Error('登录失败')
      vi.mocked(authApi.login).mockRejectedValue(error)

      const store = useAuthStore()
      await expect(store.login('test', 'wrong-password')).rejects.toThrow()

      expect(store.token).toBe('')
      expect(store.user).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.isAuthenticated).toBe(false)
      expect(ElMessage.error).toHaveBeenCalledWith('登录失败')
    })
  })

  describe('注册功能', () => {
    it('应该成功注册并更新状态', async () => {
      const mockResponse = {
        token: 'test-token',
        user: { id: 1, username: 'test', role: 'user' }
      }
      vi.mocked(authApi.register).mockResolvedValue(mockResponse)

      const store = useAuthStore()
      await store.register('test', 'password', 'test@example.com')

      expect(store.token).toBe(mockResponse.token)
      expect(store.user).toEqual(mockResponse.user)
      expect(store.loading).toBe(false)
      expect(store.isAuthenticated).toBe(true)
      expect(localStorage.getItem('token')).toBe(mockResponse.token)
      expect(ElMessage.success).toHaveBeenCalledWith('注册成功')
    })

    it('应该处理注册失败', async () => {
      const error = new Error('注册失败')
      vi.mocked(authApi.register).mockRejectedValue(error)

      const store = useAuthStore()
      await expect(store.register('test', 'password', 'invalid-email')).rejects.toThrow()

      expect(store.token).toBe('')
      expect(store.user).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.isAuthenticated).toBe(false)
      expect(ElMessage.error).toHaveBeenCalledWith('注册失败')
    })
  })

  describe('登出功能', () => {
    it('应该成功登出并清除状态', async () => {
      vi.mocked(authApi.logout).mockResolvedValue(undefined)

      const store = useAuthStore()
      store.token = 'test-token'
      store.user = { id: 1, username: 'test', role: 'user' }
      localStorage.setItem('token', 'test-token')

      await store.logout()

      expect(store.token).toBe('')
      expect(store.user).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.isAuthenticated).toBe(false)
      expect(localStorage.getItem('token')).toBeNull()
      expect(ElMessage.success).toHaveBeenCalledWith('已退出登录')
    })

    it('应该处理登出失败', async () => {
      const error = new Error('登出失败')
      vi.mocked(authApi.logout).mockRejectedValue(error)

      const store = useAuthStore()
      await expect(store.logout()).rejects.toThrow()

      expect(store.loading).toBe(false)
      expect(ElMessage.error).toHaveBeenCalledWith('退出登录失败')
    })
  })

  describe('获取用户信息', () => {
    it('应该成功获取用户信息', async () => {
      const mockUser = { id: 1, username: 'test', role: 'admin' }
      vi.mocked(authApi.getUserInfo).mockResolvedValue(mockUser)

      const store = useAuthStore()
      await store.fetchUserInfo()

      expect(store.user).toEqual(mockUser)
      expect(store.loading).toBe(false)
      expect(store.isAdmin).toBe(true)
    })

    it('应该在获取用户信息失败时清除状态', async () => {
      const error = new Error('获取用户信息失败')
      vi.mocked(authApi.getUserInfo).mockRejectedValue(error)

      const store = useAuthStore()
      store.token = 'test-token'
      store.user = { id: 1, username: 'test', role: 'user' }
      localStorage.setItem('token', 'test-token')

      await expect(store.fetchUserInfo()).rejects.toThrow()

      expect(store.token).toBe('')
      expect(store.user).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.isAuthenticated).toBe(false)
      expect(localStorage.getItem('token')).toBeNull()
    })
  })
}) 