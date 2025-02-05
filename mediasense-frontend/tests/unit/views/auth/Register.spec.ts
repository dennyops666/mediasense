import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { ElMessage } from 'element-plus'
import Register from '@/views/auth/Register.vue'
import { useAuthStore } from '@/stores/auth'

// Mock vue-router
const mockRouterPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockRouterPush
  })
}))

// Mock element-plus
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn()
  }
}))

const mountComponent = () => {
  return mount(Register, {
    global: {
      plugins: [
        createTestingPinia({
          createSpy: vi.fn,
          initialState: {
            auth: {
              loading: false
            }
          }
        })
      ],
      stubs: {
        'el-card': {
          template: '<div class="el-card"><slot name="header"></slot><slot></slot></div>'
        },
        'el-button': {
          props: ['nativeType', 'loading'],
          template: '<button :type="nativeType" :data-test="$attrs[\'data-test\']" :disabled="loading" @click="$emit(\'click\')"><slot></slot></button>'
        },
        'el-link': {
          template: '<a :data-test="$attrs[\'data-test\']" @click="$emit(\'click\')"><slot></slot></a>'
        },
        'el-input': {
          props: ['modelValue', 'type', 'placeholder'],
          template: '<div :data-test="$attrs[\'data-test\']"><input :type="type" :value="modelValue" :placeholder="placeholder" @input="$emit(\'update:modelValue\', $event.target.value)" /></div>'
        },
        'el-form': {
          props: ['model', 'rules'],
          template: '<form @submit.prevent="$emit(\'submit\')"><slot></slot></form>',
          methods: {
            validate() {
              return new Promise((resolve, reject) => {
                const errors = []
                if (!this.model.username) {
                  errors.push('请输入用户名')
                } else if (this.model.username.length < 3) {
                  errors.push('用户名至少3个字符')
                }
                
                if (!this.model.email) {
                  errors.push('请输入邮箱')
                } else if (!this.model.email.includes('@')) {
                  errors.push('请输入正确的邮箱格式')
                }
                
                if (!this.model.password) {
                  errors.push('请输入密码')
                } else if (this.model.password.length < 6) {
                  errors.push('密码至少6个字符')
                }
                
                if (this.model.password !== this.model.confirmPassword) {
                  errors.push('两次输入密码不一致')
                }
                
                if (errors.length > 0) {
                  reject(new Error(errors[0]))
                } else {
                  resolve(true)
                }
              })
            }
          }
        },
        'el-form-item': {
          props: ['label', 'prop'],
          template: '<div class="el-form-item"><label v-if="label">{{ label }}</label><slot></slot></div>'
        }
      }
    }
  })
}

describe('Register.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染注册表单', () => {
    const wrapper = mountComponent()
    expect(wrapper.find('form').exists()).toBe(true)
    expect(wrapper.find('[data-test="username-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="email-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="password-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="confirm-password-input"]').exists()).toBe(true)
  })

  it('应该在表单为空时验证失败', async () => {
    const wrapper = mountComponent()
    await wrapper.find('[data-test="register-button"]').trigger('click')
    expect(ElMessage.error).toHaveBeenCalledWith('请输入用户名')
  })

  it('应该验证用户名长度', async () => {
    const wrapper = mountComponent()
    await wrapper.find('[data-test="username-input"] input').setValue('ab')
    await wrapper.find('[data-test="register-button"]').trigger('click')
    expect(ElMessage.error).toHaveBeenCalledWith('用户名至少3个字符')
  })

  it('应该验证邮箱格式', async () => {
    const wrapper = mountComponent()
    await wrapper.find('[data-test="username-input"] input').setValue('testuser')
    await wrapper.find('[data-test="email-input"] input').setValue('invalid-email')
    await wrapper.find('[data-test="register-button"]').trigger('click')
    expect(ElMessage.error).toHaveBeenCalledWith('请输入正确的邮箱格式')
  })

  it('应该验证密码长度', async () => {
    const wrapper = mountComponent()
    await wrapper.find('[data-test="username-input"] input').setValue('testuser')
    await wrapper.find('[data-test="email-input"] input').setValue('test@example.com')
    await wrapper.find('[data-test="password-input"] input').setValue('12345')
    await wrapper.find('[data-test="register-button"]').trigger('click')
    expect(ElMessage.error).toHaveBeenCalledWith('密码至少6个字符')
  })

  it('应该验证密码确认匹配', async () => {
    const wrapper = mountComponent()
    await wrapper.find('[data-test="username-input"] input').setValue('testuser')
    await wrapper.find('[data-test="email-input"] input').setValue('test@example.com')
    await wrapper.find('[data-test="password-input"] input').setValue('123456')
    await wrapper.find('[data-test="confirm-password-input"] input').setValue('654321')
    await wrapper.find('[data-test="register-button"]').trigger('click')
    expect(ElMessage.error).toHaveBeenCalledWith('两次输入密码不一致')
  })

  it('应该在注册成功时导航到首页', async () => {
    const wrapper = mountComponent()
    const authStore = useAuthStore()
    vi.mocked(authStore.register).mockResolvedValueOnce()

    await wrapper.find('[data-test="username-input"] input').setValue('testuser')
    await wrapper.find('[data-test="email-input"] input').setValue('test@example.com')
    await wrapper.find('[data-test="password-input"] input').setValue('password123')
    await wrapper.find('[data-test="confirm-password-input"] input').setValue('password123')

    await wrapper.find('[data-test="register-button"]').trigger('click')
    await wrapper.vm.$nextTick()
    await vi.waitFor(() => {
      expect(authStore.register).toHaveBeenCalledWith('testuser', 'password123', 'test@example.com')
      expect(mockRouterPush).toHaveBeenCalledWith('/')
      expect(ElMessage.success).toHaveBeenCalledWith('注册成功')
    })
  })

  it('应该处理注册失败', async () => {
    const wrapper = mountComponent()
    const authStore = useAuthStore()
    const error = new Error('注册失败')
    vi.mocked(authStore.register).mockRejectedValueOnce(error)

    await wrapper.find('[data-test="username-input"] input').setValue('testuser')
    await wrapper.find('[data-test="email-input"] input').setValue('test@example.com')
    await wrapper.find('[data-test="password-input"] input').setValue('password123')
    await wrapper.find('[data-test="confirm-password-input"] input').setValue('password123')

    await wrapper.find('[data-test="register-button"]').trigger('click')
    await wrapper.vm.$nextTick()
    await vi.waitFor(() => {
      expect(ElMessage.error).toHaveBeenCalledWith('注册失败')
    })
  })

  it('应该在点击登录链接时导航到登录页面', async () => {
    const wrapper = mountComponent()
    
    await wrapper.find('[data-test="login-link"]').trigger('click')
    await wrapper.vm.$nextTick()
    await vi.waitFor(() => {
      expect(mockRouterPush).toHaveBeenCalledWith('/auth/login')
    })
  })
})