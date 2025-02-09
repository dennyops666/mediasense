import request from '@/utils/request'
import type { SearchParams, SearchResponse } from '@/types/search'

/**
 * 搜索新闻
 */
export const searchNews = async (params: SearchParams): Promise<SearchResponse> => {
  const response = await request.get('/api/search', { params })
  return response.data
}

/**
 * 获取搜索建议
 */
export const fetchSearchSuggestions = async (keyword: string): Promise<string[]> => {
  const response = await request.get('/api/search/suggestions', {
    params: { keyword }
  })
  return response.data
}

/**
 * 获取热门搜索词
 */
export const fetchHotKeywords = async (): Promise<string[]> => {
  const response = await request.get('/api/search/hot')
  return response.data
}

/**
 * 获取搜索历史
 */
export const getSearchHistory = async (): Promise<string[]> => {
  const response = await request.get('/api/search/history')
  return response.data
}

/**
 * 清除搜索历史
 */
export const clearSearchHistory = async (): Promise<void> => {
  try {
    await request.delete('/api/search/history')
  } catch (error) {
    throw new Error('清除搜索历史失败')
  }
}

export const searchApi = {
  async search(params: SearchParams) {
    const response = await request.get('/api/search', { params })
    return response.data
  },

  async getSuggestions(keyword: string) {
    const response = await request.get('/api/search/suggestions', {
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