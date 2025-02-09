import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useSearchStore } from '@/stores/search'
import { ElMessage } from 'element-plus'
import * as searchApi from '@/api/search'

vi.mock('@/api/search')
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

describe('Search Store', () => {
  let store: ReturnType<typeof useSearchStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useSearchStore()
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      expect(store.searchResults).toEqual([])
      expect(store.total).toBe(0)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.searchHistory).toEqual([])
      expect(store.suggestions).toEqual([])
      expect(store.searchTime).toBe(0)
    })
  })

  describe('搜索功能', () => {
    const mockSearchParams = {
      keyword: '测试',
      type: 'news',
      page: 1,
      pageSize: 10
    }

    const mockSearchResponse = {
      items: [
        { id: 1, title: '测试新闻1' },
        { id: 2, title: '测试新闻2' }
      ],
      total: 2
    }

    it('应该成功执行搜索并更新状态', async () => {
      vi.mocked(searchApi.searchNews).mockResolvedValue(mockSearchResponse)

      await store.search(mockSearchParams)

      expect(store.searchResults).toEqual(mockSearchResponse.items)
      expect(store.total).toBe(mockSearchResponse.total)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.searchHistory).toContain(mockSearchParams.keyword)
    })

    it('应该处理搜索失败', async () => {
      const error = new Error('搜索失败')
      vi.mocked(searchApi.searchNews).mockRejectedValue(error)

      await store.search(mockSearchParams)

      expect(store.searchResults).toEqual([])
      expect(store.total).toBe(0)
      expect(store.loading).toBe(false)
      expect(store.error).toBe('搜索失败')
    })
  })

  describe('搜索建议', () => {
    const mockSuggestions = ['建议1', '建议2']

    it('应该成功获取搜索建议', async () => {
      vi.mocked(searchApi.fetchSearchSuggestions).mockResolvedValue(mockSuggestions)

      await store.getSuggestions('测试')

      expect(store.suggestions).toEqual(mockSuggestions)
    })

    it('应该处理获取建议失败', async () => {
      vi.mocked(searchApi.fetchSearchSuggestions).mockRejectedValue(new Error())

      await store.getSuggestions('测试')

      expect(store.suggestions).toEqual([])
    })
  })

  describe('搜索历史', () => {
    const mockHistory = ['历史1', '历史2']

    it('应该正确获取搜索历史', async () => {
      vi.mocked(searchApi.getSearchHistory).mockResolvedValue(mockHistory)

      await store.getHistory()

      expect(store.searchHistory).toEqual(mockHistory)
    })

    it('应该正确清空搜索历史', async () => {
      vi.mocked(searchApi.clearSearchHistory).mockResolvedValue(undefined)

      await store.clearHistory()

      expect(store.searchHistory).toEqual([])
      expect(ElMessage.success).toHaveBeenCalledWith('搜索历史已清空')
    })

    it('应该处理获取历史失败', async () => {
      vi.mocked(searchApi.getSearchHistory).mockRejectedValue(new Error())

      await store.getHistory()

      expect(store.searchHistory).toEqual([])
    })

    it('应该处理清空历史失败', async () => {
      vi.mocked(searchApi.clearSearchHistory).mockRejectedValue(new Error())

      await store.clearHistory()

      expect(ElMessage.error).toHaveBeenCalledWith('清空搜索历史失败')
    })
  })

  describe('历史记录管理', () => {
    it('应该能添加搜索历史', async () => {
      const keyword = '新关键词'
      await store.addToHistory(keyword)
      expect(store.searchHistory).toContain(keyword)
    })

    it('应该限制历史记录数量', async () => {
      for (let i = 0; i < 12; i++) {
        await store.addToHistory(`关键词${i}`)
      }
      expect(store.searchHistory.length).toBeLessThanOrEqual(10)
    })

    it('应该避免重复添加', async () => {
      const keyword = '重复关键词'
      await store.addToHistory(keyword)
      await store.addToHistory(keyword)
      expect(store.searchHistory.filter(h => h === keyword).length).toBe(1)
    })
  })
}) 