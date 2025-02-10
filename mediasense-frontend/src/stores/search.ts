import { defineStore } from 'pinia'
import { ref } from 'vue'
import { searchNews, fetchSearchSuggestions } from '@/api/search'
import type { SearchParams, SearchResult } from '@/types/search'
import { ElMessage } from 'element-plus'

export const useSearchStore = defineStore('search', () => {
  // 状态
  const searchResults = ref<SearchResult[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const suggestions = ref<string[]>([])

  // 搜索
  const search = async (params: SearchParams) => {
    loading.value = true
    error.value = null

    try {
      const response = await searchNews(params)
      return {
        items: response.items,
        total: response.total
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '搜索失败'
      ElMessage.error(error.value)
      return {
        items: [],
        total: 0
      }
    } finally {
      loading.value = false
    }
  }

  // 获取搜索建议
  const getSuggestions = async (keyword: string): Promise<string[]> => {
    if (!keyword.trim()) {
      return []
    }
    
    try {
      return await fetchSearchSuggestions(keyword)
    } catch (err) {
      console.error('获取搜索建议失败:', err)
      return []
    }
  }

  // 清空搜索历史
  const clearHistory = () => {
    localStorage.removeItem('searchHistory')
  }

  return {
    // 状态
    searchResults,
    total,
    loading,
    error,
    suggestions,
    
    // 方法
    search,
    getSuggestions,
    clearHistory
  }
}) 