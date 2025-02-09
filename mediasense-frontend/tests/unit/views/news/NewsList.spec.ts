import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useNewsStore } from '@/stores/news'
import NewsList from '@/views/news/NewsList.vue'
import { nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { ElMessage } from 'element-plus'

// Mock Element Plus
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

vi.mock('vue-router', () => ({
  useRouter: vi.fn()
}))

// Mock data
const mockNewsList = [
  {
    id: 1,
    title: '测试新闻1',
    summary: '这是测试新闻1的摘要',
    source: '测试来源',
    publishTime: '2024-03-20T10:00:00Z',
    category: '科技',
    readCount: 100
  },
  {
    id: 2,
    title: '测试新闻2',
    summary: '这是测试新闻2的摘要',
    source: '测试来源',
    publishTime: '2024-03-20T11:00:00Z',
    category: '财经',
    readCount: 200
  }
]

describe('NewsList.vue', () => {
  let wrapper: any
  let store: any
  const mockRouter = {
    push: vi.fn().mockResolvedValue(undefined)
  }

  beforeEach(async () => {
    vi.mocked(useRouter).mockReturnValue(mockRouter)

    const pinia = createPinia()
    setActivePinia(pinia)

    store = useNewsStore()
    store.fetchNewsList = vi.fn().mockResolvedValue({
      items: mockNewsList,
      total: mockNewsList.length
    })
    store.fetchCategories = vi.fn().mockResolvedValue(['科技', '财经'])
    store.fetchSources = vi.fn().mockResolvedValue(['测试来源'])
    store.applyFilter = vi.fn()

    // 设置初始状态
    store.$patch({
      newsList: mockNewsList,
      total: mockNewsList.length,
      loading: false,
      error: null,
      categories: ['科技', '财经'],
      sources: ['测试来源'],
      filter: {
        page: 1,
        pageSize: 10,
        keyword: '',
        category: '',
        source: '',
        startDate: '',
        endDate: '',
        sortBy: 'publishTime',
        sortOrder: 'desc'
      }
    })

    // 创建组件
    wrapper = mount(NewsList, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              news: {
                list: mockNewsList,
                loading: false,
                error: null
              }
            }
          })
        ],
        stubs: {
          'el-card': {
            template: '<div class="el-card news-card" @click="$emit(\'click\')"><slot></slot></div>'
          },
          'el-button': {
            template: '<button class="el-button" :class="{ \'create-button\': type === \'primary\' }" @click="$emit(\'click\')"><slot></slot></button>',
            props: ['type']
          },
          'el-input': {
            template: '<div class="el-input"><input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" /><div class="el-input__suffix"><slot name="suffix"></slot></div></div>',
            props: ['modelValue']
          },
          'el-select': {
            template: '<select class="el-select" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot></slot></select>',
            props: ['modelValue']
          },
          'el-option': {
            template: '<option :value="value">{{ label }}</option>',
            props: ['value', 'label']
          },
          'el-date-picker': {
            template: '<input type="date" class="el-date-picker" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue']
          },
          'el-pagination': {
            template: '<div class="el-pagination"><button @click="$emit(\'current-change\', 2)">下一页</button></div>',
            emits: ['current-change', 'size-change']
          },
          'el-skeleton': {
            template: '<div class="el-skeleton"><slot></slot></div>'
          },
          'el-alert': {
            template: '<div class="el-alert" :title="title"><slot></slot></div>',
            props: ['title']
          },
          'el-empty': {
            template: '<div class="el-empty"><slot></slot></div>'
          },
          'el-form': {
            template: '<form class="el-form"><slot></slot></form>'
          },
          'el-form-item': {
            template: '<div class="el-form-item"><slot></slot></div>'
          },
          'el-icon': {
            template: '<i class="el-icon"><slot></slot></i>'
          },
          'router-link': {
            template: '<a><slot></slot></a>'
          },
          'el-table': {
            template: '<div class="el-table"><slot></slot></div>'
          },
          'el-table-column': {
            template: '<div class="el-table-column"><slot></slot></div>'
          },
          'el-tag': true
        },
        mocks: {
          $router: mockRouter
        }
      }
    })

    await nextTick()
  })

  it('应该在挂载时获取新闻列表', async () => {
    expect(store.fetchNewsList).toHaveBeenCalled()
    expect(store.fetchCategories).toHaveBeenCalled()
    expect(store.fetchSources).toHaveBeenCalled()
  })

  it('应该正确显示新闻列表', async () => {
    const newsCards = wrapper.findAll('.news-card')
    expect(newsCards).toHaveLength(2)
    
    const firstNews = newsCards[0]
    const secondNews = newsCards[1]
    
    expect(firstNews.exists()).toBe(true)
    expect(secondNews.exists()).toBe(true)
    
    expect(firstNews.text()).toContain('测试新闻1')
    expect(secondNews.text()).toContain('测试新闻2')
  })

  it('应该支持分页', async () => {
    const pagination = wrapper.find('.el-pagination button')
    expect(pagination.exists()).toBe(true)
    
    await pagination.trigger('click')
    
    expect(store.applyFilter).toHaveBeenCalledWith(expect.objectContaining({
      page: 2,
      pageSize: 10
    }))
  })

  it('应该支持分类筛选', async () => {
    const typeSelect = wrapper.find('.el-select')
    expect(typeSelect.exists()).toBe(true)
    
    await typeSelect.setValue('科技')
    await typeSelect.trigger('change')
    
    expect(store.applyFilter).toHaveBeenCalledWith(expect.objectContaining({
      category: '科技'
    }))
  })

  it('应该支持搜索', async () => {
    const searchInput = wrapper.find('.el-input input')
    expect(searchInput.exists()).toBe(true)
    
    await searchInput.setValue('测试')
    await searchInput.trigger('input')
    
    expect(store.applyFilter).toHaveBeenCalledWith(expect.objectContaining({
      keyword: '测试'
    }))
  })

  it('应该能跳转到新闻详情', async () => {
    const newsCard = wrapper.find('.news-card')
    expect(newsCard.exists()).toBe(true)
    
    await newsCard.trigger('click')
    
    expect(mockRouter.push).toHaveBeenCalledWith({
      name: 'news-detail',
      params: { id: '1' }
    })
  })

  it('应该能创建新闻', async () => {
    const createButton = wrapper.find('.create-button')
    expect(createButton.exists()).toBe(true)
    
    await createButton.trigger('click')
    
    expect(mockRouter.push).toHaveBeenCalledWith({
      name: 'news-create'
    })
  })

  it('应该正确处理加载状态', async () => {
    store.$patch({ loading: true })
    await nextTick()
    
    const skeleton = wrapper.find('.el-skeleton')
    expect(skeleton.exists()).toBe(true)

    store.$patch({ loading: false })
    await nextTick()
    expect(skeleton.exists()).toBe(false)
  })

  it('应该正确处理错误状态', async () => {
    store.$patch({ error: '获取新闻列表失败' })
    await nextTick()

    const errorMessage = wrapper.find('.el-alert')
    expect(errorMessage.exists()).toBe(true)
    expect(errorMessage.attributes('title')).toBe('获取新闻列表失败')
  })
}) 