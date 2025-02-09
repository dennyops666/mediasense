import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import Settings from '@/views/settings/Settings.vue'
import { useSettingsStore } from '@/stores/settings'
import { ElMessage } from 'element-plus'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

describe('系统设置集成测试', () => {
  let router: any
  let store: any
  let wrapper: any

  beforeEach(() => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/settings',
          component: Settings
        }
      ]
    })

    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        settings: {
          theme: 'light',
          language: 'zh-CN',
          autoRefresh: true,
          refreshInterval: 30,
          pageSize: 20,
          loading: false
        }
      }
    })

    wrapper = mount(Settings, {
      global: {
        plugins: [pinia, router],
        stubs: {
          'el-card': true,
          'el-form': true,
          'el-switch': true,
          'el-select': true
        }
      }
    })

    store = useSettingsStore()
  })

  describe('系统参数配置', () => {
    it('应该显示当前系统参数', () => {
      const refreshInterval = wrapper.find('[data-test="refresh-interval"]')
      const pageSize = wrapper.find('[data-test="page-size"]')
      
      expect(refreshInterval.element.value).toBe('30')
      expect(pageSize.element.value).toBe('20')
    })

    it('应该能修改自动刷新间隔', async () => {
      const intervalInput = wrapper.find('[data-test="refresh-interval"]')
      await intervalInput.setValue(60)
      await intervalInput.trigger('change')

      expect(store.updateSettings).toHaveBeenCalledWith({
        refreshInterval: 60
      })
      expect(ElMessage.success).toHaveBeenCalledWith('设置已更新')
    })

    it('应该能修改每页显示数量', async () => {
      const pageSizeInput = wrapper.find('[data-test="page-size"]')
      await pageSizeInput.setValue(50)
      await pageSizeInput.trigger('change')

      expect(store.updateSettings).toHaveBeenCalledWith({
        pageSize: 50
      })
    })

    it('应该验证参数输入范围', async () => {
      const intervalInput = wrapper.find('[data-test="refresh-interval"]')
      await intervalInput.setValue(0)
      await intervalInput.trigger('change')

      expect(store.updateSettings).not.toHaveBeenCalled()
      expect(ElMessage.error).toHaveBeenCalledWith('刷新间隔必须大于0')
    })
  })

  describe('用户偏好设置', () => {
    it('应该能切换自动刷新', async () => {
      const autoRefreshSwitch = wrapper.find('[data-test="auto-refresh"]')
      await autoRefreshSwitch.trigger('click')

      expect(store.updateSettings).toHaveBeenCalledWith({
        autoRefresh: false
      })
    })

    it('应该能设置默认视图', async () => {
      const viewSelect = wrapper.find('[data-test="default-view"]')
      await viewSelect.trigger('change', 'table')

      expect(store.updateSettings).toHaveBeenCalledWith({
        defaultView: 'table'
      })
    })

    it('应该能保存用户偏好', async () => {
      const saveButton = wrapper.find('[data-test="save-preferences"]')
      await saveButton.trigger('click')

      expect(store.savePreferences).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('偏好设置已保存')
    })
  })

  describe('主题切换', () => {
    it('应该能切换明暗主题', async () => {
      const themeSwitch = wrapper.find('[data-test="theme-switch"]')
      await themeSwitch.trigger('click')

      expect(store.updateSettings).toHaveBeenCalledWith({
        theme: 'dark'
      })
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })

    it('应该能自定义主题色', async () => {
      const colorPicker = wrapper.find('[data-test="theme-color"]')
      await colorPicker.trigger('change', '#1890ff')

      expect(store.updateSettings).toHaveBeenCalledWith({
        primaryColor: '#1890ff'
      })
    })

    it('应该能预览主题效果', async () => {
      const previewButton = wrapper.find('[data-test="theme-preview"]')
      await previewButton.trigger('click')

      const preview = wrapper.find('[data-test="theme-preview-dialog"]')
      expect(preview.exists()).toBe(true)
      expect(preview.isVisible()).toBe(true)
    })
  })

  describe('语言切换', () => {
    it('应该能切换系统语言', async () => {
      const languageSelect = wrapper.find('[data-test="language-select"]')
      await languageSelect.trigger('change', 'en-US')

      expect(store.updateSettings).toHaveBeenCalledWith({
        language: 'en-US'
      })
      expect(ElMessage.success).toHaveBeenCalledWith('Language changed')
    })

    it('应该正确显示切换后的语言', async () => {
      await store.updateSettings({ language: 'en-US' })
      
      const title = wrapper.find('[data-test="settings-title"]')
      expect(title.text()).toBe('System Settings')
    })

    it('应该保存语言偏好', async () => {
      const languageSelect = wrapper.find('[data-test="language-select"]')
      await languageSelect.trigger('change', 'en-US')

      expect(localStorage.getItem('language')).toBe('en-US')
    })
  })

  describe('错误处理', () => {
    it('应该显示设置更新错误', async () => {
      store.updateSettings.mockRejectedValue(new Error('更新失败'))
      
      const intervalInput = wrapper.find('[data-test="refresh-interval"]')
      await intervalInput.setValue(60)
      await intervalInput.trigger('change')

      expect(ElMessage.error).toHaveBeenCalledWith('更新失败')
    })

    it('应该能重置设置', async () => {
      const resetButton = wrapper.find('[data-test="reset-settings"]')
      await resetButton.trigger('click')

      expect(store.resetSettings).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('设置已重置')
    })
  })
}) 