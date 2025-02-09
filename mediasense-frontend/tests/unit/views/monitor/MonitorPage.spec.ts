import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import MonitorPage from '@/views/monitor/MonitorPage.vue'
import { useMonitorStore } from '@/stores/monitor'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { nextTick } from 'vue'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

describe('MonitorPage.vue', () => {
  let wrapper: any
  let monitorStore: any
  let userStore: any

  const mockUser = {
    id: 1,
    username: 'admin',
    role: 'admin',
    permissions: ['monitor:view', 'monitor:manage']
  }

  const mockMonitorConfig = {
    refreshInterval: 5000,
    alertThresholds: {
      cpu: 80,
      memory: 80,
      disk: 90
    },
    enabledMetrics: ['cpu', 'memory', 'disk', 'network'],
    retentionDays: 30
  }

  beforeEach(async () => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      stubActions: false
    })

    monitorStore = useMonitorStore()
    userStore = useUserStore()

    // 模拟 store 方法
    monitorStore.fetchMonitorConfig = vi.fn().mockResolvedValue(mockMonitorConfig)
    monitorStore.updateMonitorConfig = vi.fn().mockResolvedValue(mockMonitorConfig)
    monitorStore.startMonitoring = vi.fn()
    monitorStore.stopMonitoring = vi.fn()
    monitorStore.clearHistoricalData = vi.fn()

    // 设置初始状态
    monitorStore.$patch({
      config: { ...mockMonitorConfig },
      loading: false,
      error: null
    })

    userStore.$patch({
      currentUser: { ...mockUser }
    })

    wrapper = mount(MonitorPage, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-container': true,
          'el-header': true,
          'el-main': true,
          'el-aside': true,
          'el-menu': true,
          'el-menu-item': true,
          'el-submenu': true,
          'el-card': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-input-number': true,
          'el-select': true,
          'el-option': true,
          'el-switch': true,
          'el-button': true,
          'el-alert': true,
          'el-tabs': true,
          'el-tab-pane': true,
          'router-view': true
        }
      }
    })

    await nextTick()
  })

  it('应该正确渲染监控页面', () => {
    expect(wrapper.find('[data-test="monitor-page"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="monitor-header"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="monitor-menu"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="monitor-content"]').exists()).toBe(true)
  })

  it('应该在挂载时加载监控配置', () => {
    expect(monitorStore.fetchMonitorConfig).toHaveBeenCalled()
  })

  describe('权限控制', () => {
    it('应该根据用户权限显示管理选项', () => {
      const manageOptions = wrapper.find('[data-test="manage-options"]')
      expect(manageOptions.exists()).toBe(true)
    })

    it('应该在没有管理权限时隐藏管理选项', async () => {
      userStore.$patch({
        currentUser: {
          ...mockUser,
          permissions: ['monitor:view']
        }
      })
      await nextTick()

      const manageOptions = wrapper.find('[data-test="manage-options"]')
      expect(manageOptions.exists()).toBe(false)
    })
  })

  describe('监控配置', () => {
    it('应该显示当前监控配置', () => {
      const configForm = wrapper.find('[data-test="config-form"]')
      expect(configForm.exists()).toBe(true)

      const refreshInterval = wrapper.find('[data-test="refresh-interval"]')
      const cpuThreshold = wrapper.find('[data-test="cpu-threshold"]')
      const retentionDays = wrapper.find('[data-test="retention-days"]')

      expect(refreshInterval.element.value).toBe('5000')
      expect(cpuThreshold.element.value).toBe('80')
      expect(retentionDays.element.value).toBe('30')
    })

    it('应该能更新监控配置', async () => {
      const newConfig = {
        ...mockMonitorConfig,
        refreshInterval: 10000,
        alertThresholds: {
          ...mockMonitorConfig.alertThresholds,
          cpu: 90
        }
      }

      const refreshInterval = wrapper.find('[data-test="refresh-interval"]')
      const cpuThreshold = wrapper.find('[data-test="cpu-threshold"]')

      await refreshInterval.setValue(10000)
      await cpuThreshold.setValue(90)

      const saveButton = wrapper.find('[data-test="save-config"]')
      await saveButton.trigger('click')

      expect(monitorStore.updateMonitorConfig).toHaveBeenCalledWith(expect.objectContaining({
        refreshInterval: 10000,
        alertThresholds: expect.objectContaining({
          cpu: 90
        })
      }))
      expect(ElMessage.success).toHaveBeenCalledWith('监控配置已更新')
    })

    it('应该验证配置输入', async () => {
      const refreshInterval = wrapper.find('[data-test="refresh-interval"]')
      await refreshInterval.setValue(0) // 无效值

      const saveButton = wrapper.find('[data-test="save-config"]')
      await saveButton.trigger('click')

      expect(wrapper.find('[data-test="validation-error"]').exists()).toBe(true)
      expect(monitorStore.updateMonitorConfig).not.toHaveBeenCalled()
    })
  })

  describe('数据管理', () => {
    it('应该能清空历史数据', async () => {
      const clearButton = wrapper.find('[data-test="clear-history"]')
      expect(clearButton.exists()).toBe(true)

      await clearButton.trigger('click')
      
      // 确认对话框
      const confirmButton = wrapper.find('[data-test="confirm-clear"]')
      await confirmButton.trigger('click')

      expect(monitorStore.clearHistoricalData).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('历史数据已清空')
    })

    it('应该显示数据统计信息', () => {
      const statsSection = wrapper.find('[data-test="data-stats"]')
      expect(statsSection.exists()).toBe(true)
      expect(statsSection.text()).toContain('30 天')
    })
  })

  describe('监控状态', () => {
    it('应该显示当前监控状态', () => {
      const status = wrapper.find('[data-test="monitor-status"]')
      expect(status.exists()).toBe(true)
      expect(status.text()).toContain('监控中')
    })

    it('应该能暂停和恢复监控', async () => {
      const toggleButton = wrapper.find('[data-test="toggle-monitoring"]')
      expect(toggleButton.exists()).toBe(true)

      // 暂停监控
      await toggleButton.trigger('click')
      expect(monitorStore.stopMonitoring).toHaveBeenCalled()
      expect(toggleButton.text()).toContain('恢复监控')

      // 恢复监控
      await toggleButton.trigger('click')
      expect(monitorStore.startMonitoring).toHaveBeenCalledWith(5000)
      expect(toggleButton.text()).toContain('暂停监控')
    })
  })

  describe('错误处理', () => {
    it('应该显示配置加载错误', async () => {
      const error = new Error('加载监控配置失败')
      monitorStore.fetchMonitorConfig.mockRejectedValueOnce(error)
      await wrapper.vm.loadConfig()

      const errorMessage = wrapper.find('[data-test="error-message"]')
      expect(errorMessage.exists()).toBe(true)
      expect(errorMessage.text()).toContain('加载监控配置失败')
    })

    it('应该显示配置更新错误', async () => {
      const error = new Error('更新监控配置失败')
      monitorStore.updateMonitorConfig.mockRejectedValueOnce(error)

      const saveButton = wrapper.find('[data-test="save-config"]')
      await saveButton.trigger('click')

      const errorMessage = wrapper.find('[data-test="error-message"]')
      expect(errorMessage.exists()).toBe(true)
      expect(errorMessage.text()).toContain('更新监控配置失败')
    })
  })
})
