import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import SystemResourceMonitor from '../../../../src/components/monitor/SystemResourceMonitor.vue'
import { useMonitorStore } from '../../../../src/stores/monitor'
import type { SystemMetrics } from '../../../../src/types/monitor'
import { createPinia, setActivePinia } from 'pinia'
import { createTestingPinia } from '@pinia/testing'
import { nextTick } from 'vue'
import { ElMessage } from 'element-plus'

// Mock element-plus
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn()
  }
}))

// Mock element-plus icons
vi.mock('@element-plus/icons-vue', () => ({
  Monitor: {
    template: '<span>Monitor</span>'
  },
  Connection: {
    template: '<span>Connection</span>'
  },
  Files: {
    template: '<span>Files</span>'
  },
  Cpu: {
    template: '<span>Cpu</span>'
  }
}))

// Mock monitor API
vi.mock('../../../../src/api/monitor', () => ({
  getSystemMetrics: vi.fn().mockResolvedValue({
    cpu: {
      usage: 50,
      cores: 4,
      temperature: 60
    },
    memory: {
      total: '16 GB',
      used: '8 GB',
      usagePercentage: 50
    },
    disk: {
      total: '1000 GB',
      used: '500 GB',
      usagePercentage: 50
    },
    network: {
      upload: '1 MB/s',
      download: '0.5 MB/s',
      latency: 50
    }
  })
}))

// Mock echarts
vi.mock('echarts/core', () => ({
  use: vi.fn(),
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn()
  }))
}))

vi.mock('echarts/renderers', () => ({
  CanvasRenderer: vi.fn()
}))

vi.mock('echarts/charts', () => ({
  LineChart: vi.fn()
}))

vi.mock('echarts/components', () => ({
  GridComponent: vi.fn(),
  TooltipComponent: vi.fn(),
  LegendComponent: vi.fn()
}))

vi.mock('vue-echarts', () => ({
  default: {
    template: '<div class="v-chart"></div>',
    props: ['option']
  }
}))

// 创建一个模拟的资源数据
const mockResources: SystemMetrics = {
  cpu: {
    usage: 45.5,
    cores: 4,
    temperature: 65
  },
  memory: {
    total: '16 GB',
    used: '8 GB',
    usagePercentage: 50
  },
  disk: {
    total: '1000 GB',
    used: '500 GB',
    usagePercentage: 50
  },
  network: {
    upload: '1 MB/s',
    download: '0.5 MB/s',
    latency: 50
  }
}

describe('SystemResourceMonitor', () => {
  let wrapper: any
  let store: any

  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    store = useMonitorStore()

    // Mock store methods
    store.fetchSystemMetrics = vi.fn().mockResolvedValue()
    store.fetchServiceStatus = vi.fn().mockResolvedValue()
    store.fetchAlerts = vi.fn().mockResolvedValue()
    store.acknowledgeAlert = vi.fn().mockResolvedValue()
    store.restartService = vi.fn().mockResolvedValue()

    // Mock store state
    vi.spyOn(store, 'metrics', 'get').mockReturnValue({
      cpu: {
        usage: 45.5,
        cores: 4,
        temperature: 65
      },
      memory: {
        total: '16 GB',
        used: '8 GB',
        usagePercentage: 50
      },
      disk: {
        total: '1000 GB',
        used: '500 GB',
        usagePercentage: 50
      },
      network: {
        rx_bytes: 512000,
        tx_bytes: 1024000,
        connections: 100
      }
    })

    vi.spyOn(store, 'services', 'get').mockReturnValue([
      {
        name: 'nginx',
        status: 'running',
        uptime: '10d 5h',
        lastCheck: new Date().toISOString()
      },
      {
        name: 'mysql',
        status: 'stopped',
        uptime: '0',
        lastCheck: new Date().toISOString()
      }
    ])

    vi.spyOn(store, 'alerts', 'get').mockReturnValue([
      {
        id: 1,
        level: 'warning',
        message: 'CPU使用率超过80%',
        timestamp: new Date().toISOString(),
        source: 'system'
      }
    ])

    wrapper = mount(SystemResourceMonitor, {
      global: {
        plugins: [createTestingPinia({
          initialState: {
            monitor: {
              loading: false,
              alerts: [
                { id: 1, level: 'warning', message: '内存使用率超过 80%' }
              ],
              cpuHistory: [
                { timestamp: '2024-01-01 10:00:00', value: 40 },
                { timestamp: '2024-01-01 10:01:00', value: 45 }
              ],
              resources: mockResources
            }
          },
          stubActions: false
        )],
        stubs: {
          'el-card': {
            template: '<div class="el-card"><div class="el-card__header" v-if="$slots.header"><slot name="header" /></div><div class="el-card__body"><slot /></div></div>'
          },
          'el-alert': {
            template: '<div class="el-alert" :class="type" :data-test="$attrs[\'data-test\']"><slot /></div>',
            props: ['type']
          },
          'el-button': {
            template: '<button class="el-button" :disabled="disabled"><slot /></button>',
            props: ['disabled']
          },
          'el-dialog': {
            template: '<div class="el-dialog" v-if="modelValue"><slot /><slot name="footer" /></div>',
            props: ['modelValue']
          },
          'el-table': {
            template: '<div class="el-table"><slot /></div>'
          },
          'el-table-column': {
            template: '<div class="el-table-column"><slot /></div>'
          },
          'el-tag': {
            template: '<span class="el-tag" :type="type"><slot /></span>',
            props: ['type']
          },
          'el-empty': {
            template: '<div class="el-empty"><slot /></div>'
          },
          'el-icon': {
            template: '<i class="el-icon"><slot /></i>'
          },
          'v-chart': {
            template: '<div class="echarts"></div>',
            props: ['option']
          }
        }
      }
    })
  })

  it('应该正确挂载组件', () => {
    expect(wrapper.exists()).toBe(true)
  })

  it('应该在挂载时获取初始数据', () => {
    expect(store.fetchSystemMetrics).toHaveBeenCalled()
    expect(store.fetchServiceStatus).toHaveBeenCalled()
    expect(store.fetchAlerts).toHaveBeenCalled()
  })

  it('应该处理获取数据失败的情况', async () => {
    store.fetchSystemMetrics.mockRejectedValueOnce(new Error('Failed to fetch metrics'))
    await wrapper.vm.fetchMetrics()
    expect(ElMessage.error).toHaveBeenCalledWith('获取系统指标失败')
  })

  it('应该正确显示 CPU 使用率', async () => {
    const cpuUsage = wrapper.find('[data-test="cpu-usage"]')
    const cpuTemp = wrapper.find('[data-test="cpu-temp"]')
    const cpuCores = wrapper.find('[data-test="cpu-cores"]')
    expect(cpuUsage.exists()).toBe(true)
    expect(cpuTemp.exists()).toBe(true)
    expect(cpuCores.exists()).toBe(true)
    expect(cpuUsage.text()).toContain('45.5%')
    expect(cpuTemp.text()).toContain('65°C')
    expect(cpuCores.text()).toContain('4')
  })

  it('应该正确显示内存使用情况', async () => {
    const memoryUsage = wrapper.find('[data-test="memory-usage"]')
    const memoryTotal = wrapper.find('[data-test="memory-total"]')
    const memoryFree = wrapper.find('[data-test="memory-free"]')
    expect(memoryUsage.exists()).toBe(true)
    expect(memoryTotal.exists()).toBe(true)
    expect(memoryFree.exists()).toBe(true)
    expect(memoryUsage.text()).toContain('50%')
    expect(memoryTotal.text()).toContain('16 GB')
  })

  it('应该正确显示磁盘使用情况', async () => {
    const diskUsage = wrapper.find('[data-test="disk-usage"]')
    const diskTotal = wrapper.find('[data-test="disk-total"]')
    const diskFree = wrapper.find('[data-test="disk-free"]')
    expect(diskUsage.exists()).toBe(true)
    expect(diskTotal.exists()).toBe(true)
    expect(diskFree.exists()).toBe(true)
    expect(diskUsage.text()).toContain('50%')
    expect(diskTotal.text()).toContain('1000 GB')
  })

  it('应该正确显示网络使用情况', async () => {
    const networkRx = wrapper.find('[data-test="network-rx"]')
    const networkTx = wrapper.find('[data-test="network-tx"]')
    const networkConn = wrapper.find('[data-test="network-conn"]')
    expect(networkRx.exists()).toBe(true)
    expect(networkTx.exists()).toBe(true)
    expect(networkConn.exists()).toBe(true)
    expect(networkTx.text()).toContain('1 MB/s')
    expect(networkRx.text()).toContain('0.5 MB/s')
    expect(networkConn.text()).toContain('100')
  })

  it('显示告警信息', async () => {
    const alerts = wrapper.findAll('.resource-alert')
    expect(alerts.length).toBeGreaterThan(0)
    expect(alerts[0].text()).toContain('内存使用率超过 80%')
  })

  it('显示加载状态', async () => {
    wrapper = mount(SystemResourceMonitor, {
      props: {
        resources: mockResources,
        lastUpdate: new Date().toISOString(),
        error: null,
        loading: true
      },
      global: {
        plugins: [createTestingPinia({
          initialState: {
            monitor: {
              loading: true,
              alerts: [
                { id: 1, level: 'warning', message: '内存使用率超过 80%' }
              ],
              cpuHistory: [
                { timestamp: '2024-01-01 10:00:00', value: 40 },
                { timestamp: '2024-01-01 10:01:00', value: 45 }
              ],
              resources: mockResources
            }
          },
          stubActions: false
        )],
        stubs: {
          'el-card': {
            template: '<div class="el-card"><div class="el-card__header" v-if="$slots.header"><slot name="header" /></div><div class="el-card__body"><slot /></div></div>'
          },
          'el-alert': {
            template: '<div class="el-alert" :class="type" :data-test="$attrs[\'data-test\']"><slot /></div>',
            props: ['type']
          },
          'el-button': {
            template: '<button class="el-button" :disabled="disabled"><slot /></button>',
            props: ['disabled']
          },
          'el-dialog': {
            template: '<div class="el-dialog" v-if="modelValue"><slot /><slot name="footer" /></div>',
            props: ['modelValue']
          },
          'el-table': {
            template: '<div class="el-table"><slot /></div>'
          },
          'el-table-column': {
            template: '<div class="el-table-column"><slot /></div>'
          },
          'el-tag': {
            template: '<span class="el-tag" :type="type"><slot /></span>',
            props: ['type']
          },
          'el-empty': {
            template: '<div class="el-empty"><slot /></div>'
          },
          'el-icon': {
            template: '<i class="el-icon"><slot /></i>'
          },
          'v-chart': {
            template: '<div class="echarts"></div>',
            props: ['option']
          }
        }
      }
    })
    await nextTick()
    const loading = wrapper.find('.loading')
    expect(loading.exists()).toBe(true)
  })

  it('显示错误状态', async () => {
    wrapper = mount(SystemResourceMonitor, {
      props: {
        resources: mockResources,
        lastUpdate: new Date().toISOString(),
        error: '获取系统资源信息失败',
        loading: false
      },
      global: {
        plugins: [createTestingPinia({
          initialState: {
            monitor: {
              loading: false,
              alerts: [
                { id: 1, level: 'warning', message: '内存使用率超过 80%' }
              ],
              cpuHistory: [
                { timestamp: '2024-01-01 10:00:00', value: 40 },
                { timestamp: '2024-01-01 10:01:00', value: 45 }
              ],
              resources: mockResources
            }
          },
          stubActions: false
        )],
        stubs: {
          'el-card': {
            template: '<div class="el-card"><div class="el-card__header" v-if="$slots.header"><slot name="header" /></div><div class="el-card__body"><slot /></div></div>'
          },
          'el-alert': {
            template: '<div class="el-alert" :class="type" :data-test="$attrs[\'data-test\']"><slot /></div>',
            props: ['type']
          },
          'el-button': {
            template: '<button class="el-button" :disabled="disabled"><slot /></button>',
            props: ['disabled']
          },
          'el-dialog': {
            template: '<div class="el-dialog" v-if="modelValue"><slot /><slot name="footer" /></div>',
            props: ['modelValue']
          },
          'el-table': {
            template: '<div class="el-table"><slot /></div>'
          },
          'el-table-column': {
            template: '<div class="el-table-column"><slot /></div>'
          },
          'el-tag': {
            template: '<span class="el-tag" :type="type"><slot /></span>',
            props: ['type']
          },
          'el-empty': {
            template: '<div class="el-empty"><slot /></div>'
          },
          'el-icon': {
            template: '<i class="el-icon"><slot /></i>'
          },
          'v-chart': {
            template: '<div class="echarts"></div>',
            props: ['option']
          }
        }
      }
    })
    await nextTick()
    const error = wrapper.find('.error-message')
    expect(error.exists()).toBe(true)
    expect(error.text()).toContain('获取系统资源信息失败')
  })

  it('正确格式化网络速度', async () => {
    const networkUpload = wrapper.find('.network-upload')
    expect(networkUpload.text()).toContain('1 MB/s')
  })

  it('正确格式化内存大小', async () => {
    const memoryTotal = wrapper.find('.memory-total')
    expect(memoryTotal.text()).toContain('16 GB')
  })

  it('正确格式化磁盘大小', async () => {
    const diskTotal = wrapper.find('.disk-total')
    expect(diskTotal.text()).toContain('1000 GB')
  })

  it('显示最后更新时间', async () => {
    const lastUpdate = '2024-01-01 10:00:00'
    wrapper = mount(SystemResourceMonitor, {
      props: {
        resources: mockResources,
        lastUpdate,
        error: null,
        loading: false
      },
      global: {
        plugins: [createTestingPinia({
          initialState: {
            monitor: {
              loading: false,
              alerts: [
                { id: 1, level: 'warning', message: '内存使用率超过 80%' }
              ],
              cpuHistory: [
                { timestamp: '2024-01-01 10:00:00', value: 40 },
                { timestamp: '2024-01-01 10:01:00', value: 45 }
              ],
              resources: mockResources
            }
          },
          stubActions: false
        )],
        stubs: {
          'el-card': {
            template: '<div class="el-card"><div class="el-card__header" v-if="$slots.header"><slot name="header" /></div><div class="el-card__body"><slot /></div></div>'
          },
          'el-alert': {
            template: '<div class="el-alert" :class="type" :data-test="$attrs[\'data-test\']"><slot /></div>',
            props: ['type']
          },
          'el-button': {
            template: '<button class="el-button" :disabled="disabled"><slot /></button>',
            props: ['disabled']
          },
          'el-dialog': {
            template: '<div class="el-dialog" v-if="modelValue"><slot /><slot name="footer" /></div>',
            props: ['modelValue']
          },
          'el-table': {
            template: '<div class="el-table"><slot /></div>'
          },
          'el-table-column': {
            template: '<div class="el-table-column"><slot /></div>'
          },
          'el-tag': {
            template: '<span class="el-tag" :type="type"><slot /></span>',
            props: ['type']
          },
          'el-empty': {
            template: '<div class="el-empty"><slot /></div>'
          },
          'el-icon': {
            template: '<i class="el-icon"><slot /></i>'
          },
          'v-chart': {
            template: '<div class="echarts"></div>',
            props: ['option']
          }
        }
      }
    })
    await nextTick()
    const updateTime = wrapper.find('.last-update')
    expect(updateTime.exists()).toBe(true)
    expect(updateTime.text()).toContain(lastUpdate)
  })

  it('点击刷新按钮触发刷新事件', async () => {
    const refreshBtn = wrapper.find('.refresh-btn')
    await refreshBtn.trigger('click')
    expect(wrapper.emitted('refresh')).toBeTruthy()
  })

  it('点击导出按钮触发导出事件', async () => {
    const exportBtn = wrapper.find('.export-btn')
    await exportBtn.trigger('click')
    expect(wrapper.emitted('export')).toBeTruthy()
  })

  it('应该正确显示服务状态', async () => {
    const service = wrapper.find('[data-test="service-nginx"]')
    const restartButton = wrapper.find('[data-test="restart-service-btn"]')
    expect(service.exists()).toBe(true)
    expect(service.find('.service-name').text()).toBe('nginx')
    expect(service.find('.service-status').text()).toBe('running')
    expect(restartButton.exists()).toBe(false)
  })

  it('应该显示重启按钮当服务停止时', async () => {
    await wrapper.setProps({
      services: [{
        name: 'mysql',
        status: 'stopped',
        uptime: '0',
        lastCheck: new Date().toISOString()
      }]
    })
    const service = wrapper.find('[data-test="service-mysql"]')
    const restartButton = service.find('[data-test="restart-service-btn"]')
    expect(service.exists()).toBe(true)
    expect(restartButton.exists()).toBe(true)
    expect(restartButton.text()).toBe('重启服务')
  })

  it('应该正确显示告警信息', async () => {
    const alert = wrapper.find('[data-test="alert-1"]')
    const acknowledgeButton = alert.find('[data-test="acknowledge-alert-btn"]')
    expect(alert.exists()).toBe(true)
    expect(alert.find('.alert-level').text()).toBe('warning')
    expect(alert.find('.alert-message').text()).toBe('CPU使用率超过80%')
    expect(acknowledgeButton.exists()).toBe(true)
    expect(acknowledgeButton.text()).toBe('确认告警')
  })

  it('应该能够确认告警', async () => {
    const alert = wrapper.find('[data-test="alert-1"]')
    const acknowledgeButton = alert.find('[data-test="acknowledge-alert-btn"]')
    await acknowledgeButton.trigger('click')
    expect(store.acknowledgeAlert).toHaveBeenCalledWith(1)
  })

  it('应该定时更新系统指标', async () => {
    vi.useFakeTimers()
    const updateInterval = 30000 // 30秒
    
    // 第一次调用已经在 mounted 时发生
    expect(store.fetchSystemMetrics).toHaveBeenCalledTimes(1)
    
    // 等待一个更新周期
    await vi.advanceTimersByTime(updateInterval)
    expect(store.fetchSystemMetrics).toHaveBeenCalledTimes(2)
    
    // 再等待一个更新周期
    await vi.advanceTimersByTime(updateInterval)
    expect(store.fetchSystemMetrics).toHaveBeenCalledTimes(3)
    
    vi.useRealTimers()
  })

  it('应该在组件销毁时清理定时器', async () => {
    vi.useFakeTimers()
    const updateInterval = 30000 // 30秒
    
    // 第一次调用已经在 mounted 时发生
    expect(store.fetchSystemMetrics).toHaveBeenCalledTimes(1)
    
    // 销毁组件
    wrapper.unmount()
    
    // 等待一个更新周期
    await vi.advanceTimersByTime(updateInterval)
    expect(store.fetchSystemMetrics).toHaveBeenCalledTimes(1) // 不应该再次调用
    
    vi.useRealTimers()
  })

  it('应该在网络错误时显示错误信息', async () => {
    const errorMessage = '网络连接失败'
    store.fetchSystemMetrics.mockRejectedValueOnce(new Error(errorMessage))
    
    await wrapper.vm.fetchMetrics()
    
    expect(ElMessage.error).toHaveBeenCalledWith('获取系统指标失败')
    expect(console.error).toHaveBeenCalledWith('获取系统指标失败:', expect.any(Error))
  })

  it('应该在服务重启成功时显示成功消息', async () => {
    const serviceName = 'mysql'
    await wrapper.vm.handleRestartService(serviceName)
    
    expect(store.restartService).toHaveBeenCalledWith(serviceName)
    expect(ElMessage.success).toHaveBeenCalledWith('服务重启成功')
  })

  it('应该在服务重启失败时显示错误消息', async () => {
    const serviceName = 'mysql'
    const errorMessage = '服务重启失败'
    store.restartService.mockRejectedValueOnce(new Error(errorMessage))
    
    await wrapper.vm.handleRestartService(serviceName)
    
    expect(store.restartService).toHaveBeenCalledWith(serviceName)
    expect(ElMessage.error).toHaveBeenCalledWith('服务重启失败')
  })
})