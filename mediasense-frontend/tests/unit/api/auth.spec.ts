import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as authApi from '@/api/auth'
import request from '@/utils/request'
import type { LoginForm, RegisterForm } from '@/types/api'

vi.mock('@/utils/request', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}))

describe('认证 API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('应该正确调用登录接口', async () => {
      const mockResponse = {
        token: 'mock-token',
        user: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com',
          role: 'user',
          createdAt: '2024-03-20'
        }
      }

      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const loginForm: LoginForm = {
        username: 'testuser',
        password: 'password123'
      }

      const result = await authApi.login(loginForm)

      expect(request.post).toHaveBeenCalledWith('/auth/login', loginForm)
      expect(result).toEqual(mockResponse)
    })

    it('应该处理登录失败的情况', async () => {
      const error = new Error('用户名或密码错误')
      vi.mocked(request.post).mockRejectedValueOnce(error)

      const loginForm: LoginForm = {
        username: 'wronguser',
        password: 'wrongpass'
      }

      await expect(authApi.login(loginForm)).rejects.toThrow('用户名或密码错误')
    })
  })

  describe('register', () => {
    it('应该正确调用注册接口', async () => {
      const mockResponse = {
        token: 'mock-token',
        user: {
          id: '1',
          username: 'newuser',
          email: 'new@example.com',
          role: 'user',
          createdAt: '2024-03-20'
        }
      }

      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const registerForm: RegisterForm = {
        username: 'newuser',
        password: 'password123',
        email: 'new@example.com'
      }

      const result = await authApi.register(registerForm)

      expect(request.post).toHaveBeenCalledWith('/auth/register', registerForm)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getUserInfo', () => {
    it('应该正确获取用户信息', async () => {
      const mockResponse = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        role: 'user',
        createdAt: '2024-03-20'
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await authApi.getUserInfo()

      expect(request.get).toHaveBeenCalledWith('/auth/user')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('logout', () => {
    it('应该正确调用登出接口', async () => {
      vi.mocked(request.post).mockResolvedValueOnce({})

      await authApi.logout()

      expect(request.post).toHaveBeenCalledWith('/auth/logout')
    })
  })
}) 