import axios from 'axios'
import type { AxiosInstance, AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

interface ApiResponse<T> {
  status: 'success' | 'error'
  data: T
  message?: string
}

const createAxiosInstance = (): AxiosInstance => {
  const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '',
    timeout: 15000,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  // 请求拦截器
  service.interceptors.request.use(
    (config) => {
      const authStore = useAuthStore()
      if (authStore.token) {
        config.headers.Authorization = `Bearer ${authStore.token}`
      }
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // 响应拦截器
  service.interceptors.response.use(
    (response: AxiosResponse<ApiResponse<any>>) => {
      const { data } = response
      if (data.status === 'error') {
        ElMessage.error(data.message || '请求失败')
        return Promise.reject(new Error(data.message || '请求失败'))
      }
      return response
    },
    (error) => {
      ElMessage.error(error.message || '网络错误')
      return Promise.reject(error)
    }
  )

  return service
}

const request = createAxiosInstance()

export default request 