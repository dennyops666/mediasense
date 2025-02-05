import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMonitorStore } from '@/stores/monitor'
import * as monitorApi from '@/api/monitor'
import { ElMessage } from 'element-plus'

vi.mock('@/api/monitor')
vi.mock('element-plus')

describe('Monitor Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const store = useMonitorStore()
      expect(store.metrics).toBeNull()
      expect(store.logs).toEqual([])
      expect(store.totalLogs).toBe(0)
      expect(store.processes).toEqual([])
      expect(store.diskUsage).toEqual([])
      expect(store.loading).toBe(false)
      expect(store.metricsHistory).toEqual({
        timestamps: [],
        values: []
      })
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