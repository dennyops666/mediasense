import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import * as newsApi from '@/api/news'
import request from '@/utils/request'
import type { NewsItem, NewsCategory, NewsSource } from '@/types/news'

// Mock request
vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('新闻 API', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('getNewsList', () => {
    it('应该正确获取新闻列表', async () => {
      const mockNews: NewsItem[] = [
        {
          id: '1',
          title: '测试新闻',
          content: '测试内容',
          source: '测试来源',
          category: '测试分类',
          publishTime: new Date().toISOString(),
          url: 'http://example.com/news/1'
        }
      ]

      const mockResponse = {
        data: {
          items: mockNews,
          total: 1,
          page: 1,
          pageSize: 10
        }
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await newsApi.getNewsList({})
      expect(result).toEqual(mockResponse.data)
      expect(request.get).toHaveBeenCalledWith('/news', { params: {} })
    })

    it('应该处理获取新闻列表失败的情况', async () => {
      const error = new Error('获取新闻列表失败')
      vi.mocked(request.get).mockRejectedValueOnce(error)

      await expect(newsApi.getNewsList({})).rejects.toThrow('获取新闻列表失败')
    })
  })

  describe('getNewsDetail', () => {
    it('应该正确获取新闻详情', async () => {
      const mockNews: NewsItem = {
        id: '1',
        title: '测试新闻',
        content: '测试内容',
        source: '测试来源',
        category: '测试分类',
        publishTime: new Date().toISOString(),
        url: 'http://example.com/news/1'
      }

      const mockResponse = {
        data: mockNews
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await newsApi.getNewsDetail('1')
      expect(result).toEqual(mockNews)
      expect(request.get).toHaveBeenCalledWith('/news/1')
    })

    it('应该处理新闻不存在的情况', async () => {
      const error = new Error('新闻不存在')
      vi.mocked(request.get).mockRejectedValueOnce(error)

      const newsId = 'non-existent'
      await expect(newsApi.getNewsDetail(newsId)).rejects.toThrow('新闻不存在')
    })
  })

  describe('getCategories', () => {
    it('应该正确获取新闻分类列表', async () => {
      const mockCategories: NewsCategory[] = [
        { id: '1', name: '科技' },
        { id: '2', name: '财经' }
      ]

      const mockResponse = {
        data: mockCategories
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await newsApi.getCategories()
      expect(result).toEqual(mockCategories)
      expect(request.get).toHaveBeenCalledWith('/news/categories')
    })

    it('应该处理获取分类列表失败的情况', async () => {
      const error = new Error('获取分类列表失败')
      vi.mocked(request.get).mockRejectedValueOnce(error)

      await expect(newsApi.getCategories()).rejects.toThrow('获取分类列表失败')
    })
  })

  describe('getSources', () => {
    it('应该正确获取新闻来源列表', async () => {
      const mockSources: NewsSource[] = [
        { id: '1', name: '新华社' },
        { id: '2', name: '人民日报' }
      ]

      const mockResponse = {
        data: mockSources
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await newsApi.getSources()
      expect(result).toEqual(mockSources)
      expect(request.get).toHaveBeenCalledWith('/news/sources')
    })

    it('应该处理获取来源列表失败的情况', async () => {
      const error = new Error('获取来源列表失败')
      vi.mocked(request.get).mockRejectedValueOnce(error)

      await expect(newsApi.getSources()).rejects.toThrow('获取来源列表失败')
    })
  })

  describe('updateNews', () => {
    it('应该正确更新新闻', async () => {
      const newsId = '1'
      const updateData = {
        title: '更新后的标题',
        content: '更新后的内容'
      }

      const mockResponse = {
        data: {
          id: newsId,
          ...updateData,
          source: '测试来源',
          category: '测试分类',
          publishTime: new Date().toISOString(),
          url: 'http://example.com/news/1'
        }
      }

      vi.mocked(request.put).mockResolvedValueOnce(mockResponse)

      const result = await newsApi.updateNews(newsId, updateData)
      expect(result).toEqual(mockResponse.data)
      expect(request.put).toHaveBeenCalledWith(`/news/${newsId}`, updateData)
    })

    it('应该处理更新失败的情况', async () => {
      const error = new Error('更新失败')
      vi.mocked(request.put).mockRejectedValueOnce(error)

      const newsId = '1'
      const updateData = { title: '更新后的标题' }
      await expect(newsApi.updateNews(newsId, updateData)).rejects.toThrow('更新失败')
    })
  })

  describe('deleteNews', () => {
    it('应该正确删除新闻', async () => {
      const newsId = 1
      const mockResponse = {
        data: {
          success: true
        }
      }
      vi.mocked(request.delete).mockResolvedValueOnce(mockResponse)

      const result = await newsApi.deleteNews(newsId)
      expect(result).toBeUndefined()
      expect(request.delete).toHaveBeenCalledWith(`/news/${newsId}`)
    })

    it('应该处理删除失败的情况', async () => {
      const error = new Error('删除失败')
      vi.mocked(request.delete).mockRejectedValueOnce(error)

      const newsId = '1'
      await expect(newsApi.deleteNews(newsId)).rejects.toThrow('删除失败')
    })
  })
})