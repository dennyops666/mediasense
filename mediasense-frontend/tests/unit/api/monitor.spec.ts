import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import {
  fetchSystemMetrics,
  updateAlertConfig,
  getSystemMetrics,
  getSystemLogs,
  getMetricsHistory,
  getProcessList,
  getDiskUsage
} from '@/api/monitor'

vi.mock('axios')

describe('Monitor API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchSystemMetrics', () => {
    it('fetches system metrics successfully', async () => {
      const mockResponse = {
        data: {
          cpu: { usage: 45.5, cores: 4, temperature: 65 },
          memory: { total: 16384, used: 8192, free: 8192 },
          disk: { total: 512000, used: 256000, free: 256000 },
          network: { upload: 1024, download: 2048, latency: 50 }
        }
      }
      vi.mocked(axios.get).mockResolvedValue(mockResponse)

      const result = await fetchSystemMetrics()
      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith('/api/monitor/metrics')
    })

    it('handles fetch metrics error', async () => {
      const error = new Error('Network error')
      vi.mocked(axios.get).mockRejectedValue(error)

      await expect(fetchSystemMetrics()).rejects.toThrow('Network error')
    })
  })

  describe('updateAlertConfig', () => {
    it('updates alert configuration successfully', async () => {
      const newConfig = {
        cpu: { threshold: 80 },
        memory: { threshold: 90 }
      }
      const mockResponse = { data: newConfig }
      vi.mocked(axios.put).mockResolvedValue(mockResponse)

      const result = await updateAlertConfig(newConfig)
      expect(result).toEqual(newConfig)
      expect(axios.put).toHaveBeenCalledWith('/api/monitor/alerts/config', newConfig)
    })
  })

  describe('getSystemLogs', () => {
    it('fetches system logs successfully', async () => {
      const mockLogs = {
        data: {
          total: 100,
          items: [
            { id: 1, level: 'info', message: 'test log', timestamp: '2024-03-20T10:00:00Z' }
          ]
        }
      }
      vi.mocked(axios.get).mockResolvedValue(mockLogs)

      const result = await getSystemLogs({ page: 1, pageSize: 10 })
      expect(result).toEqual(mockLogs.data)
      expect(axios.get).toHaveBeenCalledWith('/api/monitor/logs', {
        params: { page: 1, pageSize: 10 }
      })
    })
  })

  describe('getMetricsHistory', () => {
    it('fetches metrics history successfully', async () => {
      const mockHistory = {
        data: {
          timestamps: ['2024-03-19T10:00:00Z', '2024-03-20T10:00:00Z'],
          values: [45, 55]
        }
      }
      vi.mocked(axios.get).mockResolvedValue(mockHistory)

      const params = {
        startTime: '2024-03-19T10:00:00Z',
        endTime: '2024-03-20T10:00:00Z',
        type: 'cpu'
      }
      const result = await getMetricsHistory(params)
      expect(result).toEqual(mockHistory.data)
      expect(axios.get).toHaveBeenCalledWith('/api/monitor/metrics/history', { params })
    })
  })

  describe('getProcessList', () => {
    it('fetches process list successfully', async () => {
      const mockProcesses = {
        data: [
          { pid: 1, name: 'process1', cpu: 10, memory: 200 },
          { pid: 2, name: 'process2', cpu: 20, memory: 300 }
        ]
      }
      vi.mocked(axios.get).mockResolvedValue(mockProcesses)

      const result = await getProcessList()
      expect(result).toEqual(mockProcesses.data)
      expect(axios.get).toHaveBeenCalledWith('/api/monitor/processes')
    })
  })

  describe('getDiskUsage', () => {
    it('fetches disk usage successfully', async () => {
      const mockDiskUsage = {
        data: [
          { device: '/dev/sda1', mountPoint: '/', total: 1000, used: 500, free: 500 }
        ]
      }
      vi.mocked(axios.get).mockResolvedValue(mockDiskUsage)

      const result = await getDiskUsage()
      expect(result).toEqual(mockDiskUsage.data)
      expect(axios.get).toHaveBeenCalledWith('/api/monitor/disk')
    })
  })
}) 