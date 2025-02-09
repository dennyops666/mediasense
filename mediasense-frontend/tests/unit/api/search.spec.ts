import { describe, it, expect, beforeEach, vi } from 'vitest'
import * as searchApi from '@/api/search'
import axios from 'axios'

vi.mock('axios')

describe('Search API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('searchNews', () => {
    it('应该正确调用搜索接口', async () => {
      const mockResponse = {
        data: {
          items: [
            { id: 1, title: '测试新闻1', content: '内容1', publishTime: '2024-03-20T10:00:00Z' },
            { id: 2, title: '测试新闻2', content: '内容2', publishTime: '2024-03-20T11:00:00Z' }
          ],
          total: 2
        }
      }
      vi.mocked(axios.get).mockResolvedValueOnce(mockResponse)

      const params = {
        keyword: '测试',
        page: 1,
        pageSize: 10,
        type: 'news',
        startDate: '2024-03-20',
        endDate: '2024-03-21',
        sortBy: 'publishTime',
        sortOrder: 'desc'
      }
      const result = await searchApi.searchNews(params)

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith('/api/search', { params })
    })

    it('应该处理搜索失败的情况', async () => {
      const error = new Error('搜索失败')
      vi.mocked(axios.get).mockRejectedValueOnce(error)

      const params = { keyword: '测试' }
      await expect(searchApi.searchNews(params)).rejects.toThrow('搜索失败')
    })
  })

  describe('fetchSearchSuggestions', () => {
    it('应该正确获取搜索建议', async () => {
      const mockResponse = {
        data: ['建议1', '建议2', '建议3']
      }
      vi.mocked(axios.get).mockResolvedValueOnce(mockResponse)

      const keyword = '测试'
      const result = await searchApi.fetchSearchSuggestions(keyword)

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith('/api/search/suggestions', {
        params: { keyword }
      })
    })

    it('应该处理获取建议失败的情况', async () => {
      const error = new Error('获取建议失败')
      vi.mocked(axios.get).mockRejectedValueOnce(error)

      await expect(searchApi.fetchSearchSuggestions('测试')).rejects.toThrow('获取建议失败')
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
      vi.mocked(axios.get).mockResolvedValueOnce(mockResponse)

      const result = await searchApi.fetchHotKeywords()

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith('/api/search/hot')
    })

    it('应该处理获取热门搜索词失败的情况', async () => {
      const error = new Error('获取热门搜索词失败')
      vi.mocked(axios.get).mockRejectedValueOnce(error)

      await expect(searchApi.fetchHotKeywords()).rejects.toThrow('获取热门搜索词失败')
    })
  })

  describe('getSearchHistory', () => {
    it('应该正确获取搜索历史', async () => {
      const mockResponse = {
        data: [
          { keyword: '历史1', timestamp: '2024-03-20T10:00:00Z' },
          { keyword: '历史2', timestamp: '2024-03-20T09:00:00Z' },
          { keyword: '历史3', timestamp: '2024-03-20T08:00:00Z' }
        ]
      }
      vi.mocked(axios.get).mockResolvedValueOnce(mockResponse)

      const result = await searchApi.getSearchHistory()

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith('/api/search/history')
    })

    it('应该处理获取搜索历史失败的情况', async () => {
      const error = new Error('获取搜索历史失败')
      vi.mocked(axios.get).mockRejectedValueOnce(error)

      await expect(searchApi.getSearchHistory()).rejects.toThrow('获取搜索历史失败')
    })
  })

  describe('clearSearchHistory', () => {
    it('应该正确清除搜索历史', async () => {
      const mockResponse = {
        data: { success: true }
      }
      vi.mocked(axios.delete).mockResolvedValueOnce(mockResponse)

      const result = await searchApi.clearSearchHistory()

      expect(result).toEqual(mockResponse.data)
      expect(axios.delete).toHaveBeenCalledWith('/api/search/history')
    })

    it('应该处理清除搜索历史失败的情况', async () => {
      const error = new Error('清除搜索历史失败')
      vi.mocked(axios.delete).mockRejectedValueOnce(error)

      await expect(searchApi.clearSearchHistory()).rejects.toThrow('清除搜索历史失败')
    })
  })

  describe('searchApi', () => {
    it('应该正确调用 search 方法', async () => {
      const mockResponse = {
        data: {
          items: [
            { id: 1, title: '测试新闻1', content: '内容1', publishTime: '2024-03-20T10:00:00Z' }
          ],
          total: 1
        }
      }
      vi.mocked(axios.get).mockResolvedValueOnce(mockResponse)

      const params = {
        keyword: '测试',
        type: 'news',
        page: 1,
        pageSize: 10
      }
      const result = await searchApi.searchApi.search(params)

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith('/api/search', { params })
    })

    it('应该正确调用 getSuggestions 方法', async () => {
      const mockResponse = {
        data: ['建议1', '建议2', '建议3']
      }
      vi.mocked(axios.get).mockResolvedValueOnce(mockResponse)

      const keyword = '测试'
      const result = await searchApi.searchApi.getSuggestions(keyword)

      expect(result).toEqual(mockResponse.data)
      expect(axios.get).toHaveBeenCalledWith('/api/search/suggestions', {
        params: { keyword }
      })
    })
  })
}) 