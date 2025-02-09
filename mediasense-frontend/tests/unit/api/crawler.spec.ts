import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import * as crawlerApi from '@/api/crawler'
import request from '@/utils/request'
import type { CrawlerConfig, CrawlerTask, CrawlerData } from '@/types/crawler'

// Mock request
vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('爬虫 API', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('配置管理', () => {
    it('应该成功获取爬虫配置列表', async () => {
      const mockConfigs: CrawlerConfig[] = [
        {
          id: '1',
          name: '测试配置1',
          url: 'http://example.com',
          rules: { title: '.title', content: '.content' },
          schedule: '0 0 * * *',
          status: 'active'
        }
      ]

      const mockResponse = {
        data: mockConfigs
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.getCrawlerConfigs()
      expect(result).toEqual(mockConfigs)
      expect(request.get).toHaveBeenCalledWith('/crawler/configs')
    })

    it('应该成功创建爬虫配置', async () => {
      const newConfig: Partial<CrawlerConfig> = {
        name: '新配置',
        url: 'http://example.com',
        rules: { title: '.title', content: '.content' }
      }

      const mockResponse = {
        data: {
          id: '1',
          ...newConfig,
          status: 'active',
          schedule: '0 0 * * *'
        }
      }

      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.createCrawlerConfig(newConfig)
      expect(result).toEqual(mockResponse.data)
      expect(request.post).toHaveBeenCalledWith('/crawler/configs', newConfig)
    })

    it('应该成功更新爬虫配置', async () => {
      const configId = '1'
      const updateData: Partial<CrawlerConfig> = {
        name: '更新后的配置',
        schedule: '0 0 * * 1'
      }

      const mockResponse = {
        data: {
          id: configId,
          ...updateData,
          url: 'http://example.com',
          rules: { title: '.title', content: '.content' },
          status: 'active'
        }
      }

      vi.mocked(request.put).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.updateCrawlerConfig(configId, updateData)
      expect(result).toEqual(mockResponse.data)
      expect(request.put).toHaveBeenCalledWith(`/crawler/configs/${configId}`, updateData)
    })

    it('应该成功删除爬虫配置', async () => {
      const configId = 1
      const mockResponse = {
        data: {
          success: true
        }
      }
      vi.mocked(request.delete).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.deleteCrawlerConfig(configId)
      expect(result).toEqual(mockResponse.data)
      expect(request.delete).toHaveBeenCalledWith(`/crawler/configs/${configId}`)
    })
  })

  describe('任务管理', () => {
    it('应该成功获取任务列表', async () => {
      const mockTasks: CrawlerTask[] = [
        {
          id: '1',
          configId: '1',
          status: 'running',
          startTime: new Date().toISOString(),
          endTime: null,
          result: null
        }
      ]

      const mockResponse = {
        data: {
          items: mockTasks,
          total: 1,
          page: 1,
          pageSize: 10
        }
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.getTasks({ page: 1, pageSize: 10 })
      expect(result).toEqual(mockResponse.data)
      expect(request.get).toHaveBeenCalledWith('/crawler/tasks', {
        params: { page: 1, pageSize: 10 }
      })
    })

    it('应该成功启动任务', async () => {
      const taskId = '1'
      const mockResponse = {
        data: {
          id: taskId,
          status: 'running',
          startTime: new Date().toISOString()
        }
      }

      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.startTask(taskId)
      expect(result).toEqual(mockResponse.data)
      expect(request.post).toHaveBeenCalledWith(`/crawler/tasks/${taskId}/start`)
    })

    it('应该成功停止任务', async () => {
      const taskId = '1'
      const mockResponse = {
        data: {
          id: taskId,
          status: 'stopped',
          endTime: new Date().toISOString()
        }
      }

      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.stopTask(taskId)
      expect(result).toEqual(mockResponse.data)
      expect(request.post).toHaveBeenCalledWith(`/crawler/tasks/${taskId}/stop`)
    })

    it('应该成功批量启动任务', async () => {
      const taskIds = ['1', '2']
      const mockResponse = {
        data: {
          success: true,
          failedIds: []
        }
      }

      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.batchStartTasks(taskIds)
      expect(result).toEqual(mockResponse.data)
      expect(request.post).toHaveBeenCalledWith('/crawler/tasks/batch-start', { ids: taskIds })
    })
  })

  describe('数据管理', () => {
    it('应该成功获取爬取数据', async () => {
      const mockData: CrawlerData[] = [
        {
          id: '1',
          taskId: '1',
          title: '测试标题',
          content: '测试内容',
          url: 'http://example.com/1',
          createdAt: new Date().toISOString()
        }
      ]

      const mockResponse = {
        data: {
          items: mockData,
          total: 1,
          page: 1,
          pageSize: 10
        }
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.getData({ page: 1, pageSize: 10 })
      expect(result).toEqual(mockResponse.data)
      expect(request.get).toHaveBeenCalledWith('/crawler/data', {
        params: { page: 1, pageSize: 10 }
      })
    })

    it('应该成功删除数据', async () => {
      const dataId = 1
      const mockResponse = {
        data: {
          success: true
        }
      }
      vi.mocked(request.delete).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.deleteData(dataId)
      expect(result).toEqual(mockResponse.data)
      expect(request.delete).toHaveBeenCalledWith(`/crawler/data/${dataId}`)
    })

    it('应该成功批量删除数据', async () => {
      const dataIds = ['1', '2']
      const mockResponse = {
        data: { success: true }
      }

      vi.mocked(request.post).mockResolvedValueOnce(mockResponse)

      await crawlerApi.batchDeleteData(dataIds)
      expect(request.post).toHaveBeenCalledWith('/crawler/data/batch-delete', {
        ids: dataIds
      })
    })

    it('应该成功导出数据', async () => {
      const mockBlob = new Blob(['test data'], { type: 'application/json' })
      const mockResponse = {
        data: mockBlob
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.exportData({ taskId: '1' })
      expect(result).toBeInstanceOf(Blob)
      expect(request.get).toHaveBeenCalledWith('/crawler/data/export', {
        params: { taskId: '1' },
        responseType: 'blob'
      })
    })
  })
}) 