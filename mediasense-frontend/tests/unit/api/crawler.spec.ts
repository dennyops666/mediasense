import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as crawlerApi from '@/api/crawler'
import request from '@/utils/request'
import type { CrawlerConfig } from '@/types/api'

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
    vi.clearAllMocks()
  })

  describe('getCrawlerConfigs', () => {
    it('应该正确获取爬虫配置列表', async () => {
      const mockData = [
        {
          id: '1',
          name: '测试爬虫1',
          siteName: '测试站点1',
          siteUrl: 'http://example1.com',
          frequency: 30,
          enabled: true,
          lastRunTime: '2025-02-04T10:00:00Z',
          createdAt: '2025-02-04T10:00:00Z',
          updatedAt: '2025-02-04T10:00:00Z'
        }
      ]

      vi.mocked(request.get).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })

      const result = await crawlerApi.getCrawlerConfigs()

      expect(request.get).toHaveBeenCalledWith('/crawler/configs')
      expect(result).toEqual(mockData)
    })

    it('应该处理获取配置列表失败的情况', async () => {
      const error = new Error('获取失败')
      vi.mocked(request.get).mockRejectedValueOnce(error)

      await expect(crawlerApi.getCrawlerConfigs()).rejects.toThrow('获取失败')
    })

    it('应该返回正确的响应格式', async () => {
      const mockData = [
        {
          id: '1',
          name: '测试爬虫1',
          siteName: '测试站点1',
          siteUrl: 'http://example1.com',
          frequency: 30,
          enabled: true,
          lastRunTime: '2025-02-04T10:00:00Z',
          createdAt: '2025-02-04T10:00:00Z',
          updatedAt: '2025-02-04T10:00:00Z'
        }
      ]

      vi.mocked(request.get).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })
      const result = await crawlerApi.getCrawlerConfigs()

      expect(Array.isArray(result)).toBe(true)
      expect(result[0]).toHaveProperty('id')
      expect(result[0]).toHaveProperty('name')
      expect(result[0]).toHaveProperty('siteName')
      expect(result[0]).toHaveProperty('siteUrl')
      expect(result[0]).toHaveProperty('frequency')
      expect(result[0]).toHaveProperty('enabled')
      expect(result[0]).toHaveProperty('lastRunTime')
      expect(result[0]).toHaveProperty('createdAt')
      expect(result[0]).toHaveProperty('updatedAt')
    })

    it('应该处理空响应', async () => {
      vi.mocked(request.get).mockResolvedValueOnce({
        status: 'success',
        data: []
      })
      const result = await crawlerApi.getCrawlerConfigs()
      expect(result).toEqual([])
    })
  })

  describe('getCrawlerConfigById', () => {
    it('应该正确获取单个爬虫配置', async () => {
      const configId = '1'
      const mockData = {
        id: configId,
        name: '测试爬虫1',
        siteName: '测试站点1',
        siteUrl: 'http://example1.com',
        frequency: 30,
        enabled: true,
        lastRunTime: '2025-02-04T10:00:00Z',
        createdAt: '2025-02-04T10:00:00Z',
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(request.get).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })

      const result = await crawlerApi.getCrawlerConfigById(configId)

      expect(request.get).toHaveBeenCalledWith(`/crawler/configs/${configId}`)
      expect(result).toEqual(mockData)
    })

    it('应该处理获取单个配置失败的情况', async () => {
      const configId = '1'
      const error = new Error('获取失败')
      vi.mocked(request.get).mockRejectedValueOnce(error)

      await expect(crawlerApi.getCrawlerConfigById(configId)).rejects.toThrow('获取失败')
    })

    it('应该处理无效的 ID 格式', async () => {
      const invalidId = ''
      const error = new Error('无效的配置 ID')
      vi.mocked(request.get).mockRejectedValueOnce(error)

      await expect(crawlerApi.getCrawlerConfigById(invalidId)).rejects.toThrow('无效的配置 ID')
    })

    it('应该处理配置不存在的情况', async () => {
      const nonExistentId = 'non-existent'
      const error = new Error('配置不存在')
      vi.mocked(request.get).mockRejectedValueOnce(error)

      await expect(crawlerApi.getCrawlerConfigById(nonExistentId)).rejects.toThrow('配置不存在')
    })
  })

  describe('createCrawlerConfig', () => {
    it('应该正确创建爬虫配置', async () => {
      const mockConfig: Omit<CrawlerConfig, 'id' | 'createdAt' | 'updatedAt'> = {
        name: '新爬虫',
        siteName: '新站点',
        siteUrl: 'http://example.com',
        frequency: 30,
        enabled: true
      }

      const mockData = {
        id: '1',
        ...mockConfig,
        createdAt: '2025-02-04T10:00:00Z',
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(request.post).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })

      const result = await crawlerApi.createCrawlerConfig(mockConfig)

      expect(request.post).toHaveBeenCalledWith('/crawler/configs', mockConfig)
      expect(result).toEqual(mockData)
    })

    it('应该处理创建配置失败的情况', async () => {
      const mockConfig = {
        name: '新爬虫',
        siteName: '新站点',
        siteUrl: 'http://example.com',
        frequency: 30,
        enabled: true
      }
      const error = new Error('创建失败')
      vi.mocked(request.post).mockRejectedValueOnce(error)

      await expect(crawlerApi.createCrawlerConfig(mockConfig)).rejects.toThrow('创建失败')
    })

    it('应该验证必填字段', async () => {
      const invalidConfig = {
        name: '',
        siteName: '',
        siteUrl: 'invalid-url',
        frequency: -1,
        enabled: true
      }

      const error = new Error('无效的配置参数')
      vi.mocked(request.post).mockRejectedValueOnce(error)

      await expect(crawlerApi.createCrawlerConfig(invalidConfig)).rejects.toThrow('无效的配置参数')
    })

    it('应该处理特殊字符', async () => {
      const configWithSpecialChars = {
        name: '测试爬虫<script>alert(1)</script>',
        siteName: '测试站点&lt;&gt;',
        siteUrl: 'http://example.com?param=value&special=true',
        frequency: 30,
        enabled: true
      }

      const mockData = {
        id: '1',
        ...configWithSpecialChars,
        name: '测试爬虫',  // 期望服务端会过滤掉脚本标签
        createdAt: '2025-02-04T10:00:00Z',
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(request.post).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })
      const result = await crawlerApi.createCrawlerConfig(configWithSpecialChars)

      expect(result.name).not.toContain('<script>')
      expect(result.siteUrl).toContain('?param=value&special=true')
    })
  })

  describe('updateCrawlerConfig', () => {
    it('应该正确更新爬虫配置', async () => {
      const configId = '1'
      const updateData = {
        name: '更新后的名称',
        frequency: 60
      }

      const mockData = {
        id: configId,
        name: '更新后的名称',
        frequency: 60,
        siteName: '测试站点',
        siteUrl: 'http://example.com',
        enabled: true,
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(request.put).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })

      const result = await crawlerApi.updateCrawlerConfig(configId, updateData)

      expect(request.put).toHaveBeenCalledWith(`/crawler/configs/${configId}`, updateData)
      expect(result).toEqual(mockData)
    })

    it('应该处理更新配置失败的情况', async () => {
      const configId = '1'
      const updateData = {
        name: '更新后的名称',
        frequency: 60
      }
      const error = new Error('更新失败')
      vi.mocked(request.put).mockRejectedValueOnce(error)

      await expect(crawlerApi.updateCrawlerConfig(configId, updateData)).rejects.toThrow('更新失败')
    })

    it('应该只更新提供的字段', async () => {
      const configId = '1'
      const partialUpdate = {
        name: '更新后的名称'
      }

      const mockData = {
        id: configId,
        name: '更新后的名称',
        siteName: '原站点名称',  // 未更新的字段保持不变
        siteUrl: 'http://example.com',
        frequency: 30,
        enabled: true,
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(request.put).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })
      const result = await crawlerApi.updateCrawlerConfig(configId, partialUpdate)

      expect(result.name).toBe(partialUpdate.name)
      expect(result.siteName).toBe('原站点名称')
      expect(result.frequency).toBe(30)
    })

    it('应该验证更新字段的类型', async () => {
      const configId = '1'
      const invalidUpdate = {
        frequency: '非数字' as any
      }

      const error = new Error('无效的字段类型')
      vi.mocked(request.put).mockRejectedValueOnce(error)

      await expect(crawlerApi.updateCrawlerConfig(configId, invalidUpdate)).rejects.toThrow('无效的字段类型')
    })
  })

  describe('deleteCrawlerConfig', () => {
    it('应该正确删除爬虫配置', async () => {
      const configId = '1'
      vi.mocked(request.delete).mockResolvedValueOnce({})

      await crawlerApi.deleteCrawlerConfig(configId)

      expect(request.delete).toHaveBeenCalledWith(`/crawler/configs/${configId}`)
    })

    it('应该处理删除配置失败的情况', async () => {
      const configId = '1'
      const error = new Error('删除失败')
      vi.mocked(request.delete).mockRejectedValueOnce(error)

      await expect(crawlerApi.deleteCrawlerConfig(configId)).rejects.toThrow('删除失败')
    })
  })

  describe('toggleCrawlerConfig', () => {
    it('应该正确切换爬虫状态', async () => {
      const configId = '1'
      const enabled = true

      const mockData = {
        id: configId,
        enabled: true,
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(request.put).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })

      const result = await crawlerApi.toggleCrawlerConfig(configId, enabled)

      expect(request.put).toHaveBeenCalledWith(`/crawler/configs/${configId}/toggle`, { enabled })
      expect(result).toEqual(mockData)
    })

    it('应该处理切换状态失败的情况', async () => {
      const configId = '1'
      const enabled = true
      const error = new Error('切换状态失败')
      vi.mocked(request.put).mockRejectedValueOnce(error)

      await expect(crawlerApi.toggleCrawlerConfig(configId, enabled)).rejects.toThrow('切换状态失败')
    })

    it('应该处理重复切换状态', async () => {
      const configId = '1'
      const enabled = true

      // 模拟配置已经处于目标状态
      const mockData = {
        id: configId,
        enabled: true,
        message: '配置已经处于启用状态',
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(request.put).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })
      const result = await crawlerApi.toggleCrawlerConfig(configId, enabled)

      expect(result.enabled).toBe(enabled)
      expect(result).toHaveProperty('message')
    })
  })

  describe('runCrawlerConfig', () => {
    it('应该正确触发爬虫任务', async () => {
      const configId = '1'
      const mockData = {
        taskId: 'task-1',
        status: 'running',
        startTime: '2025-02-04T10:00:00Z'
      }

      vi.mocked(request.post).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })

      const result = await crawlerApi.runCrawlerConfig(configId)

      expect(request.post).toHaveBeenCalledWith(`/crawler/configs/${configId}/run`)
      expect(result).toEqual(mockData)
    })

    it('应该处理任务触发失败的情况', async () => {
      const configId = '1'
      const error = new Error('任务触发失败')

      vi.mocked(request.post).mockRejectedValueOnce(error)

      await expect(crawlerApi.runCrawlerConfig(configId)).rejects.toThrow('任务触发失败')
    })

    it('应该处理重复运行任务', async () => {
      const configId = '1'
      const error = new Error('任务正在运行中')
      vi.mocked(request.post).mockRejectedValueOnce(error)

      await expect(crawlerApi.runCrawlerConfig(configId)).rejects.toThrow('任务正在运行中')
    })

    it('应该处理禁用状态下的运行请求', async () => {
      const configId = '1'
      const error = new Error('配置已禁用，无法运行任务')
      vi.mocked(request.post).mockRejectedValueOnce(error)

      await expect(crawlerApi.runCrawlerConfig(configId)).rejects.toThrow('配置已禁用，无法运行任务')
    })
  })
}) 