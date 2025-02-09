import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { User } from '@/types/api'

export function useAuth() {
  const store = useAuthStore()
  const loading = ref(false)
  const error = ref<string | null>(null)

  const user = computed(() => store.user)
  const token = computed(() => store.token)
  const isAuthenticated = computed(() => store.isAuthenticated)
  const isAdmin = computed(() => store.isAdmin)

  const login = async (credentials: { username: string; password: string }) => {
    try {
      loading.value = true
      error.value = null
      await store.login(credentials.username, credentials.password)
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const register = async (userData: { username: string; password: string; email: string }) => {
    try {
      loading.value = true
      error.value = null
      await store.register(userData.username, userData.password, userData.email)
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      loading.value = true
      error.value = null
      await store.logout()
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const checkAuth = async () => {
    try {
      loading.value = true
      error.value = null
      await store.fetchUserInfo()
      return true
    } catch (err: any) {
      error.value = err.message
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    checkAuth
  }
}