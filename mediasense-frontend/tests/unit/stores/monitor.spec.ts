import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMonitorStore } from '@/stores/monitor'
import { ElMessage } from 'element-plus'
import { 
  fetchSystemMetrics, 
  updateAlertConfig,
  getSystemMetrics,
  getSystemLogs,
  getMetricsHistory,
  getProcessList,
  getDiskUsage
} from '@/api/monitor'

vi.mock('@/api/monitor', () => ({
  fetchSystemMetrics: vi.fn(),
  updateAlertConfig: vi.fn()
}))

vi.mock('element-plus')

describe('Monitor Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('State', () => {
    it('initializes with default state', () => {
      const store = useMonitorStore()
      expect(store.resources).toEqual({
        cpu: { usage: 0, cores: 0, temperature: 0 },
        memory: { total: 0, used: 0, free: 0 },
        disk: { total: 0, used: 0, free: 0 },
        network: { upload: 0, download: 0, latency: 0 }
      })
      expect(store.alerts).toEqual([])
      expect(store.loading).toBe(false)
      expect(store.error).toBe(null)
    })
  })

  describe('Getters', () => {
    it('calculates resource usage percentages', () => {
      const store = useMonitorStore()
      store.$patch({
        resources: {
          cpu: { usage: 45.5 },
          memory: { total: 16384, used: 8192 },
          disk: { total: 512000, used: 256000 }
        }
      })

      expect(store.cpuUsagePercentage).toBe(45.5)
      expect(store.memoryUsagePercentage).toBe(50)
      expect(store.diskUsagePercentage).toBe(50)
    })

    it('determines system health status', () => {
      const store = useMonitorStore()
      store.$patch({
        resources: {
          cpu: { usage: 85 },
          memory: { total: 16384, used: 15000 }
        }
      })

      expect(store.systemHealth).toBe('warning')
    })

    it('filters critical alerts', () => {
      const store = useMonitorStore()
      store.$patch({
        alerts: [
          { level: 'critical', message: 'High CPU usage' },
          { level: 'warning', message: 'Memory usage high' }
        ]
      })

      expect(store.criticalAlerts.length).toBe(1)
      expect(store.criticalAlerts[0].message).toBe('High CPU usage')
    })
  })

  describe('Actions', () => {
    it('fetches system metrics successfully', async () => {
      const mockMetrics = {
        cpu: { usage: 50, cores: 4, temperature: 70 },
        memory: { total: 16384, used: 8192, free: 8192 },
        disk: { total: 512000, used: 256000, free: 256000 },
        network: { upload: 1024, download: 2048, latency: 50 }
      }

      fetchSystemMetrics.mockResolvedValue(mockMetrics)

      const store = useMonitorStore()
      await store.fetchResourceMetrics()

      expect(store.resources).toEqual(mockMetrics)
      expect(store.loading).toBe(false)
      expect(store.error).toBe(null)
    })

    it('handles fetch metrics error', async () => {
      const errorMessage = 'Failed to fetch metrics'
      fetchSystemMetrics.mockRejectedValue(new Error(errorMessage))

      const store = useMonitorStore()
      await store.fetchResourceMetrics()

      expect(store.loading).toBe(false)
      expect(store.error).toBe(errorMessage)
    })

    it('updates alert configuration', async () => {
      const newConfig = {
        cpu: { threshold: 80 },
        memory: { threshold: 90 },
        disk: { threshold: 85 }
      }

      updateAlertConfig.mockResolvedValue(newConfig)

      const store = useMonitorStore()
      await store.updateAlertConfig(newConfig)

      expect(store.alertConfig).toEqual(newConfig)
    })

    it('adds new alert', () => {
      const store = useMonitorStore()
      const newAlert = {
        level: 'warning',
        message: 'Memory usage high',
        timestamp: new Date().toISOString()
      }

      store.addAlert(newAlert)

      expect(store.alerts).toContainEqual(newAlert)
    })

    it('clears old alerts', () => {
      const store = useMonitorStore()
      const oldDate = new Date()
      oldDate.setDate(oldDate.getDate() - 2)

      store.$patch({
        alerts: [
          {
            level: 'warning',
            message: 'Old alert',
            timestamp: oldDate.toISOString()
          },
          {
            level: 'critical',
            message: 'New alert',
            timestamp: new Date().toISOString()
          }
        ]
      })

      store.clearOldAlerts()

      expect(store.alerts.length).toBe(1)
      expect(store.alerts[0].message).toBe('New alert')
    })
  })

  describe('Real-time Updates', () => {
    it('starts monitoring interval', () => {
      vi.useFakeTimers()
      const store = useMonitorStore()
      const fetchSpy = vi.spyOn(store, 'fetchResourceMetrics')

      store.startMonitoring()
      vi.advanceTimersByTime(60000) // 1分钟

      expect(fetchSpy).toHaveBeenCalledTimes(2) // 初始调用 + 1分钟后的调用
      vi.useRealTimers()
    })

    it('stops monitoring interval', () => {
      vi.useFakeTimers()
      const store = useMonitorStore()
      const fetchSpy = vi.spyOn(store, 'fetchResourceMetrics')

      store.startMonitoring()
      store.stopMonitoring()
      vi.advanceTimersByTime(60000)

      expect(fetchSpy).toHaveBeenCalledTimes(1) // 只有初始调用
      vi.useRealTimers()
    })
  })

  describe('Alert Thresholds', () => {
    it('triggers alerts when thresholds are exceeded', () => {
      const store = useMonitorStore()
      store.$patch({
        alertConfig: {
          cpu: { threshold: 80 },
          memory: { threshold: 90 }
        },
        resources: {
          cpu: { usage: 85 },
          memory: { total: 16384, used: 15000 }
        }
      })

      store.checkAlertThresholds()

      expect(store.alerts.length).toBe(1)
      expect(store.alerts[0].level).toBe('warning')
      expect(store.alerts[0].message).toContain('CPU usage')
    })
  })

  describe('Data Export', () => {
    it('exports monitoring data in correct format', () => {
      const store = useMonitorStore()
      store.$patch({
        resources: {
          cpu: { usage: 45.5 },
          memory: { total: 16384, used: 8192 }
        },
        alerts: [
          { level: 'warning', message: 'Test alert' }
        ]
      })

      const exportData = store.exportMonitoringData()

      expect(exportData).toHaveProperty('resources')
      expect(exportData).toHaveProperty('alerts')
      expect(exportData).toHaveProperty('timestamp')
    })
  })

  describe('获取系统指标', () => {
    it('应该成功获取系统指标', async () => {
      const mockMetrics = {
        data: {
          cpu: 50,
          memory: 70,
          disk: 60,
          network: {
            rx: 1000,
            tx: 2000
          }
        }
      }
      vi.mocked(monitorApi.getSystemMetrics).mockResolvedValue(mockMetrics.data)

      const store = useMonitorStore()
      await store.fetchSystemMetrics()

      expect(store.metrics).toEqual(mockMetrics.data)
      expect(store.loading).toBe(false)
    })

    it('应该处理获取系统指标失败', async () => {
      const error = new Error('获取系统指标失败')
      vi.mocked(monitorApi.getSystemMetrics).mockRejectedValue(error)

      const store = useMonitorStore()
      await store.fetchSystemMetrics()

      expect(store.metrics).toBeNull()
      expect(store.loading).toBe(false)
      expect(ElMessage.error).toHaveBeenCalledWith('获取系统指标失败')
    })
  })

  describe('获取系统日志', () => {
    it('应该成功获取系统日志', async () => {
      const mockLogs = {
        data: {
          total: 100,
          items: [
            { id: 1, level: 'info', message: 'test log', timestamp: '2024-03-20T10:00:00Z' }
          ]
        }
      }
      vi.mocked(monitorApi.getSystemLogs).mockResolvedValue(mockLogs.data)

      const store = useMonitorStore()
      await store.fetchSystemLogs({ page: 1, pageSize: 10 })

      expect(store.logs).toEqual(mockLogs.data.items)
      expect(store.totalLogs).toBe(mockLogs.data.total)
      expect(store.loading).toBe(false)
    })

    it('应该处理获取系统日志失败', async () => {
      const error = new Error('获取系统日志失败')
      vi.mocked(monitorApi.getSystemLogs).mockRejectedValue(error)

      const store = useMonitorStore()
      await store.fetchSystemLogs({ page: 1, pageSize: 10 })

      expect(store.logs).toEqual([])
      expect(store.totalLogs).toBe(0)
      expect(store.loading).toBe(false)
      expect(ElMessage.error).toHaveBeenCalledWith('获取系统日志失败')
    })
  })

  describe('获取指标历史', () => {
    it('应该成功获取指标历史', async () => {
      const mockHistory = {
        data: {
          timestamps: ['2024-03-19T10:00:00Z', '2024-03-20T10:00:00Z'],
          values: [45, 55]
        }
      }
      vi.mocked(monitorApi.getMetricsHistory).mockResolvedValue(mockHistory.data)

      const store = useMonitorStore()
      await store.fetchMetricsHistory({
        startTime: '2024-03-19T10:00:00Z',
        endTime: '2024-03-20T10:00:00Z',
        type: 'cpu'
      })

      expect(store.metricsHistory).toEqual(mockHistory.data)
      expect(store.loading).toBe(false)
    })

    it('应该处理获取指标历史失败', async () => {
      const error = new Error('获取指标历史失败')
      vi.mocked(monitorApi.getMetricsHistory).mockRejectedValue(error)

      const store = useMonitorStore()
      await store.fetchMetricsHistory({
        startTime: '2024-03-19T10:00:00Z',
        endTime: '2024-03-20T10:00:00Z',
        type: 'cpu'
      })

      expect(store.metricsHistory).toEqual({ timestamps: [], values: [] })
      expect(store.loading).toBe(false)
      expect(ElMessage.error).toHaveBeenCalledWith('获取指标历史失败')
    })
  })

  describe('获取进程列表', () => {
    it('应该成功获取进程列表', async () => {
      const mockProcesses = {
        data: [
          { pid: 1, name: 'process1', cpu: 10, memory: 200 },
          { pid: 2, name: 'process2', cpu: 20, memory: 300 }
        ]
      }
      vi.mocked(monitorApi.getProcessList).mockResolvedValue(mockProcesses.data)

      const store = useMonitorStore()
      await store.fetchProcessList()

      expect(store.processes).toEqual(mockProcesses.data)
      expect(store.loading).toBe(false)
    })

    it('应该处理获取进程列表失败', async () => {
      const error = new Error('获取进程列表失败')
      vi.mocked(monitorApi.getProcessList).mockRejectedValue(error)

      const store = useMonitorStore()
      await store.fetchProcessList()

      expect(store.processes).toEqual([])
      expect(store.loading).toBe(false)
      expect(ElMessage.error).toHaveBeenCalledWith('获取进程列表失败')
    })
  })

  describe('获取磁盘使用情况', () => {
    it('应该成功获取磁盘使用情况', async () => {
      const mockDiskUsage = {
        data: [
          { device: '/dev/sda1', mountPoint: '/', total: 1000, used: 500, free: 500 }
        ]
      }
      vi.mocked(monitorApi.getDiskUsage).mockResolvedValue(mockDiskUsage.data)

      const store = useMonitorStore()
      await store.fetchDiskUsage()

      expect(store.diskUsage).toEqual(mockDiskUsage.data)
      expect(store.loading).toBe(false)
    })

    it('应该处理获取磁盘使用情况失败', async () => {
      const error = new Error('获取磁盘使用情况失败')
      vi.mocked(monitorApi.getDiskUsage).mockRejectedValue(error)

      const store = useMonitorStore()
      await store.fetchDiskUsage()

      expect(store.diskUsage).toEqual([])
      expect(store.loading).toBe(false)
      expect(ElMessage.error).toHaveBeenCalledWith('获取磁盘使用情况失败')
    })
  })
}) 