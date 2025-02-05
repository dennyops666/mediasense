import request from '@/utils/request'
import type { SearchParams, SearchResults } from '@/types/search'

/**
 * 搜索新闻
 */
export const searchNews = async (params: SearchParams): Promise<SearchResults> => {
  const response = await request({
    url: '/api/search',
    method: 'get',
    params
  })
  return response.data
}

/**
 * 获取搜索建议
 */
export const fetchSearchSuggestions = async (keyword: string): Promise<string[]> => {
  const response = await request({
    url: '/api/search/suggestions',
    method: 'get',
    params: { keyword }
  })
  return response.data
}

/**
 * 获取热门搜索词
 */
export const fetchHotKeywords = async () => {
  const response = await request({
    url: '/api/search/hot',
    method: 'get'
  })
  return response.data
}

/**
 * 获取搜索历史
 */
export async function getSearchHistory(): Promise<string[]> {
  return request.get('/search/history')
}

/**
 * 清除搜索历史
 */
export async function clearSearchHistory(): Promise<void> {
  await request.post('/search/history/clear')
}

export default {
  searchNews,
  fetchSearchSuggestions,
  fetchHotKeywords,
  getSearchHistory,
  clearSearchHistory
} 