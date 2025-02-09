import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { login, register, logout } from '@/api/auth'
import { ElMessage } from 'element-plus'
import { unref } from 'vue'
import * as authApi from '@/api/auth'

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
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const store = useAuthStore()
      expect(unref(store.token)).toBe('')
      expect(unref(store.user)).toBeNull()
      expect(unref(store.loading)).toBe(false)
      expect(unref(store.isAuthenticated)).toBe(false)
      expect(unref(store.isAdmin)).toBe(false)
    })

    it('应该从 localStorage 加载 token', () => {
      const store = useAuthStore()
      const mockToken = 'test-token'
      localStorage.setItem('token', mockToken)
      store.initToken()
      expect(unref(store.token)).toBe(mockToken)
    })
  })

  describe('用户状态管理', () => {
    it('应该正确存储用户信息', async () => {
      const store = useAuthStore()
      const mockUser = {
        id: 1,
        username: 'test',
        email: 'test@example.com'
      }
      const mockResponse = { token: 'mock-token', user: mockUser }
      
      vi.mocked(login).mockResolvedValueOnce(mockResponse)
      
      await store.login('test', 'password123')
      
      expect(store.user).toEqual(mockUser)
      expect(store.token).toBe('mock-token')
      expect(store.isAuthenticated).toBe(true)
    })

    it('应该正确处理登录失败', async () => {
      const store = useAuthStore()
      const errorMessage = '用户名或密码错误'
      
      vi.mocked(login).mockRejectedValueOnce(new Error(errorMessage))
      
      await expect(store.login('wrong', 'wrong')).rejects.toThrow(errorMessage)
      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe('Token管理', () => {
    it('应该正确存储和清除token', async () => {
      const store = useAuthStore()
      const mockResponse = {
        token: 'mock-token',
        user: { id: 1, username: 'test' }
      }
      
      vi.mocked(login).mockResolvedValueOnce(mockResponse)
      await store.login('test', 'password123')
      expect(store.token).toBe('mock-token')
      
      vi.mocked(logout).mockResolvedValueOnce({ message: '登出成功' })
      await store.logout()
      expect(store.token).toBeNull()
    })

    it('应该在登出时清除所有状态', async () => {
      const store = useAuthStore()
      const mockResponse = {
        token: 'mock-token',
        user: { id: 1, username: 'test' }
      }
      
      vi.mocked(login).mockResolvedValueOnce(mockResponse)
      await store.login('test', 'password123')
      
      vi.mocked(logout).mockResolvedValueOnce({ message: '登出成功' })
      await store.logout()
      
      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe('权限控制', () => {
    it('应该正确判断用户权限', async () => {
      const store = useAuthStore()
      const mockUser = {
        id: 1,
        username: 'test',
        email: 'test@example.com',
        roles: ['admin']
      }
      const mockResponse = { token: 'mock-token', user: mockUser }
      
      vi.mocked(login).mockResolvedValueOnce(mockResponse)
      await store.login('test', 'password123')
      
      expect(store.hasRole('admin')).toBe(true)
      expect(store.hasRole('user')).toBe(false)
    })

    it('未登录时应该没有任何权限', () => {
      const store = useAuthStore()
      expect(store.hasRole('admin')).toBe(false)
      expect(store.hasRole('user')).toBe(false)
    })
  })

  describe('注册功能', () => {
    it('应该正确处理注册流程', async () => {
      const store = useAuthStore()
      const mockUser = {
        id: 1,
        username: 'newuser',
        email: 'new@example.com'
      }
      
      vi.mocked(register).mockResolvedValueOnce(mockUser)
      
      const result = await store.register({
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123'
      })
      
      expect(result).toEqual(mockUser)
    })

    it('应该处理注册失败', async () => {
      const store = useAuthStore()
      const errorMessage = '用户名已存在'
      
      vi.mocked(register).mockRejectedValueOnce(new Error(errorMessage))
      
      await expect(store.register({
        username: 'existing',
        email: 'test@example.com',
        password: 'password123'
      })).rejects.toThrow(errorMessage)
    })
  })

  describe('获取用户信息', () => {
    it('应该成功获取用户信息', async () => {
      const mockUser = { id: 1, username: 'test', role: 'admin' }
      vi.mocked(authApi.getUserInfo).mockResolvedValue(mockUser)

      const store = useAuthStore()
      store.$patch({ token: 'test-token' })

      await store.fetchUserInfo()

      expect(unref(store.user)).toEqual(mockUser)
      expect(unref(store.loading)).toBe(false)
      expect(unref(store.isAdmin)).toBe(true)
    })

    it('应该在获取用户信息失败时清除状态', async () => {
      const error = new Error('获取用户信息失败')
      vi.mocked(authApi.getUserInfo).mockRejectedValue(error)

      const store = useAuthStore()
      store.$patch({ token: 'test-token' })

      await expect(store.fetchUserInfo()).rejects.toThrow()

      expect(unref(store.token)).toBe('')
      expect(unref(store.user)).toBeNull()
      expect(unref(store.loading)).toBe(false)
      expect(unref(store.isAuthenticated)).toBe(false)
      expect(localStorage.getItem('token')).toBeNull()
    })
  })
}) 