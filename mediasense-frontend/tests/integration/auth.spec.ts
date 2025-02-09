import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/auth/Login.vue'
import Register from '@/views/auth/Register.vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('认证流程集成测试', () => {
  let router: any
  let store: any

  beforeEach(() => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/auth/login',
          name: 'Login',
          component: Login
        },
        {
          path: '/auth/register',
          name: 'Register',
          component: Register
        },
        {
          path: '/dashboard',
          name: 'Dashboard',
          component: { template: '<div>Dashboard</div>' }
        }
      ]
    })

    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        auth: {
          token: null,
          user: null,
          loading: false
        }
      }
    })

    store = useAuthStore()
  })

  describe('登录流程', () => {
    let wrapper: any

    beforeEach(() => {
      wrapper = mount(Login, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })],
          stubs: {
            'el-card': true,
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-button': true,
            'el-link': true
          }
        }
      })
    })

    it('应该能成功登录并跳转到仪表盘', async () => {
      const form = wrapper.find('[data-test="login-form"]')
      const usernameInput = wrapper.find('[data-test="username-input"]')
      const passwordInput = wrapper.find('[data-test="password-input"]')
      const submitButton = wrapper.find('[data-test="login-button"]')

      await usernameInput.setValue('testuser')
      await passwordInput.setValue('password123')
      await form.trigger('submit')

      expect(store.login).toHaveBeenCalledWith('testuser', 'password123')
      expect(router.currentRoute.value.path).toBe('/dashboard')
      expect(ElMessage.success).toHaveBeenCalledWith('登录成功')
    })

    it('应该显示登录错误信息', async () => {
      store.login.mockRejectedValue(new Error('用户名或密码错误'))

      const form = wrapper.find('[data-test="login-form"]')
      await form.trigger('submit')

      expect(ElMessage.error).toHaveBeenCalledWith('用户名或密码错误')
      expect(router.currentRoute.value.path).toBe('/auth/login')
    })

    it('应该验证表单字段', async () => {
      const form = wrapper.find('[data-test="login-form"]')
      await form.trigger('submit')

      const errors = wrapper.findAll('.el-form-item__error')
      expect(errors.length).toBeGreaterThan(0)
      expect(store.login).not.toHaveBeenCalled()
    })
  })

  describe('注册流程', () => {
    let wrapper: any

    beforeEach(() => {
      wrapper = mount(Register, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })],
          stubs: {
            'el-card': true,
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-button': true,
            'el-link': true
          }
        }
      })
    })

    it('应该能成功注册并跳转到登录页', async () => {
      const form = wrapper.find('[data-test="register-form"]')
      const usernameInput = wrapper.find('[data-test="username-input"]')
      const emailInput = wrapper.find('[data-test="email-input"]')
      const passwordInput = wrapper.find('[data-test="password-input"]')
      const confirmPasswordInput = wrapper.find('[data-test="confirm-password-input"]')

      await usernameInput.setValue('newuser')
      await emailInput.setValue('newuser@example.com')
      await passwordInput.setValue('password123')
      await confirmPasswordInput.setValue('password123')
      await form.trigger('submit')

      expect(store.register).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'newuser@example.com',
        password: 'password123'
      })
      expect(router.currentRoute.value.path).toBe('/auth/login')
      expect(ElMessage.success).toHaveBeenCalledWith('注册成功')
    })

    it('应该显示注册错误信息', async () => {
      store.register.mockRejectedValue(new Error('用户名已存在'))

      const form = wrapper.find('[data-test="register-form"]')
      await form.trigger('submit')

      expect(ElMessage.error).toHaveBeenCalledWith('用户名已存在')
      expect(router.currentRoute.value.path).toBe('/auth/register')
    })

    it('应该验证密码确认', async () => {
      const form = wrapper.find('[data-test="register-form"]')
      const passwordInput = wrapper.find('[data-test="password-input"]')
      const confirmPasswordInput = wrapper.find('[data-test="confirm-password-input"]')

      await passwordInput.setValue('password123')
      await confirmPasswordInput.setValue('password456')
      await form.trigger('submit')

      const errors = wrapper.findAll('.el-form-item__error')
      expect(errors.length).toBeGreaterThan(0)
      expect(store.register).not.toHaveBeenCalled()
    })
  })

  describe('认证状态管理', () => {
    it('应该在登录成功后更新认证状态', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com'
      }

      store.login.mockResolvedValue({ user: mockUser, token: 'mock-token' })
      
      const wrapper = mount(Login, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })]
        }
      })

      await wrapper.vm.handleSubmit()

      expect(store.isAuthenticated).toBe(true)
      expect(store.user).toEqual(mockUser)
      expect(localStorage.getItem('token')).toBe('mock-token')
    })

    it('应该在登出后清除认证状态', async () => {
      await store.logout()

      expect(store.isAuthenticated).toBe(false)
      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
      expect(localStorage.getItem('token')).toBeNull()
    })

    it('应该在token过期时重定向到登录页', async () => {
      store.token = 'expired-token'
      store.checkAuth.mockRejectedValue(new Error('Token expired'))

      await router.push('/dashboard')

      expect(router.currentRoute.value.path).toBe('/auth/login')
      expect(store.token).toBeNull()
    })
  })

  describe('路由守卫', () => {
    it('应该保护需要认证的路由', async () => {
      store.isAuthenticated = false
      await router.push('/dashboard')

      expect(router.currentRoute.value.path).toBe('/auth/login')
    })

    it('应该重定向已认证用户访问登录页', async () => {
      store.isAuthenticated = true
      await router.push('/auth/login')

      expect(router.currentRoute.value.path).toBe('/dashboard')
    })

    it('应该保存重定向地址', async () => {
      store.isAuthenticated = false
      await router.push('/dashboard')

      expect(router.currentRoute.value.query.redirect).toBe('/dashboard')
    })
  })

  describe('表单验证', () => {
    it('应该验证登录表单必填字段', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })]
        }
      })

      const form = wrapper.find('[data-test="login-form"]')
      await form.trigger('submit')

      const errors = wrapper.findAll('.el-form-item__error')
      expect(errors.length).toBe(2) // 用户名和密码都是必填
    })

    it('应该验证注册表单的邮箱格式', async () => {
      const wrapper = mount(Register, {
        global: {
          plugins: [router, createTestingPinia({ createSpy: vi.fn })]
        }
      })

      const emailInput = wrapper.find('[data-test="email-input"]')
      await emailInput.setValue('invalid-email')
      await wrapper.find('[data-test="register-form"]').trigger('submit')

      const errors = wrapper.findAll('.el-form-item__error')
      expect(errors.some(error => error.text().includes('邮箱格式'))).toBe(true)
    })
  })
}) 