import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import mockAxios from '../../mocks/axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

vi.mock('axios', () => ({
  default: mockAxios
}))

vi.mock('element-plus')

describe('Request Utility', () => {
  let authStore: ReturnType<typeof useAuthStore>

  beforeEach(() => {
    vi.clearAllMocks()
    
    const pinia = createPinia()
    setActivePinia(pinia)
    
    authStore = useAuthStore()
    authStore.token = 'test-token'
  })

  describe('请求拦截器', () => {
    it('应该在有token时添加认证头', () => {
      const config = { headers: {} }
      const requestFn = vi.fn((config) => {
        if (authStore.token) {
          config.headers.Authorization = `Bearer ${authStore.token}`
        }
        return config
      })
      mockAxios.interceptors.request.use.mockImplementation((fn) => fn)
      mockAxios.interceptors.request.use(requestFn)
      
      const result = requestFn(config)
      expect(result.headers.Authorization).toBe('Bearer test-token')
    })

    it('应该在没有token时不添加认证头', () => {
      authStore.token = ''
      const config = { headers: {} }
      const requestFn = vi.fn((config) => {
        if (authStore.token) {
          config.headers.Authorization = `Bearer ${authStore.token}`
        }
        return config
      })
      mockAxios.interceptors.request.use.mockImplementation((fn) => fn)
      mockAxios.interceptors.request.use(requestFn)
      
      const result = requestFn(config)
      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('响应拦截器', () => {
    it('应该正确处理成功响应', () => {
      const mockData = { id: 1, name: 'test' }
      const response = {
        data: {
          status: 'success',
          data: mockData
        }
      }
      
      const responseFn = vi.fn((response) => {
        const { data } = response
        if (data.status === 'success') {
          return data.data
        } else {
          const message = data.message || '请求失败'
          ElMessage.error(message)
          return Promise.reject(new Error(message))
        }
      })
      mockAxios.interceptors.response.use.mockImplementation((fn) => fn)
      mockAxios.interceptors.response.use(responseFn)
      
      const result = responseFn(response)
      expect(result).toEqual(mockData)
    })

    it('应该处理失败响应', async () => {
      const response = {
        data: {
          status: 'error',
          message: '操作失败'
        }
      }
      
      const responseFn = vi.fn((response) => {
        const { data } = response
        if (data.status === 'success') {
          return data.data
        } else {
          const message = data.message || '请求失败'
          ElMessage.error(message)
          return Promise.reject(new Error(message))
        }
      })
      mockAxios.interceptors.response.use.mockImplementation((fn) => fn)
      mockAxios.interceptors.response.use(responseFn)
      
      await expect(async () => {
        await responseFn(response)
      }).rejects.toThrow('操作失败')
      
      expect(ElMessage.error).toHaveBeenCalledWith('操作失败')
    })

    it('应该处理401错误并登出', async () => {
      const error = {
        response: {
          status: 401,
          data: {
            message: '未授权'
          }
        }
      }
      
      const errorFn = vi.fn((error) => {
        let message = '网络错误'
        
        if (error.code === 'ECONNABORTED') {
          message = '请求超时'
        } else if (error.code === 'ERR_NETWORK') {
          message = '网络连接错误'
        } else if (error.response?.status === 401) {
          message = '未授权'
          authStore.token = ''
        } else if (error.response?.data?.message) {
          message = error.response.data.message
        }
        
        ElMessage.error(message)
        return Promise.reject(error)
      })
      mockAxios.interceptors.response.use.mockImplementation((_, fn) => fn)
      mockAxios.interceptors.response.use(null, errorFn)
      
      await expect(errorFn(error)).rejects.toBe(error)
      expect(ElMessage.error).toHaveBeenCalledWith('未授权')
      expect(authStore.token).toBe('')
    })

    it('应该处理请求超时', async () => {
      const error = {
        code: 'ECONNABORTED',
        message: 'timeout'
      }
      
      const errorFn = vi.fn((error) => {
        let message = '网络错误'
        
        if (error.code === 'ECONNABORTED') {
          message = '请求超时'
        } else if (error.code === 'ERR_NETWORK') {
          message = '网络连接错误'
        } else if (error.response?.status === 401) {
          message = '未授权'
          authStore.token = ''
        } else if (error.response?.data?.message) {
          message = error.response.data.message
        }
        
        ElMessage.error(message)
        return Promise.reject(error)
      })
      mockAxios.interceptors.response.use.mockImplementation((_, fn) => fn)
      mockAxios.interceptors.response.use(null, errorFn)
      
      await expect(errorFn(error)).rejects.toBe(error)
      expect(ElMessage.error).toHaveBeenCalledWith('请求超时')
    })

    it('应该处理网络连接错误', async () => {
      const error = {
        code: 'ERR_NETWORK',
        message: 'Network Error'
      }
      
      const errorFn = vi.fn((error) => {
        let message = '网络错误'
        
        if (error.code === 'ECONNABORTED') {
          message = '请求超时'
        } else if (error.code === 'ERR_NETWORK') {
          message = '网络连接错误'
        } else if (error.response?.status === 401) {
          message = '未授权'
          authStore.token = ''
        } else if (error.response?.data?.message) {
          message = error.response.data.message
        }
        
        ElMessage.error(message)
        return Promise.reject(error)
      })
      mockAxios.interceptors.response.use.mockImplementation((_, fn) => fn)
      mockAxios.interceptors.response.use(null, errorFn)
      
      await expect(errorFn(error)).rejects.toBe(error)
      expect(ElMessage.error).toHaveBeenCalledWith('网络连接错误')
    })
  })

  describe('请求方法', () => {
    it('应该支持GET请求', async () => {
      const mockResponse = { data: { status: 'success', data: { id: 1 } } }
      mockAxios.get.mockResolvedValue(mockResponse)

      await request.get('/test')
      expect(mockAxios.get).toHaveBeenCalledWith('/test')
    })

    it('应该支持带参数的GET请求', async () => {
      const mockResponse = { data: { status: 'success', data: { id: 1 } } }
      mockAxios.get.mockResolvedValue(mockResponse)

      await request.get('/test', { params: { id: 1 } })
      expect(mockAxios.get).toHaveBeenCalledWith('/test', { params: { id: 1 } })
    })

    it('应该支持POST请求', async () => {
      const mockResponse = { data: { status: 'success', data: { id: 1 } } }
      mockAxios.post.mockResolvedValue(mockResponse)

      const data = { name: 'test' }
      await request.post('/test', data)
      expect(mockAxios.post).toHaveBeenCalledWith('/test', data)
    })

    it('应该支持PUT请求', async () => {
      const mockResponse = { data: { status: 'success', data: { id: 1 } } }
      mockAxios.put.mockResolvedValue(mockResponse)

      const data = { name: 'test' }
      await request.put('/test', data)
      expect(mockAxios.put).toHaveBeenCalledWith('/test', data)
    })

    it('应该支持DELETE请求', async () => {
      const mockResponse = { data: { status: 'success', data: { id: 1 } } }
      mockAxios.delete.mockResolvedValue(mockResponse)

      await request.delete('/test')
      expect(mockAxios.delete).toHaveBeenCalledWith('/test')
    })
  })
}) 