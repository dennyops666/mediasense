import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useNewsStore } from '@/stores/news'
import * as newsApi from '@/api/news'
import type { NewsItem, NewsFilter } from '@/types/news'

vi.mock('@/api/news')
vi.mock('element-plus')

describe('新闻 Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('获取新闻列表', () => {
    it('应该正确获取新闻列表', async () => {
      const store = useNewsStore()
      const mockNews: NewsItem = {
        id: '1',
        title: '测试新闻1',
        content: '内容1',
        category: '科技',
        source: '来源1',
        publishTime: '2024-03-20T10:00:00Z',
        status: 'published'
      }
      const mockResponse = {
        list: [mockNews],
        total: 1
      }

      vi.mocked(newsApi.getNewsList).mockResolvedValueOnce(mockResponse)

      await store.fetchNewsList({
        page: 1,
        pageSize: 10
      })

      expect(newsApi.getNewsList).toHaveBeenCalled()
      expect(store.newsList).toEqual(mockResponse.list)
      expect(store.total).toBe(mockResponse.total)
    })

    it('应该处理获取新闻列表失败的情况', async () => {
      const store = useNewsStore()
      const error = new Error('获取失败')

      vi.mocked(newsApi.getNewsList).mockRejectedValueOnce(error)

      await expect(store.fetchNewsList({
        page: 1,
        pageSize: 10
      })).rejects.toThrow('获取失败')
    })
  })

  describe('获取新闻详情', () => {
    it('应该正确获取新闻详情', async () => {
      const store = useNewsStore()
      const mockNews: NewsItem = {
        id: '1',
        title: '测试新闻',
        content: '内容',
        category: '科技',
        source: '来源1',
        publishTime: '2024-03-20T10:00:00Z',
        status: 'published'
      }

      vi.mocked(newsApi.getNewsDetail).mockResolvedValueOnce(mockNews)

      await store.fetchNewsDetail('1')

      expect(newsApi.getNewsDetail).toHaveBeenCalledWith('1')
      expect(store.currentNews).toEqual(mockNews)
    })
  })

  describe('获取分类和来源', () => {
    it('应该正确获取新闻分类列表', async () => {
      const store = useNewsStore()
      const mockCategories = [
        { id: '1', name: '科技' },
        { id: '2', name: '财经' },
        { id: '3', name: '体育' },
        { id: '4', name: '娱乐' }
      ]

      vi.mocked(newsApi.getCategories).mockResolvedValueOnce(mockCategories)

      await store.fetchCategories()

      expect(newsApi.getCategories).toHaveBeenCalled()
      expect(store.categories).toEqual(mockCategories.map(c => c.name))
    })

    it('应该正确获取新闻来源列表', async () => {
      const store = useNewsStore()
      const mockSources = [
        { id: '1', name: '来源1' },
        { id: '2', name: '来源2' },
        { id: '3', name: '来源3' }
      ]

      vi.mocked(newsApi.getSources).mockResolvedValueOnce(mockSources)

      await store.fetchSources()

      expect(newsApi.getSources).toHaveBeenCalled()
      expect(store.sources).toEqual(mockSources.map(s => s.name))
    })
  })

  describe('更新和删除新闻', () => {
    it('应该正确更新新闻', async () => {
      const store = useNewsStore()
      const mockNews: NewsItem = {
        id: '1',
        title: '更新后的标题',
        content: '更新后的内容',
        category: '科技',
        source: '来源1',
        publishTime: '2024-03-20T10:00:00Z',
        status: 'published'
      }

      vi.mocked(newsApi.updateNews).mockResolvedValueOnce(mockNews)

      const updateData = {
        title: '更新后的标题',
        content: '更新后的内容'
      }

      await store.updateNews('1', updateData)

      expect(newsApi.updateNews).toHaveBeenCalledWith('1', updateData)
    })

    it('应该正确删除新闻', async () => {
      const store = useNewsStore()
      
      vi.mocked(newsApi.deleteNews).mockResolvedValueOnce()

      await store.deleteNews('1')

      expect(newsApi.deleteNews).toHaveBeenCalledWith('1')
    })
  })

  describe('过滤和排序', () => {
    it('应该正确应用过滤条件', async () => {
      const store = useNewsStore()
      const filter: NewsFilter = {
        page: 1,
        pageSize: 10,
        keyword: '',
        category: '科技',
        source: '来源1',
        startDate: '',
        endDate: '',
        sortBy: 'publishTime',
        sortOrder: 'desc'
      }

      const mockNews: NewsItem = {
        id: '1',
        title: '测试新闻',
        content: '内容',
        category: '科技',
        source: '来源1',
        publishTime: '2024-03-20T10:00:00Z',
        status: 'published'
      }

      vi.mocked(newsApi.getNewsList).mockResolvedValueOnce({
        list: [mockNews],
        total: 1
      })

      await store.applyFilter(filter)

      expect(newsApi.getNewsList).toHaveBeenCalledWith(filter)
      expect(store.filter).toEqual(filter)
    })

    it('应该正确重置过滤条件', () => {
      const store = useNewsStore()
      store.filter = {
        page: 2,
        pageSize: 20,
        keyword: '测试',
        category: '科技',
        source: '来源1',
        startDate: '2024-03-01',
        endDate: '2024-03-20',
        sortBy: 'title',
        sortOrder: 'asc'
      }

      store.resetFilter()

      expect(store.filter).toEqual({
        page: 1,
        pageSize: 10,
        keyword: '',
        category: '',
        source: '',
        startDate: '',
        endDate: '',
        sortBy: 'publishTime',
        sortOrder: 'desc'
      })
    })
  })
}) 