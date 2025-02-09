import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import SearchPage from '@/views/search/SearchPage.vue'
import SearchResult from '@/views/search/SearchResult.vue'
import { useSearchStore } from '@/stores/search'
import { ElMessage } from 'element-plus'

// 模拟 Element Plus
vi.mock('element-plus', () => ({
  default: {
    install: vi.fn()
  },
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  }
}))

const mockSearchResults = [
  {
    id: '1',
    title: '测试新闻1',
    content: '测试内容1',
    source: '来源1',
    url: 'http://example.com/1',
    publishTime: '2024-03-20T10:00:00Z',
    score: 0.95
  },
  {
    id: '2',
    title: '测试新闻2',
    content: '测试内容2',
    source: '来源2',
    url: 'http://example.com/2',
    publishTime: '2024-03-20T11:00:00Z',
    score: 0.85
  }
]

const mockSearchHistory = [
  {
    id: '1',
    keyword: '测试关键词1',
    timestamp: '2024-03-20T10:00:00Z',
    count: 5
  },
  {
    id: '2',
    keyword: '测试关键词2',
    timestamp: '2024-03-20T11:00:00Z',
    count: 3
  }
]

describe('搜索功能集成测试', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/search',
        name: 'search',
        component: SearchPage
      },
      {
        path: '/search/result',
        name: 'search-result',
        component: SearchResult
      }
    ]
  })

  beforeEach(async () => {
    vi.clearAllMocks()
    router.push('/search')
    await router.isReady()
  })

  describe('搜索界面', () => {
    it('应该正确显示搜索界面', async () => {
      const wrapper = mount(SearchPage, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  history: mockSearchHistory,
                  loading: false
                }
              }
            })
          ]
        }
      })

      const searchInput = wrapper.find('[data-test="search-input"]')
      const searchButton = wrapper.find('[data-test="search-button"]')
      const historyList = wrapper.findAll('[data-test="history-item"]')

      expect(searchInput.exists()).toBe(true)
      expect(searchButton.exists()).toBe(true)
      expect(historyList).toHaveLength(2)
    })

    it('应该能执行搜索', async () => {
      const wrapper = mount(SearchPage, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn
            })
          ]
        }
      })

      const store = useSearchStore()
      const searchInput = wrapper.find('[data-test="search-input"]')
      const searchButton = wrapper.find('[data-test="search-button"]')

      await searchInput.setValue('测试关键词')
      await searchButton.trigger('click')

      expect(store.search).toHaveBeenCalledWith('测试关键词')
      expect(router.currentRoute.value.path).toBe('/search/result')
    })
  })

  describe('搜索历史', () => {
    it('应该显示搜索历史', async () => {
      const wrapper = mount(SearchPage, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  history: mockSearchHistory,
                  loading: false
                }
              }
            })
          ]
        }
      })

      const historyItems = wrapper.findAll('[data-test="history-item"]')
      expect(historyItems[0].text()).toContain('测试关键词1')
      expect(historyItems[1].text()).toContain('测试关键词2')
    })

    it('应该能清空搜索历史', async () => {
      const wrapper = mount(SearchPage, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  history: mockSearchHistory,
                  loading: false
                }
              }
            })
          ]
        }
      })

      const store = useSearchStore()
      const clearButton = wrapper.find('[data-test="clear-history"]')
      await clearButton.trigger('click')

      expect(store.clearHistory).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('搜索历史已清空')
    })
  })

  describe('搜索结果', () => {
    it('应该显示搜索结果', async () => {
      const wrapper = mount(SearchResult, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  results: mockSearchResults,
                  loading: false,
                  keyword: '测试关键词'
                }
              }
            })
          ]
        }
      })

      const resultItems = wrapper.findAll('[data-test="result-item"]')
      expect(resultItems).toHaveLength(2)
      expect(resultItems[0].text()).toContain('测试新闻1')
      expect(resultItems[1].text()).toContain('测试新闻2')
    })

    it('应该能按相关度排序', async () => {
      const wrapper = mount(SearchResult, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  results: mockSearchResults,
                  loading: false,
                  keyword: '测试关键词'
                }
              }
            })
          ]
        }
      })

      const store = useSearchStore()
      const sortSelect = wrapper.find('[data-test="sort-select"]')
      await sortSelect.setValue('relevance')

      expect(store.sortResults).toHaveBeenCalledWith('relevance')
    })

    it('应该能按时间排序', async () => {
      const wrapper = mount(SearchResult, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  results: mockSearchResults,
                  loading: false,
                  keyword: '测试关键词'
                }
              }
            })
          ]
        }
      })

      const store = useSearchStore()
      const sortSelect = wrapper.find('[data-test="sort-select"]')
      await sortSelect.setValue('time')

      expect(store.sortResults).toHaveBeenCalledWith('time')
    })
  })

  describe('错误处理', () => {
    it('应该处理搜索失败', async () => {
      const wrapper = mount(SearchPage, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  error: '搜索失败',
                  loading: false
                }
              }
            })
          ]
        }
      })

      const store = useSearchStore()
      store.search.mockRejectedValue(new Error('搜索失败'))

      const searchInput = wrapper.find('[data-test="search-input"]')
      const searchButton = wrapper.find('[data-test="search-button"]')

      await searchInput.setValue('测试关键词')
      await searchButton.trigger('click')

      expect(ElMessage.error).toHaveBeenCalledWith('搜索失败')
    })

    it('应该显示无结果提示', async () => {
      const wrapper = mount(SearchResult, {
        global: {
          plugins: [
            router,
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  results: [],
                  loading: false,
                  keyword: '测试关键词'
                }
              }
            })
          ]
        }
      })

      const emptyState = wrapper.find('[data-test="empty-state"]')
      expect(emptyState.exists()).toBe(true)
      expect(emptyState.text()).toContain('未找到相关结果')
    })
  })
}) 