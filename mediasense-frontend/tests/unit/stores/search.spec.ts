import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSearchStore } from '@/stores/search'
import * as searchApi from '@/api/search'
import { ElMessage } from 'element-plus'

vi.mock('@/api/search')
vi.mock('element-plus')

describe('Search Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const store = useSearchStore()
      expect(store.searchResults).toEqual({
        total: 0,
        items: [],
        facets: {
          categories: {},
          sources: {}
        }
      })
      expect(store.hotKeywords).toEqual([])
      expect(store.searchHistory).toEqual([])
      expect(store.loading).toBe(false)
    })
  })

  describe('搜索功能', () => {
    it('应该成功执行搜索并更新状态', async () => {
      const mockResponse = {
        total: 2,
        items: [
          { id: 1, title: 'Test News 1' },
          { id: 2, title: 'Test News 2' }
        ],
        facets: {
          categories: { tech: 2 },
          sources: { source1: 1, source2: 1 }
        }
      }

      vi.mocked(searchApi.searchNews).mockResolvedValue(mockResponse)

      const store = useSearchStore()
      await store.search({ keyword: 'test' })

      expect(store.searchResults).toEqual(mockResponse)
      expect(store.loading).toBe(false)
    })

    it('应该处理搜索失败', async () => {
      const error = new Error('搜索失败')
      vi.mocked(searchApi.searchNews).mockRejectedValue(error)

      const store = useSearchStore()
      await store.search({ keyword: 'test' })

      expect(store.searchResults).toEqual({
        total: 0,
        items: [],
        facets: {
          categories: {},
          sources: {}
        }
      })
      expect(store.loading).toBe(false)
      expect(ElMessage.error).toHaveBeenCalledWith('搜索失败')
    })
  })

  describe('搜索建议', () => {
    it('应该成功获取搜索建议', async () => {
      const mockSuggestions = ['suggestion1', 'suggestion2']
      vi.mocked(searchApi.fetchSearchSuggestions).mockResolvedValue(mockSuggestions)

      const store = useSearchStore()
      const suggestions = await store.fetchSuggestions('test')

      expect(suggestions).toEqual(mockSuggestions)
    })

    it('应该处理获取建议失败', async () => {
      const error = new Error('获取建议失败')
      vi.mocked(searchApi.fetchSearchSuggestions).mockRejectedValue(error)

      const store = useSearchStore()
      const suggestions = await store.fetchSuggestions('test')

      expect(suggestions).toEqual([])
      expect(ElMessage.error).toHaveBeenCalledWith('获取搜索建议失败')
    })
  })

  describe('搜索历史', () => {
    it('应该正确添加搜索历史', () => {
      const store = useSearchStore()
      const keyword = 'test keyword'
      
      store.addToSearchHistory(keyword)
      
      expect(store.searchHistory[0].keyword).toBe(keyword)
      expect(store.searchHistory).toHaveLength(1)
    })

    it('应该移除重复的搜索历史', () => {
      const store = useSearchStore()
      const keyword = 'test keyword'
      
      store.addToSearchHistory(keyword)
      store.addToSearchHistory(keyword)
      
      expect(store.searchHistory).toHaveLength(1)
      expect(store.searchHistory[0].keyword).toBe(keyword)
    })

    it('应该限制搜索历史数量', () => {
      const store = useSearchStore()
      
      for (let i = 0; i < 15; i++) {
        store.addToSearchHistory(`keyword ${i}`)
      }
      
      expect(store.searchHistory).toHaveLength(10)
      expect(store.searchHistory[0].keyword).toBe('keyword 14')
    })

    it('应该正确清空搜索历史', () => {
      const store = useSearchStore()
      store.addToSearchHistory('test keyword')
      
      store.clearSearchHistory()
      
      expect(store.searchHistory).toHaveLength(0)
    })
  })

  describe('参数更新', () => {
    it('应该正确更新搜索参数', () => {
      const store = useSearchStore()
      const newParams = {
        category: 'tech',
        source: 'source1',
        sortBy: 'date' as const,
        order: 'asc' as const
      }
      
      store.updateSearchParams(newParams)
      
      expect(store.searchParams.category).toBe(newParams.category)
      expect(store.searchParams.source).toBe(newParams.source)
      expect(store.searchParams.sortBy).toBe(newParams.sortBy)
      expect(store.searchParams.order).toBe(newParams.order)
    })
  })
}) 