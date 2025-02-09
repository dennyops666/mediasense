import request from '@/utils/request'
import type { SearchParams, SearchResponse } from '@/types/search'

/**
 * 搜索新闻
 */
export const searchNews = async (params: SearchParams): Promise<SearchResponse> => {
  const response = await request.get('/search', { params })
  return response.data
}

/**
 * 获取搜索建议
 */
export const fetchSearchSuggestions = async (keyword: string): Promise<string[]> => {
  const response = await request.get('/search/suggestions', {
    params: { keyword }
  })
  return response.data
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