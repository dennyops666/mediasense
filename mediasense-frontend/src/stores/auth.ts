import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, AuthResponse } from '@/types/api'
import * as authApi from '@/api/auth'
import { ElMessage } from 'element-plus'

export const useAuthStore = defineStore('auth', () => {
  const token = ref('')
  const user = ref<User | null>(null)
  const loading = ref(false)

  // 初始化时从localStorage加载token
  const initToken = () => {
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      token.value = storedToken
    }
  }

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = ''
    localStorage.removeItem('token')
  }

  const login = async (username: string, password: string) => {
    try {
      loading.value = true
      const data = await authApi.login({
        username,
        password
      })
      setToken(data.token)
      user.value = data.user
      ElMessage.success('登录成功')
    } catch (error) {
      clearToken()
      user.value = null
      ElMessage.error('登录失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const register = async (username: string, password: string, email: string): Promise<User> => {
    try {
      loading.value = true
      const result = await authApi.register({
        username,
        password,
        email
      })
      setToken(result.token)
      user.value = result.user
      ElMessage.success('注册成功')
      return result.user
    } catch (error) {
      clearToken()
      user.value = null
      ElMessage.error('注册失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      loading.value = true
      await authApi.logout()
      clearToken()
      user.value = null
      ElMessage.success('已退出登录')
    } catch (error) {
      ElMessage.error('退出登录失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchUserInfo = async () => {
    try {
      loading.value = true
      const data = await authApi.getUserInfo()
      user.value = data
    } catch (error) {
      clearToken()
      user.value = null
      throw error
    } finally {
      loading.value = false
    }
  }

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  const hasRole = (role: string) => {
    return user.value?.roles?.includes(role) || false
  }

  // 初始化token
  initToken()

  return {
    token,
    user,
    loading,
    login,
    register,
    logout,
    fetchUserInfo,
    isAuthenticated,
    isAdmin,
    hasRole,
    initToken
  }
}) 