import { defineStore } from 'pinia'
import { ref } from 'vue'
import { searchNews, fetchSearchSuggestions, getSearchHistory, clearSearchHistory as clearHistory } from '@/api/search'
import type { SearchParams, SearchResult } from '@/types/search'
import { ElMessage } from 'element-plus'

export const useSearchStore = defineStore('search', () => {
  // 状态
  const searchResults = ref<SearchResult[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const searchHistory = ref<string[]>([])
  const suggestions = ref<string[]>([])
  const searchTime = ref(0)

  // 搜索
  const search = async (params: SearchParams) => {
    loading.value = true
    error.value = null
    const startTime = Date.now()
    
    try {
      const response = await searchNews(params)
      searchResults.value = response.items
      total.value = response.total
      searchTime.value = (Date.now() - startTime) / 1000
      
      // 添加到搜索历史
      if (params.keyword) {
        addToHistory(params.keyword)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '搜索失败'
      searchResults.value = []
      total.value = 0
      searchTime.value = 0
    } finally {
      loading.value = false
    }
  }

  // 获取搜索建议
  const getSuggestions = async (keyword: string) => {
    if (!keyword.trim()) {
      suggestions.value = []
      return
    }
    
    try {
      const result = await fetchSearchSuggestions(keyword)
      suggestions.value = result
    } catch (err) {
      suggestions.value = []
      console.error('获取搜索建议失败:', err)
    }
  }

  // 获取搜索历史
  const getHistory = async () => {
    try {
      const history = await getSearchHistory()
      searchHistory.value = history
    } catch (err) {
      console.error('获取搜索历史失败:', err)
    }
  }

  // 清空搜索历史
  const clearHistory = async () => {
    try {
      await clearHistory()
      searchHistory.value = []
      ElMessage.success('搜索历史已清空')
    } catch (err) {
      ElMessage.error('清空搜索历史失败')
    }
  }

  // 添加到搜索历史
  const addToHistory = async (keyword: string) => {
    if (!keyword.trim()) return
    
    try {
      // 避免重复添加
      if (!searchHistory.value.includes(keyword)) {
        searchHistory.value.unshift(keyword)
        // 限制历史记录数量
        if (searchHistory.value.length > 10) {
          searchHistory.value.pop()
        }
      }
    } catch (err) {
      console.error('添加搜索历史失败:', err)
    }
  }

  return {
    // 状态
    searchResults,
    total,
    loading,
    error,
    searchHistory,
    suggestions,
    searchTime,
    
    // 方法
    search,
    getSuggestions,
    getHistory,
    clearHistory,
    addToHistory
  }
}) 