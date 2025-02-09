import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getSystemMetrics,
  getSystemLogs,
  getMetricsHistory,
  getProcessList,
  getDiskUsage,
  getServiceStatus,
  getAlerts,
  acknowledgeAlert,
  restartService
} from '../../../src/api/monitor'
import request from '../../../src/utils/request'
import type {
  SystemMetrics,
  SystemLog,
  ProcessInfo,
  DiskUsage,
  ServiceStatus,
  Alert
} from '../../../src/types/monitor'

vi.mock('../../../src/utils/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    }
  }
}))

describe('Monitor API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该能获取系统指标', async () => {
    const mockMetrics = {
      cpu: {
        usage: 50,
        cores: 4,
        temperature: 60
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
        rx_bytes: 1000,
        tx_bytes: 500,
        connections: 10,
        latency: 50
      }
    }

    vi.mocked(request.get).mockResolvedValueOnce({ data: mockMetrics })
    const result = await getSystemMetrics()
    expect(result).toEqual(mockMetrics)
    expect(request.get).toHaveBeenCalledWith('/monitor/metrics')
  })

  it('应该能获取系统日志', async () => {
    const mockLogs = {
      total: 2,
      items: [
        {
          id: '1',
          level: 'info',
          message: '系统启动',
          source: 'system',
          timestamp: '2024-03-20T10:00:00Z',
          metadata: {}
        }
      ]
    }

    vi.mocked(request.get).mockResolvedValueOnce({ data: mockLogs })
    const result = await getSystemLogs({ page: 1, pageSize: 10 })
    expect(result).toEqual(mockLogs)
    expect(request.get).toHaveBeenCalledWith('/monitor/logs', {
      params: { page: 1, pageSize: 10 }
    })
  })

  it('应该能获取指标历史数据', async () => {
    const mockHistory = {
      timestamps: ['2024-03-20T10:00:00Z'],
      values: [50]
    }

    vi.mocked(request.get).mockResolvedValueOnce({ data: mockHistory })
    const params = {
      startTime: '2024-03-20T00:00:00Z',
      endTime: '2024-03-20T23:59:59Z',
      type: 'cpu'
    }
    const result = await getMetricsHistory(params)
    expect(result).toEqual(mockHistory)
    expect(request.get).toHaveBeenCalledWith('/monitor/metrics/history', {
      params
    })
  })

  it('应该能获取进程列表', async () => {
    const mockProcesses = [{
      pid: 1,
      name: 'process1',
      command: './process1',
      cpu: 5,
      memory: 100,
      status: 'running',
      user: 'root',
      startTime: '2024-03-20T10:00:00Z',
      uptime: 3600
    }]

    vi.mocked(request.get).mockResolvedValueOnce({ data: mockProcesses })
    const result = await getProcessList()
    expect(result).toEqual(mockProcesses)
    expect(request.get).toHaveBeenCalledWith('/monitor/processes')
  })

  it('应该能获取磁盘使用情况', async () => {
    const mockDiskUsage = [{
      device: '/dev/sda1',
      mountPoint: '/',
      fsType: 'ext4',
      total: 1000000,
      used: 500000,
      free: 500000,
      usage: 50
    }]

    vi.mocked(request.get).mockResolvedValueOnce({ data: mockDiskUsage })
    const result = await getDiskUsage()
    expect(result).toEqual(mockDiskUsage)
    expect(request.get).toHaveBeenCalledWith('/monitor/disk')
  })

  it('应该能获取服务状态', async () => {
    const mockServices = [{
      name: 'nginx',
      status: 'running',
      uptime: '10d',
      lastCheck: '2024-03-20T10:00:00Z'
    }]

    vi.mocked(request.get).mockResolvedValueOnce({ data: mockServices })
    const result = await getServiceStatus()
    expect(result).toEqual(mockServices)
    expect(request.get).toHaveBeenCalledWith('/monitor/services')
  })

  it('应该能获取告警列表', async () => {
    const mockAlerts = [{
      id: 'alert1',
      type: 'cpu',
      level: 'warning',
      message: 'CPU使用率过高',
      timestamp: '2024-03-20T10:00:00Z'
    }]

    vi.mocked(request.get).mockResolvedValueOnce({ data: mockAlerts })
    const result = await getAlerts()
    expect(result).toEqual(mockAlerts)
    expect(request.get).toHaveBeenCalledWith('/monitor/alerts')
  })

  it('应该能确认告警', async () => {
    const mockResponse = { success: true, message: '已确认' }
    vi.mocked(request.post).mockResolvedValueOnce({ data: mockResponse })
    
    const result = await acknowledgeAlert('alert1')
    expect(result).toEqual(mockResponse)
    expect(request.post).toHaveBeenCalledWith('/monitor/alerts/acknowledge', {
      alertId: 'alert1'
    })
  })

  it('应该能重启服务', async () => {
    const mockResponse = { success: true, message: '服务已重启' }
    vi.mocked(request.post).mockResolvedValueOnce({ data: mockResponse })
    
    const result = await restartService('nginx')
    expect(result).toEqual(mockResponse)
    expect(request.post).toHaveBeenCalledWith('/monitor/services/restart', {
      serviceName: 'nginx'
    })
  })

  it('应该正确处理错误响应', async () => {
    const error = new Error('请求失败')
    vi.mocked(request.get).mockRejectedValueOnce(error)
    
    await expect(getSystemMetrics()).rejects.toThrow('请求失败')
  })
}) 