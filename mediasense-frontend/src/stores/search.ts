import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SearchParams, SearchResults, HotKeyword, SearchHistoryItem } from '@/types/search'
import { searchNews, fetchSearchSuggestions } from '@/api/search'
import { ElMessage } from 'element-plus'

export const useSearchStore = defineStore('search', () => {
  // 状态
  const searchResults = ref<SearchResults>({
    total: 0,
    items: [],
    facets: {
      categories: {},
      sources: {}
    }
  })

  const hotKeywords = ref<HotKeyword[]>([])
  const searchHistory = ref<SearchHistoryItem[]>([])
  const loading = ref(false)

  // 搜索参数
  const searchParams = ref<SearchParams>({
    keyword: '',
    category: '',
    source: '',
    dateRange: null,
    sortBy: 'relevance',
    order: 'desc',
    page: 1,
    pageSize: 20
  })

  // 获取搜索建议
  const fetchSuggestions = async (keyword: string) => {
    try {
      return await fetchSearchSuggestions(keyword)
    } catch (error) {
      ElMessage.error('获取搜索建议失败')
      return []
    }
  }

  // 执行搜索
  const search = async (params: Partial<SearchParams>) => {
    try {
      loading.value = true
      // 更新搜索参数
      Object.assign(searchParams.value, params)

      // 调用搜索 API
      const results = await searchNews(searchParams.value)
      searchResults.value = results

      // 更新搜索历史
      if (params.keyword) {
        addToSearchHistory(params.keyword)
      }
    } catch (error) {
      searchResults.value = {
        total: 0,
        items: [],
        facets: {
          categories: {},
          sources: {}
        }
      }
      ElMessage.error('搜索失败')
    } finally {
      loading.value = false
    }
  }

  // 更新搜索参数
  const updateSearchParams = (params: Partial<SearchParams>) => {
    Object.assign(searchParams.value, params)
  }

  // 添加搜索历史
  const addToSearchHistory = (keyword: string) => {
    const existingIndex = searchHistory.value.findIndex(
      item => item.keyword === keyword
    )

    if (existingIndex !== -1) {
      searchHistory.value.splice(existingIndex, 1)
    }

    searchHistory.value.unshift({
      keyword,
      timestamp: new Date().toISOString()
    })

    // 限制历史记录数量
    if (searchHistory.value.length > 10) {
      searchHistory.value.pop()
    }

    // 保存到本地存储
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory.value))
  }

  // 清空搜索历史
  const clearSearchHistory = () => {
    searchHistory.value = []
    localStorage.removeItem('searchHistory')
  }

  // 初始化
  const initialize = () => {
    // 从本地存储加载搜索历史
    const savedHistory = localStorage.getItem('searchHistory')
    if (savedHistory) {
      searchHistory.value = JSON.parse(savedHistory)
    }
  }

  return {
    searchResults,
    hotKeywords,
    searchHistory,
    loading,
    searchParams,
    fetchSuggestions,
    search,
    updateSearchParams,
    addToSearchHistory,
    clearSearchHistory,
    initialize
  }
}) 