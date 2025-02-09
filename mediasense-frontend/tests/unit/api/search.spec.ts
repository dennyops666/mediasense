import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import * as searchApi from '@/api/search'
import request from '@/utils/request'
import type { SearchResponse } from '@/types/search'

// Mock request
vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('搜索 API', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('searchNews', () => {
    it('应该正确调用搜索接口', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: '1',
              title: '测试新闻',
              content: '测试内容',
              source: '测试来源',
              publishTime: new Date().toISOString()
            }
          ],
          total: 1,
          page: 1,
          pageSize: 10
        }
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const params = { keyword: '测试', page: 1, pageSize: 10 }
      const result = await searchApi.searchNews(params)
      expect(result).toEqual(mockResponse.data)
      expect(request.get).toHaveBeenCalledWith('/search', { params })
    })

    it('应该处理搜索失败的情况', async () => {
      const mockError = {
        response: {
          data: {
            message: '搜索失败'
          }
        }
      }
      vi.mocked(request.get).mockRejectedValueOnce(mockError)

      const params = { keyword: '测试' }
      await expect(searchApi.searchNews(params)).rejects.toEqual(mockError)
    })
  })

  describe('fetchSearchSuggestions', () => {
    it('应该正确获取搜索建议', async () => {
      const mockResponse = {
        data: ['建议1', '建议2']
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await searchApi.fetchSearchSuggestions('测试')
      expect(result).toEqual(mockResponse.data)
      expect(request.get).toHaveBeenCalledWith('/search/suggestions', {
        params: { keyword: '测试' }
      })
    })

    it('应该处理获取建议失败的情况', async () => {
      const mockError = {
        response: {
          data: {
            message: '获取建议失败'
          }
        }
      }
      vi.mocked(request.get).mockRejectedValueOnce(mockError)

      await expect(searchApi.fetchSearchSuggestions('测试')).rejects.toEqual(mockError)
    })
  })

  describe('fetchHotKeywords', () => {
    it('应该正确获取热门搜索词', async () => {
      const mockResponse = {
        data: ['热词1', '热词2']
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await searchApi.fetchHotKeywords()
      expect(result).toEqual(mockResponse.data)
      expect(request.get).toHaveBeenCalledWith('/search/hot')
    })

    it('应该处理获取热门搜索词失败的情况', async () => {
      const mockError = {
        response: {
          data: {
            message: '获取热门搜索词失败'
          }
        }
      }
      vi.mocked(request.get).mockRejectedValueOnce(mockError)

      await expect(searchApi.fetchHotKeywords()).rejects.toEqual(mockError)
    })
  })

  describe('getSearchHistory', () => {
    it('应该正确获取搜索历史', async () => {
      const mockResponse = {
        data: ['历史1', '历史2']
      }

      vi.mocked(request.get).mockResolvedValueOnce(mockResponse)

      const result = await searchApi.getSearchHistory()
      expect(result).toEqual(mockResponse.data)
      expect(request.get).toHaveBeenCalledWith('/search/history')
    })

    it('应该处理获取搜索历史失败的情况', async () => {
      const mockError = {
        response: {
          data: {
            message: '获取搜索历史失败'
          }
        }
      }
      vi.mocked(request.get).mockRejectedValueOnce(mockError)

      await expect(searchApi.getSearchHistory()).rejects.toEqual(mockError)
    })
  })

  describe('clearSearchHistory', () => {
    it('应该正确清除搜索历史', async () => {
      const mockResponse = {
        data: {
          success: true
        }
      }
      vi.mocked(request.delete).mockResolvedValueOnce(mockResponse)

      const result = await searchApi.clearSearchHistory()
      expect(result).toEqual(mockResponse.data)
      expect(request.delete).toHaveBeenCalledWith('/search/history')
    })

    it('应该处理清除搜索历史失败的情况', async () => {
      const mockError = {
        response: {
          data: {
            message: '清除历史记录失败'
          }
        }
      }
      vi.mocked(request.delete).mockRejectedValueOnce(mockError)

      await expect(searchApi.clearSearchHistory()).rejects.toEqual(mockError)
    })
  })
}) 