import { describe, it, expect, beforeEach, vi } from 'vitest'
import { login, register, logout, refreshToken } from '@/api/auth'
import axios from 'axios'

vi.mock('axios')

describe('认证 API', () => {
  beforeEach(() => {
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
      ;(axios.post as any).mockResolvedValueOnce(mockResponse)

      const result = await login('test', 'password123')
      expect(result).toEqual(mockResponse.data)
      expect(axios.post).toHaveBeenCalledWith('/api/auth/login', {
        username: 'test',
        password: 'password123'
      })
    })

    it('使用错误的凭证应该返回错误', async () => {
      const errorMessage = '用户名或密码错误'
      ;(axios.post as any).mockRejectedValueOnce(new Error(errorMessage))

      await expect(login('wrong', 'wrong')).rejects.toThrow(errorMessage)
    })

    it('应该正确处理特殊字符输入', async () => {
      const username = 'test@#$%'
      const password = 'pass!@#$'
      
      await login(username, password)
      expect(axios.post).toHaveBeenCalledWith('/api/auth/login', {
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
      ;(axios.post as any).mockResolvedValueOnce(mockResponse)

      const result = await register({
        username: 'newuser',
        email: 'newuser@example.com',
        password: 'password123'
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('使用重复的用户名应该返回错误', async () => {
      const errorMessage = '用户名已存在'
      ;(axios.post as any).mockRejectedValueOnce(new Error(errorMessage))

      await expect(register({
        username: 'existing',
        email: 'test@example.com',
        password: 'password123'
      })).rejects.toThrow(errorMessage)
    })

    it('应该验证邮箱格式', async () => {
      const errorMessage = '无效的邮箱格式'
      ;(axios.post as any).mockRejectedValueOnce(new Error(errorMessage))

      await expect(register({
        username: 'test',
        email: 'invalid-email',
        password: 'password123'
      })).rejects.toThrow(errorMessage)
    })
  })

  describe('登出接口', () => {
    it('应该成功登出并清除token', async () => {
      const mockResponse = { data: { message: '登出成功' } }
      ;(axios.post as any).mockResolvedValueOnce(mockResponse)

      const result = await logout()
      expect(result).toEqual(mockResponse.data)
      expect(axios.post).toHaveBeenCalledWith('/api/auth/logout')
    })
  })

  describe('Token刷新接口', () => {
    it('应该成功刷新token', async () => {
      const mockResponse = {
        data: {
          token: 'new-mock-token'
        }
      }
      ;(axios.post as any).mockResolvedValueOnce(mockResponse)

      const result = await refreshToken('old-token')
      expect(result).toEqual(mockResponse.data)
      expect(axios.post).toHaveBeenCalledWith('/api/auth/refresh', {
        token: 'old-token'
      })
    })

    it('token过期时应该返回错误', async () => {
      const errorMessage = 'token已过期'
      ;(axios.post as any).mockRejectedValueOnce(new Error(errorMessage))

      await expect(refreshToken('expired-token')).rejects.toThrow(errorMessage)
    })
  })
}) 