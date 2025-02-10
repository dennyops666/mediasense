import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { ElMessage, ElMessageBox } from 'element-plus'
import MonitorDashboard from '@/views/monitor/MonitorDashboard.vue'
import { useMonitorStore } from '@/stores/monitor'

const mockMetrics = {
  cpu: {
    usage: 50,
    cores: 4,
    temperature: 45
  },
  memory: {
    total: 16.0,
    used: 8.0,
    usage: 50
  },
  disk: {
    total: 500.0,
    used: 250.0,
    usage: 50
  }
}

const mockAlerts = [
  {
    id: '1',
    type: 'warning',
    message: 'CPU 使用率超过 80%',
    timestamp: '2024-03-20 12:00:00'
  }
]

describe('MonitorDashboard 组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const createWrapper = () => {
    return mount(MonitorDashboard, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              monitor: {
                metrics: mockMetrics,
                alerts: mockAlerts,
                loading: false,
                error: null
              }
            }
          })
        ],
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-alert': true,
          'el-select': true,
          'el-option': true
        }
      }
    })
  }

  describe('指标概览', () => {
    it('应该显示 CPU 使用率和温度', () => {
      const wrapper = createWrapper()
      const cpuMetric = wrapper.find('[data-test="cpu-metric"]')
      expect(cpuMetric.exists()).toBe(true)
      expect(cpuMetric.text()).toContain('50%')
      expect(cpuMetric.text()).toContain('4 核')
      expect(cpuMetric.text()).toContain('45°C')
    })

    it('应该显示内存使用情况和使用率', () => {
      const wrapper = createWrapper()
      const memoryMetric = wrapper.find('[data-test="memory-metric"]')
      expect(memoryMetric.exists()).toBe(true)
      expect(memoryMetric.text()).toContain('16.0 GB')
      expect(memoryMetric.text()).toContain('8.0 GB')
      expect(memoryMetric.text()).toContain('50%')
    })

    it('应该显示磁盘使用情况和剩余空间', () => {
      const wrapper = createWrapper()
      const diskMetric = wrapper.find('[data-test="disk-metric"]')
      expect(diskMetric.exists()).toBe(true)
      expect(diskMetric.text()).toContain('500.0 GB')
      expect(diskMetric.text()).toContain('250.0 GB')
      expect(diskMetric.text()).toContain('50%')
    })
  })

  describe('告警处理', () => {
    it('应该显示告警列表', () => {
      const wrapper = createWrapper()
      const alerts = wrapper.findAll('[data-test="alert-item"]')
      expect(alerts).toHaveLength(1)
      expect(alerts[0].text()).toContain('CPU 使用率超过 80%')
    })

    it('应该能确认告警', async () => {
      const wrapper = createWrapper()
      const store = useMonitorStore()
      const confirmButton = wrapper.find('[data-test="confirm-alert"]')
      await confirmButton.trigger('click')

      expect(store.confirmAlert).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('告警已确认')
    })

    it('应该能清空告警历史', async () => {
      const wrapper = createWrapper()
      const store = useMonitorStore()
      const clearButton = wrapper.find('[data-test="clear-alerts"]')
      await clearButton.trigger('click')

      expect(store.clearAlerts).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('告警历史已清空')
    })
  })

  describe('错误处理', () => {
    it('应该显示错误信息', () => {
      const wrapper = createWrapper()
      const store = useMonitorStore()
      store.$patch({ error: '获取监控数据失败' })

      const errorMessage = wrapper.find('[data-test="error-message"]')
      expect(errorMessage.exists()).toBe(true)
      expect(errorMessage.text()).toContain('获取监控数据失败')
    })

    it('点击重试按钮应该清除错误并重新获取数据', async () => {
      const wrapper = createWrapper()
      const store = useMonitorStore()
      store.$patch({ error: '获取监控数据失败' })

      const retryButton = wrapper.find('[data-test="retry-button"]')
      await retryButton.trigger('click')

      expect(store.error).toBe(null)
      expect(store.fetchMetrics).toHaveBeenCalled()
    })
  })

  describe('监控设置', () => {
    it('应该能调整监控间隔', async () => {
      const wrapper = createWrapper()
      const store = useMonitorStore()
      const intervalSelect = wrapper.find('[data-test="interval-select"]')
      await intervalSelect.setValue(60)

      expect(store.setInterval).toHaveBeenCalledWith(60)
      expect(ElMessage.success).toHaveBeenCalledWith('监控间隔已更新')
    })
  })
}) 