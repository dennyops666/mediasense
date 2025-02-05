import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as newsApi from '@/api/news'
import request from '@/utils/request'
import type { NewsFilter } from '@/types/api'

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
    vi.clearAllMocks()
  })

  describe('getNewsList', () => {
    it('应该正确获取新闻列表', async () => {
      const mockData = {
        total: 100,
        items: [
          {
            id: '1',
            title: '测试新闻1',
            content: '新闻内容1',
            summary: '新闻摘要1',
            source: '新闻来源1',
            author: '作者1',
            publishTime: '2025-02-04T10:00:00Z',
            status: 'published',
            category: '科技',
            tags: ['标签1', '标签2'],
            url: 'http://example.com/news/1',
            createdAt: '2025-02-04T10:00:00Z',
            updatedAt: '2025-02-04T10:00:00Z'
          }
        ]
      }

      vi.mocked(request.get).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })

      const filter: NewsFilter = {
        category: '科技',
        page: 1,
        pageSize: 10
      }

      const result = await newsApi.getNewsList(filter)

      expect(request.get).toHaveBeenCalledWith('/news', { params: filter })
      expect(result).toEqual(mockData)
    })
  })

  describe('getNewsDetail', () => {
    it('应该正确获取新闻详情', async () => {
      const mockData = {
        id: '1',
        title: '测试新闻1',
        content: '新闻内容1',
        summary: '新闻摘要1',
        source: '新闻来源1',
        author: '作者1',
        publishTime: '2025-02-04T10:00:00Z',
        status: 'published',
        category: '科技',
        tags: ['标签1', '标签2'],
        url: 'http://example.com/news/1',
        createdAt: '2025-02-04T10:00:00Z',
        updatedAt: '2025-02-04T10:00:00Z'
      }

      vi.mocked(request.get).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })

      const newsId = '1'
      const result = await newsApi.getNewsDetail(newsId)

      expect(request.get).toHaveBeenCalledWith(`/news/${newsId}`)
      expect(result).toEqual(mockData)
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
      const mockData = ['科技', '财经', '体育', '娱乐']

      vi.mocked(request.get).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })

      const result = await newsApi.getCategories()

      expect(request.get).toHaveBeenCalledWith('/news/categories')
      expect(result).toEqual(mockData)
    })
  })

  describe('getSources', () => {
    it('应该正确获取新闻来源列表', async () => {
      const mockData = ['来源1', '来源2', '来源3']

      vi.mocked(request.get).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })

      const result = await newsApi.getSources()

      expect(request.get).toHaveBeenCalledWith('/news/sources')
      expect(result).toEqual(mockData)
    })
  })

  describe('updateNews', () => {
    it('应该正确更新新闻', async () => {
      const mockData = {
        id: '1',
        title: '更新后的标题',
        content: '更新后的内容',
        status: 'published'
      }

      vi.mocked(request.put).mockResolvedValueOnce({
        status: 'success',
        data: mockData
      })

      const newsId = '1'
      const updateData = {
        title: '更新后的标题',
        content: '更新后的内容'
      }

      const result = await newsApi.updateNews(newsId, updateData)

      expect(request.put).toHaveBeenCalledWith(`/news/${newsId}`, updateData)
      expect(result).toEqual(mockData)
    })
  })

  describe('deleteNews', () => {
    it('应该正确删除新闻', async () => {
      vi.mocked(request.delete).mockResolvedValueOnce({
        status: 'success',
        data: {}
      })

      const newsId = '1'
      await newsApi.deleteNews(newsId)

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