import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useMonitorStore } from '@/stores/monitor'
import * as monitorApi from '@/api/monitor'

// Mock API
vi.mock('@/api/monitor')

// Mock data
const mockMetrics = {
  data: {
    cpu: {
      usage: 50,
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
      download: '2 MB/s',
      latency: 20
    }
  }
}

const mockLogs = {
  data: {
    items: [{
      timestamp: '2024-03-20T10:00:00Z',
      level: 'INFO',
      message: '系统正常运行'
    }],
    total: 1
  }
}

const mockProcesses = {
  data: [{
    pid: 1,
    name: 'process1',
    cpu: 5,
    memory: 100
  }]
}

const mockAlerts = {
  data: [{
    id: 'test-alert-id',
    message: '测试告警',
    level: 'warning',
    timestamp: '2024-03-20T10:00:00Z',
    source: 'system'
  }]
}

describe('Monitor Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('获取系统指标', () => {
    it('应该成功获取系统指标', async () => {
      const store = useMonitorStore()
      vi.mocked(monitorApi.getSystemMetrics).mockResolvedValue(mockMetrics)

      await store.fetchSystemMetrics()

      expect(store.metrics).toEqual(mockMetrics.data)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('应该处理获取系统指标失败的情况', async () => {
      const store = useMonitorStore()
      const error = new Error('获取失败')
      vi.mocked(monitorApi.getSystemMetrics).mockRejectedValue(error)

      try {
        await store.fetchSystemMetrics()
      } catch (err) {
        expect(store.error).toBe('获取失败')
        expect(store.loading).toBe(false)
      }
    })
  })

  describe('获取系统日志', () => {
    it('应该成功获取系统日志', async () => {
      const store = useMonitorStore()
      vi.mocked(monitorApi.getSystemLogs).mockResolvedValue(mockLogs)

      await store.fetchSystemLogs({ page: 1, pageSize: 10 })

      expect(store.logs).toEqual(mockLogs.data.items)
      expect(store.totalLogs).toBe(mockLogs.data.total)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('应该处理获取系统日志失败的情况', async () => {
      const store = useMonitorStore()
      const error = new Error('获取失败')
      vi.mocked(monitorApi.getSystemLogs).mockRejectedValue(error)

      try {
        await store.fetchSystemLogs({ page: 1, pageSize: 10 })
      } catch (err) {
        expect(store.error).toBe('获取失败')
        expect(store.loading).toBe(false)
      }
    })
  })

  describe('获取进程列表', () => {
    it('应该成功获取进程列表', async () => {
      const store = useMonitorStore()
      vi.mocked(monitorApi.getProcessList).mockResolvedValue(mockProcesses)

      await store.fetchProcessList()

      expect(store.processes).toEqual(mockProcesses.data)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('应该处理获取进程列表失败的情况', async () => {
      const store = useMonitorStore()
      const error = new Error('获取失败')
      vi.mocked(monitorApi.getProcessList).mockRejectedValue(error)

      try {
        await store.fetchProcessList()
      } catch (err) {
        expect(store.error).toBe('获取失败')
        expect(store.loading).toBe(false)
      }
    })
  })

  describe('获取告警列表', () => {
    it('应该成功获取告警列表', async () => {
      const store = useMonitorStore()
      vi.mocked(monitorApi.getAlerts).mockResolvedValue(mockAlerts)

      await store.fetchAlerts()

      expect(store.alerts).toEqual(mockAlerts.data)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('应该处理获取告警列表失败的情况', async () => {
      const store = useMonitorStore()
      const error = new Error('获取失败')
      vi.mocked(monitorApi.getAlerts).mockRejectedValue(error)

      try {
        await store.fetchAlerts()
      } catch (err) {
        expect(store.error).toBe('获取失败')
        expect(store.loading).toBe(false)
      }
    })
  })

  describe('确认告警', () => {
    it('应该成功确认告警', async () => {
      const store = useMonitorStore()
      const alertId = 'test-alert-id'
      vi.mocked(monitorApi.acknowledgeAlert).mockResolvedValue(undefined)
      vi.mocked(monitorApi.getAlerts).mockResolvedValue(mockAlerts)

      await store.handleAcknowledgeAlert(alertId)

      expect(monitorApi.acknowledgeAlert).toHaveBeenCalledWith(alertId)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('应该处理确认告警失败的情况', async () => {
      const store = useMonitorStore()
      const error = new Error('确认失败')
      vi.mocked(monitorApi.acknowledgeAlert).mockRejectedValue(error)

      try {
        await store.handleAcknowledgeAlert('test-alert-id')
      } catch (err) {
        expect(store.error).toBe('确认失败')
        expect(store.loading).toBe(false)
      }
    })
  })
}) 