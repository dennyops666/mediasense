import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as searchApi from '@/api/search'
import request from '@/utils/request'
import type { SearchParams } from '@/types/search'

vi.mock('@/utils/request', () => {
  return {
    default: vi.fn()
  }
})

describe('搜索 API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('searchNews', () => {
    it('应该正确执行搜索请求', async () => {
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
          ],
          facets: {
            categories: {
              '科技': 50,
              '财经': 30,
              '体育': 20
            },
            sources: {
              '来源1': 40,
              '来源2': 35,
              '来源3': 25
            }
          }
        }
      }

      vi.mocked(request).mockResolvedValueOnce(mockResponse)

      const params: SearchParams = {
        keyword: '测试关键词',
        category: '科技',
        source: '来源1',
        dateRange: ['2025-02-01', '2025-02-04'] as [Date, Date],
        sortBy: 'relevance',
        order: 'desc',
        page: 1,
        pageSize: 10
      }

      const result = await searchApi.searchNews(params)

      expect(request).toHaveBeenCalledWith({
        url: '/api/search',
        method: 'get',
        params
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('应该处理搜索失败的情况', async () => {
      const error = new Error('搜索失败')
      vi.mocked(request).mockRejectedValueOnce(error)

      const params: SearchParams = {
        keyword: '测试关键词',
        category: '',
        source: '',
        dateRange: null,
        sortBy: 'relevance',
        order: 'desc',
        page: 1,
        pageSize: 10
      }

      await expect(searchApi.searchNews(params)).rejects.toThrow('搜索失败')
    })
  })

  describe('fetchSearchSuggestions', () => {
    it('应该正确获取搜索建议', async () => {
      const mockResponse = {
        data: [
          '建议1',
          '建议2',
          '建议3'
        ]
      }

      vi.mocked(request).mockResolvedValueOnce(mockResponse)

      const keyword = '测试'
      const result = await searchApi.fetchSearchSuggestions(keyword)

      expect(request).toHaveBeenCalledWith({
        url: '/api/search/suggestions',
        method: 'get',
        params: { keyword }
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('应该在关键词为空时返回空数组', async () => {
      const mockResponse = {
        data: []
      }
      vi.mocked(request).mockResolvedValueOnce(mockResponse)

      const result = await searchApi.fetchSearchSuggestions('')
      expect(result).toEqual([])
    })
  })

  describe('fetchHotKeywords', () => {
    it('应该正确获取热门搜索词', async () => {
      const mockResponse = {
        data: [
          { keyword: '热词1', count: 100 },
          { keyword: '热词2', count: 80 },
          { keyword: '热词3', count: 60 }
        ]
      }

      vi.mocked(request).mockResolvedValueOnce(mockResponse)

      const result = await searchApi.fetchHotKeywords()

      expect(request).toHaveBeenCalledWith({
        url: '/api/search/hot',
        method: 'get'
      })
      expect(result).toEqual(mockResponse.data)
    })
  })
}) 