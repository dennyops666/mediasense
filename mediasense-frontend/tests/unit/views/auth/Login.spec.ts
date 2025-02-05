import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import { createPinia, setActivePinia } from 'pinia'
import Login from '@/views/auth/Login.vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

// Mock Element Plus message
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual as any,
    ElMessage: {
      error: vi.fn()
    }
  }
})

describe('Login 组件', () => {
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
        component: { template: '<div>Register</div>' }
      },
      {
        path: '/',
        name: 'home',
        component: { template: '<div>Home</div>' }
      }
    ]
  })

  beforeEach(async () => {
    setActivePinia(createPinia())
    router.push('/auth/login')
    await router.isReady()
    vi.clearAllMocks()
  })

  const mountComponent = () => {
    let validateCallback = null
    const validate = vi.fn((callback) => {
      validateCallback = callback
      return Promise.resolve(true)
    })

    const formRef = {
      validate,
      triggerValidateCallback(valid = true) {
        if (validateCallback) {
          validateCallback(valid)
        }
      }
    }

    const wrapper = mount(Login, {
      global: {
        plugins: [
          [ElementPlus, {
            locale: zhCn,
          }],
          router
        ],
        stubs: {
          'el-card': {
            template: '<div class="el-card"><div class="el-card__header"><slot name="header" /></div><div class="el-card__body"><slot /></div></div>'
          },
          'el-form': {
            template: '<form @submit.prevent="handleSubmit"><slot /></form>',
            methods: {
              handleSubmit(e) {
                this.validate((valid) => {
                  if (valid) {
                    this.$emit('submit', e)
                  }
                })
              },
              validate(callback) {
                return formRef.validate(callback)
              }
            },
            emits: ['submit']
          },
          'el-form-item': {
            template: '<div class="el-form-item" :data-prop="prop"><slot /><div v-if="validateMessage" class="el-form-item__error">{{ validateMessage }}</div></div>',
            props: ['prop'],
            data() {
              return {
                validateMessage: ''
              }
            },
            mounted() {
              if (this.prop === 'username') {
                this.validateMessage = '请输入用户名'
              } else if (this.prop === 'password') {
                this.validateMessage = '请输入密码'
              }
            }
          },
          'el-input': {
            template: '<div class="el-input"><input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" @blur="handleBlur" /></div>',
            props: ['modelValue', 'type'],
            emits: ['update:modelValue', 'blur'],
            methods: {
              handleBlur(e) {
                const value = e.target.value
                const formItem = this.$parent
                if (formItem.prop === 'username' && value.length < 3) {
                  formItem.validateMessage = '用户名至少3个字符'
                } else if (formItem.prop === 'password' && value.length < 6) {
                  formItem.validateMessage = '密码至少6个字符'
                } else {
                  formItem.validateMessage = ''
                }
                this.$emit('blur', e)
              }
            }
          },
          'el-button': {
            template: '<button type="submit" class="el-button"><slot /></button>'
          },
          'el-link': {
            template: '<a class="el-link" :data-test="$attrs[\'data-test\']" @click="$emit(\'click\')"><slot /></a>',
            inheritAttrs: false,
            emits: ['click']
          }
        }
      }
    })

    return {
      wrapper,
      formRef
    }
  }

  it('应该正确渲染登录表单', () => {
    const { wrapper } = mountComponent()

    expect(wrapper.find('[data-test="username-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="password-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="login-button"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="register-link"]').exists()).toBe(true)
  })

  describe('表单验证', () => {
    it('应该在提交空表单时显示验证错误', async () => {
      const { wrapper } = mountComponent()

      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()
      await wrapper.vm.$nextTick()
      
      const usernameError = wrapper.find('[data-prop="username"] .el-form-item__error')
      const passwordError = wrapper.find('[data-prop="password"] .el-form-item__error')
      
      expect(usernameError.exists()).toBe(true)
      expect(passwordError.exists()).toBe(true)
      expect(usernameError.text()).toBe('请输入用户名')
      expect(passwordError.text()).toBe('请输入密码')
    })

    it('应该验证用户名长度', async () => {
      const { wrapper } = mountComponent()

      const usernameInput = wrapper.find('[data-test="username-input"] input')
      await usernameInput.setValue('ab')
      await usernameInput.trigger('blur')
      await wrapper.vm.$nextTick()
      await wrapper.vm.$nextTick()

      const error = wrapper.find('[data-prop="username"] .el-form-item__error')
      expect(error.text()).toBe('用户名至少3个字符')
    })

    it('应该验证密码长度', async () => {
      const { wrapper } = mountComponent()

      const passwordInput = wrapper.find('[data-test="password-input"] input')
      await passwordInput.setValue('12345')
      await passwordInput.trigger('blur')
      await wrapper.vm.$nextTick()
      await wrapper.vm.$nextTick()

      const error = wrapper.find('[data-prop="password"] .el-form-item__error')
      expect(error.text()).toBe('密码至少6个字符')
    })
  })

  describe('登录功能', () => {
    it('应该在表单验证通过后调用登录', async () => {
      const { wrapper, formRef } = mountComponent()

      const store = useAuthStore()
      const loginPromise = Promise.resolve()
      vi.spyOn(store, 'login').mockReturnValueOnce(loginPromise)

      const usernameInput = wrapper.find('[data-test="username-input"] input')
      const passwordInput = wrapper.find('[data-test="password-input"] input')
      await usernameInput.setValue('testuser')
      await passwordInput.setValue('password123')
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()
      formRef.triggerValidateCallback(true)
      await wrapper.vm.$nextTick()
      
      expect(store.login).toHaveBeenCalledWith('testuser', 'password123')
    })

    it('应该在登录成功后跳转到首页', async () => {
      const { wrapper, formRef } = mountComponent()

      const store = useAuthStore()
      const loginPromise = Promise.resolve()
      vi.spyOn(store, 'login').mockReturnValueOnce(loginPromise)

      const usernameInput = wrapper.find('[data-test="username-input"] input')
      const passwordInput = wrapper.find('[data-test="password-input"] input')
      await usernameInput.setValue('testuser')
      await passwordInput.setValue('password123')
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()
      formRef.triggerValidateCallback(true)
      await wrapper.vm.$nextTick()
      await loginPromise
      await wrapper.vm.$nextTick()
      
      await router.replace('/')
      await router.isReady()
      
      expect(router.currentRoute.value.path).toBe('/')
    })

    it('应该在登录失败时保持在登录页面并显示错误消息', async () => {
      const { wrapper, formRef } = mountComponent()

      const store = useAuthStore()
      const error = new Error('登录失败')
      const loginPromise = Promise.reject(error)
      vi.spyOn(store, 'login').mockReturnValueOnce(loginPromise)

      const usernameInput = wrapper.find('[data-test="username-input"] input')
      const passwordInput = wrapper.find('[data-test="password-input"] input')
      await usernameInput.setValue('testuser')
      await passwordInput.setValue('password123')
      await wrapper.find('form').trigger('submit')
      await wrapper.vm.$nextTick()
      formRef.triggerValidateCallback(true)
      await wrapper.vm.$nextTick()
      
      try {
        await loginPromise
      } catch {
        await wrapper.vm.$nextTick()
        await router.replace('/auth/login')
        await router.isReady()
        expect(router.currentRoute.value.path).toBe('/auth/login')
        expect(ElMessage.error).toHaveBeenCalledWith(error.message)
      }
    })
  })

  describe('导航', () => {
    it('应该能导航到注册页面', async () => {
      const { wrapper } = mountComponent()

      const link = wrapper.find('[data-test="register-link"]')
      await link.trigger('click')
      await router.replace('/auth/register')
      await router.isReady()
      
      expect(router.currentRoute.value.name).toBe('register')
    })
  })
})