import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import UserList from '@/views/user/UserList.vue'
import UserProfile from '@/views/user/UserProfile.vue'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

describe('用户管理集成测试', () => {
  let router: any
  let store: any
  let wrapper: any

  const mockUsers = [
    {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      role: 'admin',
      status: 'active',
      lastLogin: '2024-03-20T10:00:00Z'
    },
    {
      id: 2,
      username: 'user',
      email: 'user@example.com',
      role: 'user',
      status: 'active',
      lastLogin: '2024-03-19T15:00:00Z'
    }
  ]

  beforeEach(() => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/user',
          component: UserList
        },
        {
          path: '/user/profile',
          component: UserProfile
        }
      ]
    })

    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        user: {
          users: mockUsers,
          roles: ['admin', 'user', 'guest'],
          loading: false
        }
      }
    })

    wrapper = mount(UserList, {
      global: {
        plugins: [pinia, router],
        stubs: {
          'el-table': true,
          'el-form': true,
          'el-dialog': true
        }
      }
    })

    store = useUserStore()
  })

  describe('用户列表管理', () => {
    it('应该正确渲染用户列表', () => {
      const users = wrapper.findAll('[data-test="user-item"]')
      expect(users).toHaveLength(2)
    })

    it('应该能搜索用户', async () => {
      const searchInput = wrapper.find('[data-test="user-search"]')
      await searchInput.setValue('admin')
      await searchInput.trigger('input')

      expect(store.searchUsers).toHaveBeenCalledWith('admin')
    })

    it('应该能筛选用户状态', async () => {
      const statusFilter = wrapper.find('[data-test="status-filter"]')
      await statusFilter.trigger('change', 'active')

      expect(store.filterUsers).toHaveBeenCalledWith({ status: 'active' })
    })

    it('应该能创建新用户', async () => {
      const newUser = {
        username: 'newuser',
        email: 'new@example.com',
        role: 'user'
      }

      const addButton = wrapper.find('[data-test="add-user"]')
      await addButton.trigger('click')

      const form = wrapper.find('[data-test="user-form"]')
      await form.setValue(newUser)
      await form.trigger('submit')

      expect(store.createUser).toHaveBeenCalledWith(newUser)
      expect(ElMessage.success).toHaveBeenCalledWith('用户创建成功')
    })

    it('应该能删除用户', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm')
      
      const deleteButton = wrapper.find('[data-test="delete-user-1"]')
      await deleteButton.trigger('click')

      expect(store.deleteUser).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('用户已删除')
    })
  })

  describe('角色权限管理', () => {
    it('应该显示所有可用角色', () => {
      const roles = wrapper.findAll('[data-test="role-option"]')
      expect(roles).toHaveLength(3)
    })

    it('应该能修改用户角色', async () => {
      const roleSelect = wrapper.find('[data-test="user-role-1"]')
      await roleSelect.trigger('change', 'admin')

      expect(store.updateUserRole).toHaveBeenCalledWith(1, 'admin')
      expect(ElMessage.success).toHaveBeenCalledWith('角色已更新')
    })

    it('应该验证角色权限', async () => {
      store.hasPermission.mockReturnValue(false)
      
      const roleSelect = wrapper.find('[data-test="user-role-1"]')
      await roleSelect.trigger('change', 'admin')

      expect(store.updateUserRole).not.toHaveBeenCalled()
      expect(ElMessage.error).toHaveBeenCalledWith('没有权限执行此操作')
    })
  })

  describe('用户信息修改', () => {
    beforeEach(async () => {
      wrapper = mount(UserProfile, {
        global: {
          plugins: [pinia, router],
          stubs: {
            'el-form': true,
            'el-upload': true
          }
        }
      })
    })

    it('应该显示当前用户信息', () => {
      const username = wrapper.find('[data-test="profile-username"]')
      const email = wrapper.find('[data-test="profile-email"]')
      
      expect(username.element.value).toBe('admin')
      expect(email.element.value).toBe('admin@example.com')
    })

    it('应该能更新用户信息', async () => {
      const form = wrapper.find('[data-test="profile-form"]')
      await form.setValue({
        email: 'newemail@example.com'
      })
      await form.trigger('submit')

      expect(store.updateProfile).toHaveBeenCalledWith({
        email: 'newemail@example.com'
      })
      expect(ElMessage.success).toHaveBeenCalledWith('个人信息已更新')
    })

    it('应该能上传头像', async () => {
      const upload = wrapper.find('[data-test="avatar-upload"]')
      const file = new File([''], 'avatar.jpg', { type: 'image/jpeg' })
      await upload.trigger('change', { target: { files: [file] } })

      expect(store.uploadAvatar).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('头像已更新')
    })
  })

  describe('密码重置流程', () => {
    it('应该能发送重置密码邮件', async () => {
      const resetButton = wrapper.find('[data-test="reset-password"]')
      await resetButton.trigger('click')

      const emailInput = wrapper.find('[data-test="reset-email"]')
      await emailInput.setValue('user@example.com')
      await emailInput.trigger('submit')

      expect(store.sendResetEmail).toHaveBeenCalledWith('user@example.com')
      expect(ElMessage.success).toHaveBeenCalledWith('重置密码邮件已发送')
    })

    it('应该能重置密码', async () => {
      await router.push('/user/reset-password?token=test-token')
      
      const form = wrapper.find('[data-test="reset-form"]')
      await form.setValue({
        password: 'newpassword',
        confirmPassword: 'newpassword'
      })
      await form.trigger('submit')

      expect(store.resetPassword).toHaveBeenCalledWith({
        token: 'test-token',
        password: 'newpassword'
      })
      expect(ElMessage.success).toHaveBeenCalledWith('密码已重置')
    })

    it('应该验证密码强度', async () => {
      const form = wrapper.find('[data-test="reset-form"]')
      await form.setValue({
        password: 'weak',
        confirmPassword: 'weak'
      })
      await form.trigger('submit')

      expect(store.resetPassword).not.toHaveBeenCalled()
      expect(ElMessage.error).toHaveBeenCalledWith('密码强度不足')
    })
  })

  describe('错误处理', () => {
    it('应该显示加载错误', async () => {
      await wrapper.setData({ error: '加载失败' })
      
      const error = wrapper.find('[data-test="error-message"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('加载失败')
    })

    it('应该处理表单验证错误', async () => {
      const form = wrapper.find('[data-test="user-form"]')
      await form.trigger('submit')

      expect(store.createUser).not.toHaveBeenCalled()
      expect(ElMessage.error).toHaveBeenCalledWith('请填写必填字段')
    })

    it('应该处理重复用户名错误', async () => {
      store.createUser.mockRejectedValue(new Error('用户名已存在'))
      
      const form = wrapper.find('[data-test="user-form"]')
      await form.setValue({
        username: 'admin',
        email: 'test@example.com'
      })
      await form.trigger('submit')

      expect(ElMessage.error).toHaveBeenCalledWith('用户名已存在')
    })
  })
}) 