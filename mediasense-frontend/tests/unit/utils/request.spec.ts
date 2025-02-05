import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

vi.mock('@/stores/auth')
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

// 创建一个模拟的 axios 实例
const mockAxiosInstance = vi.hoisted(() => ({
  interceptors: {
    request: {
      use: vi.fn(),
      eject: vi.fn()
    },
    response: {
      use: vi.fn(),
      eject: vi.fn()
    }
  },
  request: vi.fn()
}))

// 模拟 axios.create
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance)
  }
}))

describe('Request 工具', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.resetModules()
  })

  describe('基本配置', () => {
    it('应该使用正确的基本配置创建 axios 实例', async () => {
      const { default: request } = await import('@/utils/request')
      
      expect(axios.create).toHaveBeenCalledWith({
        baseURL: import.meta.env.VITE_API_BASE_URL,
        timeout: 15000,
        headers: {
          'Content-Type': 'application/json'
        }
      })
    })
  })

  describe('请求拦截器', () => {
    it('应该在有 token 时添加认证头', async () => {
      const mockToken = 'test-token'
      vi.mocked(useAuthStore).mockReturnValue({
        token: mockToken,
        logout: vi.fn()
      })

      const { default: request } = await import('@/utils/request')
      
      // 获取请求拦截器的配置
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0]
      
      // 测试拦截器
      const config = { headers: {} }
      const result = requestInterceptor(config)
      
      expect(result.headers.Authorization).toBe(`Bearer ${mockToken}`)
    })

    it('应该在没有 token 时不添加认证头', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        token: '',
        logout: vi.fn()
      })

      const { default: request } = await import('@/utils/request')
      
      // 获取请求拦截器的配置
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0]
      
      // 测试拦截器
      const config = { headers: {} }
      const result = requestInterceptor(config)
      
      expect(result.headers.Authorization).toBeUndefined()
    })

    it('应该处理请求错误', async () => {
      const { default: request } = await import('@/utils/request')
      
      // 获取请求拦截器的错误处理
      const errorHandler = mockAxiosInstance.interceptors.request.use.mock.calls[0][1]
      
      const error = new Error('请求错误')
      await expect(errorHandler(error)).rejects.toThrow('请求错误')
    })
  })

  describe('响应拦截器', () => {
    it('应该在成功响应时返回数据', async () => {
      const { default: request } = await import('@/utils/request')
      
      // 获取响应拦截器的配置
      const responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][0]
      
      const mockData = { id: 1, name: 'test' }
      const response = {
        data: {
          status: 'success',
          data: mockData
        }
      }
      
      const result = responseInterceptor(response)
      expect(result).toBe(mockData)
    })

    it('应该在失败响应时显示错误消息并拒绝 Promise', async () => {
      const { default: request } = await import('@/utils/request')
      
      // 获取响应拦截器的配置
      const responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][0]
      
      const errorMessage = '操作失败'
      const response = {
        data: {
          status: 'error',
          message: errorMessage
        }
      }

      await expect(responseInterceptor(response)).rejects.toThrow(errorMessage)
      expect(ElMessage.error).toHaveBeenCalledWith(errorMessage)
    })

    it('应该处理网络错误', async () => {
      const { default: request } = await import('@/utils/request')
      
      // 获取响应拦截器的错误处理
      const errorHandler = mockAxiosInstance.interceptors.response.use.mock.calls[0][1]
      
      const error = {
        response: {
          data: {
            message: '网络错误'
          }
        }
      }

      await expect(errorHandler(error)).rejects.toBe(error)
      expect(ElMessage.error).toHaveBeenCalledWith('网络错误')
    })

    it('应该处理没有响应数据的错误', async () => {
      const { default: request } = await import('@/utils/request')
      
      // 获取响应拦截器的错误处理
      const errorHandler = mockAxiosInstance.interceptors.response.use.mock.calls[0][1]
      
      const error = new Error('网络错误')
      
      await expect(errorHandler(error)).rejects.toBe(error)
      expect(ElMessage.error).toHaveBeenCalledWith('网络错误')
    })
  })
}) 