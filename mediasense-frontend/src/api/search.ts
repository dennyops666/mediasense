import request from '@/utils/request'
import type { SearchParams, SearchResponse } from '@/types/search'

/**
 * 搜索新闻
 * @param params 搜索参数
 * @returns 搜索结果
 */
export const searchNews = async (params: SearchParams): Promise<SearchResponse> => {
  const response = await request.get('/api/search', {
    params: {
      ...params,
      type: params.type || undefined,
      date: params.date || undefined
    }
  })
  return {
    items: response.data.items.map((item: any) => ({
      id: String(item.id),
      title: item.title,
      content: item.content,
      source: item.source,
      publishTime: item.publishTime,
      relevanceScore: Number(item.relevanceScore || item.score || 0)
    })),
    total: response.data.total
  }
}

/**
 * 获取搜索建议
 * @param keyword 搜索关键词
 * @returns 搜索建议列表
 */
export const fetchSearchSuggestions = async (keyword: string): Promise<string[]> => {
  const response = await request.get('/api/search/suggestions', {
    params: { keyword }
  })
  return Array.isArray(response.data) ? response.data : []
}

/**
 * 获取热门搜索词
 */
export const fetchHotKeywords = async (): Promise<string[]> => {
  const response = await request.get('/search/hot')
  return response.data
}

/**
 * 获取搜索历史
 */
export const getSearchHistory = async (): Promise<string[]> => {
  const response = await request.get('/search/history')
  return response.data
}

/**
 * 清除搜索历史
 */
export const clearSearchHistory = async (): Promise<{ success: boolean }> => {
  const response = await request.delete('/search/history')
  return response.data
}

export const searchApi = {
  async search(params: SearchParams) {
    const response = await request.get('/search', { params })
    return response.data
  },

  async getSuggestions(keyword: string) {
    const response = await request.get('/search/suggestions', {
      params: { keyword }
    })
    return response.data
  }
}

export default {
  searchNews,
  fetchSearchSuggestions,
  fetchHotKeywords,
  getSearchHistory,
  clearSearchHistory
} 