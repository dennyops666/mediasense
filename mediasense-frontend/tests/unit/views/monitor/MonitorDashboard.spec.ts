import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import MonitorDashboard from '@/views/monitor/MonitorDashboard.vue'
import { useMonitorStore } from '@/stores/monitor'
import * as monitorApi from '@/api/monitor'
import { ElMessage } from 'element-plus'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

// Mock monitor API
vi.mock('@/api/monitor', () => ({
  getSystemMetrics: vi.fn().mockResolvedValue({
    cpu: { usage: 50, cores: 4, temperature: 45 },
    memory: { total: '16.0 GB', used: '8.0 GB', usagePercentage: 50 },
    disk: { total: '500.0 GB', used: '250.0 GB', usagePercentage: 50 },
    network: { upload: '1.0 MB/s', download: '0.5 MB/s', latency: 20 }
  }),
  getAlerts: vi.fn().mockResolvedValue([
    { id: '1', message: 'CPU 使用率过高', level: 'warning', timestamp: '2024-01-01 10:00:00' },
    { id: '2', message: '内存使用率过高', level: 'error', timestamp: '2024-01-01 10:05:00' }
  ])
}))

describe('MonitorDashboard.vue', () => {
  let wrapper: any
  let store: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        monitor: {
          metrics: {
            cpu: { usage: 50, cores: 4, temperature: 45 },
            memory: { total: '16.0 GB', used: '8.0 GB', usagePercentage: 50 },
            disk: { total: '500.0 GB', used: '250.0 GB', usagePercentage: 50 },
            network: { upload: '1.0 MB/s', download: '0.5 MB/s', latency: 20 }
          },
          alerts: [],
          isMonitoring: true,
          errorMessage: null
        }
      }
    })

    wrapper = mount(MonitorDashboard, {
      global: {
        plugins: [pinia]
      }
    })

    store = useMonitorStore()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染仪表板', () => {
    expect(wrapper.exists()).toBe(true)
  })

  it('应该在挂载时开始监控', async () => {
    await vi.waitFor(() => {
      expect(store.startMonitoring).toHaveBeenCalledWith(5000)
    })
  })

  it('应该在卸载时停止监控', () => {
    wrapper.unmount()
    expect(store.stopMonitoring).toHaveBeenCalled()
  })

  describe('指标概览', () => {
    it('应该显示 CPU 使用率和温度', () => {
      const cpuMetric = wrapper.find('[data-test="cpu-metric"]')
      expect(cpuMetric.exists()).toBe(true)
      expect(cpuMetric.text()).toContain('50%')
      expect(cpuMetric.text()).toContain('4 核')
      expect(cpuMetric.text()).toContain('45°C')
    })

    it('应该显示内存使用情况和使用率', () => {
      const memoryMetric = wrapper.find('[data-test="memory-metric"]')
      expect(memoryMetric.exists()).toBe(true)
      expect(memoryMetric.text()).toContain('16.0 GB')
      expect(memoryMetric.text()).toContain('8.0 GB')
      expect(memoryMetric.text()).toContain('50%')
    })

    it('应该显示磁盘使用情况和剩余空间', () => {
      const diskMetric = wrapper.find('[data-test="disk-metric"]')
      expect(diskMetric.exists()).toBe(true)
      expect(diskMetric.text()).toContain('500.0 GB')
      expect(diskMetric.text()).toContain('250.0 GB')
      expect(diskMetric.text()).toContain('50%')
    })

    it('应该显示网络状态和延迟', () => {
      const networkMetric = wrapper.find('[data-test="network-metric"]')
      expect(networkMetric.exists()).toBe(true)
      expect(networkMetric.text()).toContain('1.0 MB/s')
      expect(networkMetric.text()).toContain('0.5 MB/s')
      expect(networkMetric.text()).toContain('20ms')
    })
  })

  describe('告警处理', () => {
    beforeEach(() => {
      store.$patch({
        alerts: [
          { id: 1, message: '告警1', level: 'error', timestamp: '2024-03-20 10:00:00' },
          { id: 2, message: '告警2', level: 'warning', timestamp: '2024-03-20 11:00:00' }
        ]
      })
    })

    it('应该显示告警列表', () => {
      const alertsCard = wrapper.find('[data-test="alerts-card"]')
      expect(alertsCard.exists()).toBe(true)
      const alerts = wrapper.findAll('[data-test="alert-item"]')
      expect(alerts).toHaveLength(2)
    })

    it('应该能确认告警', async () => {
      const alertItem = wrapper.find('[data-test="alert-item"]')
      await alertItem.find('.el-alert__closebtn').trigger('click')
      expect(store.acknowledgeAlert).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('告警已确认')
    })

    it('应该能清空告警历史', async () => {
      const clearButton = wrapper.find('[data-test="clear-alerts-btn"]')
      await clearButton.trigger('click')
      expect(store.clearAllAlerts).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('告警历史已清空')
    })
  })

  describe('错误处理', () => {
    beforeEach(() => {
      store.$patch({
        errorMessage: '获取监控数据失败'
      })
    })

    it('应该显示错误信息', () => {
      const errorMessage = wrapper.find('[data-test="error-message"]')
      expect(errorMessage.exists()).toBe(true)
      expect(errorMessage.text()).toContain('获取监控数据失败')
    })

    it('点击重试按钮应该清除错误并重新获取数据', async () => {
      const retryButton = wrapper.find('[data-test="retry-btn"]')
      await retryButton.trigger('click')
      
      expect(store.clearError).toHaveBeenCalled()
      expect(store.startMonitoring).toHaveBeenCalled()
    })
  })

  describe('监控设置', () => {
    it('应该能调整监控间隔', async () => {
      const intervalSelect = wrapper.find('[data-test="monitor-interval"]')
      await intervalSelect.setValue(10000)
      await intervalSelect.trigger('change')
      
      expect(store.stopMonitoring).toHaveBeenCalled()
      expect(store.startMonitoring).toHaveBeenCalledWith(10000)
      expect(ElMessage.success).toHaveBeenCalledWith('监控间隔已更新')
    })

    it('应该显示当前监控状态', () => {
      const status = wrapper.find('[data-test="monitor-status"]')
      expect(status.exists()).toBe(true)
      expect(status.text()).toBe('监控中')
    })
  })

  describe('数据导出', () => {
    it('应该能导出监控数据', async () => {
      const exportButton = wrapper.find('[data-test="export-btn"]')
      await exportButton.trigger('click')
      expect(store.exportMonitoringData).toHaveBeenCalled()
    })
  })
})

