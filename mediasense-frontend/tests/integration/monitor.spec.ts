import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createTestingPinia } from '@pinia/testing'
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import SystemMonitor from '../../src/views/monitor/SystemMonitor.vue'
import { useMonitorStore } from '../../src/stores/monitor'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 模拟 Element Plus 消息组件
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn()
  }
}))

// 模拟监控 API
vi.mock('../../src/api/monitor', () => ({
  getSystemMetrics: vi.fn().mockResolvedValue({
    cpu: {
      usage: 45.5,
      cores: 8,
      temperature: 65
    },
    memory: {
      total: 16384,
      used: 8192,
      free: 8192
    },
    disk: {
      total: 1024000,
      used: 512000,
      free: 512000
    },
    network: {
      rx_bytes: 1024000,
      tx_bytes: 512000,
      connections: 100
    }
  }),
  getServiceStatus: vi.fn().mockResolvedValue([
    {
      name: 'nginx',
      status: 'stopped',
      uptime: '0',
      lastCheck: '2024-03-20T10:00:00Z'
    }
  ]),
  getAlerts: vi.fn().mockResolvedValue([
    {
      id: '1',
      type: 'cpu',
      level: 'warning',
      message: 'CPU使用率过高',
      timestamp: '2024-03-20T10:00:00Z'
    }
  ]),
  restartService: vi.fn().mockResolvedValue({ success: true, message: '服务已重启' }),
  acknowledgeAlert: vi.fn().mockResolvedValue({ success: true, message: '告警已确认' })
}))

describe('系统监控流程集成测试', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/',
        name: 'monitor',
        component: SystemMonitor
      }
    ]
  })

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    router.push('/')
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const mountComponent = async () => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        monitor: {
          metrics: {
            cpu: {
              usage: 45.5,
              cores: 4,
              temperature: 50
            },
            memory: {
              total: 16384,
              used: 8192,
              free: 8192
            },
            disk: {
              total: 1024000,
              used: 512000,
              free: 512000
            },
            network: {
              rx_bytes: 1024,
              tx_bytes: 2048,
              connections: 100
            }
          },
          services: [
            {
              name: 'nginx',
              status: 'stopped',
              uptime: '0',
              lastCheck: '2024-03-20T10:00:00Z'
            }
          ],
          alerts: [
            {
              id: '1',
              type: 'cpu',
              level: 'warning',
              message: 'CPU使用率过高',
              timestamp: '2024-03-20T10:00:00Z'
            }
          ]
        }
      },
      stubActions: false
    })

    const wrapper = mount(SystemMonitor, {
      global: {
        plugins: [pinia, router],
        components: {
          ...ElementPlusIconsVue
        },
        stubs: {
          'el-card': {
            template: '<div><slot name="header" /><slot /></div>'
          },
          'el-button': {
            template: '<button><slot /></button>'
          },
          'el-table': {
            template: '<div><slot /></div>'
          },
          'el-table-column': {
            template: '<div><slot /></div>'
          },
          'v-chart': true,
          'el-icon': {
            template: '<div><slot /></div>'
          },
          'el-tag': {
            template: '<span><slot /></span>'
          }
        }
      }
    })

    await router.isReady()
    await nextTick()
    return wrapper
  }

  describe('系统资源监控', () => {
    it('应该正确显示系统资源使用情况', async () => {
      const wrapper = await mountComponent()
      
      // 验证 CPU 使用率显示
      const cpuUsage = wrapper.find('[data-test="cpu-usage"]')
      expect(cpuUsage.exists()).toBe(true)
      expect(cpuUsage.text()).toContain('45.5%')
      
      // 验证内存使用率显示
      const memoryUsage = wrapper.find('[data-test="memory-usage"]')
      expect(memoryUsage.exists()).toBe(true)
      expect(memoryUsage.text()).toContain('50.0%')
      
      // 验证磁盘使用率显示
      const diskUsage = wrapper.find('[data-test="disk-usage"]')
      expect(diskUsage.exists()).toBe(true)
      expect(diskUsage.text()).toContain('50.0%')
    })

    it('应该定期更新系统指标', async () => {
      const wrapper = await mountComponent()
      const store = useMonitorStore()
      
      await vi.advanceTimersByTime(60000) // 前进1分钟
      
      expect(store.fetchSystemMetrics).toHaveBeenCalled()
    })

    it('应该处理指标获取失败的情况', async () => {
      const wrapper = await mountComponent()
      const store = useMonitorStore()
      
      // 模拟获取指标失败
      store.fetchSystemMetrics = vi.fn().mockRejectedValue(new Error('获取系统指标失败'))
      
      // 手动调用 fetchMetrics 方法
      await (wrapper.vm as any).fetchMetrics()
      
      expect(ElMessage.error).toHaveBeenCalledWith('获取系统指标失败')
    })

    it('应该正确显示网络 I/O 信息', async () => {
      const wrapper = await mountComponent()
      const store = useMonitorStore()
      
      // 设置网络指标
      store.$patch({
        metrics: {
          ...store.metrics,
          network: {
            rx_bytes: 0,
            tx_bytes: 0,
            connections: 100
          }
        }
      })
      
      await nextTick()
      
      const networkRx = wrapper.find('[data-test="network-rx"]')
      const networkTx = wrapper.find('[data-test="network-tx"]')
      
      expect(networkRx.exists()).toBe(true)
      expect(networkTx.exists()).toBe(true)
      expect(networkRx.text()).toContain('0MB/s')
      expect(networkTx.text()).toContain('0MB/s')
    })
  })

  describe('服务状态监控', () => {
    it('应该正确显示服务状态', async () => {
      const wrapper = await mountComponent()
      
      const serviceRow = wrapper.find('[data-test="service-nginx"]')
      expect(serviceRow.exists()).toBe(true)
      expect(serviceRow.text()).toContain('nginx')
      expect(serviceRow.text()).toContain('stopped')
    })

    it('应该正确处理服务重启操作', async () => {
      const wrapper = await mountComponent()
      const store = useMonitorStore()
      
      // 手动设置 store 方法
      store.restartService = vi.fn().mockResolvedValue({ success: true, message: '服务已重启' })
      
      const restartBtn = wrapper.find('[data-test="restart-service-btn"]')
      expect(restartBtn.exists()).toBe(true)
      await restartBtn.trigger('click')
      
      expect(store.restartService).toHaveBeenCalledWith('nginx')
      expect(ElMessage.success).toHaveBeenCalledWith('服务已重启')
    })

    it('应该处理服务重启失败的情况', async () => {
      const wrapper = await mountComponent()
      const store = useMonitorStore()
      
      // 模拟重启服务失败
      store.restartService = vi.fn().mockRejectedValue(new Error('重启服务失败'))
      
      const restartBtn = wrapper.find('[data-test="restart-service-btn"]')
      await restartBtn.trigger('click')
      
      expect(ElMessage.error).toHaveBeenCalledWith('重启服务失败')
    })

    it('应该在服务运行时禁用重启按钮', async () => {
      const wrapper = await mountComponent()
      const store = useMonitorStore()
      
      // 设置服务状态为运行中
      store.$patch({
        services: [
          {
            name: 'nginx',
            status: 'running',
            uptime: '1d 2h 30m',
            lastCheck: '2024-03-20T10:00:00Z'
          }
        ]
      })
      
      await nextTick()
      
      const restartBtn = wrapper.find('[data-test="restart-service-btn"]')
      expect(restartBtn.exists()).toBe(false)
    })
  })

  describe('告警管理', () => {
    it('应该正确显示告警信息', async () => {
      const wrapper = await mountComponent()
      
      const alertRow = wrapper.find('[data-test="alert-1"]')
      expect(alertRow.exists()).toBe(true)
      expect(alertRow.text()).toContain('CPU使用率过高')
    })

    it('应该正确处理告警确认操作', async () => {
      const wrapper = await mountComponent()
      const store = useMonitorStore()
      
      // 手动设置 store 方法
      store.acknowledgeAlert = vi.fn().mockResolvedValue({ success: true, message: '告警已确认' })
      
      const acknowledgeBtn = wrapper.find('[data-test="acknowledge-alert-btn"]')
      expect(acknowledgeBtn.exists()).toBe(true)
      await acknowledgeBtn.trigger('click')
      
      expect(store.acknowledgeAlert).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('告警已确认')
    })

    it('应该处理告警确认失败的情况', async () => {
      const wrapper = await mountComponent()
      const store = useMonitorStore()
      
      // 模拟确认告警失败
      store.acknowledgeAlert = vi.fn().mockRejectedValue(new Error('确认告警失败'))
      
      const acknowledgeBtn = wrapper.find('[data-test="acknowledge-alert-btn"]')
      expect(acknowledgeBtn.exists()).toBe(true)
      await acknowledgeBtn.trigger('click')
      
      expect(ElMessage.error).toHaveBeenCalledWith('确认告警失败')
    })

    it('应该根据告警级别显示不同的标签样式', async () => {
      const wrapper = await mountComponent()
      const store = useMonitorStore()
      
      // 设置不同级别的告警
      store.$patch({
        alerts: [
          {
            id: '1',
            type: 'cpu',
            level: 'critical',
            message: 'CPU使用率严重超标',
            timestamp: '2024-03-20T10:00:00Z'
          },
          {
            id: '2',
            type: 'memory',
            level: 'warning',
            message: '内存使用率过高',
            timestamp: '2024-03-20T10:00:00Z'
          },
          {
            id: '3',
            type: 'disk',
            level: 'info',
            message: '磁盘使用率正常',
            timestamp: '2024-03-20T10:00:00Z'
          }
        ]
      })
      
      await nextTick()
      
      const criticalAlert = wrapper.find('[data-test="alert-1"] .alert-level')
      const warningAlert = wrapper.find('[data-test="alert-2"] .alert-level')
      const infoAlert = wrapper.find('[data-test="alert-3"] .alert-level')
      
      expect(criticalAlert.exists()).toBe(true)
      expect(warningAlert.exists()).toBe(true)
      expect(infoAlert.exists()).toBe(true)
      
      expect(criticalAlert.text()).toBe('critical')
      expect(warningAlert.text()).toBe('warning')
      expect(infoAlert.text()).toBe('info')
    })
  })

  describe('组件生命周期', () => {
    it('应该在组件卸载时清理定时器', async () => {
      const wrapper = await mountComponent()
      const store = useMonitorStore()
      
      // 记录初始调用次数
      const initialCalls = store.fetchSystemMetrics.mock.calls.length
      
      // 卸载组件
      wrapper.unmount()
      
      // 前进时间
      await vi.advanceTimersByTime(60000)
      
      // 验证没有新的调用
      expect(store.fetchSystemMetrics.mock.calls.length).toBe(initialCalls)
    })
  })
}) 