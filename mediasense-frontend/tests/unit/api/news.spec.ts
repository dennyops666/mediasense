import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as newsApi from '@/api/news'
import axios from 'axios'
import type { NewsFilter, NewsItem, NewsUpdateData } from '@/types/api'

vi.mock('axios')

describe('新闻 API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getNewsList', () => {
    it('应该正确获取新闻列表', async () => {
      const mockResponse = {
        data: {
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
      }

      vi.mocked(axios.get).mockResolvedValueOnce(mockResponse)

      const filter: NewsFilter = {
        category: '科技',
        page: 1,
        pageSize: 10,
        keyword: '',
        source: '',
        startDate: '',
        endDate: '',
        sortBy: 'publishTime',
        sortOrder: 'desc'
      }

      const result = await newsApi.getNewsList(filter)

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith('/api/news', { params: filter })
    })

    it('应该处理获取新闻列表失败的情况', async () => {
      const error = new Error('获取新闻列表失败')
      vi.mocked(axios.get).mockRejectedValueOnce(error)

      await expect(newsApi.getNewsList({})).rejects.toThrow('获取新闻列表失败')
    })
  })

  describe('getNewsDetail', () => {
    it('应该正确获取新闻详情', async () => {
      const mockResponse = {
        data: {
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
      }

      vi.mocked(axios.get).mockResolvedValueOnce(mockResponse)

      const newsId = '1'
      const result = await newsApi.getNewsDetail(newsId)

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith(`/api/news/${newsId}`)
    })

    it('应该处理新闻不存在的情况', async () => {
      const error = new Error('新闻不存在')
      vi.mocked(axios.get).mockRejectedValueOnce(error)

      const newsId = 'non-existent'
      await expect(newsApi.getNewsDetail(newsId)).rejects.toThrow('新闻不存在')
    })
  })

  describe('getCategories', () => {
    it('应该正确获取新闻分类列表', async () => {
      const mockResponse = {
        data: ['科技', '财经', '体育', '娱乐']
      }

      vi.mocked(axios.get).mockResolvedValueOnce(mockResponse)

      const result = await newsApi.getCategories()

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith('/api/news/categories')
    })

    it('应该处理获取分类列表失败的情况', async () => {
      const error = new Error('获取分类列表失败')
      vi.mocked(axios.get).mockRejectedValueOnce(error)

      await expect(newsApi.getCategories()).rejects.toThrow('获取分类列表失败')
    })
  })

  describe('getSources', () => {
    it('应该正确获取新闻来源列表', async () => {
      const mockResponse = {
        data: ['来源1', '来源2', '来源3']
      }

      vi.mocked(axios.get).mockResolvedValueOnce(mockResponse)

      const result = await newsApi.getSources()

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith('/api/news/sources')
    })

    it('应该处理获取来源列表失败的情况', async () => {
      const error = new Error('获取来源列表失败')
      vi.mocked(axios.get).mockRejectedValueOnce(error)

      await expect(newsApi.getSources()).rejects.toThrow('获取来源列表失败')
    })
  })

  describe('updateNews', () => {
    it('应该正确更新新闻', async () => {
      const mockResponse = {
        data: {
          id: '1',
          title: '更新后的标题',
          content: '更新后的内容',
          status: 'published'
        }
      }

      vi.mocked(axios.put).mockResolvedValueOnce(mockResponse)

      const newsId = '1'
      const updateData: NewsUpdateData = {
        title: '更新后的标题',
        content: '更新后的内容'
      }

      const result = await newsApi.updateNews(newsId, updateData)

      expect(result).toEqual(mockResponse.data)
      expect(axios.put).toHaveBeenCalledWith(`/api/news/${newsId}`, updateData)
    })

    it('应该处理更新失败的情况', async () => {
      const error = new Error('更新失败')
      vi.mocked(axios.put).mockRejectedValueOnce(error)

      const newsId = '1'
      const updateData = { title: '更新后的标题' }
      await expect(newsApi.updateNews(newsId, updateData)).rejects.toThrow('更新失败')
    })
  })

  describe('deleteNews', () => {
    it('应该正确删除新闻', async () => {
      const mockResponse = {
        data: { success: true }
      }

      vi.mocked(axios.delete).mockResolvedValueOnce(mockResponse)

      const newsId = '1'
      const result = await newsApi.deleteNews(newsId)

      expect(result).toEqual(mockResponse.data)
      expect(axios.delete).toHaveBeenCalledWith(`/api/news/${newsId}`)
    })

    it('应该处理删除失败的情况', async () => {
      const error = new Error('删除失败')
      vi.mocked(axios.delete).mockRejectedValueOnce(error)

      const newsId = '1'
      await expect(newsApi.deleteNews(newsId)).rejects.toThrow('删除失败')
    })
  })
}) 