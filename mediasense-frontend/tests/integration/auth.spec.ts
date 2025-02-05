import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/auth/Login.vue'
import Register from '@/views/auth/Register.vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

vi.mock('element-plus')

describe('认证流程集成测试', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/auth/login',
        name: 'login',
        component: Login
      },
      {
        path: '/auth/register',
        name: 'register',
        component: Register
      },
      {
        path: '/',
        name: 'home'
      }
    ]
  })

  beforeEach(() => {
    vi.clearAllMocks()
    router.push('/auth/login')
  })

  describe('登录流程', () => {
    it('应该完成完整的登录流程', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                auth: {
                  token: null,
                  user: null
                }
              }
            }),
            router
          ]
        }
      })

      const store = useAuthStore()
      const mockUser = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        role: 'user',
        createdAt: '2024-03-20'
      }

      // 模拟登录成功
      vi.mocked(store.login).mockResolvedValueOnce({
        token: 'mock-token',
        user: mockUser
      })

      // 填写登录表单
      await wrapper.find('input[name="username"]').setValue('testuser')
      await wrapper.find('input[name="password"]').setValue('password123')

      // 提交表单
      await wrapper.find('form').trigger('submit.prevent')

      // 验证登录调用
      expect(store.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123'
      })

      // 验证路由跳转
      expect(router.currentRoute.value.path).toBe('/')

      // 验证存储状态
      expect(store.isAuthenticated).toBe(true)
      expect(store.user).toEqual(mockUser)
      expect(localStorage.getItem('token')).toBe('mock-token')
    })

    it('应该正确处理登录失败', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useAuthStore()
      vi.mocked(store.login).mockRejectedValueOnce(new Error('登录失败'))

      // 填写登录表单
      await wrapper.find('input[name="username"]').setValue('wronguser')
      await wrapper.find('input[name="password"]').setValue('wrongpass')

      // 提交表单
      await wrapper.find('form').trigger('submit.prevent')

      // 验证错误提示
      expect(ElMessage.error).toHaveBeenCalledWith('登录失败')

      // 验证未跳转
      expect(router.currentRoute.value.path).toBe('/auth/login')

      // 验证状态未改变
      expect(store.isAuthenticated).toBe(false)
      expect(store.user).toBeNull()
      expect(localStorage.getItem('token')).toBeNull()
    })
  })

  describe('注册流程', () => {
    it('应该完成完整的注册流程', async () => {
      await router.push('/auth/register')
      
      const wrapper = mount(Register, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useAuthStore()
      const mockUser = {
        id: '1',
        username: 'newuser',
        email: 'new@example.com',
        role: 'user',
        createdAt: '2024-03-20'
      }

      // 模拟注册成功
      vi.mocked(store.register).mockResolvedValueOnce({
        token: 'mock-token',
        user: mockUser
      })

      // 填写注册表单
      await wrapper.find('input[name="username"]').setValue('newuser')
      await wrapper.find('input[name="email"]').setValue('new@example.com')
      await wrapper.find('input[name="password"]').setValue('password123')
      await wrapper.find('input[name="confirmPassword"]').setValue('password123')

      // 提交表单
      await wrapper.find('form').trigger('submit.prevent')

      // 验证注册调用
      expect(store.register).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123'
      })

      // 验证路由跳转
      expect(router.currentRoute.value.path).toBe('/')

      // 验证存储状态
      expect(store.isAuthenticated).toBe(true)
      expect(store.user).toEqual(mockUser)
      expect(localStorage.getItem('token')).toBe('mock-token')
    })
  })

  describe('登出流程', () => {
    it('应该完成完整的登出流程', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                auth: {
                  token: 'existing-token',
                  user: {
                    id: '1',
                    username: 'testuser'
                  }
                }
              }
            }),
            router
          ]
        }
      })

      const store = useAuthStore()
      vi.mocked(store.logout).mockResolvedValueOnce()

      await store.logout()

      // 验证路由跳转
      expect(router.currentRoute.value.path).toBe('/auth/login')

      // 验证状态清除
      expect(store.isAuthenticated).toBe(false)
      expect(store.user).toBeNull()
      expect(localStorage.getItem('token')).toBeNull()
    })
  })

  describe('路由守卫', () => {
    it('应该正确处理需要认证的路由', async () => {
      const store = useAuthStore()
      store.isAuthenticated = false

      // 尝试访问需要认证的路由
      await router.push('/monitor')

      // 验证重定向到登录页
      expect(router.currentRoute.value.path).toBe('/auth/login')
      expect(ElMessage.warning).toHaveBeenCalledWith('请先登录')
    })

    it('应该正确处理需要管理员权限的路由', async () => {
      const store = useAuthStore()
      store.isAuthenticated = true
      store.isAdmin = false

      // 尝试访问需要管理员权限的路由
      await router.push('/monitor')

      // 验证重定向到首页
      expect(router.currentRoute.value.path).toBe('/')
      expect(ElMessage.error).toHaveBeenCalledWith('需要管理员权限')
    })
  })
}) 