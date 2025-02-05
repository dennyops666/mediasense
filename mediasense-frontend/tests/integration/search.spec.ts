import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import Search from '@/views/search/Search.vue'
import { useSearchStore } from '@/stores/search'
import { ElMessage } from 'element-plus'

vi.mock('element-plus')

describe('搜索流程集成测试', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/search',
        name: 'search',
        component: Search
      },
      {
        path: '/news/:id',
        name: 'news-detail'
      }
    ]
  })

  beforeEach(() => {
    vi.clearAllMocks()
    router.push('/search')
  })

  describe('搜索功能', () => {
    it('应该完成基本搜索流程', async () => {
      const wrapper = mount(Search, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useSearchStore()
      const mockResults = {
        total: 100,
        items: [
          {
            id: '1',
            title: '测试新闻1',
            summary: '摘要1',
            source: '来源1',
            publishTime: '2024-03-20T10:00:00Z'
          }
        ],
        facets: {
          categories: {
            '科技': 50,
            '财经': 30
          },
          sources: {
            '来源1': 40,
            '来源2': 35
          }
        }
      }

      // 模拟搜索结果
      vi.mocked(store.search).mockResolvedValueOnce(mockResults)

      // 输入搜索关键词
      await wrapper.find('.search-input').setValue('测试关键词')
      
      // 提交搜索
      await wrapper.find('form').trigger('submit.prevent')

      expect(store.search).toHaveBeenCalledWith(expect.objectContaining({
        keyword: '测试关键词'
      }))

      await wrapper.vm.$nextTick()

      // 验证结果显示
      const resultItems = wrapper.findAll('.search-result-item')
      expect(resultItems).toHaveLength(1)
      expect(resultItems[0].text()).toContain('测试新闻1')
    })

    it('应该正确处理搜索建议', async () => {
      const wrapper = mount(Search, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useSearchStore()
      const mockSuggestions = ['建议1', '建议2', '建议3']

      // 模拟搜索建议
      vi.mocked(store.fetchSuggestions).mockResolvedValueOnce(mockSuggestions)

      // 输入搜索关键词
      await wrapper.find('.search-input').setValue('测')

      // 等待防抖
      await new Promise(resolve => setTimeout(resolve, 300))

      expect(store.fetchSuggestions).toHaveBeenCalledWith('测')

      await wrapper.vm.$nextTick()

      // 验证建议显示
      const suggestions = wrapper.findAll('.suggestion-item')
      expect(suggestions).toHaveLength(3)
      expect(suggestions[0].text()).toBe('建议1')
    })
  })

  describe('过滤和排序', () => {
    it('应该正确应用过滤条件', async () => {
      const wrapper = mount(Search, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  searchResults: [],
                  facets: {
                    categories: {
                      '科技': 50
                    },
                    sources: {
                      '来源1': 40
                    }
                  }
                }
              }
            }),
            router
          ]
        }
      })

      const store = useSearchStore()

      // 选择分类
      await wrapper.find('.category-select').trigger('click')
      await wrapper.find('.category-option').trigger('click')

      expect(store.updateSearchParams).toHaveBeenCalledWith(expect.objectContaining({
        category: '科技'
      }))

      // 选择来源
      await wrapper.find('.source-select').trigger('click')
      await wrapper.find('.source-option').trigger('click')

      expect(store.updateSearchParams).toHaveBeenCalledWith(expect.objectContaining({
        source: '来源1'
      }))

      // 选择日期范围
      const datePicker = wrapper.findComponent({ name: 'el-date-picker' })
      await datePicker.vm.$emit('change', ['2024-03-01', '2024-03-20'])

      expect(store.updateSearchParams).toHaveBeenCalledWith(expect.objectContaining({
        dateRange: ['2024-03-01', '2024-03-20']
      }))
    })

    it('应该正确应用排序条件', async () => {
      const wrapper = mount(Search, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useSearchStore()

      // 选择排序方式
      await wrapper.find('.sort-select').trigger('click')
      await wrapper.find('.sort-option-date').trigger('click')

      expect(store.updateSearchParams).toHaveBeenCalledWith(expect.objectContaining({
        sortBy: 'date'
      }))

      // 切换排序顺序
      await wrapper.find('.order-select').trigger('click')
      await wrapper.find('.order-option-asc').trigger('click')

      expect(store.updateSearchParams).toHaveBeenCalledWith(expect.objectContaining({
        order: 'asc'
      }))
    })
  })

  describe('热门搜索和历史记录', () => {
    it('应该正确显示热门搜索词', async () => {
      const wrapper = mount(Search, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  hotKeywords: [
                    { keyword: '热词1', count: 100 },
                    { keyword: '热词2', count: 80 }
                  ]
                }
              }
            }),
            router
          ]
        }
      })

      const hotKeywords = wrapper.findAll('.hot-keyword')
      expect(hotKeywords).toHaveLength(2)
      expect(hotKeywords[0].text()).toContain('热词1')
    })

    it('应该正确显示搜索历史', async () => {
      const wrapper = mount(Search, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  searchHistory: [
                    { keyword: '历史1', timestamp: '2024-03-20T10:00:00Z' },
                    { keyword: '历史2', timestamp: '2024-03-19T10:00:00Z' }
                  ]
                }
              }
            }),
            router
          ]
        }
      })

      const historyItems = wrapper.findAll('.history-item')
      expect(historyItems).toHaveLength(2)
      expect(historyItems[0].text()).toContain('历史1')
    })

    it('应该正确清除搜索历史', async () => {
      const wrapper = mount(Search, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  searchHistory: [
                    { keyword: '历史1', timestamp: '2024-03-20T10:00:00Z' }
                  ]
                }
              }
            }),
            router
          ]
        }
      })

      const store = useSearchStore()
      vi.mocked(store.clearSearchHistory).mockResolvedValueOnce()

      await wrapper.find('.clear-history-btn').trigger('click')

      expect(store.clearSearchHistory).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('搜索历史已清除')
    })
  })

  describe('分页功能', () => {
    it('应该正确处理分页', async () => {
      const wrapper = mount(Search, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  searchResults: [],
                  total: 100
                }
              }
            }),
            router
          ]
        }
      })

      const store = useSearchStore()

      const pagination = wrapper.findComponent({ name: 'el-pagination' })
      
      // 切换页码
      await pagination.vm.$emit('current-change', 2)

      expect(store.search).toHaveBeenCalledWith(expect.objectContaining({
        page: 2
      }))

      // 切换每页条数
      await pagination.vm.$emit('size-change', 20)

      expect(store.search).toHaveBeenCalledWith(expect.objectContaining({
        pageSize: 20,
        page: 1
      }))
    })
  })

  describe('错误处理', () => {
    it('应该正确处理搜索失败', async () => {
      const wrapper = mount(Search, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn
            }),
            router
          ]
        }
      })

      const store = useSearchStore()
      vi.mocked(store.search).mockRejectedValueOnce(new Error('搜索失败'))

      await wrapper.find('.search-input').setValue('测试关键词')
      await wrapper.find('form').trigger('submit.prevent')

      expect(ElMessage.error).toHaveBeenCalledWith('搜索失败')
    })

    it('应该正确处理空结果', async () => {
      const wrapper = mount(Search, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                search: {
                  searchResults: [],
                  total: 0
                }
              }
            }),
            router
          ]
        }
      })

      const emptyState = wrapper.findComponent({ name: 'el-empty' })
      expect(emptyState.exists()).toBe(true)
      expect(emptyState.text()).toContain('暂无搜索结果')
    })
  })
}) 