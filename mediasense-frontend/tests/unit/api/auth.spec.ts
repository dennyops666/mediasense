import axios from 'axios'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import * as authApi from '@/api/auth'
import request from '@/utils/request'

// Mock request
vi.mock('@/utils/request', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('认证 API', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('登录接口', () => {
    it('使用正确的用户名和密码应该成功登录', async () => {
      const mockResponse = {
        data: {
          token: 'mock-token',
          user: {
            id: 1,
            username: 'test',
            email: 'test@example.com'
          }
        }
      }
      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const result = await authApi.login({
        username: 'test',
        password: 'password123'
      })
      expect(result).toEqual(mockResponse.data)
      expect(request.post).toHaveBeenCalledWith('/auth/login', {
        username: 'test',
        password: 'password123'
      })
    })

    it('使用错误的凭证应该返回错误', async () => {
      const mockError = {
        response: {
          data: {
            message: 'Invalid credentials'
          }
        }
      }
      vi.mocked(request.post).mockRejectedValueOnce(mockError)

      await expect(authApi.login({
        username: 'wrong',
        password: 'wrong'
      })).rejects.toEqual(mockError)
    })

    it('应该正确处理特殊字符输入', async () => {
      const username = 'test@#$%'
      const password = 'pass!@#$'
      const mockResponse = {
        data: {
          token: 'mock-token',
          user: {
            id: 1,
            username: username,
            email: 'test@example.com'
          }
        }
      }
      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)
      
      await authApi.login({
        username,
        password
      })
      expect(request.post).toHaveBeenCalledWith('/auth/login', {
        username,
        password
      })
    })
  })

  describe('注册接口', () => {
    it('使用有效信息应该成功注册', async () => {
      const mockResponse = {
        data: {
          id: 1,
          username: 'newuser',
          email: 'newuser@example.com'
        }
      }
      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const result = await authApi.register({
        username: 'newuser',
        email: 'newuser@example.com',
        password: 'password123'
      })
      expect(result).toEqual(mockResponse.data)
      expect(request.post).toHaveBeenCalledWith('/auth/register', {
        username: 'newuser',
        email: 'newuser@example.com',
        password: 'password123'
      })
    })

    it('使用重复的用户名应该返回错误', async () => {
      const mockError = {
        response: {
          data: {
            message: 'Username already exists'
          }
        }
      }
      vi.mocked(request.post).mockRejectedValueOnce(mockError)

      await expect(authApi.register({
        username: 'existing',
        email: 'test@example.com',
        password: 'password123'
      })).rejects.toEqual(mockError)
    })

    it('应该验证邮箱格式', async () => {
      const mockError = {
        response: {
          data: {
            message: 'Invalid email format'
          }
        }
      }
      vi.mocked(request.post).mockRejectedValueOnce(mockError)

      await expect(authApi.register({
        username: 'newuser',
        email: 'invalid-email',
        password: 'password123'
      })).rejects.toEqual(mockError)
    })
  })

  describe('登出接口', () => {
    it('应该成功登出并清除token', async () => {
      const mockResponse = {
        data: {
          message: '登出成功'
        }
      }
      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const result = await authApi.logout()
      expect(result).toEqual(mockResponse.data)
      expect(request.post).toHaveBeenCalledWith('/auth/logout')
    })
  })

  describe('Token刷新接口', () => {
    it('应该成功刷新token', async () => {
      const mockResponse = {
        data: {
          token: 'new-mock-token'
        }
      }
      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const result = await authApi.refreshToken()
      expect(result).toEqual(mockResponse.data)
      expect(request.post).toHaveBeenCalledWith('/auth/refresh')
    })

    it('token过期时应该返回错误', async () => {
      const mockError = {
        response: {
          data: {
            message: 'Token expired'
          }
        }
      }
      vi.mocked(request.post).mockRejectedValueOnce(mockError)

      await expect(authApi.refreshToken()).rejects.toEqual(mockError)
    })
  })
})