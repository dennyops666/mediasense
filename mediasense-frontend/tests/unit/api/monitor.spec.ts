import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as monitorApi from '@/api/monitor'
import request from '@/utils/request'
import type { SystemMetrics, SystemLog } from '@/types/api'

// 修改 mock 实现
vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

describe('监控 API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getSystemMetrics', () => {
    it('应该正确获取系统指标', async () => {
      const mockResponse = {
        data: {
          cpuUsage: 45.5,
          memoryUsage: 65.8,
          diskUsage: 72.3,
          processCount: 128,
          lastUpdate: '2024-03-20T10:00:00Z',
          networkIo: {
            input: 1024,
            output: 2048
          }
        }
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await monitorApi.getSystemMetrics()

      expect(request.get).toHaveBeenCalledWith('/api/monitor/metrics')
      expect(result).toEqual(mockResponse.data)
    })

    it('应该处理获取系统指标失败的情况', async () => {
      const error = new Error('获取系统指标失败')
      vi.mocked(request.get).mockRejectedValueOnce(error)

      await expect(monitorApi.getSystemMetrics()).rejects.toThrow('获取系统指标失败')
    })
  })

  describe('getSystemLogs', () => {
    it('应该正确获取系统日志', async () => {
      const mockResponse = {
        data: {
          total: 100,
          items: [
            {
              id: '1',
              timestamp: '2024-03-20T10:00:00Z',
              level: 'info',
              module: 'crawler',
              message: '爬虫任务开始执行'
            },
            {
              id: '2',
              timestamp: '2024-03-20T10:01:00Z',
              level: 'error',
              module: 'database',
              message: '数据库连接失败'
            }
          ] as SystemLog[]
        }
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const params = {
        page: 1,
        pageSize: 10,
        level: 'error'
      }

      const result = await monitorApi.getSystemLogs(params)

      expect(request.get).toHaveBeenCalledWith('/api/monitor/logs', { params })
      expect(result).toEqual(mockResponse.data)
    })

    it('应该处理获取系统日志失败的情况', async () => {
      const error = new Error('获取系统日志失败')
      vi.mocked(request.get).mockRejectedValueOnce(error)

      const params = {
        page: 1,
        pageSize: 10
      }

      await expect(monitorApi.getSystemLogs(params)).rejects.toThrow('获取系统日志失败')
    })
  })

  describe('getMetricsHistory', () => {
    it('应该正确获取历史指标数据', async () => {
      const mockResponse = {
        data: {
          timestamps: ['2024-03-20T10:00:00Z', '2024-03-20T10:01:00Z'],
          values: [45.5, 48.2]
        }
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const params = {
        startTime: '2024-03-20T10:00:00Z',
        endTime: '2024-03-20T10:01:00Z',
        type: 'cpu'
      }

      const result = await monitorApi.getMetricsHistory(params)

      expect(request.get).toHaveBeenCalledWith('/api/monitor/metrics/history', { params })
      expect(result).toEqual(mockResponse.data)
    })

    it('应该处理获取历史指标数据失败的情况', async () => {
      const error = new Error('获取历史指标数据失败')
      vi.mocked(request.get).mockRejectedValueOnce(error)

      const params = {
        startTime: '2024-03-20T10:00:00Z',
        endTime: '2024-03-20T10:01:00Z',
        type: 'cpu'
      }

      await expect(monitorApi.getMetricsHistory(params)).rejects.toThrow('获取历史指标数据失败')
    })
  })

  describe('getProcessList', () => {
    it('应该正确获取进程列表', async () => {
      const mockResponse = {
        data: [
          {
            pid: 1234,
            name: 'node',
            cpu: 2.5,
            memory: 128.5,
            status: 'running',
            startTime: '2024-03-20T10:00:00Z'
          }
        ]
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await monitorApi.getProcessList()

      expect(request.get).toHaveBeenCalledWith('/api/monitor/processes')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getDiskUsage', () => {
    it('应该正确获取磁盘使用情况', async () => {
      const mockResponse = {
        data: [
          {
            path: '/',
            total: 1024000,
            used: 512000,
            free: 512000,
            usage: 50
          }
        ]
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await monitorApi.getDiskUsage()

      expect(request.get).toHaveBeenCalledWith('/api/monitor/disk')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('getServiceStatus', () => {
    it('应该正确获取服务状态', async () => {
      const mockResponse = {
        data: [
          {
            name: 'nginx',
            status: 'running',
            uptime: '10d 2h 30m',
            memory: 128.5,
            cpu: 0.5
          }
        ]
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await monitorApi.getServiceStatus()

      expect(request.get).toHaveBeenCalledWith('/api/monitor/services')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('restartService', () => {
    it('应该正确重启服务', async () => {
      const mockResponse = {
        data: { success: true, message: '服务重启成功' }
      }

      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const serviceName = 'nginx'
      const result = await monitorApi.restartService(serviceName)

      expect(request.post).toHaveBeenCalledWith('/api/monitor/services/restart', { serviceName })
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('acknowledgeAlert', () => {
    it('应该正确确认告警', async () => {
      const mockResponse = {
        data: { success: true, message: '告警已确认' }
      }

      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const alertId = 'alert-123'
      const result = await monitorApi.acknowledgeAlert(alertId)

      expect(request.post).toHaveBeenCalledWith('/api/monitor/alerts/acknowledge', { alertId })
      expect(result).toEqual(mockResponse.data)
    })
  })
}) 