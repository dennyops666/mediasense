import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useCrawlerStore } from '../../../src/stores/crawler'
import * as crawlerApi from '../../../src/api/crawler'
import { ElMessage } from 'element-plus'
import type { CrawlerConfig, CrawlerTask, CrawlerData } from '../../../src/types/crawler'

vi.mock('../../../src/api/crawler')
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  }
}))

describe('爬虫配置管理', () => {
  let store: ReturnType<typeof useCrawlerStore>

  const mockCrawlerConfig: CrawlerConfig = {
    id: '1',
    name: '测试配置',
    type: 'news',
    url: 'http://example.com',
    enabled: true,
    targetUrl: 'http://example.com',
    method: 'GET',
    headers: [],
    selectors: [
      { field: 'title', selector: '.title', type: 'css' }
    ],
    timeout: 30,
    retries: 3,
    concurrency: 1,
    selector: {
      title: '.title',
      content: '.content'
    },
    userAgent: 'Mozilla/5.0'
  }

  const mockTask: CrawlerTask = {
    id: '1',
    name: '测试任务',
    type: 'news',
    schedule: '0 0 * * *',
    config: {},
    status: 'running',
    lastRunTime: '2024-03-20T10:00:00Z',
    count: 100,
    configId: '1',
    startTime: '2024-03-20T10:00:00Z',
    totalItems: 100,
    successItems: 80,
    failedItems: 20,
    createdAt: '2024-03-20T10:00:00Z',
    updatedAt: '2024-03-20T10:00:00Z'
  }

  const mockData: CrawlerData = {
    id: '1',
    taskId: '1',
    title: '测试数据',
    content: '测试内容',
    url: 'http://example.com',
    source: '测试来源',
    category: '测试分类',
    publishTime: '2024-03-20T10:00:00Z',
    crawlTime: '2024-03-20T10:00:00Z',
    rawData: {}
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useCrawlerStore()
    vi.clearAllMocks()

    // 模拟 API 方法
    vi.mocked(crawlerApi.getCrawlerConfigs).mockResolvedValue([mockCrawlerConfig])
    vi.mocked(crawlerApi.createCrawlerConfig).mockResolvedValue(mockCrawlerConfig)
    vi.mocked(crawlerApi.updateCrawlerConfig).mockResolvedValue(mockCrawlerConfig)
    vi.mocked(crawlerApi.deleteCrawlerConfig).mockResolvedValue(undefined)
    vi.mocked(crawlerApi.getTasks).mockResolvedValue({
      data: [mockTask],
      total: 1,
      page: 1,
      pageSize: 10
    })
    vi.mocked(crawlerApi.startTask).mockResolvedValue({ success: true })
    vi.mocked(crawlerApi.stopTask).mockResolvedValue({ success: true })
    vi.mocked(crawlerApi.batchStartTasks).mockResolvedValue({ success: true })
    vi.mocked(crawlerApi.batchStopTasks).mockResolvedValue({ success: true })
    vi.mocked(crawlerApi.getData).mockResolvedValue({
      data: [mockData],
      total: 1,
      page: 1,
      pageSize: 10
    })
    vi.mocked(crawlerApi.deleteData).mockResolvedValue(undefined)
    vi.mocked(crawlerApi.batchDeleteData).mockResolvedValue(undefined)
    vi.mocked(crawlerApi.exportData).mockResolvedValue(new Blob(['test data'], { type: 'application/json' }))
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('配置管理', () => {
    it('应该成功获取配置列表', async () => {
      await store.fetchConfigs()
      expect(store.configs).toEqual([mockCrawlerConfig])
      expect(store.loading).toBe(false)
    })

    it('应该成功创建新配置', async () => {
      await store.createConfig(mockCrawlerConfig)
      expect(crawlerApi.createCrawlerConfig).toHaveBeenCalledWith(mockCrawlerConfig)
      expect(ElMessage.success).toHaveBeenCalledWith('创建爬虫配置成功')
    })

    it('应该成功更新配置', async () => {
      const updatedConfig = { ...mockCrawlerConfig, name: '更新后的配置' }
      await store.updateConfig('1', updatedConfig)
      expect(crawlerApi.updateCrawlerConfig).toHaveBeenCalledWith('1', updatedConfig)
      expect(ElMessage.success).toHaveBeenCalledWith('更新配置成功')
    })

    it('应该成功删除配置', async () => {
      await store.deleteConfig('1')
      expect(crawlerApi.deleteCrawlerConfig).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('删除配置成功')
    })
  })

  describe('任务管理', () => {
    it('应该成功获取任务列表', async () => {
      await store.fetchTasks({ page: 1, pageSize: 10 })

      expect(store.tasks).toEqual([mockTask])
      expect(store.loading).toBe(false)
    })

    it('应该成功启动任务', async () => {
      await store.startTask('1')
      expect(crawlerApi.startTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('启动任务成功')
    })

    it('应该成功停止任务', async () => {
      await store.stopTask('1')
      expect(crawlerApi.stopTask).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('停止任务成功')
    })

    it('应该成功批量启动任务', async () => {
      await store.batchStartTasks(['1', '2'])
      expect(crawlerApi.batchStartTasks).toHaveBeenCalledWith(['1', '2'])
      expect(ElMessage.success).toHaveBeenCalledWith('批量启动任务成功')
    })
  })

  describe('数据管理', () => {
    it('应该成功获取爬取数据', async () => {
      await store.fetchData({ page: 1, pageSize: 10 })

      expect(store.data).toEqual([mockData])
      expect(store.loading).toBe(false)
    })

    it('应该成功删除数据', async () => {
      await store.deleteData('1')
      expect(crawlerApi.deleteData).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('删除数据成功')
    })

    it('应该成功批量删除数据', async () => {
      await store.batchDeleteData(['1', '2'])
      expect(crawlerApi.batchDeleteData).toHaveBeenCalledWith(['1', '2'])
      expect(ElMessage.success).toHaveBeenCalledWith('批量删除数据成功')
    })

    it('应该成功导出数据', async () => {
      await store.exportData({ taskId: '1' })

      expect(crawlerApi.exportData).toHaveBeenCalledWith({ taskId: '1' })
      expect(ElMessage.success).toHaveBeenCalledWith('导出成功')
    })
  })

  describe('错误处理', () => {
    it('应该处理获取配置失败的情况', async () => {
      const error = new Error('获取失败')
      vi.mocked(crawlerApi.getCrawlerConfigs).mockRejectedValue(error)

      try {
        await store.fetchConfigs()
      } catch (err) {
        expect(store.loading).toBe(false)
        expect(ElMessage.error).toHaveBeenCalled()
      }
    })

    it('应该处理创建配置失败的情况', async () => {
      const error = new Error('创建失败')
      vi.mocked(crawlerApi.createCrawlerConfig).mockRejectedValue(error)

      try {
        await store.createConfig(mockCrawlerConfig)
      } catch (err) {
        expect(ElMessage.error).toHaveBeenCalled()
      }
    })

    it('应该处理任务操作失败的情况', async () => {
      const error = new Error('操作失败')
      vi.mocked(crawlerApi.startTask).mockRejectedValue(error)

      try {
        await store.startTask('1')
      } catch (err) {
        expect(ElMessage.error).toHaveBeenCalled()
      }
    })
  })
}) 