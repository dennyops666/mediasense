import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, AuthResponse } from '@/types/api'
import * as authApi from '@/api/auth'
import { ElMessage } from 'element-plus'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<User | null>(null)
  const loading = ref(false)

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
      ElMessage.error('登录失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const register = async (username: string, password: string, email: string) => {
    try {
      loading.value = true
      const data = await authApi.register({
        username,
        password,
        email
      })
      setToken(data.token)
      user.value = data.user
      ElMessage.success('注册成功')
    } catch (error) {
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

  return {
    token,
    user,
    loading,
    login,
    register,
    logout,
    fetchUserInfo,
    isAuthenticated,
    isAdmin
  }
}) 