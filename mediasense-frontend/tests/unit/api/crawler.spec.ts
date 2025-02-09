import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as crawlerApi from '@/api/crawler'
import axios from 'axios'
import type { CrawlerConfig, CrawlerTask, CrawlerData } from '@/types/crawler'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('爬虫 API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('配置管理', () => {
    it('应该成功获取爬虫配置列表', async () => {
      const mockResponse = {
        data: {
          items: [
        {
          id: '1',
              name: '新闻爬虫',
              type: 'news',
              url: 'http://example.com',
          enabled: true,
              targetUrl: 'http://example.com',
              method: 'GET',
              headers: [],
              selectors: [],
              timeout: 30,
              retries: 3,
              concurrency: 1,
              selector: {
                title: '.title',
                content: '.content'
              }
            }
          ],
          total: 1
        }
      }
      ;(axios.get as any).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.getCrawlerConfigs()
      expect(result.items).toHaveLength(1)
      expect(result.total).toBe(1)
      expect(axios.get).toHaveBeenCalledWith('/api/crawler/configs')
    })

    it('应该成功创建爬虫配置', async () => {
      const mockConfig: Partial<CrawlerConfig> = {
        name: '新闻爬虫',
        type: 'news',
        url: 'http://example.com',
        enabled: true
      }
      const mockResponse = {
        data: { id: '1', ...mockConfig }
      }
      ;(axios.post as any).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.createCrawlerConfig(mockConfig)
      expect(result.id).toBe('1')
      expect(result.name).toBe('新闻爬虫')
      expect(axios.post).toHaveBeenCalledWith('/api/crawler/configs', mockConfig)
    })

    it('应该成功更新爬虫配置', async () => {
      const mockConfig: Partial<CrawlerConfig> = {
        name: '更新后的爬虫',
        enabled: false
      }
      const mockResponse = {
        data: { id: '1', ...mockConfig }
      }
      ;(axios.put as any).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.updateCrawlerConfig('1', mockConfig)
      expect(result.name).toBe('更新后的爬虫')
      expect(axios.put).toHaveBeenCalledWith('/api/crawler/configs/1', mockConfig)
    })

    it('应该成功删除爬虫配置', async () => {
      const mockResponse = {
        data: { success: true }
      }
      ;(axios.delete as any).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.deleteCrawlerConfig('1')
      expect(result.success).toBe(true)
      expect(axios.delete).toHaveBeenCalledWith('/api/crawler/configs/1')
    })
  })

  describe('任务管理', () => {
    it('应该成功获取任务列表', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: '1',
              name: '新闻爬取任务',
              status: 'running',
              configId: '1',
              startTime: '2024-01-01T00:00:00Z',
              totalItems: 100,
              successItems: 80,
              failedItems: 20
            }
          ],
          total: 1,
          page: 1,
          pageSize: 10
        }
      }
      ;(axios.get as any).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.getTasks({ page: 1, pageSize: 10 })
      expect(result.items).toHaveLength(1)
      expect(result.total).toBe(1)
      expect(axios.get).toHaveBeenCalledWith('/api/crawler/tasks', {
        params: { page: 1, pageSize: 10 }
      })
    })

    it('应该成功启动任务', async () => {
      const mockResponse = {
        data: { success: true, taskId: '1' }
      }
      ;(axios.post as any).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.startTask('1')
      expect(result.success).toBe(true)
      expect(result.taskId).toBe('1')
      expect(axios.post).toHaveBeenCalledWith('/api/crawler/tasks/1/start')
    })

    it('应该成功停止任务', async () => {
      const mockResponse = {
        data: { success: true }
      }
      ;(axios.post as any).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.stopTask('1')
      expect(result.success).toBe(true)
      expect(axios.post).toHaveBeenCalledWith('/api/crawler/tasks/1/stop')
    })

    it('应该成功批量启动任务', async () => {
      ;(axios.post as any).mockResolvedValueOnce({ data: { success: true } })

      await crawlerApi.batchStartTasks(['1', '2'])
      expect(axios.post).toHaveBeenCalledWith('/api/crawler/tasks/batch-start', {
        ids: ['1', '2']
      })
    })
  })

  describe('数据管理', () => {
    it('应该成功获取爬取数据', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: '1',
              taskId: '1',
              title: '测试新闻',
              content: '测试内容',
              url: 'http://example.com/news/1',
              source: '测试来源',
              publishTime: '2024-01-01T00:00:00Z',
              crawlTime: '2024-01-01T00:00:00Z'
            }
          ],
          total: 1,
          page: 1,
          pageSize: 10
        }
      }
      ;(axios.get as any).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.getData({
        taskId: '1',
        page: 1,
        pageSize: 10
      })
      expect(result.items).toHaveLength(1)
      expect(result.total).toBe(1)
      expect(axios.get).toHaveBeenCalledWith('/api/crawler/data', {
        params: { taskId: '1', page: 1, pageSize: 10 }
      })
    })

    it('应该成功删除数据', async () => {
      const mockResponse = {
        data: { success: true }
      }
      ;(axios.delete as any).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.deleteData('1')
      expect(result.success).toBe(true)
      expect(axios.delete).toHaveBeenCalledWith('/api/crawler/data/1')
    })

    it('应该成功批量删除数据', async () => {
      ;(axios.post as any).mockResolvedValueOnce({ data: { success: true } })

      await crawlerApi.batchDeleteData(['1', '2'])
      expect(axios.post).toHaveBeenCalledWith('/api/crawler/data/batch-delete', {
        ids: ['1', '2']
      })
    })

    it('应该成功导出数据', async () => {
      const mockBlob = new Blob(['test data'], { type: 'application/json' })
      const mockResponse = {
        data: mockBlob,
        headers: {
          'content-disposition': 'attachment; filename=crawler-data.json'
        }
      }
      ;(axios.get as any).mockResolvedValueOnce(mockResponse)

      const result = await crawlerApi.exportData({
        taskId: '1',
        format: 'json'
      })
      expect(result).toBeInstanceOf(Blob)
      expect(axios.get).toHaveBeenCalledWith('/api/crawler/data/export', {
        params: { taskId: '1', format: 'json' },
        responseType: 'blob'
      })
    })
  })
}) 