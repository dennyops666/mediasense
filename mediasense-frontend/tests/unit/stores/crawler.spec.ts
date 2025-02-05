import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useCrawlerStore } from '@/stores/crawler'
import * as crawlerApi from '@/api/crawler'
import { ElMessage } from 'element-plus'
import type { CrawlerConfig } from '@/types/api'

vi.mock('@/api/crawler')
vi.mock('element-plus')

describe('爬虫 Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('获取配置列表', () => {
    it('应该正确获取爬虫配置列表', async () => {
      const store = useCrawlerStore()
      const mockConfigs: CrawlerConfig[] = [
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

      vi.mocked(crawlerApi.getCrawlerConfigs).mockResolvedValueOnce(mockConfigs)

      await store.fetchConfigs()

      expect(crawlerApi.getCrawlerConfigs).toHaveBeenCalled()
      expect(store.configs).toEqual(mockConfigs)
    })

    it('应该处理获取配置列表失败的情况', async () => {
      const store = useCrawlerStore()
      const error = new Error('获取失败')

      vi.mocked(crawlerApi.getCrawlerConfigs).mockRejectedValueOnce(error)

      await expect(store.fetchConfigs()).rejects.toThrow('获取失败')
    })
  })

  describe('获取单个配置', () => {
    it('应该正确获取单个爬虫配置', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const mockConfig = {
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

      vi.mocked(crawlerApi.getCrawlerConfigById).mockResolvedValueOnce(mockConfig)

      await store.fetchConfigById(configId)

      expect(crawlerApi.getCrawlerConfigById).toHaveBeenCalledWith(configId)
      expect(store.currentConfig).toEqual(mockConfig)
    })

    it('应该处理获取单个配置失败的情况', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const error = new Error('获取失败')

      vi.mocked(crawlerApi.getCrawlerConfigById).mockRejectedValueOnce(error)

      await expect(store.fetchConfigById(configId)).rejects.toThrow('获取失败')
      expect(store.currentConfig).toBeNull()
    })
  })

  describe('创建配置', () => {
    it('应该正确创建爬虫配置', async () => {
      const store = useCrawlerStore()
      const mockConfig = {
        name: '新爬虫',
        siteName: '新站点',
        siteUrl: 'http://example.com',
        frequency: 30,
        enabled: true
      }

      const mockResponse = {
        id: '1',
        ...mockConfig,
        lastRunTime: null,
        createdAt: '2025-02-04T10:00:00Z',
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(crawlerApi.createCrawlerConfig).mockResolvedValueOnce(mockResponse)
      vi.mocked(crawlerApi.getCrawlerConfigs).mockResolvedValueOnce([mockResponse])

      await store.createConfig(mockConfig)

      expect(crawlerApi.createCrawlerConfig).toHaveBeenCalledWith(mockConfig)
      expect(crawlerApi.getCrawlerConfigs).toHaveBeenCalled()
    })

    it('应该处理创建配置失败的情况', async () => {
      const store = useCrawlerStore()
      const mockConfig = {
        name: '新爬虫',
        siteName: '新站点',
        siteUrl: 'http://example.com',
        frequency: 30,
        enabled: true
      }
      const error = new Error('创建失败')

      vi.mocked(crawlerApi.createCrawlerConfig).mockRejectedValueOnce(error)

      await expect(store.createConfig(mockConfig)).rejects.toThrow('创建失败')
    })
  })

  describe('更新配置', () => {
    it('应该正确更新爬虫配置', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const updateData = {
        name: '更新后的名称',
        frequency: 60
      }

      const mockResponse = {
        id: configId,
        name: '更新后的名称',
        frequency: 60,
        siteName: '测试站点',
        siteUrl: 'http://example.com',
        enabled: true,
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(crawlerApi.updateCrawlerConfig).mockResolvedValueOnce(mockResponse)
      vi.mocked(crawlerApi.getCrawlerConfigs).mockResolvedValueOnce([mockResponse])

      await store.updateConfig(configId, updateData)

      expect(crawlerApi.updateCrawlerConfig).toHaveBeenCalledWith(configId, updateData)
      expect(crawlerApi.getCrawlerConfigs).toHaveBeenCalled()
    })

    it('应该处理更新配置失败的情况', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const updateData = {
        name: '更新后的名称',
        frequency: 60
      }
      const error = new Error('更新失败')

      vi.mocked(crawlerApi.updateCrawlerConfig).mockRejectedValueOnce(error)

      await expect(store.updateConfig(configId, updateData)).rejects.toThrow('更新失败')
    })
  })

  describe('删除配置', () => {
    it('应该正确删除爬虫配置', async () => {
      const store = useCrawlerStore()
      const configId = '1'

      vi.mocked(crawlerApi.deleteCrawlerConfig).mockResolvedValueOnce()
      vi.mocked(crawlerApi.getCrawlerConfigs).mockResolvedValueOnce([])

      await store.deleteConfig(configId)

      expect(crawlerApi.deleteCrawlerConfig).toHaveBeenCalledWith(configId)
      expect(crawlerApi.getCrawlerConfigs).toHaveBeenCalled()
    })

    it('应该处理删除配置失败的情况', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const error = new Error('删除失败')

      vi.mocked(crawlerApi.deleteCrawlerConfig).mockRejectedValueOnce(error)

      await expect(store.deleteConfig(configId)).rejects.toThrow('删除失败')
    })
  })

  describe('切换配置状态', () => {
    it('应该正确切换爬虫状态', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const enabled = true

      const mockResponse = {
        id: configId,
        enabled: true,
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(crawlerApi.toggleCrawlerConfig).mockResolvedValueOnce(mockResponse)
      vi.mocked(crawlerApi.getCrawlerConfigs).mockResolvedValueOnce([mockResponse])

      await store.toggleConfig(configId, enabled)

      expect(crawlerApi.toggleCrawlerConfig).toHaveBeenCalledWith(configId, enabled)
      expect(crawlerApi.getCrawlerConfigs).toHaveBeenCalled()
    })

    it('应该处理切换状态失败的情况', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const enabled = true
      const error = new Error('切换状态失败')

      vi.mocked(crawlerApi.toggleCrawlerConfig).mockRejectedValueOnce(error)

      await expect(store.toggleConfig(configId, enabled)).rejects.toThrow('切换状态失败')
    })
  })

  describe('运行爬虫', () => {
    it('应该正确触发爬虫任务', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const mockResponse = {
        taskId: 'task-1',
        status: 'running',
        startTime: '2025-02-04T10:00:00Z'
      }

      vi.mocked(crawlerApi.runCrawlerConfig).mockResolvedValueOnce(mockResponse)

      await store.runConfig(configId)

      expect(crawlerApi.runCrawlerConfig).toHaveBeenCalledWith(configId)
    })

    it('应该处理任务触发失败的情况', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const error = new Error('任务触发失败')

      vi.mocked(crawlerApi.runCrawlerConfig).mockRejectedValueOnce(error)

      await expect(store.runConfig(configId)).rejects.toThrow('任务触发失败')
    })
  })

  describe('loading 状态管理', () => {
    it('应该在操作开始时设置 loading 为 true，结束时设置为 false', async () => {
      const store = useCrawlerStore()
      const mockConfigs = [
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

      vi.mocked(crawlerApi.getCrawlerConfigs).mockResolvedValueOnce(mockConfigs)

      expect(store.loading).toBe(false)
      
      const promise = store.fetchConfigs()
      expect(store.loading).toBe(true)
      
      await promise
      expect(store.loading).toBe(false)
    })

    it('应该在操作失败时也正确重置 loading 状态', async () => {
      const store = useCrawlerStore()
      const error = new Error('获取失败')

      vi.mocked(crawlerApi.getCrawlerConfigs).mockRejectedValueOnce(error)

      expect(store.loading).toBe(false)
      
      try {
        const promise = store.fetchConfigs()
        expect(store.loading).toBe(true)
        await promise
      } catch (e) {
        expect(store.loading).toBe(false)
      }
    })
  })

  describe('错误处理和消息提示', () => {
    it('应该在操作成功时显示成功消息', async () => {
      const store = useCrawlerStore()
      const mockConfig = {
        name: '新爬虫',
        siteName: '新站点',
        siteUrl: 'http://example.com',
        frequency: 30,
        enabled: true
      }

      const mockResponse = {
        id: '1',
        ...mockConfig,
        lastRunTime: null,
        createdAt: '2025-02-04T10:00:00Z',
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(crawlerApi.createCrawlerConfig).mockResolvedValueOnce(mockResponse)
      vi.mocked(crawlerApi.getCrawlerConfigs).mockResolvedValueOnce([mockResponse])

      await store.createConfig(mockConfig)

      expect(ElMessage.success).toHaveBeenCalledWith('创建爬虫配置成功')
    })

    it('应该在操作失败时显示错误消息', async () => {
      const store = useCrawlerStore()
      const error = new Error('创建失败')

      vi.mocked(crawlerApi.createCrawlerConfig).mockRejectedValueOnce(error)

      try {
        await store.createConfig({})
      } catch (e) {
        expect(ElMessage.error).toHaveBeenCalledWith('创建爬虫配置失败')
      }
    })
  })

  describe('并发操作处理', () => {
    it('应该正确处理并发的获取请求', async () => {
      const store = useCrawlerStore()
      const mockConfigs1 = [{ id: '1', name: '配置1' }]
      const mockConfigs2 = [{ id: '2', name: '配置2' }]

      vi.mocked(crawlerApi.getCrawlerConfigs)
        .mockResolvedValueOnce(mockConfigs1)
        .mockResolvedValueOnce(mockConfigs2)

      const [result1, result2] = await Promise.all([
        store.fetchConfigs(),
        store.fetchConfigs()
      ])

      expect(store.configs).toEqual(mockConfigs2)
    })

    it('应该正确处理并发的更新操作', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const update1 = { name: '更新1' }
      const update2 = { name: '更新2' }

      const mockResponse1 = {
        id: configId,
        ...update1,
        updatedAt: '2025-02-04T10:00:00Z'
      }

      const mockResponse2 = {
        id: configId,
        ...update2,
        updatedAt: '2025-02-04T10:00:01Z'
      }

      vi.mocked(crawlerApi.updateCrawlerConfig)
        .mockResolvedValueOnce(mockResponse1)
        .mockResolvedValueOnce(mockResponse2)

      vi.mocked(crawlerApi.getCrawlerConfigs)
        .mockResolvedValueOnce([mockResponse1])
        .mockResolvedValueOnce([mockResponse2])

      await Promise.all([
        store.updateConfig(configId, update1),
        store.updateConfig(configId, update2)
      ])

      expect(store.configs[0].name).toBe('更新2')
    })
  })

  describe('状态一致性', () => {
    it('应该在更新操作后保持列表和当前配置的一致性', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const mockConfig = {
        id: configId,
        name: '测试爬虫',
        siteName: '测试站点',
        siteUrl: 'http://example.com',
        frequency: 30,
        enabled: true,
        lastRunTime: null,
        createdAt: '2025-02-04T10:00:00Z',
        updatedAt: '2025-02-04T10:00:00Z'
      }

      const updateData = {
        name: '更新后的名称'
      }

      const updatedConfig = {
        ...mockConfig,
        ...updateData,
        updatedAt: '2025-02-04T10:00:01Z'
      }

      // 设置初始状态
      vi.mocked(crawlerApi.getCrawlerConfigById).mockResolvedValueOnce(mockConfig)
      await store.fetchConfigById(configId)

      // 执行更新
      vi.mocked(crawlerApi.updateCrawlerConfig).mockResolvedValueOnce(updatedConfig)
      vi.mocked(crawlerApi.getCrawlerConfigs).mockResolvedValueOnce([updatedConfig])
      vi.mocked(crawlerApi.getCrawlerConfigById).mockResolvedValueOnce(updatedConfig)

      await store.updateConfig(configId, updateData)

      // 验证状态一致性
      expect(store.configs[0]).toEqual(updatedConfig)
      expect(store.currentConfig).toEqual(updatedConfig)
    })

    it('应该在删除操作后正确清理相关状态', async () => {
      const store = useCrawlerStore()
      const configId = '1'
      const mockConfig = {
        id: configId,
        name: '测试爬虫',
        siteName: '测试站点',
        siteUrl: 'http://example.com',
        frequency: 30,
        enabled: true,
        lastRunTime: null,
        createdAt: '2025-02-04T10:00:00Z',
        updatedAt: '2025-02-04T10:00:00Z'
      }

      // 设置初始状态
      vi.mocked(crawlerApi.getCrawlerConfigById).mockResolvedValueOnce(mockConfig)
      await store.fetchConfigById(configId)

      // 执行删除
      vi.mocked(crawlerApi.deleteCrawlerConfig).mockResolvedValueOnce(undefined)
      vi.mocked(crawlerApi.getCrawlerConfigs).mockResolvedValueOnce([])

      await store.deleteConfig(configId)

      // 验证状态清理
      expect(store.configs).toHaveLength(0)
      expect(store.currentConfig).toBeNull()
    })
  })
}) 