import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { nextTick } from 'vue'
import Search from '@/views/search/Search.vue'
import { useSearchStore } from '@/stores/search'
import { ElMessage } from 'element-plus'
import { vi, describe, it, expect, beforeEach } from 'vitest'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('Search.vue', () => {
  let wrapper
  let store

  const mockResults = [
    {
      id: '1',
      title: '测试新闻1',
      content: '测试内容1',
      source: '测试来源1',
      publishTime: '2024-03-20',
      relevanceScore: 0.95
    },
    {
      id: '2',
      title: '测试新闻2',
      content: '测试内容2',
      source: '测试来源2',
      publishTime: '2024-03-21',
      relevanceScore: 0.85
    }
  ]

  beforeEach(async () => {
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      clear: vi.fn()
    }
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock
    })

    const pinia = createTestingPinia({
      createSpy: vi.fn,
      initialState: {
        search: {
          results: [],
          loading: false,
          error: null,
          suggestions: [],
          total: 0
        }
      }
    })

    store = useSearchStore(pinia)
    store.search = vi.fn().mockResolvedValue({ items: mockResults, total: 2 })
    store.getSuggestions = vi.fn().mockResolvedValue(['建议1', '建议2'])
    store.clearHistory = vi.fn()

    wrapper = mount(Search, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-input': {
            template: '<input v-model="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue']
          },
          'el-button': {
            template: '<button @click="$emit(\'click\')"><slot/></button>'
          },
          'el-select': {
            template: '<select v-model="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot/></select>',
            props: ['modelValue']
          },
          'el-option': {
            template: '<option :value="value"><slot/></option>',
            props: ['value']
          },
          'el-date-picker': {
            template: '<input type="date" v-model="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue']
          },
          'el-loading': true,
          'el-pagination': true
        }
      }
    })

    await nextTick()
  })

  it('应该正确渲染搜索表单', () => {
    expect(wrapper.find('.search-form').exists()).toBe(true)
    expect(wrapper.find('.search-input').exists()).toBe(true)
    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('应该支持基本搜索', async () => {
    const input = wrapper.find('input')
    await input.setValue('测试关键词')
    
    const button = wrapper.find('button')
    await button.trigger('click')

    expect(store.search).toHaveBeenCalledWith({
      keyword: '测试关键词',
      type: '',
      date: null,
      page: 1,
      pageSize: 10
    })
  })

  it('应该显示搜索建议', async () => {
    const input = wrapper.find('input')
    await input.setValue('测试')
    await nextTick()

    expect(store.getSuggestions).toHaveBeenCalledWith('测试')
    
    // 模拟搜索建议返回
    wrapper.vm.suggestions = ['建议1', '建议2']
    await nextTick()
    
    const suggestions = wrapper.findAll('.suggestion-item')
    expect(suggestions).toHaveLength(2)
    expect(suggestions[0].text()).toBe('建议1')
  })

  it('应该支持类型筛选', async () => {
    const select = wrapper.find('select')
    await select.setValue('news')
    
    expect(store.search).toHaveBeenCalledWith({
      keyword: '',
      type: 'news',
      date: null,
      page: 1,
      pageSize: 10
    })
  })

  it('应该支持日期筛选', async () => {
    const datePicker = wrapper.find('input[type="date"]')
    await datePicker.setValue('2024-03-20')
    
    expect(store.search).toHaveBeenCalledWith({
      keyword: '',
      type: '',
      date: '2024-03-20',
      page: 1,
      pageSize: 10
    })
  })

  it('应该正确显示搜索结果', async () => {
    // 设置搜索结果
    wrapper.vm.results = mockResults
    wrapper.vm.total = 2
    await nextTick()

    const items = wrapper.findAll('.search-result-item')
    expect(items).toHaveLength(2)
    expect(items[0].text()).toContain('测试新闻1')
    expect(items[0].find('.relevance-score').text()).toContain('0.95')
  })

  it('应该正确处理加载状态', async () => {
    wrapper.vm.loading = true
    await nextTick()
    expect(wrapper.find('.loading').exists()).toBe(true)

    wrapper.vm.loading = false
    await nextTick()
    expect(wrapper.find('.loading').exists()).toBe(false)
  })

  it('应该正确处理错误状态', async () => {
    wrapper.vm.error = '搜索失败'
    await nextTick()
    expect(wrapper.find('.error-message').text()).toBe('搜索失败')
  })

  it('应该正确处理搜索历史', async () => {
    const history = ['历史1', '历史2']
    localStorage.getItem.mockReturnValue(JSON.stringify(history))
    
    // 重新挂载组件以触发 onMounted
    await wrapper.unmount()
    wrapper = mount(Search, {
      global: {
        plugins: [createTestingPinia({ createSpy: vi.fn })],
        stubs: {
          'el-input': true,
          'el-button': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true,
          'el-loading': true,
          'el-pagination': true
        }
      }
    })

    await nextTick()
    expect(wrapper.vm.searchHistory).toEqual(history)
  })

  it('应该正确处理详情查看', async () => {
    wrapper.vm.results = mockResults
    await nextTick()

    const item = wrapper.find('.search-result-item')
    await item.trigger('click')

    expect(wrapper.emitted('view-detail')).toBeTruthy()
    expect(wrapper.emitted('view-detail')[0]).toEqual(['1'])
  })

  it('应该正确处理分页', async () => {
    wrapper.vm.currentPage = 2
    await nextTick()
    
    expect(store.search).toHaveBeenCalledWith({
      keyword: '',
      type: '',
      date: null,
      page: 2,
      pageSize: 10
    })
  })
})