import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory } from 'vue-router'
import NewsList from '@/views/news/NewsList.vue'
import { useNewsStore } from '@/stores/news'
import type { News } from '@/types/news'

const mockNews: News[] = [
  {
    id: '1',
    title: '测试新闻标题1',
    content: '测试新闻内容1',
    author: '测试作者1',
    publishTime: '2024-01-01 12:00:00',
    source: '测试来源1',
    category: '科技',
    tags: ['标签1', '标签2'],
    views: 100
  },
  {
    id: '2',
    title: '测试新闻标题2',
    content: '测试新闻内容2',
    author: '测试作者2',
    publishTime: '2024-01-02 12:00:00',
    source: '测试来源2',
    category: '科技',
    tags: ['标签3', '标签4'],
    views: 200
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/news/:id',
      name: 'NewsDetail',
      component: () => import('@/views/news/NewsDetail.vue')
    }
  ]
})

describe('NewsList 组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const createWrapper = () => {
    return mount(NewsList, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              news: {
                newsList: mockNews,
                total: mockNews.length,
                loading: false,
                error: null,
                categories: ['科技', '财经', '体育'],
                sources: ['测试来源1', '测试来源2']
              }
            }
          }),
          router
        ]
      }
    })
  }

  it('应该在挂载时获取新闻列表', async () => {
    const wrapper = createWrapper()
    const store = useNewsStore()
    await wrapper.vm.$nextTick()

    expect(store.fetchNewsList).toHaveBeenCalled()
    expect(store.fetchCategories).toHaveBeenCalled()
    expect(store.fetchSources).toHaveBeenCalled()
  })

  it('应该正确显示新闻列表', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    const newsCards = wrapper.findAll('.news-card')
    expect(newsCards).toHaveLength(2)
    
    const firstNews = newsCards[0]
    expect(firstNews.text()).toContain('测试新闻标题1')
    expect(firstNews.text()).toContain('测试作者1')
    expect(firstNews.text()).toContain('测试来源1')
  })

  it('应该支持分页', async () => {
    const wrapper = createWrapper()
    const store = useNewsStore()
    await wrapper.vm.$nextTick()

    const pagination = wrapper.find('.el-pagination__next')
    await pagination.trigger('click')
    
    expect(store.applyFilter).toHaveBeenCalledWith(expect.objectContaining({
      page: 2,
      pageSize: 10
    }))
  })

  it('应该支持分类筛选', async () => {
    const wrapper = createWrapper()
    const store = useNewsStore()
    await wrapper.vm.$nextTick()

    const typeSelect = wrapper.find('[data-test="category-select"]')
    await typeSelect.setValue('科技')
    
    expect(store.applyFilter).toHaveBeenCalledWith(expect.objectContaining({
      category: '科技'
    }))
  })

  it('应该支持搜索', async () => {
    const wrapper = createWrapper()
    const store = useNewsStore()
    await wrapper.vm.$nextTick()

    const searchInput = wrapper.find('[data-test="search-input"]')
    await searchInput.setValue('测试')
    
    expect(store.applyFilter).toHaveBeenCalledWith(expect.objectContaining({
      keyword: '测试'
    }))
  })

  it('应该能跳转到新闻详情', async () => {
    const wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    const newsCard = wrapper.find('.news-card')
    expect(newsCard.exists()).toBe(true)
    
    await newsCard.trigger('click')
    expect(router.currentRoute.value.path).toBe('/news/1')
  })

  it('应该正确处理加载状态', async () => {
    const wrapper = createWrapper()
    const store = useNewsStore()
    store.$patch({ loading: true })
    await wrapper.vm.$nextTick()
    
    const skeleton = wrapper.find('.el-skeleton')
    expect(skeleton.exists()).toBe(true)

    store.$patch({ loading: false })
    await wrapper.vm.$nextTick()
    expect(skeleton.exists()).toBe(false)
  })

  it('应该正确处理错误状态', async () => {
    const wrapper = createWrapper()
    const store = useNewsStore()
    store.$patch({ error: '获取新闻列表失败' })
    await wrapper.vm.$nextTick()

    const errorMessage = wrapper.find('.el-alert')
    expect(errorMessage.exists()).toBe(true)
    expect(errorMessage.attributes('title')).toBe('获取新闻列表失败')
  })
}) 