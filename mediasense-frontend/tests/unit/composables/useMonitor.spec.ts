import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { useMonitorStore } from '@/stores/monitor'
import { useMonitor } from '@/composables/useMonitor'
import { setActivePinia } from 'pinia'
import { ref } from 'vue'

// Mock data
const mockMetrics = {
  cpu: 50,
  cpuCores: 4,
  memoryTotal: 16384,
  memoryUsed: 8192,
  memoryFree: 8192,
  diskTotal: 1024000,
  diskUsed: 512000,
  diskFree: 512000,
  networkUpload: 500,
  networkDownload: 1000,
  networkLatency: 20
}

const mockLogs = {
  items: [{
    timestamp: '2024-03-20T10:00:00Z',
    level: 'INFO',
    message: '系统正常运行'
  }],
  total: 1
}

const mockProcesses = [{
  pid: 1,
  name: 'process1',
  cpu: 5,
  memory: 100
}]

const mockAlerts = [{
  id: 'alert1',
  level: 'WARNING',
  message: '系统负载过高',
  timestamp: '2024-03-20T10:00:00Z'
}]

describe('useMonitor', () => {
  let store: any

  beforeEach(() => {
    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        monitor: {
          metrics: ref(mockMetrics),
          logs: ref(mockLogs.items),
          processes: ref(mockProcesses),
          alerts: ref(mockAlerts),
          loading: ref(false),
          error: ref(null)
        }
      }
    })
    setActivePinia(pinia)
    store = useMonitorStore()

    // Mock store methods
    store.fetchSystemMetrics = vi.fn().mockImplementation(async () => {
      store.metrics = mockMetrics
      return mockMetrics
    })
    store.fetchSystemLogs = vi.fn().mockImplementation(async () => {
      store.logs = mockLogs.items
      return mockLogs
    })
    store.fetchProcessList = vi.fn().mockImplementation(async () => {
      store.processes = mockProcesses
      return mockProcesses
    })
    store.fetchAlerts = vi.fn().mockImplementation(async () => {
      store.alerts = mockAlerts
      return mockAlerts
    })
    store.handleAcknowledgeAlert = vi.fn()
    store.deleteAlert = vi.fn()
    store.clearAllAlerts = vi.fn()
    store.startAutoUpdate = vi.fn()
    store.stopAutoUpdate = vi.fn()
    store.exportMonitoringData = vi.fn().mockResolvedValue('exported data')
    store.setError = vi.fn()
  })

  it('初始化时应该有默认值', () => {
    const { resources, logs, processes, alerts, loading, error } = useMonitor()
    expect(resources.value).toBeDefined()
    expect(logs.value).toBeDefined()
    expect(processes.value).toBeDefined()
    expect(alerts.value).toBeDefined()
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('应该能够获取系统指标', async () => {
    const { resources, fetchMetrics, loading, error } = useMonitor()
    await fetchMetrics()
    
    expect(store.fetchSystemMetrics).toHaveBeenCalled()
    expect(resources.value).toEqual({
      cpu: { usage: mockMetrics.cpu, cores: mockMetrics.cpuCores },
      memory: {
        total: mockMetrics.memoryTotal,
        used: mockMetrics.memoryUsed,
        free: mockMetrics.memoryFree
      },
      disk: {
        total: mockMetrics.diskTotal,
        used: mockMetrics.diskUsed,
        free: mockMetrics.diskFree
      },
      network: {
        upload: mockMetrics.networkUpload,
        download: mockMetrics.networkDownload,
        latency: mockMetrics.networkLatency
      }
    })
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('应该能够获取系统日志', async () => {
    const { logs, fetchLogs, loading, error } = useMonitor()
    await fetchLogs()
    
    expect(store.fetchSystemLogs).toHaveBeenCalled()
    expect(logs.value).toEqual(mockLogs.items)
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('应该能够获取进程列表', async () => {
    const { processes, fetchProcesses, loading, error } = useMonitor()
    await fetchProcesses()
    
    expect(store.fetchProcessList).toHaveBeenCalled()
    expect(processes.value).toEqual(mockProcesses)
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('应该能够获取告警列表', async () => {
    const { alerts, fetchAlerts, loading, error } = useMonitor()
    await fetchAlerts()
    
    expect(store.fetchAlerts).toHaveBeenCalled()
    expect(alerts.value).toEqual(mockAlerts)
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('应该能够确认告警', async () => {
    const alertId = 'alert1'
    store.handleAcknowledgeAlert.mockResolvedValue()

    const { acknowledgeAlert } = useMonitor()
    await acknowledgeAlert(alertId)

    expect(store.handleAcknowledgeAlert).toHaveBeenCalledWith(alertId)
  })

  it('应该能够删除告警', async () => {
    const alertId = 'alert1'
    store.deleteAlert.mockResolvedValue()

    const { deleteAlert } = useMonitor()
    await deleteAlert(alertId)

    expect(store.deleteAlert).toHaveBeenCalledWith(alertId)
  })

  it('应该能够清除所有告警', async () => {
    store.clearAllAlerts.mockResolvedValue()

    const { clearAllAlerts } = useMonitor()
    await clearAllAlerts()

    expect(store.clearAllAlerts).toHaveBeenCalled()
  })

  describe('自动更新', () => {
    it('应该能够开始自动更新', () => {
      const { startAutoUpdate } = useMonitor()
      startAutoUpdate()
      expect(store.startAutoUpdate).toHaveBeenCalled()
    })

    it('应该能够停止自动更新', () => {
      const { stopAutoUpdate } = useMonitor()
      stopAutoUpdate()
      expect(store.stopAutoUpdate).toHaveBeenCalled()
    })

    it('应该在组件卸载时停止自动更新', () => {
      const { stopAutoUpdate } = useMonitor()
      stopAutoUpdate()
      expect(store.stopAutoUpdate).toHaveBeenCalled()
    })
  })

  it('应该能够导出监控数据', async () => {
    const { exportData } = useMonitor()
    const result = await exportData()
    
    expect(store.exportMonitoringData).toHaveBeenCalled()
    expect(result).toBe('exported data')
  })

  it('应该正确处理错误', async () => {
    const error = new Error('测试错误')
    store.fetchSystemMetrics.mockRejectedValueOnce(error)
    
    const { fetchMetrics, loading, error: errorState } = useMonitor()
    try {
      await fetchMetrics()
    } catch (err) {
      // 忽略错误
    }
    
    expect(errorState.value).toBe('测试错误')
    expect(loading.value).toBe(false)
  })
})



