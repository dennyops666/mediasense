import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import Search from '@/views/search/Search.vue'
import { useSearchStore } from '@/stores/search'
import { nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { ElMessage } from 'element-plus'

vi.mock('vue-router', () => ({
  useRouter: vi.fn()
}))

vi.mock('lodash-es', () => ({
  debounce: (fn: Function) => fn
}))

// Mock data
const mockSearchResults = [
  {
    id: 1,
    title: '测试新闻1',
    content: '这是测试新闻1的内容',
    source: '来源1',
    publishTime: '2024-03-20T10:00:00Z',
    score: 0.95
  },
  {
    id: 2,
    title: '测试新闻2',
    content: '这是测试新闻2的内容',
    source: '来源2',
    publishTime: '2024-03-20T11:00:00Z',
    score: 0.85
  }
]

describe('Search.vue', () => {
  let wrapper: any
  let store: any
  const mockRouter = {
    push: vi.fn()
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useSearchStore()
    vi.mocked(useRouter).mockReturnValue(mockRouter)
    
    wrapper = mount(Search, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              search: {
                results: mockSearchResults,
                suggestions: ['历史1', '历史2'],
                loading: false,
                error: null
              }
            }
          })
        ],
        stubs: {
          'el-input': {
            template: '<div class="el-input"><slot></slot></div>'
          },
          'el-select': {
            template: '<div class="el-select"><slot></slot></div>'
          },
          'el-option': true,
          'el-date-picker': true,
          'el-button': true,
          'el-card': {
            template: '<div class="el-card"><slot></slot></div>'
          }
        }
      }
    })
  })

  it('应该正确渲染搜索表单', () => {
    expect(wrapper.find('.search-form').exists()).toBe(true)
    expect(wrapper.find('.el-input').exists()).toBe(true)
    expect(wrapper.find('.el-button').exists()).toBe(true)
  })

  it('应该支持基本搜索', async () => {
    const searchInput = wrapper.find('.search-input input')
    await searchInput.setValue('测试')
    
    const searchButton = wrapper.find('.search-button')
    await searchButton.trigger('click')
    
    expect(store.search).toHaveBeenCalledWith({
      keyword: '测试',
      type: '',
      date: null
    })
  })

  it('应该显示搜索建议', async () => {
    const searchInput = wrapper.find('.search-input input')
    await searchInput.setValue('测试')
    await searchInput.trigger('input')
    
    expect(store.getSuggestions).toHaveBeenCalledWith('测试')
    
    const suggestions = wrapper.findAll('.suggestion-item')
    expect(suggestions).toHaveLength(2)
    expect(suggestions[0].text()).toBe('历史1')
  })

  it('应该支持类型筛选', async () => {
    const select = wrapper.find('.type-select')
    await select.setValue('news')
    await select.trigger('change')
    
    expect(store.search).toHaveBeenCalledWith(expect.objectContaining({
      type: 'news'
    }))
  })

  it('应该支持日期筛选', async () => {
    const datePicker = wrapper.find('.date-picker')
    await datePicker.setValue('2024-03-20')
    await datePicker.trigger('change')
    
    expect(store.search).toHaveBeenCalledWith(expect.objectContaining({
      date: '2024-03-20'
    }))
  })

  it('应该正确显示搜索结果', async () => {
    const items = wrapper.findAll('.search-result-item')
    expect(items).toHaveLength(2)
    expect(items[0].text()).toContain('测试新闻1')
    expect(items[0].find('.relevance-score').text()).toContain('0.95')
  })

  it('应该正确处理加载状态', async () => {
    store.$patch({ loading: true })
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('[loading="true"]').exists()).toBe(true)
  })

  it('应该正确处理错误状态', async () => {
    store.$patch({ error: '搜索失败' })
    await wrapper.vm.$nextTick()
    
    const errorMessage = wrapper.find('.error-message')
    expect(errorMessage.exists()).toBe(true)
    expect(errorMessage.text()).toContain('搜索失败')
  })

  it('应该支持分页', async () => {
    const pagination = wrapper.find('.el-pagination')
    await pagination.vm.$emit('current-change', 2)
    
    expect(store.search).toHaveBeenCalledWith(expect.objectContaining({
      page: 2
    }))
  })

  it('应该能跳转到搜索结果详情', async () => {
    store.$patch({
      searchResults: mockSearchResults
    })
    await nextTick()
    
    const resultItem = wrapper.find('.search-result-item')
    await resultItem.trigger('click')
    
    expect(mockRouter.push).toHaveBeenCalledWith('/detail/1')
  })

  it('应该显示搜索结果统计', async () => {
    store.$patch({
      searchResults: mockSearchResults,
      total: mockSearchResults.length
    })
    await nextTick()
    
    const stats = wrapper.find('.search-stats')
    expect(stats.exists()).toBe(true)
    expect(stats.text()).toContain('2')
  })

  it('应该显示相关性得分', async () => {
    store.$patch({
      searchResults: mockSearchResults
    })
    await nextTick()
    
    const scores = wrapper.findAll('.relevance-score')
    expect(scores).toHaveLength(2)
    expect(scores[0].text()).toContain('0.95')
  })

  describe('搜索历史', () => {
    it('应该显示搜索历史', async () => {
      const history = wrapper.findAll('.history-item')
      expect(history).toHaveLength(2)
      expect(history[0].text()).toContain('历史1')
    })

    it('应该能清空搜索历史', async () => {
      const clearButton = wrapper.find('.clear-history')
      await clearButton.trigger('click')
      
      expect(store.clearHistory).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('搜索历史已清空')
    })
  })
})