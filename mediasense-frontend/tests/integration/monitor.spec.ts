import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import MonitorDashboard from '@/views/monitor/MonitorDashboard.vue'
import { useMonitorStore } from '@/stores/monitor'
import { ElMessage } from 'element-plus'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

describe('监控系统集成测试', () => {
  let router: any
  let store: any

  beforeEach(() => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/monitor',
          name: 'Monitor',
          component: MonitorDashboard
        }
      ]
    })

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
          alerts: [
            { id: '1', message: 'CPU使用率过高', level: 'warning', timestamp: '2024-03-20T10:00:00Z', source: 'system' }
          ],
          processes: [
            { pid: 1234, name: 'node', cpu: 2.5, memory: 150.5, status: 'running', startTime: '2024-03-20T10:00:00Z' }
          ],
          loading: false,
          error: null
        }
      }
    })

    store = useMonitorStore()
  })

  describe('系统指标监控', () => {
    it('应该正确显示系统资源使用情况', async () => {
      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      expect(wrapper.find('[data-test="cpu-usage"]').text()).toContain('50%')
      expect(wrapper.find('[data-test="memory-usage"]').text()).toContain('8.0 GB / 16.0 GB')
      expect(wrapper.find('[data-test="disk-usage"]').text()).toContain('250.0 GB / 500.0 GB')
      expect(wrapper.find('[data-test="network-status"]').text()).toContain('1.0 MB/s')
    })

    it('应该定期刷新监控数据', async () => {
      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      await wrapper.vm.$nextTick()
      expect(store.startMonitoring).toHaveBeenCalled()
      
      wrapper.unmount()
      expect(store.stopMonitoring).toHaveBeenCalled()
    })
  })

  describe('告警管理', () => {
    it('应该显示告警列表', async () => {
      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      const alerts = wrapper.findAll('[data-test="alert-item"]')
      expect(alerts).toHaveLength(1)
      expect(alerts[0].text()).toContain('CPU使用率过高')
    })

    it('应该能确认告警', async () => {
      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      const ackButton = wrapper.find('[data-test="ack-alert-1"]')
      await ackButton.trigger('click')

      expect(store.handleAcknowledgeAlert).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('已确认告警')
    })

    it('应该能清空所有告警', async () => {
      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      const clearButton = wrapper.find('[data-test="clear-alerts"]')
      await clearButton.trigger('click')

      expect(store.clearAllAlerts).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('已清空所有告警')
    })
  })

  describe('进程管理', () => {
    it('应该显示进程列表', async () => {
      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      const processes = wrapper.findAll('[data-test="process-item"]')
      expect(processes).toHaveLength(1)
      expect(processes[0].text()).toContain('node')
    })

    it('应该能终止进程', async () => {
      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      const killButton = wrapper.find('[data-test="kill-process-1234"]')
      await killButton.trigger('click')

      expect(store.killProcess).toHaveBeenCalledWith(1234)
      expect(ElMessage.success).toHaveBeenCalledWith('已终止进程')
    })

    it('应该能按资源使用率排序进程', async () => {
      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      const cpuSort = wrapper.find('[data-test="cpu-sort"]')
      await cpuSort.trigger('click')

      expect(wrapper.vm.sortBy).toBe('cpu')
      expect(wrapper.vm.sortOrder).toBe('descending')
    })
  })

  describe('错误处理', () => {
    it('应该显示加载错误', async () => {
      store.$patch({ error: '获取监控数据失败' })

      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      const error = wrapper.find('[data-test="error-message"]')
      expect(error.exists()).toBe(true)
      expect(error.text()).toContain('获取监控数据失败')
    })

    it('应该能重试加载', async () => {
      store.$patch({ error: '获取监控数据失败' })

      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      const retryButton = wrapper.find('[data-test="retry-button"]')
      await retryButton.trigger('click')

      expect(store.fetchSystemMetrics).toHaveBeenCalled()
    })
  })

  describe('监控设置', () => {
    it('应该能调整监控间隔', async () => {
      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      const intervalSelect = wrapper.find('[data-test="monitor-interval"]')
      await intervalSelect.setValue(10000)
      await intervalSelect.trigger('change')

      expect(store.stopMonitoring).toHaveBeenCalled()
      expect(store.startMonitoring).toHaveBeenCalledWith(10000)
      expect(ElMessage.success).toHaveBeenCalledWith('监控间隔已更新')
    })
  })

  describe('数据导出', () => {
    it('应该能导出监控数据', async () => {
      const wrapper = mount(MonitorDashboard, {
        global: {
          plugins: [router, pinia]
        }
      })

      const exportButton = wrapper.find('[data-test="export-data"]')
      await exportButton.trigger('click')

      expect(store.exportMonitoringData).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('数据导出成功')
    })
  })
}) 